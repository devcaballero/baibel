from __future__ import annotations

import asyncio
import logging
import sys
import types
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

# nest_asyncio (imported by ragas) + asyncio.timeout break evaluate() on Python 3.14.
import nest_asyncio

nest_asyncio.apply = lambda *args, **kwargs: None  # type: ignore[method-assign]

# ragas 0.2 imports ChatVertexAI from langchain_community; newer community dropped it.
_vertexai = types.ModuleType("langchain_community.chat_models.vertexai")
_vertexai.ChatVertexAI = type("ChatVertexAI", (), {})
sys.modules.setdefault("langchain_community.chat_models.vertexai", _vertexai)

from ragas import EvaluationDataset, evaluate
from ragas.dataset_schema import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness
from ragas.run_config import RunConfig

from holy_bible.eval.dataset import EVAL_DATASET
from holy_bible.rag.application.service import RagService
from holy_bible.rag.domain.entities import BiblicalChunk, QueryResult
from holy_bible.shared.settings import CLAUDE_MODEL, PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)
OUTPUT_PATH = PROJECT_ROOT / "eval" / "faithfulness_run.md"


@dataclass
class QuestionEval:
    question: str
    note: str
    answer: str | None
    chunks: list[BiblicalChunk]
    score: float | None
    error: str | None


def _preview(text: str, limit: int = 80) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1] + "…"


def _format_contexts(chunks: list[BiblicalChunk]) -> str:
    if not chunks:
        return "_(sin contexto)_"
    parts: list[str] = []
    for chunk in chunks:
        ref = f"{chunk.book} {chunk.chapter}:{chunk.verse_start}-{chunk.verse_end}"
        parts.append(f"**{ref}**\n\n{chunk.text}")
    return "\n\n".join(parts)


def _extract_score(result: object) -> float:
    scores = getattr(result, "scores", None)
    if isinstance(scores, list) and scores:
        row = scores[0]
        if isinstance(row, dict):
            for key in ("faithfulness", "Faithfulness"):
                if key in row and row[key] is not None:
                    return float(row[key])
            numeric = [value for value in row.values() if isinstance(value, (int, float))]
            if numeric:
                return float(numeric[0])
    to_pandas = getattr(result, "to_pandas", None)
    if callable(to_pandas):
        frame = to_pandas()
        for column in ("faithfulness", "Faithfulness"):
            if column in frame.columns:
                value = frame[column].iloc[0]
                if value is not None and value == value:
                    return float(value)
    raise RuntimeError(f"Could not read faithfulness score from {result!r}")


def _score_sample(sample: SingleTurnSample, judge: LangchainLLMWrapper) -> float:
    dataset = EvaluationDataset(samples=[sample])
    try:
        result = evaluate(
            dataset,
            metrics=[Faithfulness()],
            llm=judge,
            raise_exceptions=True,
            show_progress=False,
            run_config=RunConfig(timeout=180, max_retries=2, max_workers=1),
        )
        return _extract_score(result)
    except RuntimeError as exc:
        if "Timeout should be used inside a task" not in str(exc):
            raise
        metric = Faithfulness()
        metric.llm = judge
        return float(asyncio.run(metric.single_turn_ascore(sample)))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    service = RagService()
    judge = LangchainLLMWrapper(ChatAnthropic(model=CLAUDE_MODEL))

    samples: list[SingleTurnSample] = []
    rows: list[QuestionEval] = []
    for item in EVAL_DATASET:
        try:
            result: QueryResult = service.query(item.question)
        except Exception as exc:
            logger.exception("Generation failed for %s", item.question)
            rows.append(
                QuestionEval(
                    question=item.question,
                    note=item.note,
                    answer=None,
                    chunks=[],
                    score=None,
                    error=f"generation: {exc}",
                )
            )
            continue

        sample = SingleTurnSample(
            user_input=item.question,
            response=result.answer,
            retrieved_contexts=[
                (
                    f"[{index}] {chunk.book} {chunk.chapter}:"
                    f"{chunk.verse_start}-{chunk.verse_end}\n{chunk.text}"
                )
                for index, chunk in enumerate(result.chunks, start=1)
            ],
        )
        samples.append(sample)
        try:
            score = _score_sample(sample, judge)
            rows.append(
                QuestionEval(
                    question=item.question,
                    note=item.note,
                    answer=result.answer,
                    chunks=result.chunks,
                    score=score,
                    error=None,
                )
            )
        except Exception as exc:
            logger.exception("Ragas evaluate failed for %s", item.question)
            rows.append(
                QuestionEval(
                    question=item.question,
                    note=item.note,
                    answer=result.answer,
                    chunks=result.chunks,
                    score=None,
                    error=f"ragas: {exc}",
                )
            )

    if samples:
        EvaluationDataset(samples=samples)

    scored = [row for row in rows if row.score is not None]
    failed = [row for row in rows if row.score is None]
    mean = sum(row.score for row in scored) / len(scored) if scored else None

    question_width = max(len(row.question) for row in rows)
    print()
    print(f"{'question':<{question_width}}  {'faithfulness':>12}  preview")
    print("-" * (question_width + 16 + 80))
    for row in rows:
        score_cell = f"{row.score:.3f}" if row.score is not None else "ERROR"
        preview = _preview(row.answer or row.error or "")
        print(f"{row.question:<{question_width}}  {score_cell:>12}  {preview}")
    if mean is not None:
        print(f"\nPromedio faithfulness ({len(scored)}/{len(rows)}): {mean:.3f}")
    else:
        print("\nPromedio faithfulness: n/a (ninguna pregunta evaluada)")
    if failed:
        print(f"Fallidas: {len(failed)}/{len(rows)}")

    md_lines = [
        "# Faithfulness eval",
        "",
        f"Evaluadas con éxito: {len(scored)}/{len(rows)}",
        f"Promedio: {mean:.3f}" if mean is not None else "Promedio: n/a",
        "",
        "## Tabla",
        "",
        "| question | faithfulness | preview |",
        "|---|---:|---|",
    ]
    for row in rows:
        score_cell = f"{row.score:.3f}" if row.score is not None else "ERROR"
        preview = _preview(row.answer or row.error or "").replace("|", "\\|")
        md_lines.append(f"| {row.question} | {score_cell} | {preview} |")

    md_lines.extend(["", "## Detalle"])
    for index, row in enumerate(rows, start=1):
        score_cell = f"{row.score:.3f}" if row.score is not None else f"ERROR ({row.error})"
        md_lines.extend(
            [
                "",
                f"### {index}. {row.question}",
                "",
                f"- note: {row.note}",
                f"- faithfulness: {score_cell}",
                "",
                "#### Respuesta",
                "",
                row.answer or "_(sin respuesta)_",
                "",
                "#### Contexto recuperado",
                "",
                _format_contexts(row.chunks),
            ]
        )
        if row.error and row.score is None:
            md_lines.extend(["", "#### Error", "", f"```\n{row.error}\n```"])

    md_lines.append("")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\nWrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
