"""Audit-friendly adaptation decisions that never mutate story canon.

The adaptation layer records creative production choices separately from source
canon.  It intentionally asks for concise editorial evidence, not private
reasoning traces.
"""

from __future__ import annotations

from typing import Any, Mapping

DECISION_STATUSES = frozenset({"proposed", "approved", "rejected"})
ADDITION_TYPES = frozenset(
    {"undisclosed_outfit", "set_decoration", "additional_dialogue", "scene_transition"}
)
CONFIDENCE_LEVELS = frozenset({"low", "medium", "high"})
CANONIZATION_RULE = (
    "Adaptation decisions are non-canonical and cannot update canon automatically; "
    "canon changes require a separately sourced editorial_decision."
)


class AdaptationDecisionValidationError(ValueError):
    """Raised when an adaptation decision breaks the non-canon contract."""


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdaptationDecisionValidationError(f"{field} must be a non-empty string.")
    return value


def _require_string_list(value: Any, field: str, *, nonempty: bool = False) -> None:
    if not isinstance(value, list) or (nonempty and not value):
        qualifier = " a non-empty" if nonempty else " an"
        raise AdaptationDecisionValidationError(f"{field} must be{qualifier} array of strings.")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise AdaptationDecisionValidationError(f"{field} must contain only non-empty strings.")


def _validate_justification(value: Any, field: str) -> None:
    if not isinstance(value, Mapping):
        raise AdaptationDecisionValidationError(f"{field} must be an object.")
    _require_string_list(value.get("sources_used"), f"{field}.sources_used", nonempty=True)
    _require_nonempty_string(value.get("canonical_rule"), f"{field}.canonical_rule")
    _require_nonempty_string(value.get("hypothesis"), f"{field}.hypothesis")
    if value.get("confidence") not in CONFIDENCE_LEVELS:
        raise AdaptationDecisionValidationError(
            f"{field}.confidence must be one of {sorted(CONFIDENCE_LEVELS)}."
        )
    _require_string_list(value.get("rejected_alternatives"), f"{field}.rejected_alternatives")
    if not isinstance(value.get("human_validation_required"), bool):
        raise AdaptationDecisionValidationError(f"{field}.human_validation_required must be a boolean.")


def validate_adaptation_decisions(payload: Mapping[str, Any]) -> None:
    """Validate a chapter's creative additions and preserve canon separation.

    ``approved`` grants permission to use an addition in this adaptation only;
    it never promotes it to canon.  Any canon field or altered policy is
    rejected so downstream code cannot infer a silent canon update.
    """
    if not isinstance(payload, Mapping):
        raise AdaptationDecisionValidationError("Adaptation decisions must be a JSON object.")
    _require_nonempty_string(payload.get("chapter_id"), "chapter_id")
    if payload.get("canonization_rule") != CANONIZATION_RULE:
        raise AdaptationDecisionValidationError("canonization_rule must preserve the non-automatic canon rule.")
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        raise AdaptationDecisionValidationError("decisions must be an array.")

    decision_ids: set[str] = set()
    for index, decision in enumerate(decisions):
        field = f"decisions[{index}]"
        if not isinstance(decision, Mapping):
            raise AdaptationDecisionValidationError(f"{field} must be an object.")
        forbidden = {"canon_status", "canon_update", "becomes_canon"} & set(decision)
        if forbidden:
            raise AdaptationDecisionValidationError(
                f"{field} contains canon-changing field(s): {', '.join(sorted(forbidden))}."
            )
        decision_id = _require_nonempty_string(decision.get("decision_id"), f"{field}.decision_id")
        if decision_id in decision_ids:
            raise AdaptationDecisionValidationError(f"{field}.decision_id must be unique.")
        decision_ids.add(decision_id)
        if decision.get("addition_type") not in ADDITION_TYPES:
            raise AdaptationDecisionValidationError(
                f"{field}.addition_type must be one of {sorted(ADDITION_TYPES)}."
            )
        _require_nonempty_string(decision.get("proposal"), f"{field}.proposal")
        _require_string_list(decision.get("source_locators"), f"{field}.source_locators", nonempty=True)
        if decision.get("status") not in DECISION_STATUSES:
            raise AdaptationDecisionValidationError(
                f"{field}.status must be one of {sorted(DECISION_STATUSES)}."
            )
        if decision.get("adaptation_only") is not True:
            raise AdaptationDecisionValidationError(f"{field}.adaptation_only must be true.")
        _validate_justification(decision.get("editorial_justification"), f"{field}.editorial_justification")
