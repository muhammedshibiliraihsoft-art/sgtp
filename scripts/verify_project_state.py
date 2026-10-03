#!/usr/bin/env python3
"""Validate SGTP repository state and current-state documentation.

This module intentionally uses only the Python standard library.  It checks
repository facts and a small, explicit set of current-state claims; historical
references remain valid when they are labelled as historical.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence


PHASE_STATUS_RE = re.compile(
    r"\bPhase\s+(?P<phase>\d+)\s+(?:is\s+)?"
    r"(?P<status>complete|completed|active|in progress|not started)\b",
    re.IGNORECASE,
)
TASK_RE = re.compile(
    r"\b(?:PRE-P3-\d{2}(?:-[A-Z0-9]+)*|"
    r"GARMENT-(?:FAMILIES|VARIANTS)-\d{2}|"
    r"[A-Z]\d{1,2}-\d{2}[A-Z]?(?:-[A-Z0-9]+)*)\b"
)
TEST_COUNT_RE = re.compile(
    r"\b(?P<count>\d+)\s+tests?\s+(?:verified\s+)?" r"(?:pass|passed|passing|green)\b",
    re.IGNORECASE,
)
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


GitRunner = Callable[[Sequence[str]], str]


class ProjectStateValidator:
    """Perform deterministic checks against one repository root."""

    def __init__(
        self,
        root: Path,
        *,
        git_runner: GitRunner | None = None,
        test_discoverer: Callable[[], int | None] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.result = ValidationResult()
        self._git_runner = git_runner or self._run_git
        self._test_discoverer = test_discoverer or self.discover_tests

    def _run_git(self, args: Sequence[str]) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        return completed.stdout.strip()

    def read(self, relative: str) -> str:
        path = self.root / relative
        return (
            path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        )

    @staticmethod
    def _normal_status(value: str) -> str:
        value = value.lower()
        return "complete" if value == "completed" else value

    def _current_section(self, text: str, heading: str) -> str:
        match = re.search(
            rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
        return match.group(1) if match else ""

    def phase_facts(self, relative: str) -> dict[int, str]:
        text = self.read(relative)
        if relative.endswith("HANDOFF.md"):
            text = self._current_section(text, "Current phase")
        elif relative.endswith("PROJECT_STATE.md"):
            text = self._current_section(text, "Status")
        facts: dict[int, str] = {}
        for line in text.splitlines():
            if "historical" in line.lower():
                continue
            for match in PHASE_STATUS_RE.finditer(line):
                facts[int(match.group("phase"))] = self._normal_status(
                    match.group("status")
                )
            if re.search(r"Phase\s+3[^\n]*NOT STARTED", line, re.IGNORECASE):
                facts[3] = "not started"
        return facts

    def current_task(self, relative: str) -> str | None:
        text = self.read(relative)
        if relative.endswith("PROJECT_STATE.md"):
            section = next(
                (line for line in text.splitlines() if "Current task:" in line),
                "",
            )
        elif relative.endswith("HANDOFF.md"):
            section = self.current_handoff_section() or self._current_section(
                text, "Current task"
            )
        else:
            section = self._current_section(text, "Current task")
        match = TASK_RE.search(section)
        return match.group(0) if match else None

    def current_handoff_section(self) -> str:
        match = re.search(
            r"^##\s+Current handoff[^\n]*\n([\s\S]*?)(?=^##\s+|\Z)",
            self.read("docs/HANDOFF.md"),
            re.MULTILINE | re.IGNORECASE,
        )
        return match.group(0) if match else ""

    def discover_tests(self) -> int | None:
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--collect-only",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                ],
                cwd=self.root,
                check=False,
                capture_output=True,
                text=True,
                timeout=90,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        output = f"{completed.stdout}\n{completed.stderr}"
        matches = re.findall(r"(?:collected|tests collected)\s+(\d+)", output)
        if not matches:
            matches = re.findall(r"(\d+)\s+tests? collected", output)
        return int(matches[-1]) if matches else None

    def check_phase_and_task_state(self) -> None:
        state = self.phase_facts("docs/PROJECT_STATE.md")
        handoff = self.phase_facts("docs/HANDOFF.md")
        for phase in sorted(set(state) | set(handoff)):
            if phase in state and phase in handoff and state[phase] != handoff[phase]:
                self.result.error(
                    f"Phase {phase} disagrees: PROJECT_STATE={state[phase]}, "
                    f"HANDOFF={handoff[phase]}."
                )
        self.result.facts["phase_state"] = ", ".join(
            f"Phase {phase}={status}" for phase, status in sorted(state.items())
        )

        state_task = self.current_task("docs/PROJECT_STATE.md")
        handoff_task = self.current_task("docs/HANDOFF.md")
        if state_task and handoff_task and state_task != handoff_task:
            self.result.error(
                f"Current task disagrees: PROJECT_STATE={state_task}, "
                f"HANDOFF={handoff_task}."
            )
        if state_task:
            self.result.facts["current_task"] = state_task
            for relative in ("docs/PROJECT_STATE.md", "docs/HANDOFF.md"):
                section = self._current_section(self.read(relative), "Current task")
                if re.search(
                    rf"{re.escape(state_task)}[^\n]*(?:awaiting confirmation|not started)",
                    section,
                    re.IGNORECASE,
                ):
                    self.result.error(
                        f"Current task {state_task} is described as incomplete in {relative}."
                    )

        phase3_active = state.get(3) in {
            "active",
            "in progress",
            "complete",
        } or handoff.get(3) in {"active", "in progress", "complete"}
        if phase3_active:
            activation_marker = re.compile(r"\bCONFIRM\s+PHASE\s+3\b", re.IGNORECASE)
            for relative, heading in (
                ("docs/PROJECT_STATE.md", "Status"),
                ("docs/HANDOFF.md", "Current phase"),
            ):
                section = self._current_section(self.read(relative), heading)
                if not activation_marker.search(section):
                    self.result.error(
                        f"Phase 3 is active but explicit activation is not recorded in {relative}."
                    )

    def check_test_count(self) -> None:
        claims: list[int] = []
        sections = (
            ("docs/PROJECT_STATE.md", "Current Verification Results"),
            ("docs/HANDOFF.md", "Tests and checks"),
        )
        for relative, heading in sections:
            for line in self._current_section(
                self.read(relative), heading
            ).splitlines():
                match = TEST_COUNT_RE.search(line)
                if match:
                    claims.append(int(match.group("count")))
        actual = self._test_discoverer()
        if actual is not None:
            self.result.facts["discovered_tests"] = str(actual)
            if claims and any(claim != actual for claim in claims):
                self.result.error(
                    f"Current test-count claim(s) {sorted(set(claims))} "
                    f"do not match discovered count {actual}."
                )
        else:
            self.result.warning(
                "Test discovery unavailable; documented test count was not independently checked."
            )

    def check_stale_commit_claims(self) -> None:
        for relative in (
            "docs/PROJECT_STATE.md",
            "docs/HANDOFF.md",
            "docs/ARCHITECTURE.md",
        ):
            for number, line in enumerate(self.read(relative).splitlines(), start=1):
                lowered = line.lower()
                if (
                    "historical" in lowered
                    or "previous" in lowered
                    or "initial" in lowered
                ):
                    continue
                if not re.search(r"(?:current|latest|authoritative|head)", lowered):
                    continue
                shas = SHA_RE.findall(line)
                if shas:
                    self.result.error(
                        f"{relative}:{number} stores a current/latest commit reference; derive HEAD from Git."
                    )

    def check_git_state(self) -> None:
        try:
            head = self._git_runner(["rev-parse", "HEAD"])
            branch = self._git_runner(["branch", "--show-current"])
            status = self._git_runner(["status", "--porcelain"])
        except (OSError, subprocess.SubprocessError) as exc:
            self.result.error(f"Unable to inspect Git state: {exc}")
            return
        self.result.facts.update(
            {
                "head": head,
                "branch": branch or "(detached)",
                "working_tree": "DIRTY" if status else "CLEAN",
            }
        )
        if status:
            self.result.warning(
                "Working tree is DIRTY; review local modifications before committing."
            )

        try:
            remote_line = self._git_runner(["ls-remote", "origin", "refs/heads/main"])
            remote_head = remote_line.split()[0]
            self.result.facts["origin_main"] = remote_head
            if remote_head == head:
                relation = "PARITY"
            else:
                try:
                    counts = self._git_runner(
                        [
                            "rev-list",
                            "--left-right",
                            "--count",
                            f"{head}...{remote_head}",
                        ]
                    )
                    ahead, behind = (int(value) for value in counts.split())
                    relation = (
                        "DIVERGED"
                        if ahead and behind
                        else "AHEAD" if ahead else "BEHIND"
                    )
                except (OSError, ValueError, subprocess.SubprocessError):
                    relation = "REMOTE DIFFERENT (ahead/behind unavailable)"
            self.result.facts["remote_relation"] = relation
        except (OSError, subprocess.SubprocessError, IndexError):
            self.result.facts["remote_relation"] = "REMOTE UNAVAILABLE"
            self.result.warning("Remote origin/main could not be verified.")

    def check_phase3_surface(self) -> None:
        forbidden = (
            "backend/apps/shops",
            "backend/apps/clients",
            "backend/apps/catalog",
            "backend/apps/works",
            "backend/apps/billing",
            "apps/shops",
            "apps/clients",
            "apps/catalog",
            "apps/works",
            "apps/billing",
        )
        present = [path for path in forbidden if (self.root / path).exists()]
        state = self.phase_facts("docs/PROJECT_STATE.md")
        handoff = self.phase_facts("docs/HANDOFF.md")
        phase4_is_activated_consistently = (
            state.get(4) == "active"
            and handoff.get(4) == "active"
            and re.search(
                r"\bCONFIRM\s+PHASE\s+4\b",
                self._current_section(self.read("docs/PROJECT_STATE.md"), "Status"),
                re.IGNORECASE,
            )
            and re.search(
                r"\bCONFIRM\s+PHASE\s+4\b",
                self._current_section(self.read("docs/HANDOFF.md"), "Current phase"),
                re.IGNORECASE,
            )
        )
        if phase4_is_activated_consistently:
            current_handoff_text = self.current_handoff_section()
            # A task-specific confirmation is required before its business app
            # may appear; Phase activation alone never unlocks future modules.
            allowed = {"apps/clients"}
            state_task = self.current_task("docs/PROJECT_STATE.md")
            handoff_task = self.current_task("docs/HANDOFF.md")
            if (
                state_task == handoff_task == "T4-02"
                and re.search(
                    r"\bCONFIRM\s+TASK\s+T4-02\b",
                    self.read("docs/PROJECT_STATE.md"),
                    re.IGNORECASE,
                )
                and re.search(
                    r"\bCONFIRM\s+TASK\s+T4-02\b",
                    self.read("docs/HANDOFF.md"),
                    re.IGNORECASE,
                )
            ):
                allowed.add("apps/catalog")
            if (
                state_task == handoff_task == "T4-03"
                and re.search(
                    r"\bCONFIRM\s+TASK\s+T4-03\b",
                    self._current_section(self.read("docs/PROJECT_STATE.md"), "Status"),
                    re.IGNORECASE,
                )
                and re.search(
                    r"\bCONFIRM\s+TASK\s+T4-03\b",
                    current_handoff_text,
                    re.IGNORECASE,
                )
            ):
                allowed.add("apps/catalog")
            if (
                state_task == handoff_task == "T4-03A"
                and re.search(
                    r"\bCONFIRM\s+TASK\s+T4-03A\b",
                    self._current_section(self.read("docs/PROJECT_STATE.md"), "Status"),
                    re.IGNORECASE,
                )
                and re.search(
                    r"\bCONFIRM\s+TASK\s+T4-03A\b",
                    current_handoff_text,
                    re.IGNORECASE,
                )
            ):
                allowed.add("apps/catalog")
            if (
                state_task == handoff_task == "GARMENT-FAMILIES-01"
                and re.search(
                    r"\bCONFIRM\s+TASK\s+GARMENT-FAMILIES-01\b",
                    self._current_section(self.read("docs/PROJECT_STATE.md"), "Status"),
                    re.IGNORECASE,
                )
                and re.search(
                    r"\bCONFIRM\s+TASK\s+GARMENT-FAMILIES-01\b",
                    current_handoff_text,
                    re.IGNORECASE,
                )
            ):
                allowed.add("apps/catalog")
            if (
                state_task == handoff_task == "GARMENT-VARIANTS-01"
                and re.search(
                    r"\bCONFIRM\s+TASK\s+GARMENT-VARIANTS-01\b",
                    self._current_section(self.read("docs/PROJECT_STATE.md"), "Status"),
                    re.IGNORECASE,
                )
                and re.search(
                    r"\bCONFIRM\s+TASK\s+GARMENT-VARIANTS-01\b",
                    current_handoff_text,
                    re.IGNORECASE,
                )
            ):
                allowed.add("apps/catalog")
            # A later frontend-only task may be the current handoff after the
            # backend Catalog foundation is already complete. Preserve the
            # guard for new/unapproved modules while recognizing that
            # explicitly approved, completed foundation in both canonical docs.
            if (
                re.search(
                    r"(?im)^\s*-\s.*\bT4-03A\b.*\bCOMPLETE\b",
                    self._current_section(self.read("docs/PROJECT_STATE.md"), "Status"),
                    re.IGNORECASE,
                )
                and re.search(
                    r"\bCONFIRM\s+TASK\s+T4-03A\b",
                    self.read("docs/PROJECT_STATE.md"),
                    re.IGNORECASE,
                )
                and re.search(
                    r"\bCONFIRM\s+TASK\s+T4-03A\b",
                    self.read("docs/HANDOFF.md"),
                    re.IGNORECASE,
                )
            ):
                allowed.add("apps/catalog")
            present = [path for path in present if path not in allowed]
        if present:
            self.result.error(
                "Business module paths are outside the currently authorized phase/task: "
                + ", ".join(present)
            )

    def check_duplicate_current_state(self) -> None:
        relative = "docs/PROJECT_STATE.md"
        headings = re.findall(
            r"^##\s+(Status|Implementation Status)\s*$",
            self.read(relative),
            re.IGNORECASE | re.MULTILINE,
        )
        if len(headings) > 1:
            self.result.warning(
                f"{relative} contains {len(headings)} current-state/status sections; "
                "keep one canonical current-state section where practical."
            )

    def check_product_naming(self) -> None:
        decisions = self.read("docs/DECISIONS.md").lower()
        if not re.search(
            r"public company/product name has\s+not been finalized", decisions
        ):
            self.result.warning(
                "Naming decision rule is not explicitly recorded in DECISIONS.md."
            )
        for relative in ("AGENTS.md", "docs", "README.md"):
            paths: Iterable[Path]
            base = self.root / relative
            paths = base.rglob("*.md") if base.is_dir() else (base,)
            for path in paths:
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                except (OSError, UnicodeDecodeError):
                    continue
                if re.search(
                    r"public\s+(?:product|company|brand)\s*(?:name)?\s*[:=]",
                    text,
                    re.IGNORECASE,
                ):
                    self.result.error(
                        f"{path.relative_to(self.root)} declares an unapproved public brand."
                    )
                if re.search(
                    r"production\s+(?:domain|hostname|url)\s*[:=]", text, re.IGNORECASE
                ):
                    self.result.error(
                        f"{path.relative_to(self.root)} declares an unapproved production endpoint."
                    )

    def check_line_endings(self) -> None:
        attrs = self.root / ".gitattributes"
        if not attrs.exists() or "eol=lf" not in attrs.read_text(encoding="utf-8"):
            self.result.error(
                ".gitattributes does not enforce LF normalization for text files."
            )
        try:
            output = self._git_runner(["ls-files", "--eol"])
        except (OSError, subprocess.SubprocessError) as exc:
            self.result.error(f"Unable to inspect Git line-ending metadata: {exc}")
            return
        bad = []
        for line in output.splitlines():
            if "i/crlf" in line.lower() or "attr/eol=crlf" in line.lower():
                bad.append(line)
        if bad:
            self.result.error("Tracked text files have non-LF index line endings.")

    def run(self) -> ValidationResult:
        self.check_phase_and_task_state()
        self.check_test_count()
        self.check_stale_commit_claims()
        self.check_git_state()
        self.check_phase3_surface()
        self.check_duplicate_current_state()
        self.check_product_naming()
        self.check_line_endings()
        return self.result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args(argv)
    result = ProjectStateValidator(args.root).run()
    for key, value in result.facts.items():
        print(f"FACT {key}: {value}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")
    print(f"RESULT: {'PASS' if result.ok else 'FAIL'}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
