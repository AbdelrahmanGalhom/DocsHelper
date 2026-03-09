"""Core data models shared across the DocsHelper pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class CrawledPage:
    """Represents one crawled page with extracted text and metadata.

    Attributes:
        url: Source URL.
        title: Extracted page title.
        text: Cleaned visible text content.
        depth: Crawl depth where the page was found.
        crawled_at: UTC ISO-8601 crawl timestamp.
    """

    url: str
    title: str
    text: str
    depth: int
    crawled_at: str


@dataclass(slots=True)
class Chunk:
    """Represents one retrievable text chunk and metadata.

    Attributes:
        chunk_id: Stable unique ID for deduplication/upsert.
        text: Chunk content used for embedding and retrieval.
        metadata: Associated source metadata (URL, title, indexes).
    """

    chunk_id: str
    text: str
    metadata: dict[str, Any]


@dataclass(slots=True)
class AskResult:
    """Final answer payload returned by the RAG engine.

    Attributes:
        answer: Generated answer text.
        sources: Source URLs used to build context.
        retrieved_chunks: Number of chunks included in context.
        created_at: UTC timestamp when answer was created.
    """

    answer: str
    sources: list[str]
    retrieved_chunks: int
    created_at: datetime
