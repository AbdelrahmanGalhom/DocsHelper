"""DocsHelper: CLI tool for crawling documentation and RAG-based Q&A."""

from docshelper.config import get_settings
from docshelper.crawling import DocumentationCrawler, RobotsChecker, SitemapParser
from docshelper.indexing import ChromaStore, OpenAIEmbedder, SemanticChunker
from docshelper.models import AskResult, Chunk, CrawledPage
from docshelper.observability import MetricsCollector
from docshelper.retrieval import BaseLLMProvider, OpenAIProvider, RAGEngine
from docshelper.storage import CacheManager

__all__ = [
    "__version__",
    # Config
    "get_settings",
    # Models
    "CrawledPage",
    "Chunk",
    "AskResult",
    # Crawling
    "DocumentationCrawler",
    "RobotsChecker",
    "SitemapParser",
    # Indexing
    "SemanticChunker",
    "OpenAIEmbedder",
    "ChromaStore",
    # Retrieval
    "RAGEngine",
    "BaseLLMProvider",
    "OpenAIProvider",
    # Storage
    "CacheManager",
    # Observability
    "MetricsCollector",
]

__version__ = "0.1.0"
