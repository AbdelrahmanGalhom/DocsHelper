"""Local filesystem cache for crawled pages and dataset metadata."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from docshelper.models import CrawledPage


class CacheManager:
    """Read/write cached crawled pages and dataset manifests."""

    def __init__(self, cache_root: Path) -> None:
        self.cache_root = cache_root
        self.cache_root.mkdir(parents=True, exist_ok=True)

    def dataset_dir(self, dataset: str) -> Path:
        """Return the dataset directory path, creating it if needed.

        Args:
            dataset: Dataset name.

        Returns:
            Path: Dataset directory path.
        """
        path = self.cache_root / dataset
        path.mkdir(parents=True, exist_ok=True)
        return path

    def pages_file(self, dataset: str) -> Path:
        return self.dataset_dir(dataset) / "pages.jsonl"

    def manifest_file(self, dataset: str) -> Path:
        return self.dataset_dir(dataset) / "manifest.json"

    def save_pages(self, dataset: str, pages: list[CrawledPage], source_url: str) -> None:
        """Append newly crawled pages to cache and update manifest.

        Args:
            dataset: Dataset name.
            pages: Newly crawled pages.
            source_url: Root URL used for crawling.
        """
        pages_path = self.pages_file(dataset)
        seen_urls: set[str] = set()

        if pages_path.exists():
            for line in pages_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                seen_urls.add(record["url"])

        with pages_path.open("a", encoding="utf-8") as f:
            for page in pages:
                if page.url in seen_urls:
                    continue
                f.write(json.dumps(asdict(page), ensure_ascii=True) + "\n")

        self._write_manifest(dataset, source_url)

    def load_pages(self, dataset: str) -> list[CrawledPage]:
        """Load all cached pages for a dataset from JSONL format.

        Args:
            dataset: Dataset name.

        Returns:
            list[CrawledPage]: Parsed cached pages.
        """
        pages_path = self.pages_file(dataset)
        if not pages_path.exists():
            return []

        items: list[CrawledPage] = []
        for line in pages_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            items.append(CrawledPage(**record))
        return items

    def list_datasets(self) -> list[str]:
        """List available dataset folder names under the cache root.

        Returns:
            list[str]: Sorted dataset names.
        """
        if not self.cache_root.exists():
            return []
        return sorted([p.name for p in self.cache_root.iterdir() if p.is_dir()])

    def dataset_stats(self, dataset: str) -> dict[str, str | int]:
        """Return basic cache stats and manifest metadata for a dataset.

        Args:
            dataset: Dataset name.

        Returns:
            dict[str, str | int]: Cache and manifest summary.
        """
        pages = self.load_pages(dataset)
        manifest = {}
        manifest_path = self.manifest_file(dataset)
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {
            "dataset": dataset,
            "pages": len(pages),
            "source_url": manifest.get("source_url", ""),
            "last_crawled_at": manifest.get("last_crawled_at", ""),
        }

    def _write_manifest(self, dataset: str, source_url: str) -> None:
        payload = {
            "source_url": source_url,
            "last_crawled_at": datetime.now(timezone.utc).isoformat(),
        }
        self.manifest_file(dataset).write_text(json.dumps(payload, indent=2), encoding="utf-8")
