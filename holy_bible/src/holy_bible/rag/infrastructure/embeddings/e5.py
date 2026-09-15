from __future__ import annotations

from sentence_transformers import SentenceTransformer

from holy_bible.shared.settings import EMBEDDING_MODEL


class E5EmbeddingModel:
    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(EMBEDDING_MODEL)
        return self._model

    def encode_query(self, text: str) -> list[float]:
        embedding = self._get_model().encode(
            [f"query: {text}"],
            show_progress_bar=False,
        )
        return embedding[0].tolist()

    def encode_passages(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        prefixed = [f"passage: {text}" for text in texts]
        embeddings = self._get_model().encode(
            prefixed,
            show_progress_bar=True,
            batch_size=batch_size,
        )
        return embeddings.tolist()
