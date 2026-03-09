"""Embedding helpers backed by the OpenAI embeddings API."""

from __future__ import annotations

from langsmith import wrappers
from openai import OpenAI


class OpenAIEmbedder:
    """Generate vectors for documents and queries using OpenAI with LangSmith tracing."""

    def __init__(self, api_key: str, model: str) -> None:
        client = OpenAI(api_key=api_key)
        self.client = wrappers.wrap_openai(client)
        self.model = model

    def embed_texts(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """Embed multiple texts in batches.

        Args:
            texts: Text inputs to embed.
            batch_size: Maximum number of texts per API call.

        Returns:
            list[list[float]]: Embedding vectors in input order.
        """
        vectors: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self.client.embeddings.create(model=self.model, input=batch)
            vectors.extend(item.embedding for item in response.data)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query.

        Args:
            text: Query text.

        Returns:
            list[float]: Embedding vector for the query.
        """
        response = self.client.embeddings.create(model=self.model, input=[text])
        return response.data[0].embedding
