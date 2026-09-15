"""API REST RAG para el chatbot católico (Biblia Torres Amat)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from holy_bible.rag.application.service import get_rag_service
from holy_bible.rag.domain.entities import BiblicalChunk
from holy_bible.rag.domain.exceptions import (
    ChromaUnavailableError,
    RagGenerationError,
    RagSearchError,
)
from holy_bible.rag.api.schemas import (
    Citation,
    HealthResponse,
    QueryRequest,
    QueryResponse,
)

load_dotenv()


def _chunk_to_citation(chunk: BiblicalChunk) -> Citation:
    return Citation(
        book=chunk.book,
        chapter=chunk.chapter,
        verse_start=chunk.verse_start,
        verse_end=chunk.verse_end,
        text=chunk.text,
        source=chunk.source,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Biblia Torres Amat RAG API",
    description="RAG API for querying the Catholic Bible (Torres Amat edition).",
    lifespan=lifespan,
)

# TODO: restringir origins antes de cualquier deploy real
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    for err in errors:
        if err.get("loc") == ("body", "question") and err.get("type") != "missing":
            return JSONResponse(
                status_code=400,
                content={"detail": "question must not be empty"},
            )
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    status, count, detail = get_rag_service().get_health()
    return HealthResponse(status=status, indexed_chunks=count, detail=detail)


@app.post("/query", response_model=QueryResponse)
def query(body: QueryRequest) -> QueryResponse:
    service = get_rag_service()
    try:
        result = service.query(
            body.question,
            num_results=body.num_results,
            testament=body.testament,
            book=body.book,
        )
    except ChromaUnavailableError as exc:
        service.vector_store.reset_cache()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RagSearchError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RagGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return QueryResponse(
        answer=result.answer,
        citations=[_chunk_to_citation(c) for c in result.chunks],
    )
