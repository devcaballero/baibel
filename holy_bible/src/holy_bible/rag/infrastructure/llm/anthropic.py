from __future__ import annotations

from typing import Any

import anthropic

from holy_bible.rag.domain.entities import BiblicalChunk
from holy_bible.rag.domain.exceptions import RagGenerationError
from holy_bible.shared.settings import CLAUDE_MODEL, SYSTEM_PROMPT


class AnthropicGenerator:
    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def generate(self, question: str, chunks: list[BiblicalChunk]) -> str:
        if not chunks:
            return (
                "No se encontró contexto bíblico suficiente para responder esta pregunta "
                "con los pasajes recuperados."
            )

        context = self._format_context(chunks)
        user_message = (
            f"Pregunta: {question}\n\n"
            f"Pasajes bíblicos de contexto:\n{context}\n\n"
            "Respondé la pregunta usando únicamente estos pasajes. "
            "Si ninguno de los pasajes es relevante para la pregunta, "
            "indicá explícitamente que no hay contexto suficiente "
            "en lugar de inventar una respuesta."
        )

        try:
            response = self._get_client().messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
        except anthropic.RateLimitError as exc:
            raise RagGenerationError(
                "Language model rate limit exceeded; try again later"
            ) from exc
        except anthropic.APIConnectionError as exc:
            raise RagGenerationError(
                "Could not connect to language model service"
            ) from exc
        except anthropic.APIStatusError as exc:
            raise RagGenerationError(
                "Language model service returned an error"
            ) from exc
        except Exception as exc:
            raise RagGenerationError(
                "Unexpected error generating response"
            ) from exc

        return response.content[0].text

    @staticmethod
    def _format_context(chunks: list[BiblicalChunk]) -> str:
        lines: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            ref = (
                f"{chunk.book} {chunk.chapter}:"
                f"{chunk.verse_start}-{chunk.verse_end}"
            )
            lines.append(f"[{index}] {ref}\n{chunk.text}")
        return "\n\n".join(lines)
