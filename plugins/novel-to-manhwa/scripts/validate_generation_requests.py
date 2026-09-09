#!/usr/bin/env python3
"""Validate NTM panel-generation request storage paths and file names."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate_requests(root: Path) -> list[str]:
    """Return storage violations for request JSON files below *root*."""
    errors: list[str] = []
    if not root.exists():
        return [f"request directory does not exist: {root}"]

    for path in sorted(root.rglob("*.json")):
        try:
            request = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"{path}: invalid JSON ({error.msg})")
            continue
        if not isinstance(request, dict):
            errors.append(f"{path}: request must be a JSON object")
            continue

        request_id = request.get("request_id")
        chapter_id = request.get("chapter_id")
        if not isinstance(request_id, str) or not request_id:
            errors.append(f"{path}: missing non-empty request_id")
        elif path.stem != request_id:
            errors.append(f"{path}: filename must be {request_id}.json")
        if not isinstance(chapter_id, str) or not chapter_id:
            errors.append(f"{path}: missing non-empty chapter_id")
        elif path.parent != root / chapter_id:
            errors.append(f"{path}: must be stored in {root / chapter_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default="generation/requests", type=Path)
    args = parser.parse_args()
    errors = validate_requests(args.root)
    if errors:
        print("Invalid generation request storage:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"Generation request storage is valid: {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
