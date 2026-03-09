"""CLI entrypoints for crawling, indexing, and querying documentation."""

from __future__ import annotations

import asyncio
import json

import typer
from dotenv import load_dotenv

from docshelper.config import get_settings
from docshelper.crawling import DocumentationCrawler
from docshelper.indexing import OpenAIEmbedder, SemanticChunker
from docshelper.indexing import ChromaStore
from docshelper.observability import MetricsCollector
from docshelper.retrieval import OpenAIProvider, RAGEngine
from docshelper.storage import CacheManager

app = typer.Typer(help="DocsHelper CLI: crawl docs and query them with RAG.")


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Documentation root URL."),
    dataset: str = typer.Option(..., "--dataset", "-d", help="Dataset name used for local cache."),
    max_depth: int = typer.Option(2, help="Maximum crawl depth."),
    max_pages: int = typer.Option(100, help="Maximum number of pages to crawl."),
    delay: float = typer.Option(0.4, help="Delay between requests in seconds."),
    use_sitemap: bool = typer.Option(False, "--sitemap", help="Use sitemap.xml for crawling."),
    respect_robots: bool = typer.Option(True, "--respect-robots/--no-respect-robots", help="Respect robots.txt."),
    concurrent: int = typer.Option(5, help="Number of concurrent requests."),
) -> None:
    """Crawl a documentation site and cache extracted pages.

    Args:
        url: Root documentation URL to crawl.
        dataset: Dataset name used for local cache storage.
        max_depth: Maximum crawl depth from the root page.
        max_pages: Maximum number of pages to store.
        delay: Delay in seconds between crawl batches.
        use_sitemap: Whether to seed crawling from sitemap.xml.
        respect_robots: Whether to enforce robots.txt rules.
        concurrent: Number of concurrent URL fetches.
    """
    settings = get_settings()
    cache = CacheManager(settings.cache_root)
    crawler = DocumentationCrawler(
        user_agent=settings.user_agent,
        timeout_seconds=settings.request_timeout_seconds,
        delay_seconds=delay,
        respect_robots=respect_robots,
        concurrent_requests=concurrent,
    )

    mode = "sitemap" if use_sitemap else "spider"
    typer.echo(f"Crawling {url} (mode={mode}, depth={max_depth}, pages={max_pages}, concurrent={concurrent}) ...")
    pages = asyncio.run(crawler.crawl(url, max_depth=max_depth, max_pages=max_pages, use_sitemap=use_sitemap))
    cache.save_pages(dataset=dataset, pages=pages, source_url=url)
    typer.echo(f"Saved {len(pages)} pages to dataset '{dataset}'.")


