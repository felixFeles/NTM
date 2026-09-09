"""Domain primitives for Novel To Manhwa continuity work."""

from .ingestion import StoryIngestor
from .retrieval import HybridStoryIndex

__all__ = ["HybridStoryIndex", "StoryIngestor"]
