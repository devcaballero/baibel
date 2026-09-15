from __future__ import annotations

from typing import Any

import chromadb

from holy_bible.rag.domain.entities import BiblicalChunk
from holy_bible.rag.domain.exceptions import ChromaUnavailableError, RagSearchError
from holy_bible.rag.infrastructure.embeddings.e5 import E5EmbeddingModel
from holy_bible.shared.settings import CHROMA_DIR, COLLECTION_NAME


class ChromaVectorStore:
    def __init__(self, embeddings: E5EmbeddingModel | None = None) -> None:
        self._embeddings = embeddings or E5EmbeddingModel()
        self._chroma_client: chromadb.PersistentClient | None = None
        self._collection: Any | None = None

    def reset_cache(self) -> None:
        self._chroma_client = None
        self._collection = None

    def _ensure_chroma_dir(self) -> None:
        if not CHROMA_DIR.exists():
            self.reset_cache()
            raise ChromaUnavailableError(
                f"Chroma database not found at {CHROMA_DIR}"
            )

    def _get_chroma_client(self) -> chromadb.PersistentClient:
        self._ensure_chroma_dir()
        if self._chroma_client is None:
            self._chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        return self._chroma_client

    def _get_collection(self):
        self._ensure_chroma_dir()
        if self._collection is None:
            try:
                self._collection = self._get_chroma_client().get_collection(
                    name=COLLECTION_NAME
                )
            except ChromaUnavailableError:
                raise
            except Exception as exc:
                self.reset_cache()
                raise ChromaUnavailableError(
                    f"Chroma collection '{COLLECTION_NAME}' is not available"
                ) from exc
        return self._collection

    def count(self) -> int:
        return self._get_collection().count()

    def search(
        self,
        question: str,
        n_results: int = 5,
        testament: str | None = None,
        book: str | None = None,
    ) -> list[BiblicalChunk]:
        try:
            collection = self._get_collection()
            query_embedding = self._embeddings.encode_query(question)

            query_kwargs: dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": n_results,
            }
            where = self._build_where_filter(testament, book)
            if where:
                query_kwargs["where"] = where

            results = collection.query(**query_kwargs)
        except ChromaUnavailableError:
            raise
        except Exception as exc:
            raise RagSearchError("Error searching biblical context") from exc

        chunks: list[BiblicalChunk] = []
        for chunk_id, doc, meta in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
        ):
            chunks.append(self._chunk_from_metadata(doc, meta, chunk_id))
        return chunks

    @staticmethod
    def _build_where_filter(testament: str | None, book: str | None) -> dict | None:
        filters: list[dict] = []
        if testament:
            filters.append({"testamento": testament})
        if book:
            filters.append({"libro": book})

        if not filters:
            return None
        if len(filters) == 1:
            return filters[0]
        return {"$and": filters}

    @staticmethod
    def _resolve_source(meta: dict) -> str:
        for key in ("fuente", "source"):
            value = meta.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return "bibliatodo"

    @classmethod
    def _chunk_from_metadata(
        cls, text: str, meta: dict, chunk_id: str
    ) -> BiblicalChunk:
        return BiblicalChunk(
            id=chunk_id,
            text=text,
            book=meta["libro"],
            chapter=int(meta["capitulo"]),
            verse_start=int(meta["versiculo_inicio"]),
            verse_end=int(meta["versiculo_fin"]),
            source=cls._resolve_source(meta),
            testament=meta["testamento"],
        )
