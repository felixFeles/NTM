#!/usr/bin/env python3
"""Fail when an NTM continuity report declares FINAL with unresolved blockers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def check(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    findings = data.get("findings", [])
    blockers = [f.get("id", "<unnamed>") for f in findings if f.get("severity") == "blocker" and f.get("disposition") == "open"]
    errors: list[str] = []
    if data.get("status") == "final" and blockers:
        errors.append(f"{path}: final report has open blockers: {', '.join(blockers)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", help="report file or directory")
    args = parser.parse_args()
    path = Path(args.reports)
    files = [path] if path.is_file() else sorted(path.glob("*.json"))
    if not files:
        print("no report files found")
        return 0
    errors = [error for file in files for error in check(file)]
    if errors:
        print("\n".join(errors))
        return 1
    print(f"validated {len(files)} report(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
