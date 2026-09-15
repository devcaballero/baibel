from __future__ import annotations

from holy_bible.rag.domain.entities import QueryResult
from holy_bible.rag.domain.exceptions import ChromaUnavailableError
from holy_bible.rag.infrastructure.llm.anthropic import AnthropicGenerator
from holy_bible.shared.settings import CHROMA_DIR, COLLECTION_NAME
from holy_bible.rag.infrastructure.vector_store.chroma import ChromaVectorStore


class RagService:
    def __init__(
        self,
        vector_store: ChromaVectorStore | None = None,
        generator: AnthropicGenerator | None = None,
    ) -> None:
        self._vector_store = vector_store or ChromaVectorStore()
        self._generator = generator or AnthropicGenerator()

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

    def query(
        self,
        question: str,
        num_results: int = 5,
        testament: str | None = None,
        book: str | None = None,
    ) -> QueryResult:
        chunks = self._vector_store.search(
            question,
            n_results=num_results,
            testament=testament,
            book=book,
        )
        answer = self._generator.generate(question, chunks)
        return QueryResult(answer=answer, chunks=chunks)


_default_service: RagService | None = None


def get_rag_service() -> RagService:
    global _default_service
    if _default_service is None:
        _default_service = RagService()
    return _default_service
