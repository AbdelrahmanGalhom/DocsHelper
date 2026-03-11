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
            "You are answering a documentation question for software engineers.\n"
            "Use only the CONTEXT BLOCKS below.\n"
            "If the context is missing, incomplete, or ambiguous, say what is known and what is missing.\n"
            "If there is not enough information to answer, respond exactly: "
            "'I do not have enough context to answer this question.'\n"
            "Do not invent APIs, parameters, versions, or behavior.\n"
            "When possible, mention the relevant source title or URL from the context.\n\n"
            "QUESTION:\n"
            f"{question}\n\n"
            "CONTEXT BLOCKS:\n"
            f"{context_text}"
        )

        answer = self.llm_provider.answer(prompt)
        return AskResult(
            answer=answer.strip(),
            sources=sources,
            retrieved_chunks=len(documents),
            created_at=datetime.utcnow(),
        )
