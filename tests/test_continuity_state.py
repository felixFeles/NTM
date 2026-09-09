import json
from pathlib import Path

from ntm.continuity import CanonStateResolver, resolve_entity_state


FIXTURE = Path(__file__).parent / "fixtures" / "canonical_state_transitions.json"


def _canon():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_persistent_injury_and_documented_healing_are_resolved_by_timeline():
    canon = _canon()
    resolver = CanonStateResolver(canon["entities"], canon["events"])

    before_healing = resolver.resolve_entity_state("character_aria", 40)
    after_healing = resolver.resolve_entity_state("character_aria", 50)

    assert before_healing["state"]["health_state"]["injuries"][0]["status"] == "open"
    assert after_healing["state"]["health_state"]["injuries"][0]["status"] == "healed"
    assert before_healing["state"]["physical_state"] == {"height_cm": 156, "build": "athletic"}


def test_transfer_damage_and_repair_do_not_rewrite_past_state():
    canon = _canon()
    resolver = CanonStateResolver(canon["entities"], canon["events"])

    assert resolver.resolve_entity_state("item_ring_001", 10)["state"]["ownership_state"]["owner_id"] == "character_bram"
    assert resolver.resolve_entity_state("item_ring_001", 20)["state"]["ownership_state"]["owner_id"] == "character_cora"
    assert resolver.resolve_entity_state("item_sword_001", 30)["state"]["material_state"]["condition"] == "cracked"
    repaired = resolve_entity_state("item_sword_001", {"date": "2026-01-08", "order": 60}, entities=canon["entities"], events=canon["events"])
    assert repaired["state"]["material_state"]["condition"] == "repaired"


def test_returned_snapshot_is_detached_from_canon_and_future_resolutions():
    canon = _canon()
    resolver = CanonStateResolver(canon["entities"], canon["events"])
    snapshot = resolver.resolve_entity_state("character_aria", 10)
    snapshot["state"]["health_state"]["condition"] = "altered outside canon"

    assert resolver.resolve_entity_state("character_aria", 10)["state"]["health_state"]["condition"] == "injured"


def test_versioned_contracts_expose_all_state_compartments_and_sourced_timeline_events():
    root = Path(__file__).parents[1]
    entity_schema = json.loads((root / "plugins/novel-to-manhwa/schemas/v1/entity.schema.json").read_text())
    event_schema = json.loads((root / "plugins/novel-to-manhwa/schemas/v1/event.schema.json").read_text())
    expected = {
        "physical_state", "health_state", "appearance_state", "wardrobe_state",
        "inventory_state", "ownership_state", "location_state", "knowledge_state",
        "ability_state", "material_state", "texture_state", "energy_state",
    }

    assert expected <= set(entity_schema["$defs"]["entityState"]["properties"])
    assert expected <= set(event_schema["$defs"]["statePatch"]["properties"])
    assert {"date", "order", "scene_id"} <= set(event_schema["$defs"]["timelinePosition"]["required"])
    assert "provenance" in event_schema["required"]
