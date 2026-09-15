from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BiblicalChunk:
    id: str
    text: str
    book: str
    chapter: int
    verse_start: int
    verse_end: int
    source: str
    testament: str


@dataclass
class QueryResult:
    answer: str
    chunks: list[BiblicalChunk]
