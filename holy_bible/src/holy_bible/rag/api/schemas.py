from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from holy_bible.shared.settings import DEFAULT_N_RESULTS, MAX_N_RESULTS


class QueryRequest(BaseModel):
    question: str = Field(..., description="User question about the Bible")
    num_results: int = Field(default=DEFAULT_N_RESULTS, ge=1, le=MAX_N_RESULTS)
    testament: Literal["AT", "NT"] | None = None
    book: str | None = None

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be empty")
        return value.strip()

    @field_validator("book")
    @classmethod
    def book_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("book must not be empty when provided")
        return value.strip() if value else None


class Citation(BaseModel):
    book: str
    chapter: int
    verse_start: int
    verse_end: int
    text: str
    source: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]


class HealthResponse(BaseModel):
    status: str
    indexed_chunks: int | None = None
    detail: str | None = None
