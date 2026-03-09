# DocsHelper Quick Reference

## Crawl Modes Comparison

| Feature | Standard Crawl | Sitemap Crawl |
|---------|---------------|---------------|
| Command Flag | (default) | `--sitemap` |
| URL Discovery | Spider (follows links) | From sitemap.xml |
| Best For | Small/medium sites | Large sites with good sitemaps |
| Speed | Moderate | Very fast |
| Coverage | Can discover unlisted pages | Only sitemap URLs |

## Concurrency Options

```bash
# Conservative (rate-limit friendly)
--concurrent 3 --delay 0.5

# Balanced (default)
--concurrent 5 --delay 0.4

# Aggressive (fast servers only)
--concurrent 15 --delay 0.2
```

## Command Examples

### Fast Crawl (Sitemap + High Concurrency)
```bash
docshelper crawl https://docs.site.com --dataset mysite \
  --sitemap --concurrent 15 --max-pages 500
```

### Polite Crawl (Respects robots.txt + Lower Concurrency)
```bash
docshelper crawl https://docs.site.com --dataset mysite \
  --respect-robots --concurrent 3 --delay 1.0 --max-pages 100
```

### Bypass robots.txt (Use Responsibly!)
```bash
docshelper crawl https://docs.site.com --dataset mysite \
  --no-respect-robots --max-pages 50
```

### View Metrics After Querying
```bash
docshelper ask --dataset mysite "What is the API rate limit?"
docshelper metrics --dataset mysite --recent 5
```

### Enable LangSmith Monitoring
```bash
# In .env file, add:
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key-from-langsmith
LANGCHAIN_PROJECT=docshelper

# Then use normally:
docshelper ask --dataset mysite "Your question"
# View traces at https://smith.langchain.com/
```

## Metrics Output Example

```json
{
  "total_queries": 12,
  "avg_retrieval_count": 5.0,
  "avg_score": 0.847,
  "avg_answer_length": 342.5
}

Recent 5 Queries:
- [2026-03-09T14:23:42] How do I authenticate API requests?... (score: 0.892, chunks: 5)
- [2026-03-09T14:22:15] What is rate limiting?... (score: 0.856, chunks: 5)
```

## When to Use What

| Scenario | Recommendation |
|----------|---------------|
| First crawl of unknown site | Standard crawl, depth=2, concurrent=5 |
| Re-crawl large docs site | Sitemap mode, concurrent=15, max-pages=500 |
| Small personal docs | Standard crawl, concurrent=3 |
| Site with strict rate limits | --delay 1.0, concurrent=2, respect-robots |
| Site blocks crawlers | Check robots.txt first, may need --no-respect-robots |
| Measuring retrieval quality | Run queries, then check `docshelper metrics` regularly |
| Debugging LLM behavior | Enable LangSmith to trace prompts/responses |

## Performance Tips

1. **Sitemap first**: Always try `--sitemap` for sites with good sitemaps (10-50x faster)
2. **Tune concurrency**: Start at 5, increase if no errors, decrease if seeing timeouts
3. **Watch metrics**: Low avg_score (<0.5) suggests need better chunking or more pages
4. **Chunk tuning**: Run `index` with different `--chunk-words` values, compare metrics
5. **robots.txt delays**: If site specifies crawl-delay in robots.txt, it will override --delay

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Crawl very slow | Try `--sitemap` mode or increase `--concurrent` |
| Getting timeouts | Decrease `--concurrent`, increase `--delay` |
| Empty crawl result | Check robots.txt, try `--no-respect-robots` |
| Low retrieval scores | Increase `--max-pages`, adjust `--chunk-words` |
| Memory issues | Decrease `--max-pages`, do multiple crawls |
