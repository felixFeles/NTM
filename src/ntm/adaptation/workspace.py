"""Create non-destructive, per-chapter adaptation workspaces."""

from __future__ import annotations

import json
from pathlib import Path

from .decisions import CANONIZATION_RULE

ADAPTATION_ARTIFACTS = (
    "summary.md",
    "narrative_breakdown.json",
    "explicit_facts.json",
    "inferences.json",
    "visual_hypotheses.json",
    "dialogue_proposals.json",
    "added_scenes.json",
    "offscreen_elements.json",
    "continuity_risks.json",
    "adaptation_decision.json",
)


def _json_artifact(chapter_id: str, artifact: str) -> dict[str, object]:
    if artifact == "adaptation_decision.json":
        return {
            "chapter_id": chapter_id,
            "canonization_rule": CANONIZATION_RULE,
            "decisions": [],
        }
    return {"chapter_id": chapter_id, "items": []}


def initialize_chapter_adaptation(root: str | Path, chapter_id: str) -> Path:
    """Create an empty chapter folder without overwriting editorial work.

    JSON artifacts carry source locators and concise, auditable editorial
    justifications when populated.  The Markdown summary is intentionally a
    short faithful synopsis rather than a reasoning trace.
    """
    if not isinstance(chapter_id, str) or not chapter_id.strip():
        raise ValueError("chapter_id must be a non-empty string.")
    chapter_dir = Path(root) / chapter_id
    chapter_dir.mkdir(parents=True, exist_ok=True)
    for artifact in ADAPTATION_ARTIFACTS:
        path = chapter_dir / artifact
        if path.exists():
            continue
        if artifact == "summary.md":
            path.write_text(
                f"# Résumé fidèle — {chapter_id}\n\n"
                "Décrire uniquement les événements étayés par les localisateurs de source.\n",
                encoding="utf-8",
            )
        else:
            path.write_text(
                json.dumps(_json_artifact(chapter_id, artifact), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return chapter_dir
