# Getting Started

## Prerequisites

- Python 3.10+
- OpenAI API key

## Install

```bash
pip install -e .
```

`pip install -e .` reads `pyproject.toml` and installs all runtime dependencies plus the `docshelper` console command.

For development dependencies (tests and linting):

```bash
pip install -e ".[dev]"
```

To verify the CLI entrypoint from `pyproject.toml`:

```bash
docshelper --help
```

## Configure

```bash
copy .env.example .env
```

Edit `.env` and set:
- `OPENAI_API_KEY`
- `DOCSHELPER_CACHE_DIR` and `DOCSHELPER_CHROMA_DIR` with absolute paths to your project directory

**Important:** The example `.env` uses absolute paths so you can run `docshelper` commands from any directory. Update these paths to match your installation location:
```
DOCSHELPER_CACHE_DIR=d:\Abdelrahman\DocsHelper\.docshelper\cache
DOCSHELPER_CHROMA_DIR=d:\Abdelrahman\DocsHelper\.docshelper\chroma
```

### Optional: Enable LangSmith Monitoring

To trace all LLM calls (prompts, responses, latency, token usage):

1. Get API key from https://smith.langchain.com/
2. Add to `.env`:
   ```
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your-key-here
   LANGCHAIN_PROJECT=docshelper
   ```

LangSmith will automatically capture:
- Full prompts with retrieved context
- LLM responses and token counts
- Request latency and model parameters
- Error traces and debugging info

View traces at https://smith.langchain.com/ in your `docshelper` project.

## Basic Usage

### 1. Crawl documentation

**Standard spider crawl:**
```bash
docshelper crawl https://python.langchain.com/docs --dataset langchain \
  --max-depth 2 --max-pages 100 --concurrent 10
```

**Sitemap-based crawl (faster):**
```bash
docshelper crawl https://python.langchain.com/docs --dataset langchain \
  --sitemap --max-pages 200 --concurrent 15
```

**Crawl without robots.txt restrictions (not recommended):**
```bash
docshelper crawl https://example.com/docs --dataset example \
  --no-respect-robots --max-pages 50
```

### 2. Index the dataset

```bash
docshelper index langchain
```

Customize chunking:
```bash
docshelper index langchain --chunk-words 400 --overlap-words 80
```

### 3. Ask questions

```bash
docshelper ask --dataset langchain "How do I create an agent?"
```

### 4. View status and metrics

**Dataset status:**
```bash
docshelper status --dataset langchain
```

**Query metrics:**
```bash
docshelper metrics --dataset langchain --recent 20
```

**List all datasets:**
```bash
docshelper list-docs
```

## Advanced Examples

### High-concurrency crawl for large docs

```bash
docshelper crawl https://docs.python.org/ --dataset python-docs \
  --sitemap --max-pages 500 --concurrent 20 --delay 0.2
```

### Multi-dataset workflow

```bash
# Crawl multiple doc sites
docshelper crawl https://fastapi.tiangolo.com --dataset fastapi --sitemap --max-pages 100
docshelper crawl https://python.langchain.com/docs --dataset langchain --max-pages 150

# Index both
docshelper index fastapi
docshelper index langchain

# Query each
docshelper ask --dataset fastapi "How do I use dependency injection?"
docshelper ask --dataset langchain "What is a retriever?"

# Compare metrics
docshelper metrics --dataset fastapi
docshelper metrics --dataset langchain
```

## Tips

- **Concurrency**: Start with `--concurrent 5-10`; increase if site handles load well
- **Sitemap mode**: Much faster for large sites with comprehensive sitemaps
- **robots.txt**: Respected by default; check crawl is allowed before large-scale crawls
- **Chunking**: Larger chunks (400-500 words) for conceptual questions; smaller (200-300) for factual lookups
- **Top-k retrieval**: Default 5; increase to 8-10 for complex multi-part questions
