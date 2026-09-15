from __future__ import annotations

import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from holy_bible.etl.chunking import CHUNKS_FILE
from holy_bible.rag.domain.entities import BiblicalChunk

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_STOPWORDS_ES = {
    "el",
    "la",
    "los",
    "las",
    "un",
    "una",
    "unos",
    "unas",
    "de",
    "del",
    "en",
    "que",
    "y",
    "a",
    "su",
    "sus",
    "como",
    "es",
    "por",
    "con",
    "se",
    "lo",
    "al",
    "o",
    "pero",
    "qué",
    "quién",
    "cómo",
    "cuál",
    "cuáles",
    "para",
    "no",
    "ni",
    "le",
    "les",
    "me",
    "te",
    "nos",
    "más",
    "muy",
    "ya",
    "si",
    "porque",
    "cuando",
    "donde",
    "era",
    "fue",
    "son",
    "ser",
    "hay",
    "este",
    "esta",
    "eso",
    "esa",
}


def _tokenize(text: str, filter_stopwords: bool = False) -> list[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    if not filter_stopwords:
        return tokens
    return [token for token in tokens if token not in _STOPWORDS_ES]


class BM25Retriever:
    def __init__(self, chunks_file: Path | None = None) -> None:
        self._chunks_file = chunks_file or CHUNKS_FILE
        self._bm25: BM25Okapi | None = None
        self._chunks: list[BiblicalChunk] = []
        self._unavailable = False
        self._loaded = False

    def search(
        self,
        question: str,
        n_results: int = 5,
        testament: str | None = None,
        book: str | None = None,
    ) -> list[BiblicalChunk]:
        return [
            chunk
            for chunk, _ in self.search_with_scores(
                question,
                n_results=n_results,
                testament=testament,
                book=book,
            )
        ]

    def search_with_scores(
        self,
        question: str,
        n_results: int = 5,
        testament: str | None = None,
        book: str | None = None,
    ) -> list[tuple[BiblicalChunk, float]]:
        self._ensure_index()
        if self._unavailable or self._bm25 is None:
            return []

        tokens = _tokenize(question)
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)
        ranked: list[tuple[BiblicalChunk, float]] = []
        for score, chunk in zip(scores, self._chunks):
            if score <= 0:
                continue
            if testament and chunk.testament != testament:
                continue
            if book and chunk.book != book:
                continue
            ranked.append((chunk, float(score)))

        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:n_results]

    def max_question_idf(self, question: str) -> float:
        self._ensure_index()
        if self._unavailable or self._bm25 is None:
            return 0.0
        tokens = _tokenize(question, filter_stopwords=True)
        idfs = [float(self._bm25.idf.get(token, 0.0)) for token in tokens]
        return max(idfs) if idfs else 0.0

    def _ensure_index(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self._chunks_file.exists():
            self._unavailable = True
            return

        corpus: list[list[str]] = []
        chunks: list[BiblicalChunk] = []
        with self._chunks_file.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                chunks.append(
                    BiblicalChunk(
                        id=str(raw["id"]),
                        text=raw["texto"],
                        book=raw["libro"],
                        chapter=int(raw["capitulo"]),
                        verse_start=int(raw["versiculo_inicio"]),
                        verse_end=int(raw["versiculo_fin"]),
                        source=str(raw.get("fuente") or "bibliatodo"),
                        testament=raw["testamento"],
                    )
                )
                corpus.append(_tokenize(raw["texto"]))

        if not chunks:
            self._unavailable = True
            return

        self._chunks = chunks
        self._bm25 = BM25Okapi(corpus)
