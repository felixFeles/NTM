"""Immutable values emitted by ingestion.

The locator is deliberately made of source coordinates, rather than byte offsets:
editorial changes can be reviewed against the original file, paragraph and phrase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


def frozen_mapping(values: Mapping[str, object] | None = None) -> Mapping[str, object]:
    return MappingProxyType(dict(values or {}))


@dataclass(frozen=True, slots=True)
class Locator:
    file: str
    paragraph: int
    phrase: int

    @property
    def stable_id(self) -> str:
        return f"{self.file}:p{self.paragraph}:s{self.phrase}"


@dataclass(frozen=True, slots=True)
class Occurrence:
    text: str
    locator: Locator


@dataclass(frozen=True, slots=True)
class SourceRecord:
    file: str
    sha256: str
    size: int


@dataclass(frozen=True, slots=True)
class Chapter:
    chapter_id: str
    title: str
    source: SourceRecord
    publication_order: int
    chronological_order: int
    flashback: bool = False
    flashback_of: str | None = None
    metadata: Mapping[str, object] = field(default_factory=frozen_mapping)
    occurrences: tuple[Occurrence, ...] = ()


@dataclass(frozen=True, slots=True)
class Manifest:
    """A snapshot; its tuples and mappings cannot be changed after import."""

    source_root: str
    sources: tuple[SourceRecord, ...]
    chapters: tuple[Chapter, ...]
    manifest_sha256: str

    def chapter(self, chapter_id: str) -> Chapter:
        for chapter in self.chapters:
            if chapter.chapter_id == chapter_id:
                return chapter
        raise KeyError(f"unknown chapter_id: {chapter_id}")
