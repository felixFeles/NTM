"""In-memory hybrid index with source-first retrieval results.

It intentionally keeps separate publication and diegetic timelines.  Scores are
only used to rank evidence; every returned item carries the original locator.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, Literal

from ntm.ingestion import Chapter, Manifest, Occurrence

_WORD = re.compile(r"[\wÀ-ÖØ-öø-ÿ'-]+", re.UNICODE)
Direction = Literal["prior", "subsequent", "both"]


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(token.casefold() for token in _WORD.findall(text))


@dataclass(frozen=True, slots=True)
class Entity:
    entity_id: str
    name: str
    aliases: tuple[str, ...] = ()
    kind: str = "entity"

    @property
    def terms(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


@dataclass(frozen=True, slots=True)
class Event:
    event_id: str
    chapter_id: str
    description: str
    entity_ids: tuple[str, ...] = ()
    causes: tuple[str, ...] = ()
    contradicts: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SearchHit:
    chapter_id: str
    occurrence: Occurrence
    score: float
    channels: tuple[str, ...]
    entity_ids: tuple[str, ...] = ()
    event_ids: tuple[str, ...] = ()

    @property
    def source(self) -> str:
        return self.occurrence.locator.stable_id


@dataclass(frozen=True, slots=True)
class RetrievalContext:
    focus_chapter_id: str
    current: tuple[SearchHit, ...]
    prior_occurrences: tuple[SearchHit, ...]
    subsequent_occurrences: tuple[SearchHit, ...]
    causal_events: tuple[Event, ...]
    potential_contradictions: tuple[Event, ...]
    sources: tuple[str, ...]


class HybridStoryIndex:
    """Lexical, vector, graph and temporal indexes over a :class:`Manifest`."""

    def __init__(self, manifest: Manifest) -> None:
        self.manifest = manifest
        self._chapters = {chapter.chapter_id: chapter for chapter in manifest.chapters}
        if len(self._chapters) != len(manifest.chapters):
            raise ValueError("chapter_id values must be unique")
        self._entities: dict[str, Entity] = {}
        self._events: dict[str, Event] = {}
        self._entity_occurrences: dict[str, list[tuple[str, Occurrence]]] = defaultdict(list)
        self._event_entities: dict[str, set[str]] = defaultdict(set)
        self._lexical: dict[str, set[tuple[str, int]]] = defaultdict(set)
        self._documents: dict[tuple[str, int], Counter[str]] = {}
        self._document_frequency: Counter[str] = Counter()
        self._chronological = tuple(sorted(manifest.chapters, key=lambda c: (c.chronological_order, c.publication_order)))
        self._publication = tuple(sorted(manifest.chapters, key=lambda c: c.publication_order))
        self._build_text_indexes()

    @property
    def publication_timeline(self) -> tuple[Chapter, ...]:
        return self._publication

    @property
    def chronological_timeline(self) -> tuple[Chapter, ...]:
        return self._chronological

    def add_entity(self, entity: Entity) -> None:
        if entity.entity_id in self._entities:
            raise ValueError(f"duplicate entity_id: {entity.entity_id}")
        self._entities[entity.entity_id] = entity
        terms = {_normalise(term) for term in entity.terms}
        for chapter in self.manifest.chapters:
            for occurrence in chapter.occurrences:
                phrase = _normalise(occurrence.text)
                if any(term and term in phrase for term in terms):
                    self._entity_occurrences[entity.entity_id].append((chapter.chapter_id, occurrence))

    def add_event(self, event: Event) -> None:
        if event.chapter_id not in self._chapters:
            raise KeyError(f"event {event.event_id} references unknown chapter {event.chapter_id}")
        if event.event_id in self._events:
            raise ValueError(f"duplicate event_id: {event.event_id}")
        self._events[event.event_id] = event
        for entity_id in event.entity_ids:
            self._event_entities[entity_id].add(event.event_id)

    def search(self, query: str, *, limit: int = 10) -> tuple[SearchHit, ...]:
        """Combine lexical overlap and TF-IDF cosine vector similarity."""
        query_terms = _tokens(query)
        if not query_terms:
            return ()
        candidates = set().union(*(self._lexical.get(term, set()) for term in set(query_terms)))
        query_vector = Counter(query_terms)
        hits: list[SearchHit] = []
        for key in candidates:
            lexical = sum(1 for term in query_terms if term in self._documents[key]) / len(query_terms)
            vector = self._cosine(query_vector, self._documents[key])
            chapter_id, phrase_index = key
            occurrence = self._chapters[chapter_id].occurrences[phrase_index]
            hits.append(SearchHit(chapter_id, occurrence, lexical * 0.45 + vector * 0.55, ("lexical", "vector")))
        return tuple(sorted(hits, key=lambda hit: (-hit.score, hit.source))[:limit])

    def retrieve_entity_context(self, entity_id: str, chapter_id: str, direction: Direction = "both") -> RetrievalContext:
        """Retrieve named evidence around a chapter in *publication* order."""
        if entity_id not in self._entities:
            raise KeyError(f"unknown entity_id: {entity_id}")
        chapter = self._chapter(chapter_id)
        entity_hits = tuple(self._entity_hit(entity_id, found_chapter, occurrence)
                            for found_chapter, occurrence in self._entity_occurrences[entity_id])
        current, prior, subsequent = self._partition(entity_hits, chapter, direction)
        events = self._causal_events(entity_id)
        contradictions = self._contradictions(events)
        return self._context(chapter_id, current, prior, subsequent, events, contradictions)

    def retrieve_chapter_context(self, chapter_id: str) -> RetrievalContext:
        """Return adjacent chapter evidence plus events and explicit source IDs."""
        chapter = self._chapter(chapter_id)
        current = tuple(self._hit(chapter.chapter_id, occurrence, 1.0, ("chapter",)) for occurrence in chapter.occurrences)
        related_entities = {entity_id for entity_id, found in self._entity_occurrences.items()
                            if any(found_chapter == chapter_id for found_chapter, _ in found)}
        all_hits = tuple(hit for entity_id in related_entities for hit in
                         (self._entity_hit(entity_id, found_chapter, occurrence)
                          for found_chapter, occurrence in self._entity_occurrences[entity_id]))
        _, prior, subsequent = self._partition(all_hits, chapter, "both")
        events = tuple(event for event in self._events.values() if event.chapter_id == chapter_id or
                       related_entities.intersection(event.entity_ids))
        return self._context(chapter_id, current, prior, subsequent, events, self._contradictions(events))

    def _build_text_indexes(self) -> None:
        for chapter in self.manifest.chapters:
            for index, occurrence in enumerate(chapter.occurrences):
                key = (chapter.chapter_id, index)
                bag = Counter(_tokens(occurrence.text))
                self._documents[key] = bag
                self._document_frequency.update(bag.keys())
                for term in bag:
                    self._lexical[term].add(key)

    def _cosine(self, left: Counter[str], right: Counter[str]) -> float:
        def weight(term: str, count: int) -> float:
            return count * (math.log((1 + len(self._documents)) / (1 + self._document_frequency[term])) + 1)
        dot = sum(weight(term, count) * weight(term, right.get(term, 0)) for term, count in left.items())
        left_norm = math.sqrt(sum(weight(term, count) ** 2 for term, count in left.items()))
        right_norm = math.sqrt(sum(weight(term, count) ** 2 for term, count in right.items()))
        return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0

    def _partition(self, hits: Iterable[SearchHit], focus: Chapter, direction: Direction) -> tuple[tuple[SearchHit, ...], tuple[SearchHit, ...], tuple[SearchHit, ...]]:
        if direction not in {"prior", "subsequent", "both"}:
            raise ValueError("direction must be 'prior', 'subsequent', or 'both'")
        current: list[SearchHit] = []; prior: list[SearchHit] = []; subsequent: list[SearchHit] = []
        for hit in hits:
            order = self._chapters[hit.chapter_id].publication_order
            if hit.chapter_id == focus.chapter_id: current.append(hit)
            elif order < focus.publication_order and direction in {"prior", "both"}: prior.append(hit)
            elif order > focus.publication_order and direction in {"subsequent", "both"}: subsequent.append(hit)
        sort = lambda items: tuple(sorted(items, key=lambda h: (self._chapters[h.chapter_id].publication_order, h.source)))
        return sort(current), sort(prior), sort(subsequent)

    def _causal_events(self, entity_id: str) -> tuple[Event, ...]:
        roots = self._event_entities[entity_id]
        selected = set(roots)
        pending = list(roots)
        while pending:
            event = self._events[pending.pop()]
            for cause in event.causes:
                if cause in self._events and cause not in selected:
                    selected.add(cause); pending.append(cause)
        return tuple(sorted((self._events[event_id] for event_id in selected), key=lambda e: (self._chapters[e.chapter_id].publication_order, e.event_id)))

    def _contradictions(self, events: Iterable[Event]) -> tuple[Event, ...]:
        ids = {event.event_id for event in events}
        contradiction_ids = {
            contradiction_id
            for selected_id in ids
            for contradiction_id in self._events[selected_id].contradicts
            if contradiction_id in self._events
        }
        return tuple(sorted((self._events[event_id] for event_id in contradiction_ids), key=lambda event: event.event_id))

    def _context(self, chapter_id: str, current: tuple[SearchHit, ...], prior: tuple[SearchHit, ...], subsequent: tuple[SearchHit, ...], events: Iterable[Event], contradictions: Iterable[Event]) -> RetrievalContext:
        sources = tuple(sorted({hit.source for hit in (*current, *prior, *subsequent)} | {self._chapters[event.chapter_id].source.file for event in events}))
        return RetrievalContext(chapter_id, current, prior, subsequent, tuple(events), tuple(contradictions), sources)

    def _chapter(self, chapter_id: str) -> Chapter:
        try: return self._chapters[chapter_id]
        except KeyError as exc: raise KeyError(f"unknown chapter_id: {chapter_id}") from exc

    def _entity_hit(self, entity_id: str, chapter_id: str, occurrence: Occurrence) -> SearchHit:
        event_ids = tuple(sorted(self._event_entities[entity_id]))
        return self._hit(chapter_id, occurrence, 1.0, ("entity_graph",), (entity_id,), event_ids)

    def _hit(self, chapter_id: str, occurrence: Occurrence, score: float, channels: tuple[str, ...], entity_ids: tuple[str, ...] = (), event_ids: tuple[str, ...] = ()) -> SearchHit:
        return SearchHit(chapter_id, occurrence, score, channels, entity_ids, event_ids)


def _normalise(value: str) -> str:
    return " ".join(_tokens(value))
