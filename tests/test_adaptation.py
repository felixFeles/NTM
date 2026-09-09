import json

import pytest

from ntm.adaptation import (
    CANONIZATION_RULE,
    AdaptationDecisionValidationError,
    initialize_chapter_adaptation,
    validate_adaptation_decisions,
)


def valid_payload():
    return {
        "chapter_id": "chapter_001",
        "canonization_rule": CANONIZATION_RULE,
        "decisions": [
            {
                "decision_id": "chapter_001-decision-001",
                "addition_type": "additional_dialogue",
                "proposal": "Add a wordless acknowledgement before the departure.",
                "source_locators": ["chapter_001.md:p4:s2"],
                "status": "proposed",
                "adaptation_only": True,
                "editorial_justification": {
                    "sources_used": ["chapter_001.md:p4:s2"],
                    "canonical_rule": "The source confirms the departure but not the wording.",
                    "hypothesis": "The acknowledgement clarifies pacing without revealing new facts.",
                    "confidence": "medium",
                    "rejected_alternatives": ["Add an explanation of the character's secret motive."],
                    "human_validation_required": True,
                },
            }
        ],
    }


def test_decision_model_keeps_approved_additions_non_canonical():
    payload = valid_payload()
    payload["decisions"][0]["status"] = "approved"

    validate_adaptation_decisions(payload)


def test_decision_model_rejects_silent_canon_promotion():
    payload = valid_payload()
    payload["decisions"][0]["becomes_canon"] = True

    with pytest.raises(AdaptationDecisionValidationError, match="canon-changing"):
        validate_adaptation_decisions(payload)


def test_chapter_workspace_contains_every_adaptation_artifact(tmp_path):
    chapter_dir = initialize_chapter_adaptation(tmp_path, "chapter_001")

    assert (chapter_dir / "summary.md").is_file()
    decisions = json.loads((chapter_dir / "adaptation_decision.json").read_text())
    assert decisions == {
        "chapter_id": "chapter_001",
        "canonization_rule": CANONIZATION_RULE,
        "decisions": [],
    }
    original_summary = (chapter_dir / "summary.md").read_text()
    initialize_chapter_adaptation(tmp_path, "chapter_001")
    assert (chapter_dir / "summary.md").read_text() == original_summary