@app.command()
def index(
    dataset: str = typer.Argument(..., help="Dataset name to index."),
    chunk_words: int = typer.Option(300, help="Target words per chunk."),
    overlap_words: int = typer.Option(60, help="Overlap words per chunk."),
) -> None:
    """Chunk cached pages and index embeddings into Chroma.

    Args:
        dataset: Dataset name to load from local cache.
        chunk_words: Target words per chunk.
        overlap_words: Overlap words between adjacent chunks.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise typer.BadParameter("OPENAI_API_KEY is required for indexing.")

    cache = CacheManager(settings.cache_root)
    pages = cache.load_pages(dataset)
    if not pages:
        raise typer.BadParameter(f"No cached pages found for dataset '{dataset}'. Run crawl first.")

    chunker = SemanticChunker(target_words=chunk_words, overlap_words=overlap_words)
    chunks = chunker.chunk_pages(pages)
    if not chunks:
        raise typer.BadParameter("No chunks produced. Try crawling more pages.")

    embedder = OpenAIEmbedder(api_key=settings.openai_api_key, model=settings.openai_embedding_model)
    store = ChromaStore(persist_dir=str(settings.chroma_dir))

    typer.echo(f"Embedding {len(chunks)} chunks ...")
    vectors = embedder.embed_texts([chunk.text for chunk in chunks])
    inserted = store.upsert_chunks(dataset=dataset, chunks=chunks, embeddings=vectors)

    typer.echo(f"Indexed {inserted} chunks into Chroma collection '{dataset}'.")


@app.command()
def ask(
    dataset: str = typer.Option(..., "--dataset", "-d", help="Dataset to query."),
    question: str = typer.Argument(..., help="Your question."),
    top_k: int = typer.Option(5, help="Top-k retrieved chunks."),
) -> None:
    """Answer a question using RAG over a selected dataset.

    Args:
        dataset: Dataset name to query.
        question: User question to answer.
        top_k: Number of chunks to retrieve.
    """
    settings = get_settings()
    
    if not settings.openai_api_key:
        raise typer.BadParameter("OPENAI_API_KEY is required for embeddings and LLM.")
    
    store = ChromaStore(persist_dir=str(settings.chroma_dir))
    llm = OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_chat_model)
    embedder = OpenAIEmbedder(api_key=settings.openai_api_key, model=settings.openai_embedding_model)

    query_vector = embedder.embed_query(question)
    retrieved = store.query(dataset=dataset, query_embedding=query_vector, top_k=top_k)

    engine = RAGEngine(llm_provider=llm)
    result = engine.answer_question(question=question, retrieved=retrieved)

    # Record metrics
    metrics_collector = MetricsCollector(settings.cache_root / "metrics")
    query_metrics = metrics_collector.record_query(
        query=question,
        dataset=dataset,
        retrieved=retrieved,
        answer=result.answer,
    )

    typer.echo("\nAnswer:\n")
    typer.echo(result.answer)
    typer.echo("\nSources:")
    for src in result.sources:
        typer.echo(f"- {src}")
    typer.echo(f"\n[Retrieved {query_metrics.retrieved_chunks} chunks, avg score: {query_metrics.avg_score:.3f}]")


@app.command("list-docs")
def list_docs() -> None:
    """List available cached datasets and basic crawl stats."""
    settings = get_settings()
    cache = CacheManager(settings.cache_root)
    datasets = cache.list_datasets()

    if not datasets:
        typer.echo("No datasets found.")
        return

    for ds in datasets:
        stats = cache.dataset_stats(ds)
        typer.echo(
            f"- {stats['dataset']}: pages={stats['pages']}, "
            f"last_crawled_at={stats['last_crawled_at']}"
        )


@app.command()
def status(dataset: str = typer.Option(None, "--dataset", "-d", help="Optional dataset name.")) -> None:
    """Show cache and vector index counts.

    Args:
        dataset: Optional dataset name. If omitted, prints all datasets.
    """
    settings = get_settings()
    cache = CacheManager(settings.cache_root)
    store = ChromaStore(persist_dir=str(settings.chroma_dir))

    targets = [dataset] if dataset else cache.list_datasets()
    if not targets:
        typer.echo("No datasets found.")
        return

    for ds in targets:
        stats = cache.dataset_stats(ds)
        vector_count = store.collection_count(ds)
        typer.echo(json.dumps({**stats, "indexed_chunks": vector_count}, indent=2))


@app.command()
def config() -> None:
    """Print effective runtime configuration excluding secrets."""
    load_dotenv()
    settings = get_settings()
    payload = {
        "cache_root": str(settings.cache_root),
        "chroma_dir": str(settings.chroma_dir),
        "openai_chat_model": settings.openai_chat_model,
        "openai_embedding_model": settings.openai_embedding_model,
        "openai_api_key_configured": bool(settings.openai_api_key),
    }
    typer.echo(json.dumps(payload, indent=2))


@app.command()
def metrics(
    dataset: str = typer.Option(None, "--dataset", "-d", help="Optional dataset name to filter metrics."),
    recent: int = typer.Option(10, help="Number of recent queries to show."),
) -> None:
    """Show retrieval quality metrics summary and recent queries.

    Args:
        dataset: Optional dataset filter.
        recent: Number of recent query entries to display.
    """
    settings = get_settings()
    metrics_collector = MetricsCollector(settings.cache_root / "metrics")
    
    # Show summary stats
    stats = metrics_collector.get_stats(dataset=dataset)
    typer.echo("Metrics Summary:")
    typer.echo(json.dumps(stats, indent=2))
    
    # Show recent queries
    recent_queries = metrics_collector.get_recent_queries(limit=recent, dataset=dataset)
    if recent_queries:
        typer.echo(f"\nRecent {len(recent_queries)} Queries:")
        for q in recent_queries:
            typer.echo(f"- [{q.timestamp[:19]}] {q.query[:60]}... (score: {q.avg_score:.3f}, chunks: {q.retrieved_chunks})")


def main() -> None:
    """Run the Typer application entrypoint."""
    app()


if __name__ == "__main__":
    main()
