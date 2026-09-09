"""Material ingestion and canon-safe adaptation helpers."""

from .author_material import (
    IngestionResult,
    MaterialValidationError,
    facts_available_for_dialogue,
    find_conflicts,
    ingest_author_material,
)

__all__ = [
    "IngestionResult",
    "MaterialValidationError",
    "facts_available_for_dialogue",
    "find_conflicts",
    "ingest_author_material",
]
