from ntm.ingestion.author_material import (
    facts_available_for_dialogue,
    find_conflicts,
    ingest_author_material,
)


def test_author_note_secret_is_not_injected_into_dialogue_before_canon_revelation():
    secret_note = ingest_author_material(
        {
            "source_id": "note-17",
            "source_type": "author_note",
            "facts": [
                {
                    "fact_id": "secret-parentage-note",
                    "claim_key": "mira.parentage",
                    "claim": "Mira is the missing heir.",
                    "canon_status": "approved_private",
                    "audience_visibility": "reader_hidden",
                    "character_knowledge": {"mira": {"state": "knows"}},
                }
            ],
        }
    )

    assert facts_available_for_dialogue(secret_note.facts, "mira") == []


def test_published_revelation_can_be_used_after_it_is_reader_known():
    chapter = ingest_author_material(
        {
            "source_id": "chapter-20",
            "source_type": "published_chapter",
            "facts": [
                {
                    "fact_id": "secret-parentage-revealed",
                    "claim_key": "mira.parentage",
                    "claim": "Mira is the missing heir.",
                    "canon_status": "published",
                    "audience_visibility": "reader_known",
                    "character_knowledge": {"mira": {"state": "knows"}},
                }
            ],
        }
    )

    assert [fact["fact_id"] for fact in facts_available_for_dialogue(chapter.facts, "mira")] == [
        "secret-parentage-revealed"
    ]


def test_opposed_active_claims_are_blocking_and_keep_published_reference():
    published = ingest_author_material(
        {
            "source_id": "chapter-1",
            "source_type": "published_chapter",
            "facts": [{"fact_id": "published-age", "claim_key": "mira.age", "claim": "Mira is 18.", "canon_status": "published", "audience_visibility": "reader_known", "character_knowledge": {}}],
        }
    )
    draft = ingest_author_material(
        {
            "source_id": "outline-2",
            "source_type": "outline",
            "facts": [{"fact_id": "draft-age", "claim_key": "mira.age", "claim": "Mira is 19.", "canon_status": "provisional", "audience_visibility": "author_only", "character_knowledge": {}}],
        }
    )

    conflicts = find_conflicts((*published.facts, *draft.facts))

    assert len(conflicts) == 1
    assert conflicts[0].blocking is True
    assert conflicts[0].authoritative_fact_id == "published-age"
