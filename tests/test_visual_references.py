import hashlib
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER = REPO_ROOT / "plugins/novel-to-manhwa/scripts/build_scene_references.py"
VALIDATOR = REPO_ROOT / "plugins/novel-to-manhwa/scripts/validate_generation_requests.py"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _asset(asset_id: str, asset_type: str, roles: list[str], **rules):
    return {"asset_id": asset_id, "type": asset_type, "path": f"references/character_aya/{asset_id}.png", "sha256": _hash(asset_id), "validation_status": "validated", "provenance": {"source": "approved concept", "recorded_at": "2026-01-01T00:00:00Z"}, "panel_query_rules": {"roles": roles, **rules}}


def _manifest():
    identity = _asset("aya_identity", "identity_sheet", ["identity"])
    texture = _asset("aya_silk", "material_texture", ["texture", "material"])
    damage = _asset("aya_injured", "damage_variant", ["damage"], state_match={"health_state": {"injured": True}})
    return {"schema_version": "ntm/reference-manifest/v1", "entity_id": "character_aya", "visual_importance": "important", "canonical_identity_asset_id": "aya_identity", "required_views": ["front", "back"], "state_variants": [{"name": "injured", "asset_id": "aya_injured", "state_match": {"health_state": {"injured": True}}}], "palette": [{"name": "coat", "hex": "#112233"}], "materials": [{"name": "silk", "finish": "matte", "asset_id": "aya_silk"}], "texture_maps": [{"name": "silk_weave", "asset_id": "aya_silk"}], "geometry_constraints": ["Keep the left-eye scar position fixed."], "version_history": [{"version": "1.0.0", "changed_at": "2026-01-01T00:00:00Z", "change_summary": "Initial canonical design.", "provenance": "concept approval"}], "assets": [identity, texture, damage]}


def test_scene_reference_builder_selects_canonical_state_and_material_assets(tmp_path):
    references = tmp_path / "references/character_aya"
    references.mkdir(parents=True)
    (references / "manifest.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    scene = {"scene_id": "scene_001", "timeline_order": 5, "entities": [{"entity_id": "character_aya", "state": {"health_state": {"injured": True}}}]}
    scene_path, output = tmp_path / "scene.json", tmp_path / "generation/references/scene_001.json"
    scene_path.write_text(json.dumps(scene), encoding="utf-8")

    result = subprocess.run([sys.executable, str(BUILDER), str(scene_path), "--references-root", str(tmp_path / "references"), "--output", str(output)], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stdout
    chosen = json.loads(output.read_text())
    assert {asset["reference_id"] for asset in chosen["entities"][0]["assets"]} == {"aya_identity", "aya_silk", "aya_injured"}


def test_request_validation_blocks_missing_canonical_reference_and_texture(tmp_path):
    request_root = tmp_path / "generation/requests/chapter_001"
    request_root.mkdir(parents=True)
    request = {"request_id": "panel_001", "chapter_id": "chapter_001", "timeline_order": 5, "visible_entities": [{"entity_id": "character_aya", "presentation": "close-up"}], "resolved_canonical_states": [{"entity_id": "character_aya", "state": {}}], "required_textures": [{"entity_id": "character_aya", "texture": "silk_weave"}]}
    path = request_root / "panel_001.json"
    path.write_text(json.dumps(request), encoding="utf-8")

    missing = subprocess.run([sys.executable, str(VALIDATOR), str(tmp_path / "generation/requests")], capture_output=True, text=True, check=False)
    assert missing.returncode == 1
    assert "no canonical reference manifest" in missing.stdout
    assert "required texture" in missing.stdout

    manifest_dir = tmp_path / "references/character_aya"
    manifest_dir.mkdir(parents=True)
    manifest_dir.joinpath("manifest.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    valid = subprocess.run([sys.executable, str(VALIDATOR), str(tmp_path / "generation/requests")], capture_output=True, text=True, check=False)
    assert valid.returncode == 0, valid.stdout
