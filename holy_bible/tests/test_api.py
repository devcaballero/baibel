#!/usr/bin/env python3
"""Pruebas manuales de la API RAG."""

from __future__ import annotations

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from holy_bible.rag.domain.exceptions import RagGenerationError
from holy_bible.shared.settings import LIBROS, PROJECT_ROOT
from holy_bible.rag.api.app import app

NT_BOOKS = {libro["nombre"] for libro in LIBROS if libro["testamento"] == "NT"}
MISSING_CHROMA_DIR = PROJECT_ROOT / "chroma_biblia_missing_for_test"


def test_docs(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200, "/docs should be available"
    assert "swagger" in response.text.lower()
    print("\n=== /docs ===\nOK: Swagger UI disponible")


def test_empty_question_400(client: TestClient) -> None:
    for payload in [{"question": ""}, {"question": "   "}]:
        response = client.post("/query", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "empty" in response.json()["detail"].lower()
    print("\n=== empty question ===\nOK: devuelve 400")


def test_missing_question_422(client: TestClient) -> None:
    response = client.post("/query")
    assert response.status_code == 422, response.text
    response = client.post("/query", json={})
    assert response.status_code == 422, response.text
    print("\n=== missing question ===\nOK: devuelve 422")


def test_book_filter(client: TestClient) -> None:
    response = client.post(
        "/query",
        json={
            "question": "¿Qué dice sobre la sabiduría?",
            "num_results": 5,
            "book": "Eclesiástico",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["citations"], "Expected citations"
    assert all(c["book"] == "Eclesiástico" for c in data["citations"]), data["citations"]
    print("\n=== book filter (Eclesiástico) ===\nOK: todas las citations son de Eclesiástico")


def test_testament_filter(client: TestClient) -> None:
    response = client.post(
        "/query",
        json={
            "question": "¿Qué enseña sobre el amor?",
            "num_results": 5,
            "testament": "NT",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["citations"], "Expected citations"
    assert all(c["book"] in NT_BOOKS for c in data["citations"]), data["citations"]
    print("\n=== testament filter (NT) ===\nOK: todas las citations son del NT")


def test_off_topic(client: TestClient) -> None:
    response = client.post(
        "/query",
        json={
            "question": "¿Cuál es el impacto de la inteligencia artificial en la economía global en 2026?",
            "num_results": 5,
        },
    )
    assert response.status_code == 200, response.text
    answer = response.json()["answer"].lower()
    insufficient_markers = [
        "no contienen",
        "no hay",
        "no se encontr",
        "no encuentro",
        "no proporcion",
        "insuficiente",
        "no es posible responder",
        "no puedo responder",
        "no permiten responder",
    ]
    assert any(marker in answer for marker in insufficient_markers), answer
    print("\n=== off-topic question ===\nOK: Claude indica contexto insuficiente")
    print(json.dumps({"answer": response.json()["answer"]}, ensure_ascii=False, indent=2))


def test_missing_chroma(client_factory) -> None:
    from holy_bible.rag.application import service as rag_module
    from holy_bible.shared import settings
    from holy_bible.rag.infrastructure.vector_store import chroma as chroma_module

    with patch.object(settings, "CHROMA_DIR", MISSING_CHROMA_DIR), patch.object(
        chroma_module, "CHROMA_DIR", MISSING_CHROMA_DIR
    ):
        rag_module._default_service = None
        client = client_factory()

        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "error"
        assert "not found" in health.json()["detail"].lower()

        query = client.post("/query", json={"question": "¿Qué dice sobre el perdón?"})
        assert query.status_code == 503, query.text
        assert "not found" in query.json()["detail"].lower()
        print("\n=== missing chroma ===\nOK: /health error + /query 503")

    rag_module._default_service = None


def test_anthropic_rate_limit(client_factory) -> None:
    from holy_bible.rag.application.service import RagService

    with patch.object(
        RagService,
        "query",
        side_effect=RagGenerationError(
            "Language model rate limit exceeded; try again later"
        ),
    ):
        from holy_bible.rag.application import service as rag_module

        rag_module._default_service = None
        client = client_factory()
        response = client.post(
            "/query",
            json={"question": "¿Qué dice sobre el perdón?"},
        )
        assert response.status_code == 502, response.text
        assert "rate limit" in response.json()["detail"].lower()
        print("\n=== anthropic rate limit ===\nOK: /query devuelve 502")

    from holy_bible.rag.application import service as rag_module

    rag_module._default_service = None


def main() -> None:
    def client_factory():
        return TestClient(app)

    client = client_factory()

    test_docs(client)
    test_empty_question_400(client)
    test_missing_question_422(client)
    test_book_filter(client)
    test_testament_filter(client)
    test_off_topic(client)
    test_missing_chroma(client_factory)
    test_anthropic_rate_limit(client_factory)

    print("\n\nTodas las pruebas pasaron.")


if __name__ == "__main__":
    main()
