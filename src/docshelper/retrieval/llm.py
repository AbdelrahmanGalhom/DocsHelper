"""LLM provider abstractions for answer generation."""

from __future__ import annotations

from langsmith import wrappers
from openai import OpenAI


class BaseLLMProvider:
    """Interface for answer-generation providers used by the RAG engine."""

    def answer(self, prompt: str) -> str:
        """Generate an answer for a fully constructed prompt.

        Args:
            prompt: Prompt text including retrieved context.

        Returns:
            str: Model-generated response text.
        """
        raise NotImplementedError


class OpenAIProvider(BaseLLMProvider):
    """OpenAI chat completion provider with LangSmith tracing."""

    SYSTEM_PROMPT = (
        "You are DocsHelper, a documentation Q&A assistant. "
        "Your job is to answer user questions using only the retrieved documentation context provided in the user message.\n\n"
        "Rules:\n"
        "1) Grounding: Do not use outside knowledge. If the answer is not clearly supported by context, say you do not have enough context.\n"
        "2) Accuracy: Do not invent APIs, parameters, paths, versions, or behavior.\n"
        "3) Uncertainty: When context is partial or ambiguous, say what is known and what is missing.\n"
        "4) Output style: Be clear, concise, and practical. Prefer short paragraphs and bullet points for steps.\n"
        "5) Citations: When possible, reference the source title or URL present in context blocks.\n"
        "6) Safety: If context includes conflicting information, highlight the conflict and provide the safer interpretation.\n"
        "7) Scope: Focus on implementation and usage details relevant to software engineers.\n"
        "8) If context is empty, respond exactly: 'I do not have enough context to answer this question.'"
    )

    def __init__(self, api_key: str, model: str) -> None:
        client = OpenAI(api_key=api_key)
        self.client = wrappers.wrap_openai(client)
        self.model = model

    def answer(self, prompt: str) -> str:
        """Generate a grounded answer using the configured OpenAI model.

        Args:
            prompt: Prompt text including retrieved context.

        Returns:
            str: Model-generated response text.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
