from __future__ import annotations

import logging

from holy_bible.rag.domain.entities import BiblicalChunk, QueryResult
from holy_bible.rag.domain.exceptions import ChromaUnavailableError
from holy_bible.rag.domain.ranking import reciprocal_rank_fusion
from holy_bible.rag.infrastructure.llm.anthropic import AnthropicGenerator
from holy_bible.rag.infrastructure.retrieval.bm25 import BM25Retriever
from holy_bible.rag.infrastructure.vector_store.chroma import ChromaVectorStore
from holy_bible.shared.settings import (
    CHROMA_DIR,
    COLLECTION_NAME,
    RETRIEVAL_POOL_SIZE,
    RRF_K,
)

logger = logging.getLogger(__name__)


class RagService:
    def __init__(
        self,
        vector_store: ChromaVectorStore | None = None,
        generator: AnthropicGenerator | None = None,
        bm25_retriever: BM25Retriever | None = None,
    ) -> None:
        self._vector_store = vector_store or ChromaVectorStore()
        self._generator = generator or AnthropicGenerator()
        self._bm25_retriever = bm25_retriever or BM25Retriever()

    @property
    def vector_store(self) -> ChromaVectorStore:
        return self._vector_store

    def get_health(self) -> tuple[str, int | None, str | None]:
        if not CHROMA_DIR.exists():
            return (
                "error",
                None,
                f"Chroma database not found at {CHROMA_DIR}",
            )
        try:
            return ("ok", self._vector_store.count(), None)
        except ChromaUnavailableError as exc:
            self._vector_store.reset_cache()
            return ("error", None, str(exc))
        except Exception:
            self._vector_store.reset_cache()
            return (
                "error",
                None,
                f"Chroma collection '{COLLECTION_NAME}' is not available",
            )

    def retrieve(
        self,
        question: str,
        num_results: int = 5,
        testament: str | None = None,
        book: str | None = None,
        hybrid: bool = True,
    ) -> list[BiblicalChunk]:
        if hybrid:
            return self._hybrid_search(question, num_results, testament, book)
        return self._vector_store.search(
            question, n_results=num_results, testament=testament, book=book
        )

    def query(
        self,
        question: str,
        num_results: int = 5,
        testament: str | None = None,
        book: str | None = None,
        hybrid: bool = True,
    ) -> QueryResult:
        chunks = self.retrieve(question, num_results, testament, book, hybrid)
        answer = self._generator.generate(question, chunks)
        return QueryResult(answer=answer, chunks=chunks)

    def _hybrid_search(
        self,
        question: str,
        num_results: int,
        testament: str | None,
        book: str | None,
    ) -> list[BiblicalChunk]:
        search_kwargs = {
            "n_results": RETRIEVAL_POOL_SIZE,
            "testament": testament,
            "book": book,
        }
        dense_results = self._vector_store.search(question, **search_kwargs)
        sparse_results = self._bm25_retriever.search(question, **search_kwargs)
        if not sparse_results:
            logger.warning("BM25 retrieval unavailable, falling back to dense-only")
            return dense_results[:num_results]
        fused = reciprocal_rank_fusion(
            [dense_results, sparse_results],
            k=RRF_K,
        )
        return fused[:num_results]


_default_service: RagService | None = None


def get_rag_service() -> RagService:
    global _default_service
    if _default_service is None:
        _default_service = RagService()
    return _default_service
