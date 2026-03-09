"""robots.txt helper utilities used by the crawler."""

from __future__ import annotations

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


class RobotsChecker:
    """Cache and query robots.txt policies per domain."""

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    def can_fetch(self, url: str) -> bool:
        """Check whether a URL is allowed by robots.txt.

        Args:
            url: Target URL to validate.

        Returns:
            bool: True when fetching is allowed.
        """
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        if base not in self._parsers:
            parser = RobotFileParser()
            parser.set_url(f"{base}/robots.txt")
            try:
                parser.read()
            except Exception:
                # If robots.txt cannot be fetched, allow by default
                pass
            self._parsers[base] = parser
        
        return self._parsers[base].can_fetch(self.user_agent, url)

    def get_crawl_delay(self, url: str) -> float | None:
        """Get crawl delay for a URL's domain if defined in robots.txt.

        Args:
            url: URL used to identify the domain.

        Returns:
            float | None: Crawl delay in seconds, or None if unspecified.
        """
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        if base in self._parsers:
            return self._parsers[base].crawl_delay(self.user_agent)
        return None
