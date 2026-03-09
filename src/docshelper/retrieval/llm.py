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
                {"role": "system", "content": "You are a documentation assistant. Use the provided context only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
