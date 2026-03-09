"""Text chunking utilities for turning pages into retrievable units."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from docshelper.models import Chunk, CrawledPage


class SemanticChunker:
    """Create overlapping chunks from crawled documentation pages."""

    def __init__(self, target_words: int = 300, overlap_words: int = 60) -> None:
        self.target_words = target_words
        self.overlap_words = overlap_words

    def chunk_pages(self, pages: list[CrawledPage]) -> list[Chunk]:
        """Chunk all pages and return a flat list of chunks.

        Args:
            pages: Crawled pages to split.

        Returns:
            list[Chunk]: Chunked documents with retrieval metadata.
        """
        chunks: list[Chunk] = []
        for page in pages:
            chunks.extend(self._chunk_page(page))
        return chunks

    def _chunk_page(self, page: CrawledPage) -> list[Chunk]:
        segments = self._segment_by_structure(page.text)
        word_windows = self._windows(segments)

        out: list[Chunk] = []
        for idx, words in enumerate(word_windows):
            content = " ".join(words).strip()
            if len(content) < 120:
                continue
            chunk_id = self._build_chunk_id(page.url, idx, content)
            out.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=content,
                    metadata={
                        "url": page.url,
                        "title": page.title,
                        "depth": page.depth,
                        "chunk_index": idx,
                        "crawled_at": page.crawled_at,
                    },
                )
            )
        return out

    def _segment_by_structure(self, text: str) -> list[str]:
        normalized = re.sub(r"\n{3,}", "\n\n", text)
        segments = [block.strip() for block in normalized.split("\n\n") if block.strip()]
        return segments

    def _windows(self, segments: Iterable[str]) -> list[list[str]]:
        words = "\n".join(segments).split()
        windows: list[list[str]] = []
        i = 0
        n = len(words)

        while i < n:
            end = min(i + self.target_words, n)
            windows.append(words[i:end])
            if end == n:
                break
            i = max(0, end - self.overlap_words)

        return windows

    def _build_chunk_id(self, url: str, idx: int, content: str) -> str:
        digest = hashlib.sha1(f"{url}-{idx}-{content[:200]}".encode("utf-8")).hexdigest()
        return digest
