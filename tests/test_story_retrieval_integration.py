from pathlib import Path

from ntm.ingestion import StoryIngestor
from ntm.retrieval import Entity, Event, HybridStoryIndex


def _write(root: Path, name: str, text: str) -> None:
    (root / name).write_text(text, encoding="utf-8")


def test_distant_character_object_and_secret_are_retrievable(tmp_path: Path) -> None:
    source = tmp_path / "story" / "source"
    source.mkdir(parents=True)
    _write(source, "01-arrival.md", "---\nchapter_id: arrival\npublication_order: 1\nchronological_order: 1\n---\nMara gives the silver key to Ivo. The key opens the hidden archive.\n")
    _write(source, "02-memory.md", "---\nchapter_id: memory\npublication_order: 2\nchronological_order: 0\nflashback: true\nflashback_of: arrival\n---\nYoung Mara swore never to reveal the secret name.\n")
    _write(source, "09-revelation.md", "---\nchapter_id: revelation\npublication_order: 9\nchronological_order: 9\n---\nIvo uses the silver key. Mara reveals the secret name at last.\n")

    manifest = StoryIngestor(source).ingest()
    index = HybridStoryIndex(manifest)
    index.add_entity(Entity("character:mara", "Mara", kind="character"))
    index.add_entity(Entity("object:silver-key", "silver key", aliases=("key",), kind="object"))
    index.add_entity(Entity("secret:true-name", "secret name", aliases=("hidden archive",), kind="secret"))
    index.add_event(Event("event:gift", "arrival", "Mara gives Ivo the key", ("character:mara", "object:silver-key")))
    index.add_event(Event("event:reveal", "revelation", "The secret is exposed", ("character:mara", "secret:true-name"), ("event:gift",)))
    index.add_event(Event("event:denial", "memory", "Mara says it stays hidden", ("secret:true-name",), (), ("event:reveal",)))

    context = index.retrieve_entity_context("object:silver-key", "revelation", "prior")
    assert [hit.chapter_id for hit in context.prior_occurrences] == ["arrival", "arrival"]
    assert not context.subsequent_occurrences
    assert "01-arrival.md:p1:s1" in context.sources
    assert {event.event_id for event in context.causal_events} == {"event:gift"}

    secret = index.retrieve_entity_context("secret:true-name", "revelation", "both")
    assert {hit.chapter_id for hit in secret.prior_occurrences} == {"arrival", "memory"}
    assert [event.event_id for event in secret.potential_contradictions] == ["event:reveal"]
    assert [chapter.chapter_id for chapter in index.publication_timeline] == ["arrival", "memory", "revelation"]
    assert [chapter.chapter_id for chapter in index.chronological_timeline] == ["memory", "arrival", "revelation"]
    assert manifest.chapter("memory").flashback


def test_manifest_and_locators_are_deterministic_and_immutable(tmp_path: Path) -> None:
    source = tmp_path / "story" / "source"
    source.mkdir(parents=True)
    _write(source, "chapter.txt", "One sentence. Second sentence.\n\nAnother paragraph.")
    first = StoryIngestor(source).ingest()
    second = StoryIngestor(source).ingest()
    assert first.manifest_sha256 == second.manifest_sha256
    assert first.sources[0].sha256
    assert [item.locator.stable_id for item in first.chapters[0].occurrences] == ["chapter.txt:p1:s1", "chapter.txt:p1:s2", "chapter.txt:p2:s1"]
    try:
        first.chapters[0].metadata["new"] = "value"  # type: ignore[index]
    except TypeError:
        pass
    else:
        raise AssertionError("manifest metadata must be immutable")
