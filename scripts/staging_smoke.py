#!/usr/bin/env python3
"""Check public staging health endpoints without sending credentials."""

from __future__ import annotations

import argparse
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def check_health(base_url: str, timeout: float = 10.0) -> list[tuple[str, int]]:
    parsed = urlsplit(base_url)
    if (
        parsed.scheme not in {"https", "http"}
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Base URL must be an HTTP(S) origin without credentials or query data."
        )

    origin = f"{parsed.scheme}://{parsed.netloc}"
    results = []
    for path in ("/api/health/live/", "/api/health/ready/"):
        request = Request(f"{origin}{path}", method="GET")
        try:
            with urlopen(request, timeout=timeout) as response:
                result = (path, response.status)
        except HTTPError as exc:
            result = (path, exc.code)
        except URLError as exc:
            raise RuntimeError(
                f"Health request failed for {path} ({exc.reason})."
            ) from exc
        results.append(result)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "base_url",
        nargs="?",
        default=os.getenv("STAGING_API_BASE_URL", "https://api-staging.birky.com"),
        help="Staging API origin (defaults to STAGING_API_BASE_URL or the canonical staging host).",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args(argv)

    try:
        results = check_health(args.base_url, timeout=args.timeout)
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    for path, status_code in results:
        print(f"{path}: HTTP {status_code}")
    return 0 if all(status_code == 200 for _, status_code in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
