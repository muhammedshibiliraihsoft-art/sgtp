from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.verify_project_state import ProjectStateValidator


class FakeGit:
    def __init__(self, *, status="", remote="head", counts="0 0", remote_error=False):
        self.status = status
        self.remote = remote
        self.counts = counts
        self.remote_error = remote_error

    def __call__(self, args):
        command = " ".join(args)
        if args[:2] == ["rev-parse", "HEAD"]:
            return "head"
        if args[:2] == ["branch", "--show-current"]:
            return "main"
        if args[:2] == ["status", "--porcelain"]:
            return self.status
        if args[:2] == ["ls-remote", "origin"]:
            if self.remote_error:
                raise OSError("remote unavailable")
            return f"{self.remote}\trefs/heads/main"
        if args[:2] == ["rev-list", "--left-right"]:
            return self.counts
        if args[:2] == ["ls-files", "--eol"]:
            return "i/lf    w/lf attr/text=auto eol=lf\tdocs/PROJECT_STATE.md"
        raise AssertionError(f"Unexpected git command: {command}")


def make_repo(project_state: str, handoff: str, *, naming: str = "") -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "docs").mkdir()
    (root / "docs/PROJECT_STATE.md").write_text(project_state, encoding="utf-8")
    (root / "docs/HANDOFF.md").write_text(handoff, encoding="utf-8")
    (root / "docs/DECISIONS.md").write_text(
        "The public product/company name has not been finalized.", encoding="utf-8"
    )
    (root / ".gitattributes").write_text("* text=auto eol=lf\n", encoding="utf-8")
    if naming:
        (root / "README.md").write_text(naming, encoding="utf-8")
    return root


VALID_STATE = """## Status
- Phase 2 is complete.
- Current task: B2-05 is complete and audit-cleared.
- Phase 3 is explicitly NOT STARTED.
## Current Verification Results
- Application tests: 2 tests verified passing.
"""
VALID_HANDOFF = """## Current phase
Phase 2 is complete. Phase 3 has not started.
## Current task
Task B2-05 is complete and audit-cleared.
## Tests and checks
- Validation performed: 2 tests pass.
"""


class ValidatorTests(unittest.TestCase):
    def validator(self, root, git=None, count=2):
        return ProjectStateValidator(
            root,
            git_runner=git or FakeGit(),
            test_discoverer=lambda: count,
        )

    def test_matching_phase_and_task_state(self):
        result = self.validator(make_repo(VALID_STATE, VALID_HANDOFF)).run()
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.facts["current_task"], "B2-05")

    def test_contradictory_phase_state_is_blocking(self):
        handoff = VALID_HANDOFF.replace("Phase 2 is complete", "Phase 2 is active")
        result = self.validator(make_repo(VALID_STATE, handoff)).run()
        self.assertTrue(any("Phase 2 disagrees" in error for error in result.errors))

    def test_contradictory_task_state_is_blocking(self):
        handoff = VALID_HANDOFF.replace("B2-05 is complete", "B2-06 is complete")
        result = self.validator(make_repo(VALID_STATE, handoff)).run()
        self.assertTrue(
            any("Current task disagrees" in error for error in result.errors)
        )

    def test_stale_current_commit_is_blocking(self):
        state = VALID_STATE.replace("## Status", "## Status\nCurrent HEAD: deadbeef")
        result = self.validator(make_repo(state, VALID_HANDOFF)).run()
        self.assertTrue(
            any("current/latest commit" in error for error in result.errors)
        )

    def test_historical_commit_is_allowed(self):
        state = VALID_STATE.replace(
            "## Status", "## Status\nHistorical commit: deadbeef"
        )
        result = self.validator(make_repo(state, VALID_HANDOFF)).run()
        self.assertFalse(any("commit reference" in error for error in result.errors))

    def test_test_count_mismatch_is_blocking(self):
        result = self.validator(make_repo(VALID_STATE, VALID_HANDOFF), count=3).run()
        self.assertTrue(any("test-count claim" in error for error in result.errors))

    def test_clean_parity_and_local_ahead_are_distinguished(self):
        clean = self.validator(make_repo(VALID_STATE, VALID_HANDOFF), FakeGit()).run()
        self.assertEqual(clean.facts["working_tree"], "CLEAN")
        self.assertEqual(clean.facts["remote_relation"], "PARITY")
        ahead = self.validator(
            make_repo(VALID_STATE, VALID_HANDOFF), FakeGit(remote="other", counts="1 0")
        ).run()
        self.assertEqual(ahead.facts["remote_relation"], "AHEAD")

    def test_product_naming_violation_is_blocking(self):
        result = self.validator(
            make_repo(
                VALID_STATE, VALID_HANDOFF, naming="Public product name: TailorPro"
            )
        ).run()
        self.assertTrue(any("public brand" in error for error in result.errors))

    def test_internal_sgtp_naming_is_allowed(self):
        result = self.validator(
            make_repo(
                VALID_STATE, VALID_HANDOFF, naming="SGTP is an internal identifier."
            )
        ).run()
        self.assertFalse(any("public brand" in error for error in result.errors))

    def test_duplicate_current_state_is_a_warning(self):
        state = (
            VALID_STATE
            + "\n## Current Verification Results\n- 2 tests pass.\n## Implementation Status\n- Phase 2 complete.\n"
        )
        result = self.validator(make_repo(state, VALID_HANDOFF)).run()
        self.assertTrue(
            any(
                "current-state/status sections" in warning
                for warning in result.warnings
            )
        )
        self.assertTrue(result.ok, result.errors)

    def test_remote_unavailable_is_a_warning(self):
        result = self.validator(
            make_repo(VALID_STATE, VALID_HANDOFF), FakeGit(remote_error=True)
        ).run()
        self.assertEqual(result.facts["remote_relation"], "REMOTE UNAVAILABLE")
        self.assertTrue(any("origin/main" in warning for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()
