from pathlib import Path

from docshelper.observability import MetricsCollector


def test_metrics_collector_record_query(tmp_path: Path) -> None:
    collector = MetricsCollector(tmp_path)
    
    retrieved = {
        "documents": [["doc1", "doc2", "doc3"]],
        "distances": [[0.1, 0.2, 0.3]],
        "metadatas": [[{}, {}, {}]],
    }
    
    metrics = collector.record_query(
        query="test question",
        dataset="test_dataset",
        retrieved=retrieved,
        answer="test answer",
    )
    
    assert metrics.query == "test question"
    assert metrics.dataset == "test_dataset"
    assert metrics.retrieved_chunks == 3
    assert metrics.answer_length == len("test answer")
    assert len(metrics.top_scores) == 3


def test_metrics_collector_get_stats(tmp_path: Path) -> None:
    collector = MetricsCollector(tmp_path)
    
    retrieved = {
        "documents": [["doc1", "doc2"]],
        "distances": [[0.1, 0.2]],
        "metadatas": [[{}, {}]],
    }
    
    # Record a few queries
    for i in range(3):
        collector.record_query(
            query=f"question {i}",
            dataset="test",
            retrieved=retrieved,
            answer="answer",
        )
    
    stats = collector.get_stats(dataset="test")
    assert stats["total_queries"] == 3
    assert stats["avg_retrieval_count"] == 2.0


def test_metrics_collector_get_recent_queries(tmp_path: Path) -> None:
    collector = MetricsCollector(tmp_path)
    
    retrieved = {
        "documents": [["doc1"]],
        "distances": [[0.1]],
        "metadatas": [[{}]],
    }
    
    # Record queries
    for i in range(5):
        collector.record_query(
            query=f"question {i}",
            dataset="test",
            retrieved=retrieved,
            answer="answer",
        )
    
    recent = collector.get_recent_queries(limit=3, dataset="test")
    assert len(recent) == 3
    assert recent[-1].query == "question 4"
