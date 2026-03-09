"""RAG orchestration: build context prompt and synthesize final answers."""

from __future__ import annotations

from datetime import datetime

from docshelper.models import AskResult

from .llm import BaseLLMProvider


class RAGEngine:
    """Compose retrieved context and delegate final answer generation to an LLM provider."""

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self.llm_provider = llm_provider

    def answer_question(
        self,
        question: str,
        retrieved: dict,
    ) -> AskResult:
        """Produce a grounded answer and source list from retrieval output.

        Args:
            question: End-user question.
            retrieved: Raw retrieval payload from the vector store.

        Returns:
            AskResult: Final answer text, source URLs, and retrieval metadata.
        """
        documents = retrieved.get("documents", [[]])[0]
        metadatas = retrieved.get("metadatas", [[]])[0]

        context_blocks: list[str] = []
        sources: list[str] = []

        for doc, meta in zip(documents, metadatas):
            source_url = str(meta.get("url", ""))
            title = str(meta.get("title", ""))
            if source_url and source_url not in sources:
                sources.append(source_url)
            context_blocks.append(f"Source: {title} ({source_url})\n{doc}")

        context_text = "\n\n".join(context_blocks)
        prompt = (
            "Answer the question only using the context. "
            "If the answer is missing, say you do not have enough context.\n\n"
            f"Question:\n{question}\n\n"
            f"Context:\n{context_text}"
        )

        answer = self.llm_provider.answer(prompt)
        return AskResult(
            answer=answer.strip(),
            sources=sources,
            retrieved_chunks=len(documents),
            created_at=datetime.utcnow(),
        )
