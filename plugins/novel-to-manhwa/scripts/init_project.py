#!/usr/bin/env python3
"""Initialize a non-destructive canon-first Novel To Manhwa project."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

DIRECTORIES = (
    "canon/entities",
    "canon/events",
    "story/source",
    "story/extractions",
    "storyboard",
    "visual_bible",
    "references",
    "generation/requests",
    "generation/outputs",
    "validation",
    "chapters",
    "reports",
    "tools",
)

README = """# Novel To Manhwa project\n\nThis project is canon-first: structured files are authoritative; an LLM context is not.\n\n1. Put immutable novel files in `story/source/`.\n2. Create sourced entities in `canon/entities/` and transitions in `canon/events/`.\n3. Resolve a scene state before writing storyboards or generation requests.\n4. Write a continuity report for every chapter; `final` requires no open blocker.\n\nDo not overwrite canonical facts to hide contradictions. Preserve evidence and record a decision event.\n"""
SCRIPT_DIR = Path(__file__).resolve().parent


def write_file(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        print(f"preserved {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="target project directory")
    parser.add_argument("--force", action="store_true", help="replace starter files only")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for directory in DIRECTORIES:
        (root / directory).mkdir(parents=True, exist_ok=True)
    write_file(root / "README.md", README, args.force)
    write_file(
        root / "reports" / ".gitkeep",
        "Generated continuity reports are retained here.\n",
        args.force,
    )
    write_file(
        root / "generation" / "requests" / "README.md",
        "# Panel generation requests\n\n"
        "Store each request at `<chapter_id>/<request_id>.json`. The filename must "
        "match the request's `request_id`. Validate storage with "
        "`tools/validate_generation_requests.py generation/requests`. Requests also need "
        "`timeline_order`; validation blocks a visible entity without a validated canonical "
        "reference or a required texture without a validated texture map.\n",
        args.force,
    )
    validator_target = root / "tools" / "validate_generation_requests.py"
    if not validator_target.exists() or args.force:
        shutil.copyfile(SCRIPT_DIR / "validate_generation_requests.py", validator_target)
        print(f"wrote {validator_target}")
    else:
        print(f"preserved {validator_target}")
    reference_builder_target = root / "tools" / "build_scene_references.py"
    if not reference_builder_target.exists() or args.force:
        shutil.copyfile(SCRIPT_DIR / "build_scene_references.py", reference_builder_target)
        print(f"wrote {reference_builder_target}")
    else:
        print(f"preserved {reference_builder_target}")
    write_file(
        root / "references" / "README.md",
        "# Visual reference manifests\n\n"
        "Every visually important entity must have `references/<entity_id>/manifest.json` "
        "conforming to `reference-manifest.schema.json`. A manifest records its canonical "
        "identity sheet, required views, state variants, palette, materials, texture maps, "
        "geometry constraints, version history, and hash/provenance/validation/query rules for "
        "every asset. Build a scene list with `tools/build_scene_references.py scene.json "
        "--output generation/references/<scene_id>.json`.\n",
        args.force,
    )
    manifest = {"format": "ntm-project/v1", "canon_policy": "canon_over_model_memory", "status": "initialized"}
    write_file(root / "ntm-project.json", json.dumps(manifest, indent=2) + "\n", args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
