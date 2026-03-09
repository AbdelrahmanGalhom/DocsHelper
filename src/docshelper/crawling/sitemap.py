"""Sitemap discovery and parsing utilities."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

import httpx


class SitemapParser:
    """Parse sitemap documents and return crawlable page URLs."""

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def parse_sitemap(self, base_url: str) -> list[str]:
        """Parse sitemap documents for a site and return URL entries.

        Args:
            base_url: Root URL used for sitemap discovery.

        Returns:
            list[str]: URLs extracted from sitemap files.
        """
        urls: list[str] = []
        sitemap_url = self._find_sitemap_url(base_url)
        
        if not sitemap_url:
            return urls
        
        content = self._fetch_url(sitemap_url)
        if not content:
            return urls
        
        try:
            root = ET.fromstring(content)
            # Handle sitemap index (sitemap of sitemaps)
            if "sitemapindex" in root.tag:
                for sitemap_elem in root.findall(".//{*}sitemap"):
                    loc = sitemap_elem.find("{*}loc")
                    if loc is not None and loc.text:
                        sub_urls = self._parse_sitemap_content(self._fetch_url(loc.text))
                        urls.extend(sub_urls)
            else:
                # Regular sitemap
                urls = self._parse_sitemap_content(content)
        except ET.ParseError:
            pass
        
        return urls

    def _find_sitemap_url(self, base_url: str) -> str | None:
        """Try common sitemap locations for a given site.

        Args:
            base_url: Root URL used to build sitemap candidates.

        Returns:
            str | None: First reachable sitemap URL, if found.
        """
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        candidates = [
            urljoin(base_url, "sitemap.xml"),
            urljoin(base, "/sitemap.xml"),
            urljoin(base, "/sitemap_index.xml"),
        ]
        
        for url in candidates:
            if self._url_exists(url):
                return url
        
        return None

    def _url_exists(self, url: str) -> bool:
        """Check whether a URL is reachable.

        Args:
            url: URL to probe.

        Returns:
            bool: True when the endpoint returns HTTP 200.
        """
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.head(url, follow_redirects=True)
                return response.status_code == 200
        except Exception:
            return False

    def _fetch_url(self, url: str) -> str | None:
        """Fetch URL content.

        Args:
            url: URL to fetch.

        Returns:
            str | None: Response text on success, otherwise None.
        """
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    return response.text
        except Exception:
            pass
        return None

    def _parse_sitemap_content(self, content: str | None) -> list[str]:
        """Parse sitemap XML content and extract URLs.

        Args:
            content: Raw XML content.

        Returns:
            list[str]: URL entries found in `<url><loc>` elements.
        """
        if not content:
            return []
        
        urls: list[str] = []
        try:
            root = ET.fromstring(content)
            for url_elem in root.findall(".//{*}url"):
                loc = url_elem.find("{*}loc")
                if loc is not None and loc.text:
                    urls.append(loc.text)
        except ET.ParseError:
            pass
        
        return urls
