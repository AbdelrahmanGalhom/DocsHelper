from docshelper.crawling import RobotsChecker


def test_robots_checker_can_fetch() -> None:
    checker = RobotsChecker(user_agent="TestBot")
    # Most sites allow crawling by default
    result = checker.can_fetch("https://example.com/page")
    assert isinstance(result, bool)


def test_robots_checker_get_crawl_delay() -> None:
    checker = RobotsChecker(user_agent="TestBot")
    delay = checker.get_crawl_delay("https://example.com/page")
    # Should return None or a float
    assert delay is None or isinstance(delay, float)
