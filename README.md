# DocsHelper

A production-ready CLI tool for crawling documentation websites and answering questions using Retrieval-Augmented Generation (RAG).

## Overview

DocsHelper provides a complete RAG pipeline with:
- **Advanced crawling**: Concurrent async fetching, robots.txt respect, sitemap parsing
- **Smart indexing**: Semantic chunking with OpenAI embeddings and Chroma vector store
- **Quality retrieval**: Context-grounded answers with source citations and metrics tracking
- **LangSmith integration**: Full observability for embeddings and LLM calls
- **Multi-dataset support**: Manage and query multiple documentation sources

**Perfect for:**
- Building internal documentation Q&A systems
- Production-grade crawling and data pipeline work

## Features

### Crawling Engine
- Concurrent async fetching with configurable parallelism
- robots.txt respect with per-domain caching
- Sitemap.xml parsing and URL seeding
- Depth/page limits and request delay control
- Smart content extraction from HTML

### Indexing & Retrieval
- Semantic chunking with configurable overlap
- OpenAI embeddings with batch processing
- Persistent Chroma vector store (per-dataset collections)
- Top-k retrieval with similarity scoring

### Quality & Observability
- Local metrics tracking (retrieval scores, query history)
- LangSmith integration for full LLM/embedding tracing
- Source citation in all answers
- Context-grounded responses (LLM instructed to use only retrieved context)

### Developer Experience
- Clean CLI with 7 intuitive commands
- Multi-dataset management (switch between doc sources)
- Absolute path configuration (run from any directory)
- Production-ready error handling and validation

## Architecture

1. `crawl`: Website HTML -> cleaned text pages -> local JSONL cache
2. `index`: cached pages -> semantic chunks -> embeddings -> Chroma vector DB
3. `ask`: question -> query embedding -> top-k retrieval -> LLM answer with context

## Package Structure

```
src/docshelper/
├── cli.py              # Typer CLI interface
├── config.py           # Configuration management
├── models.py           # Data models
├── crawling/           # Web fetching & discovery
│   ├── crawler.py      # Async concurrent crawler
│   ├── robots.py       # robots.txt checker
│   └── sitemap.py      # Sitemap XML parser
├── indexing/           # Chunking & embeddings
│   ├── processor.py    # Semantic chunking
│   ├── embeddings.py   # OpenAI embedding wrapper
│   └── vector_store.py # Chroma vector DB interface
├── retrieval/          # RAG & LLM
│   ├── rag.py          # RAG prompt assembly
│   └── llm.py          # LLM provider abstraction
├── storage/            # Local caching
│   └── cache_manager.py # JSONL cache storage
└── observability/      # Metrics & tracking
    └── metrics.py      # Retrieval quality metrics
```

## Quick Start

### 1. Install dependencies

```bash
pip install -e .
```

This uses `pyproject.toml` to install the package and runtime dependencies, and registers the `docshelper` CLI script.

For development tooling:

```bash
pip install -e ".[dev]"
```

Note: `requirements.txt` is kept for compatibility, but `pyproject.toml` is the source of truth for package installation.

### 2. Configure environment

```bash
copy .env.example .env
```

Edit `.env` and set:
- `OPENAI_API_KEY` (required)
- `DOCSHELPER_CACHE_DIR` and `DOCSHELPER_CHROMA_DIR` with absolute paths

**Example:**
```bash
DOCSHELPER_CACHE_DIR=/path/to/project/.docshelper/cache
DOCSHELPER_CHROMA_DIR=/path/to/project/.docshelper/chroma
```

**Optional** - Enable LangSmith monitoring:
- `LANGCHAIN_TRACING_V2=true`
- `LANGCHAIN_API_KEY` (get from https://smith.langchain.com/)
- `LANGCHAIN_PROJECT=docshelper`

### 3. Crawl documentation

```bash
docshelper crawl https://python.langchain.com/docs --dataset langchain --max-depth 2 --max-pages 120
```

### 4. Index dataset

```bash
docshelper index langchain
```

### 5. Ask questions

```bash
docshelper ask --dataset langchain "How do I build a basic chain?"
```

## CLI Commands

**Crawl**
```bash
docshelper crawl <url> --dataset <name> \
  [--max-depth N] [--max-pages N] [--delay S] \
  [--sitemap] [--respect-robots/--no-respect-robots] [--concurrent N]
```

**Index**
```bash
docshelper index <dataset> [--chunk-words N] [--overlap-words N]
```

**Ask**
```bash
docshelper ask --dataset <name> <question> [--top-k N]
```

**List Datasets**
```bash
docshelper list-docs
```

**Status**
```bash
docshelper status [--dataset <name>]
```

**Metrics**
```bash
docshelper metrics [--dataset <name>] [--recent N]
```

**Config**
```bash
docshelper config
```

## Example Workflows

### Standard crawl with concurrent fetching
```bash
docshelper crawl https://fastapi.tiangolo.com/ --dataset fastapi \
  --max-depth 2 --max-pages 80 --concurrent 10
docshelper index fastapi
docshelper ask --dataset fastapi "How do I define query parameters?"
docshelper metrics --dataset fastapi
```

### Sitemap-based crawl (faster for large sites)
```bash
docshelper crawl https://python.langchain.com/docs --dataset langchain \
  --sitemap --max-pages 200 --concurrent 15
docshelper index langchain
docshelper ask --dataset langchain "What is LCEL?"
docshelper metrics --dataset langchain
```

## Notes

- **robots.txt**: Respected by default; use `--no-respect-robots` to bypass (not recommended)
- **Concurrency**: Default 5 concurrent requests; increase for faster crawling but watch rate limits
- **Sitemap mode**: Faster for large sites with comprehensive sitemaps
- **Metrics**: Automatically tracked in `.docshelper/cache/metrics/query_metrics.jsonl`
- **LangSmith**: Optional full-stack tracing for debugging and optimization
- **Context grounding**: LLM only uses retrieved context; states when insufficient
- **Best results**: Sites with clear `<main>`/`<article>` semantic HTML structure

## Technical Stack

- **Python 3.10+** with asyncio for concurrent crawling
- **OpenAI API** for embeddings (text-embedding-3-small) and chat (gpt-4o-mini)
- **Chroma** for persistent vector storage
- **aiohttp** for async HTTP requests
- **BeautifulSoup4** for HTML parsing
- **Typer** for CLI interface
- **LangSmith** for optional observability

## Project Structure

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Development

Install with dev dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

Code formatting:
```bash
black src/ tests/
ruff check src/ tests/
```

## Documentation

- [Getting Started Guide](docs/GETTING_STARTED.md) - Detailed setup and usage
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and components
- [Quick Reference](docs/QUICK_REFERENCE.md) - Command cheat sheet and tips

## License

MIT
