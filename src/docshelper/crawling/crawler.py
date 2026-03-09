"""Asynchronous crawler for documentation websites."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from docshelper.models import CrawledPage

from .robots import RobotsChecker
from .sitemap import SitemapParser


class DocumentationCrawler:
    """Crawl documentation pages with robots checks and concurrency controls."""

    def __init__(
        self,
        user_agent: str,
        timeout_seconds: int = 20,
        delay_seconds: float = 0.4,
        respect_robots: bool = True,
        concurrent_requests: int = 5,
    ) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.delay_seconds = delay_seconds
        self.respect_robots = respect_robots
        self.concurrent_requests = concurrent_requests
        self.robots_checker = RobotsChecker(user_agent) if respect_robots else None

    async def crawl(
        self,
        root_url: str,
        max_depth: int,
        max_pages: int,
        use_sitemap: bool = False,
    ) -> list[CrawledPage]:
        """Crawl a root URL and return extracted pages.

        Args:
            root_url: Root URL for the documentation website.
            max_depth: Maximum link depth to traverse.
            max_pages: Maximum number of pages to return.
            use_sitemap: Whether to seed URLs from sitemap.xml.

        Returns:
            list[CrawledPage]: Extracted pages with text and metadata.
        """
        allowed_domain = urlparse(root_url).netloc
        
        # Initialize queue with sitemap URLs if requested
        if use_sitemap:
            sitemap_urls = await self._get_sitemap_urls(root_url)
            queue: deque[tuple[str, int]] = deque([(url, 0) for url in sitemap_urls[:max_pages]])
        else:
            queue = deque([(root_url, 0)])
        
        visited: set[str] = set()
        pages: list[CrawledPage] = []

        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        headers = {"User-Agent": self.user_agent}

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            while queue and len(pages) < max_pages:
                # Batch processing: collect up to concurrent_requests URLs
                batch: list[tuple[str, int]] = []
                for _ in range(min(self.concurrent_requests, len(queue))):
                    if not queue:
                        break
                    url, depth = queue.popleft()
                    clean = self._normalize(url)
                    
                    if clean in visited or depth > max_depth:
                        continue
                    
                    # Check robots.txt
                    if self.robots_checker and not self.robots_checker.can_fetch(clean):
                        continue
                    
                    visited.add(clean)
                    batch.append((clean, depth))
                
                if not batch:
                    continue
                
                # Fetch all URLs in batch concurrently
                results = await asyncio.gather(
                    *[self._fetch_and_parse(session, url, depth, allowed_domain, max_depth, queue)
                      for url, depth in batch],
                    return_exceptions=True
                )
                
                # Collect successful pages
                for result in results:
                    if isinstance(result, CrawledPage) and result.text.strip():
                        pages.append(result)
                        if len(pages) >= max_pages:
                            break
                
                # Respect delay between batches
                if queue:
                    await asyncio.sleep(self.delay_seconds)

        return pages

    async def _fetch_and_parse(
        self,
        session: aiohttp.ClientSession,
        url: str,
        depth: int,
        allowed_domain: str,
        max_depth: int,
        queue: deque[tuple[str, int]],
    ) -> CrawledPage | None:
        """Fetch and parse a single URL and enqueue discovered links.

        Args:
            session: Active aiohttp session.
            url: URL to fetch.
            depth: Current crawl depth for this URL.
            allowed_domain: Domain boundary for link traversal.
            max_depth: Maximum allowed crawl depth.
            queue: Crawl queue used to append discovered links.

        Returns:
            CrawledPage | None: Parsed page when successful, else None.
        """
        html = await self._fetch_html(session, url)
        if not html:
            return None

        page = self._extract_page(url, html, depth)
        
        # Extract and queue links if not at max depth
        if depth < max_depth:
            for next_url in self._extract_links(url, html):
                parsed = urlparse(next_url)
                if parsed.netloc == allowed_domain:
                    queue.append((next_url, depth + 1))
        
        return page

    async def _get_sitemap_urls(self, base_url: str) -> list[str]:
        """Resolve sitemap URLs asynchronously.

        Args:
            base_url: Root site URL used for sitemap discovery.

        Returns:
            list[str]: URLs discovered from sitemap documents.
        """
        loop = asyncio.get_event_loop()
        parser = SitemapParser(timeout_seconds=self.timeout_seconds)
        return await loop.run_in_executor(None, parser.parse_sitemap, base_url)

    async def _fetch_html(self, session: aiohttp.ClientSession, url: str) -> str | None:
        """Fetch URL content and return HTML for successful text/html responses.

        Args:
            session: Active aiohttp session.
            url: URL to fetch.

        Returns:
            str | None: HTML content when available; otherwise None.
        """
        try:
            async with session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    return None
                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    return None
                return await response.text(errors="ignore")
        except aiohttp.ClientError:
            return None

    def _extract_page(self, url: str, html: str, depth: int) -> CrawledPage:
        """Extract a normalized page object from HTML.

        Args:
            url: Source URL.
            html: Raw HTML response body.
            depth: Crawl depth for this page.

        Returns:
            CrawledPage: Parsed page with cleaned text content.
        """
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript", "svg", "footer", "nav", "aside"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else url

        main_candidate = soup.find("main") or soup.find("article") or soup.body or soup
        text = main_candidate.get_text("\n", strip=True)

        return CrawledPage(
            url=url,
            title=title,
            text=text,
            depth=depth,
            crawled_at=datetime.now(timezone.utc).isoformat(),
        )

    def _extract_links(self, base_url: str, html: str) -> Iterable[str]:
        """Yield normalized absolute HTTP(S) links found in anchor tags.

        Args:
            base_url: URL used to resolve relative links.
            html: HTML content to scan.

        Yields:
            str: Normalized absolute link.
        """
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href or href.startswith("mailto:") or href.startswith("javascript:"):
                continue
            absolute = self._normalize(urljoin(base_url, href))
            if absolute.startswith("http://") or absolute.startswith("https://"):
                yield absolute

    def _normalize(self, url: str) -> str:
        """Normalize URL for deduplication.

        Args:
            url: URL to normalize.

        Returns:
            str: URL without fragment/query and with stable path formatting.
        """
        normalized, _ = urldefrag(url)
        parsed = urlparse(normalized)
        path = parsed.path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return parsed._replace(path=path, query="").geturl()
