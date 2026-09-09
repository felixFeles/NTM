"""Import files below ``story/source`` into an immutable manifest."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

from .models import Chapter, Locator, Manifest, Occurrence, SourceRecord, frozen_mapping

_SENTENCES = re.compile(r"(?<=[.!?…])(?:[\"'»”)]*)\s+|\n+(?=\S)")
_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_CHAPTER_EXTENSIONS = {".txt", ".md", ".markdown"}


class StoryIngestor:
    """Import a source tree without assigning identifiers from file iteration order."""

    def __init__(self, source_root: str | Path = "story/source") -> None:
        self.source_root = Path(source_root)

    def ingest(self) -> Manifest:
        if not self.source_root.is_dir():
            raise FileNotFoundError(f"source directory does not exist: {self.source_root}")
        files = sorted(
            (p for p in self.source_root.rglob("*") if p.is_file() and p.suffix.lower() in _CHAPTER_EXTENSIONS),
            key=lambda p: p.relative_to(self.source_root).as_posix(),
        )
        chapters = tuple(self._chapter(path, position) for position, path in enumerate(files, start=1))
        sources = tuple(chapter.source for chapter in chapters)
        canonical = {
            "sources": [{"file": s.file, "sha256": s.sha256, "size": s.size} for s in sources],
            "chapters": [
                {"chapter_id": c.chapter_id, "publication_order": c.publication_order,
                 "chronological_order": c.chronological_order, "flashback": c.flashback,
                 "flashback_of": c.flashback_of}
                for c in chapters
            ],
        }
        digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return Manifest(str(self.source_root), sources, chapters, digest)

    def _chapter(self, path: Path, default_order: int) -> Chapter:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        relative = path.relative_to(self.source_root).as_posix()
        metadata, body = _split_front_matter(text)
        stem = re.sub(r"[^a-z0-9]+", "-", Path(relative).with_suffix("").as_posix().lower()).strip("-")
        chapter_id = str(metadata.get("chapter_id") or f"chapter:{stem}")
        source = SourceRecord(relative, hashlib.sha256(raw).hexdigest(), len(raw))
        return Chapter(
            chapter_id=chapter_id,
            title=str(metadata.get("title") or Path(relative).stem),
            source=source,
            publication_order=_as_int(metadata.get("publication_order"), default_order),
            chronological_order=_as_int(metadata.get("chronological_order"), default_order),
            flashback=_as_bool(metadata.get("flashback"), False),
            flashback_of=_as_optional_string(metadata.get("flashback_of")),
            metadata=frozen_mapping(metadata),
            occurrences=tuple(_occurrences(relative, body)),
        )


def _split_front_matter(text: str) -> tuple[dict[str, object], str]:
    match = _FRONT_MATTER.match(text)
    if not match:
        return {}, text
    metadata: dict[str, object] = {}
    for line in match.group(1).splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"\'')
    return metadata, text[match.end():]


def _occurrences(file: str, body: str) -> Iterable[Occurrence]:
    for paragraph_number, paragraph in enumerate(re.split(r"\n\s*\n", body.strip()), start=1):
        cleaned = " ".join(line.strip().lstrip("#").strip() for line in paragraph.splitlines()).strip()
        if not cleaned:
            continue
        for phrase_number, phrase in enumerate(_SENTENCES.split(cleaned), start=1):
            phrase = phrase.strip()
            if phrase:
                yield Occurrence(phrase, Locator(file, paragraph_number, phrase_number))


def _as_int(value: object, default: int) -> int:
    try:
        return int(str(value)) if value not in (None, "") else default
    except ValueError as exc:
        raise ValueError(f"expected integer metadata value, got {value!r}") from exc


def _as_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    return str(value).lower() in {"1", "true", "yes", "on"}


def _as_optional_string(value: object) -> str | None:
    return str(value) if value not in (None, "") else None
