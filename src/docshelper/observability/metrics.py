"""Query-time retrieval metrics collection and reporting."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class QueryMetrics:
    """Recorded metrics for a single ask/query execution."""

    query: str
    dataset: str
    retrieved_chunks: int
    top_scores: list[float]
    avg_score: float
    answer_length: int
    timestamp: str


class MetricsCollector:
    """Persist query metrics as JSONL and provide aggregate summaries."""

    def __init__(self, metrics_dir: Path) -> None:
        self.metrics_dir = metrics_dir
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_dir / "query_metrics.jsonl"

    def record_query(
        self,
        query: str,
        dataset: str,
        retrieved: dict,
        answer: str,
    ) -> QueryMetrics:
        """Record metrics for a single query execution.

        Args:
            query: User question text.
            dataset: Dataset name queried.
            retrieved: Raw retrieval payload from vector search.
            answer: Generated final answer.

        Returns:
            QueryMetrics: Persisted metrics object for this query.
        """
        distances = retrieved.get("distances", [[]])[0]
        # Convert distances to similarity scores (lower distance = higher similarity)
        scores = [1.0 / (1.0 + d) for d in distances] if distances else []
        
        metrics = QueryMetrics(
            query=query,
            dataset=dataset,
            retrieved_chunks=len(retrieved.get("documents", [[]])[0]),
            top_scores=scores[:5],
            avg_score=sum(scores) / len(scores) if scores else 0.0,
            answer_length=len(answer),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        # Append to metrics file
        with self.metrics_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metrics)) + "\n")
        
        return metrics

    def get_stats(self, dataset: str | None = None) -> dict:
        """Return aggregate query statistics.

        Args:
            dataset: Optional dataset filter.

        Returns:
            dict: Aggregate metrics summary.
        """
        if not self.metrics_file.exists():
            return {
                "total_queries": 0,
                "avg_retrieval_count": 0.0,
                "avg_score": 0.0,
                "avg_answer_length": 0.0,
            }
        
        metrics_list: list[QueryMetrics] = []
        for line in self.metrics_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            if dataset is None or data["dataset"] == dataset:
                metrics_list.append(QueryMetrics(**data))
        
        if not metrics_list:
            return {
                "total_queries": 0,
                "avg_retrieval_count": 0.0,
                "avg_score": 0.0,
                "avg_answer_length": 0.0,
            }
        
        return {
            "total_queries": len(metrics_list),
            "avg_retrieval_count": sum(m.retrieved_chunks for m in metrics_list) / len(metrics_list),
            "avg_score": sum(m.avg_score for m in metrics_list) / len(metrics_list),
            "avg_answer_length": sum(m.answer_length for m in metrics_list) / len(metrics_list),
        }

    def get_recent_queries(self, limit: int = 10, dataset: str | None = None) -> list[QueryMetrics]:
        """Return recent recorded queries.

        Args:
            limit: Maximum number of results.
            dataset: Optional dataset filter.

        Returns:
            list[QueryMetrics]: Recent metrics entries in chronological order.
        """
        if not self.metrics_file.exists():
            return []
        
        metrics_list: list[QueryMetrics] = []
        for line in self.metrics_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            if dataset is None or data["dataset"] == dataset:
                metrics_list.append(QueryMetrics(**data))
        
        return metrics_list[-limit:]
