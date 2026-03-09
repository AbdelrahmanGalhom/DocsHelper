"""Chroma vector store adapter used by indexing and retrieval steps."""

from __future__ import annotations

import chromadb
from chromadb.api.models.Collection import Collection

from docshelper.models import Chunk


class ChromaStore:
    """Persist and query chunk embeddings in a Chroma collection per dataset."""

    def __init__(self, persist_dir: str) -> None:
        self.client = chromadb.PersistentClient(path=persist_dir)

    def get_or_create_collection(self, dataset: str) -> Collection:
        """Get or create the normalized collection for a dataset.

        Args:
            dataset: Logical dataset name.

        Returns:
            Collection: Chroma collection bound to the dataset.
        """
        name = dataset.replace(" ", "-").lower()
        return self.client.get_or_create_collection(name=name)

    def upsert_chunks(
        self,
        dataset: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> int:
        """Upsert chunk documents and embeddings.

        Args:
            dataset: Dataset collection name.
            chunks: Chunk payloads with text and metadata.
            embeddings: Embedding vectors aligned with chunks.

        Returns:
            int: Number of chunks submitted to Chroma.
        """
        collection = self.get_or_create_collection(dataset)
        collection.upsert(
            ids=[c.chunk_id for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[c.metadata for c in chunks],
            embeddings=embeddings,
        )
        return len(chunks)

    def query(
        self,
        dataset: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> dict:
        """Run nearest-neighbor search for a query embedding.

        Args:
            dataset: Dataset collection name.
            query_embedding: Query vector.
            top_k: Number of nearest results to return.

        Returns:
            dict: Raw Chroma query output.
        """
        collection = self.get_or_create_collection(dataset)
        return collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

    def collection_count(self, dataset: str) -> int:
        """Return number of indexed vectors for a dataset.

        Args:
            dataset: Dataset collection name.

        Returns:
            int: Stored vector count.
        """
        collection = self.get_or_create_collection(dataset)
        return collection.count()
