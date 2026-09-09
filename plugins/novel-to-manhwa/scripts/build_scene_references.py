#!/usr/bin/env python3
"""Build the validated, timeline-aware reference list for one resolved scene."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VALIDATED = "validated"


def _matches(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(key in actual and _matches(value, actual[key]) for key, value in expected.items())
    return expected == actual


def _asset_applies(asset: dict[str, Any], timeline_order: int, state: dict[str, Any]) -> bool:
    rules = asset.get("panel_query_rules", {})
    return (asset.get("validation_status") == VALIDATED
            and timeline_order >= rules.get("timeline_start", 0)
            and timeline_order <= rules.get("timeline_end", timeline_order)
            and _matches(rules.get("state_match", {}), state))


def select_scene_references(scene: dict[str, Any], references_root: Path) -> tuple[dict[str, Any], list[str]]:
    """Return a portable reference manifest and deterministic blocking errors."""
    errors: list[str] = []
    selected: list[dict[str, Any]] = []
    timeline_order = scene.get("timeline_order")
    if not isinstance(timeline_order, int) or timeline_order < 0:
        return {}, ["scene: timeline_order must be a non-negative integer"]
    for entity in scene.get("entities", []):
        if not entity.get("visible", True):
            continue
        entity_id, state = entity.get("entity_id"), entity.get("state", {})
        manifest_path = references_root / str(entity_id) / "manifest.json"
        if not isinstance(entity_id, str) or not manifest_path.is_file():
            errors.append(f"{entity_id}: visible entity has no canonical reference manifest")
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append(f"{entity_id}: invalid reference manifest JSON")
            continue
        assets = {asset.get("asset_id"): asset for asset in manifest.get("assets", []) if isinstance(asset, dict)}
        canonical = assets.get(manifest.get("canonical_identity_asset_id"))
        if not canonical or canonical.get("type") != "identity_sheet" or not _asset_applies(canonical, timeline_order, state):
            errors.append(f"{entity_id}: no validated canonical identity_sheet applies at timeline {timeline_order}")
            continue
        chosen = [canonical]
        for variant in manifest.get("state_variants", []):
            if _matches(variant.get("state_match", {}), state):
                asset = assets.get(variant.get("asset_id"))
                if asset and _asset_applies(asset, timeline_order, state):
                    chosen.append(asset)
        for asset in assets.values():
            if asset not in chosen and _asset_applies(asset, timeline_order, state):
                chosen.append(asset)
        selected.append({"entity_id": entity_id, "canonical_asset_id": canonical["asset_id"], "assets": [{"reference_id": a["asset_id"], "path": a["path"], "roles": a["panel_query_rules"]["roles"]} for a in chosen]})
    return {"schema_version": "ntm/scene-references/v1", "scene_id": scene.get("scene_id"), "timeline_order": timeline_order, "entities": selected}, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("--references-root", type=Path, default=Path("references"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    scene = json.loads(args.scene.read_text(encoding="utf-8"))
    result, errors = select_scene_references(scene, args.references_root)
    if errors:
        print("Scene reference selection blocked:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Scene references written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
