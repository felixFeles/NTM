#!/usr/bin/env python3
"""Validate NTM panel-generation request storage paths and file names."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_scene_references import _asset_applies


def _load_manifest(references_root: Path, entity_id: str) -> dict | None:
    path = references_root / entity_id / "manifest.json"
    if not path.is_file():
        return None
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return content if isinstance(content, dict) else None


def validate_visual_references(request: dict, references_root: Path) -> list[str]:
    """Reject visible entities without an applicable canonical sheet or requested texture."""
    errors: list[str] = []
    states = {
        item.get("entity_id"): item.get("state", {})
        for item in request.get("resolved_canonical_states", [])
        if isinstance(item, dict) and isinstance(item.get("entity_id"), str)
    }
    timeline_order = request.get("timeline_order", 0)
    if not isinstance(timeline_order, int) or timeline_order < 0:
        errors.append("timeline_order must be a non-negative integer for visual reference validation")
        return errors
    manifests: dict[str, dict] = {}
    for presence in request.get("visible_entities", []):
        if not isinstance(presence, dict) or not isinstance(presence.get("entity_id"), str):
            continue
        entity_id = presence["entity_id"]
        manifest = _load_manifest(references_root, entity_id)
        if manifest is None:
            errors.append(f"{entity_id}: visible entity has no canonical reference manifest")
            continue
        assets = {asset.get("asset_id"): asset for asset in manifest.get("assets", []) if isinstance(asset, dict)}
        canonical = assets.get(manifest.get("canonical_identity_asset_id"))
        if not canonical or canonical.get("type") != "identity_sheet" or not _asset_applies(canonical, timeline_order, states.get(entity_id, {})):
            errors.append(f"{entity_id}: visible entity has no validated canonical identity_sheet")
            continue
        manifests[entity_id] = manifest
    for requirement in request.get("required_textures", []):
        if not isinstance(requirement, dict):
            continue
        entity_id, texture_name = requirement.get("entity_id"), requirement.get("texture")
        manifest = manifests.get(entity_id) or _load_manifest(references_root, entity_id)
        if not isinstance(entity_id, str) or not isinstance(texture_name, str) or manifest is None:
            errors.append(f"{entity_id}: required texture {texture_name!r} has no reference manifest")
            continue
        assets = {asset.get("asset_id"): asset for asset in manifest.get("assets", []) if isinstance(asset, dict)}
        texture_ids = {entry.get("asset_id") for entry in manifest.get("texture_maps", []) if entry.get("name") == texture_name}
        requested_id = requirement.get("reference_id")
        if requested_id:
            texture_ids &= {requested_id}
        if not any((asset := assets.get(asset_id)) and asset.get("type") == "material_texture" and _asset_applies(asset, timeline_order, states.get(entity_id, {})) for asset_id in texture_ids):
            errors.append(f"{entity_id}: required texture {texture_name!r} has no validated applicable material_texture")
    return errors


def validate_requests(root: Path) -> list[str]:
    """Return storage violations for request JSON files below *root*."""
    errors: list[str] = []
    if not root.exists():
        return [f"request directory does not exist: {root}"]

    references_root = root.parent.parent / "references"
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
        errors.extend(f"{path}: {error}" for error in validate_visual_references(request, references_root))
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
