"""Ingest author material without leaking private canon into dialogue.

The module intentionally uses the small, explicit contract defined in
``canon/sources`` so it can run in editorial tooling without third-party
validation dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

SOURCE_TYPES = frozenset(
    {
        "published_chapter",
        "author_note",
        "worldbuilding_draft",
        "outline",
        "visual_reference",
        "editorial_decision",
        "superseded_material",
    }
)
CANON_STATUSES = frozenset(
    {"published", "approved_private", "provisional", "superseded", "non_canon"}
)
AUDIENCE_VISIBILITIES = frozenset({"author_only", "reader_hidden", "reader_known"})
KNOWLEDGE_STATES = frozenset({"unknown", "suspects", "knows"})
INACTIVE_STATUSES = frozenset({"superseded", "non_canon"})


class MaterialValidationError(ValueError):
    """Raised when a source does not obey the canon source contract."""


@dataclass(frozen=True)
class CanonConflict:
    """A blocking contradiction that needs an editorial decision."""

    claim_key: str
    fact_ids: tuple[str, ...]
    claims: tuple[str, ...]
    authoritative_fact_id: str | None
    blocking: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim_key": self.claim_key,
            "fact_ids": list(self.fact_ids),
            "claims": list(self.claims),
            "authoritative_fact_id": self.authoritative_fact_id,
            "blocking": self.blocking,
        }


@dataclass(frozen=True)
class IngestionResult:
    """Normalized facts plus unresolved editorial conflicts."""

    facts: tuple[dict[str, Any], ...]
    conflicts: tuple[CanonConflict, ...]

    def conflict_report(self) -> dict[str, Any]:
        """Return the JSON payload consumed by the conflict-review interface."""
        return {"conflicts": [conflict.as_dict() for conflict in self.conflicts]}


def _read_payload(material: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    if isinstance(material, (str, Path)):
        try:
            payload = json.loads(Path(material).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise MaterialValidationError(f"Unable to read source material: {error}") from error
    else:
        payload = material
    if not isinstance(payload, Mapping):
        raise MaterialValidationError("Source material must be a JSON object.")
    return payload


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MaterialValidationError(f"{field} must be a non-empty string.")
    return value


def _validate_fact(fact: Any, index: int) -> dict[str, Any]:
    if not isinstance(fact, Mapping):
        raise MaterialValidationError(f"facts[{index}] must be an object.")
    normalized = dict(fact)
    for field in ("fact_id", "claim"):
        _require_string(normalized.get(field), f"facts[{index}].{field}")
    if normalized.get("canon_status") not in CANON_STATUSES:
        raise MaterialValidationError(f"facts[{index}].canon_status is not supported.")
    if normalized.get("audience_visibility") not in AUDIENCE_VISIBILITIES:
        raise MaterialValidationError(f"facts[{index}].audience_visibility is not supported.")
    knowledge = normalized.get("character_knowledge")
    if not isinstance(knowledge, Mapping):
        raise MaterialValidationError(f"facts[{index}].character_knowledge must be an object.")
    for character_id, record in knowledge.items():
        _require_string(character_id, f"facts[{index}].character_knowledge key")
        if not isinstance(record, Mapping) or record.get("state") not in KNOWLEDGE_STATES:
            raise MaterialValidationError(
                f"facts[{index}].character_knowledge[{character_id!r}] needs a valid state."
            )
    if "claim_key" in normalized:
        _require_string(normalized["claim_key"], f"facts[{index}].claim_key")
    return normalized


def ingest_author_material(material: Mapping[str, Any] | str | Path) -> IngestionResult:
    """Normalize one source document and identify its blocking contradictions.

    Private source material is retained for adaptation planning, not made
    dialogue-eligible. Conflicts are reported rather than silently selecting a
    winner; a published fact is only marked as the authoritative reference for
    the editor's review.
    """
    payload = _read_payload(material)
    source_id = _require_string(payload.get("source_id"), "source_id")
    source_type = payload.get("source_type")
    if source_type not in SOURCE_TYPES:
        raise MaterialValidationError("source_type is not one of the seven supported source types.")
    raw_facts = payload.get("facts")
    if not isinstance(raw_facts, list) or not raw_facts:
        raise MaterialValidationError("facts must be a non-empty array.")

    facts: list[dict[str, Any]] = []
    for index, raw_fact in enumerate(raw_facts):
        fact = _validate_fact(raw_fact, index)
        fact["source_id"] = source_id
        fact["source_type"] = source_type
        facts.append(fact)
    return IngestionResult(tuple(facts), tuple(find_conflicts(facts)))


def find_conflicts(facts: Iterable[Mapping[str, Any]]) -> list[CanonConflict]:
    by_key: dict[str, list[Mapping[str, Any]]] = {}
    for fact in facts:
        if fact["canon_status"] in INACTIVE_STATUSES or not fact.get("claim_key"):
            continue
        by_key.setdefault(str(fact["claim_key"]), []).append(fact)

    conflicts: list[CanonConflict] = []
    for claim_key, candidates in by_key.items():
        claims = {str(fact["claim"]) for fact in candidates}
        if len(claims) < 2:
            continue
        published = [
            fact for fact in candidates
            if fact["source_type"] == "published_chapter" and fact["canon_status"] == "published"
        ]
        conflicts.append(
            CanonConflict(
                claim_key=claim_key,
                fact_ids=tuple(str(fact["fact_id"]) for fact in candidates),
                claims=tuple(sorted(claims)),
                authoritative_fact_id=str(published[0]["fact_id"]) if published else None,
            )
        )
    return conflicts


def facts_available_for_dialogue(
    facts: Iterable[Mapping[str, Any]], speaker_id: str
) -> list[Mapping[str, Any]]:
    """Return facts a speaker can say without exposing unrevealed author knowledge.

    A fact must be published in a published chapter, reader-known, and known by
    the speaker. This deliberately excludes notes and drafts even when the
    author has marked a character as knowing their contents.
    """
    return [
        fact
        for fact in facts
        if fact.get("source_type") == "published_chapter"
        and fact.get("canon_status") == "published"
        and fact.get("audience_visibility") == "reader_known"
        and isinstance(fact.get("character_knowledge"), Mapping)
        and fact["character_knowledge"].get(speaker_id, {}).get("state") == "knows"
    ]
