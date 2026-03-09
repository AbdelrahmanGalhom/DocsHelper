from pathlib import Path

from docshelper.models import CrawledPage
from docshelper.storage import CacheManager


def test_cache_manager_save_and_load(tmp_path: Path) -> None:
    cache = CacheManager(tmp_path)
    page = CrawledPage(
        url="https://example.com",
        title="Example",
        text="Some text",
        depth=0,
        crawled_at="2026-03-09T00:00:00+00:00",
    )

    cache.save_pages(dataset="example", pages=[page], source_url="https://example.com")
    loaded = cache.load_pages("example")

    assert len(loaded) == 1
    assert loaded[0].url == "https://example.com"
