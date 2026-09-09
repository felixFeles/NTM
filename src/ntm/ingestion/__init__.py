"""Deterministic source import and canon-safe adaptation helpers."""

from .author_material import (
    IngestionResult,
    MaterialValidationError,
    facts_available_for_dialogue,
    find_conflicts,
    ingest_author_material,
)
from .models import Chapter, Locator, Manifest, Occurrence, SourceRecord
from .service import StoryIngestor

__all__ = [
    "Chapter",
    "IngestionResult",
    "Locator",
    "Manifest",
    "MaterialValidationError",
    "Occurrence",
    "SourceRecord",
    "StoryIngestor",
    "facts_available_for_dialogue",
    "find_conflicts",
    "ingest_author_material",
]
