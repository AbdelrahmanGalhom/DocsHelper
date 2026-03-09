"""Configuration loading from environment variables and .env files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    """Application settings used across crawling, indexing, and retrieval."""

    openai_api_key: str
    openai_chat_model: str
    openai_embedding_model: str
    cache_root: Path
    chroma_dir: Path
    user_agent: str
    request_timeout_seconds: int


def get_settings() -> Settings:
    """Load settings from environment variables and .env.

    Returns:
        Settings: Fully populated settings object with defaults applied.
    """
    load_dotenv()

    cache_root = Path(os.getenv("DOCSHELPER_CACHE_DIR", ".docshelper/cache")).resolve()
    chroma_dir = Path(os.getenv("DOCSHELPER_CHROMA_DIR", ".docshelper/chroma")).resolve()

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        cache_root=cache_root,
        chroma_dir=chroma_dir,
        user_agent=os.getenv("DOCSHELPER_USER_AGENT", "DocsHelper/0.1 (+https://example.local)"),
        request_timeout_seconds=int(os.getenv("DOCSHELPER_TIMEOUT", "20")),
    )
