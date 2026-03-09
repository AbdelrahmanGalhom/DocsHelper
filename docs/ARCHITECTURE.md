# Architecture

DocsHelper is organized into domain-specific subpackages for maintainability and clarity:

```
src/docshelper/
├── crawling/          # Web fetching, robots.txt, sitemap parsing
├── indexing/          # Chunking, embeddings, vector storage
├── retrieval/         # RAG engine, LLM providers
├── storage/           # Local cache management
└── observability/     # Metrics collection
```

## Three-Stage RAG Pipeline

DocsHelper uses a three-stage RAG pipeline with production-ready crawling features:

## 1. Crawl Stage

**Components:**
- `DocumentationCrawler`: Async concurrent fetcher with configurable parallelism (default: 5 requests at once)
- `RobotsChecker`: Caches and respects robots.txt per domain; extracts crawl delays
- `SitemapParser`: Parses sitemap.xml and sitemap index files to seed crawl queue

**Crawl modes:**
- **Spider mode** (default): BFS traversal with depth limits, discovers links from pages
- **Sitemap mode** (`--sitemap`): Seeds queue from sitemap.xml, faster for well-structured sites

**Features:**
- Domain-restricted crawling (stays within original domain)
- URL normalization (removes fragments, trailing slashes, query params)
- Content extraction from `<main>`, `<article>`, or `<body>` tags
- Filters out scripts, styles, nav, footer, sidebar elements
- Configurable delay between request batches

## 2. Index Stage

- `CacheManager`: Loads cached pages from JSONL
- `SemanticChunker`: Converts pages into overlapping word-based chunks (default: 300 words with 60-word overlap)
- `OpenAIEmbedder`: Creates vector embeddings via OpenAI API (batch processing for efficiency)
- `ChromaStore`: Persists embeddings/documents per dataset collection with upsert for deduplication

## 3. Ask Stage

- Query text is embedded using `OpenAIEmbedder`
- Top-k chunks retrieved from Chroma (default: 5) with distance scores
- `RAGEngine`: Builds grounded prompt with retrieved context + source metadata
- `OpenAIProvider` generates the final answer with automatic LangSmith tracing when configured
- `MetricsCollector`: Records query, retrieval scores, chunk counts, answer length to JSONL

## Storage Layout

```
.docshelper/
├── cache/
│   ├── <dataset>/
│   │   ├── pages.jsonl          # Crawled pages (one per line)
│   │   └── manifest.json        # Metadata (source URL, last crawl time)
│   └── metrics/
│       └── query_metrics.jsonl  # Query history with retrieval scores
└── chroma/                       # Chroma vector DB persistent storage
    └── <collection>/             # One collection per dataset
```

## Observability

DocsHelper provides two layers of observability:

1. **Local Metrics** (`MetricsCollector`):
   - Retrieval quality scores (distances/similarities)
   - Chunk counts and answer lengths
   - Stored in `.docshelper/cache/metrics/query_metrics.jsonl`
   - Queryable via `docshelper metrics` command

2. **LangSmith Tracing** (optional):
   - Full LLM prompt/response logging
   - Token usage and latency tracking
   - Multi-step trace visualization (retrieval → prompt → LLM → response)
   - Web UI for debugging and dataset export
   - Enabled via `LANGCHAIN_TRACING_V2` environment variable

## Concurrency Model

- Crawler uses `asyncio.gather()` to fetch multiple URLs in parallel batches
- Batch size controlled by `concurrent_requests` parameter (default: 5)
- Each batch respects `delay_seconds` between completion and next batch
- robots.txt crawl-delay overrides the configured delay if present
