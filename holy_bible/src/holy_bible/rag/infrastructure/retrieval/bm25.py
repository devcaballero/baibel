from __future__ import annotations

import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from holy_bible.etl.chunking import CHUNKS_FILE
from holy_bible.rag.domain.entities import BiblicalChunk

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


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
        self._ensure_index()
        if self._unavailable or self._bm25 is None:
            return []

        tokens = _tokenize(question)
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)
        ranked: list[tuple[float, BiblicalChunk]] = []
        for score, chunk in zip(scores, self._chunks):
            if score <= 0:
                continue
            if testament and chunk.testament != testament:
                continue
            if book and chunk.book != book:
                continue
            ranked.append((float(score), chunk))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in ranked[:n_results]]

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
