from docshelper.indexing import SemanticChunker
from docshelper.models import CrawledPage


def test_semantic_chunker_produces_chunks() -> None:
    page = CrawledPage(
        url="https://example.com/docs",
        title="Docs",
        text="\n\n".join(["word " * 200, "next " * 200]),
        depth=0,
        crawled_at="2026-03-09T00:00:00+00:00",
    )

    chunker = SemanticChunker(target_words=120, overlap_words=20)
    chunks = chunker.chunk_pages([page])

    assert len(chunks) >= 2
    assert all(chunk.metadata["url"] == page.url for chunk in chunks)
