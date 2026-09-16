from __future__ import annotations

from typing import Any

import anthropic

from holy_bible.rag.domain.entities import BiblicalChunk
from holy_bible.rag.domain.exceptions import RagGenerationError
from holy_bible.shared.settings import CLAUDE_MODEL, SYSTEM_PROMPT

SUBMIT_ANSWER_TOOL: dict[str, Any] = {
    "name": "submit_answer",
    "description": (
        "Enviá la respuesta final junto con los índices de los pasajes "
        "que efectivamente usaste para construirla."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": (
                    "La respuesta completa a la pregunta, en el mismo formato y tono "
                    "que ya se usa (prosa + citas de libro/capítulo/versículo tal "
                    "como aparecen en el contexto)."
                ),
            },
            "cited_indices": {
                "type": "array",
                "items": {"type": "integer"},
                "description": (
                    "Los números [N] de los pasajes de contexto que fueron "
                    "efectivamente usados para construir la respuesta. Si un pasaje "
                    "no aportó nada a la respuesta, no lo incluyas aunque haya "
                    "estado en el contexto."
                ),
            },
        },
        "required": ["answer", "cited_indices"],
    },
}

EMPTY_CONTEXT_ANSWER = (
    "No se encontró contexto bíblico suficiente para responder esta pregunta "
    "con los pasajes recuperados."
)


class AnthropicGenerator:
    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def generate(
        self, question: str, chunks: list[BiblicalChunk]
    ) -> tuple[str, list[int]]:
        if not chunks:
            return (EMPTY_CONTEXT_ANSWER, [])

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
                tools=[SUBMIT_ANSWER_TOOL],
                tool_choice={"type": "tool", "name": "submit_answer"},
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

        return self._extract_tool_answer(response)

    @staticmethod
    def _extract_tool_answer(response: Any) -> tuple[str, list[int]]:
        for block in getattr(response, "content", []) or []:
            if getattr(block, "type", None) != "tool_use":
                continue
            payload = getattr(block, "input", None)
            if not isinstance(payload, dict):
                break
            answer = payload.get("answer")
            indices = payload.get("cited_indices")
            if not isinstance(answer, str) or not answer.strip():
                raise RagGenerationError(
                    "Language model tool response did not include an answer"
                )
            if not isinstance(indices, list):
                raise RagGenerationError(
                    "Language model tool response did not include cited_indices"
                )
            cited_indices: list[int] = []
            for item in indices:
                if isinstance(item, bool):
                    continue
                if isinstance(item, int):
                    cited_indices.append(item)
                elif isinstance(item, float) and item.is_integer():
                    cited_indices.append(int(item))
            return answer, cited_indices
        raise RagGenerationError(
            "Language model did not return a submit_answer tool_use block"
        )

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
