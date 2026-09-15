from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from holy_bible.eval.dataset import EVAL_DATASET, EvalQuestion, ExpectedPassage
from holy_bible.rag.application.service import RagService
from holy_bible.rag.domain.entities import BiblicalChunk
from holy_bible.shared.settings import PROJECT_ROOT

K_VALUES = [1, 3, 5]
LAST_RUN_PATH = PROJECT_ROOT / "eval" / "last_run.md"


class _UnusedGenerator:
    def generate(self, question: str, chunks: list[BiblicalChunk]) -> str:
        raise RuntimeError("eval must not call the language model")


def is_hit(chunk: BiblicalChunk, expected: list[ExpectedPassage]) -> bool:
    return any(
        chunk.book == passage.book
        and chunk.chapter == passage.chapter
        and chunk.verse_start <= passage.verse_end
        and passage.verse_start <= chunk.verse_end
        for passage in expected
    )


def _hits_at_k(chunks: list[BiblicalChunk], expected: list[ExpectedPassage]) -> dict[int, bool]:
    return {
        k: any(is_hit(chunk, expected) for chunk in chunks[:k]) for k in K_VALUES
    }


def _format_pct(hits: int, total: int) -> str:
    return f"{(100.0 * hits / total):5.1f}%"


def _table_lines(totals: dict[bool, dict[int, int]], n_questions: int) -> list[str]:
    header = f"{'Recall@k':<16} {'k=1':>8} {'k=3':>8} {'k=5':>8}"
    rows = [header]
    for hybrid, label in ((True, "hybrid=True"), (False, "hybrid=False")):
        cells = "  ".join(_format_pct(totals[hybrid][k], n_questions) for k in K_VALUES)
        rows.append(f"{label:<16} {cells}")
    return rows


def main() -> None:
    service = RagService(generator=_UnusedGenerator())
    totals: dict[bool, dict[int, int]] = {
        True: defaultdict(int),
        False: defaultdict(int),
    }
    per_question: list[tuple[EvalQuestion, dict[bool, dict[int, bool]]]] = []

    for question in EVAL_DATASET:
        modes: dict[bool, dict[int, bool]] = {}
        for hybrid in (True, False):
            chunks = service.retrieve(
                question.question,
                num_results=max(K_VALUES),
                hybrid=hybrid,
            )
            hits = _hits_at_k(chunks, question.expected)
            modes[hybrid] = hits
            for k, hit in hits.items():
                totals[hybrid][k] += int(hit)
        per_question.append((question, modes))

    n_questions = len(EVAL_DATASET)
    table = _table_lines(totals, n_questions)
    print()
    print("\n".join(table))

    disagreements: list[str] = []
    for question, modes in per_question:
        hit_hybrid = modes[True][max(K_VALUES)]
        hit_dense = modes[False][max(K_VALUES)]
        if hit_hybrid == hit_dense:
            continue
        disagreements.append(
            f"- {question.question}  |  hybrid@5={'hit' if hit_hybrid else 'miss'}  "
            f"dense@5={'hit' if hit_dense else 'miss'}  ({question.note})"
        )

    print()
    if disagreements:
        print("Disagreements at k=5:")
        print("\n".join(disagreements))
    else:
        print("Disagreements at k=5: none")

    LAST_RUN_PATH.parent.mkdir(parents=True, exist_ok=True)
    detail_lines = []
    for question, modes in per_question:
        hybrid_bits = " ".join(
            f"@{k}={'Y' if modes[True][k] else 'N'}" for k in K_VALUES
        )
        dense_bits = " ".join(
            f"@{k}={'Y' if modes[False][k] else 'N'}" for k in K_VALUES
        )
        detail_lines.append(
            f"- {question.question}\n"
            f"  hybrid {hybrid_bits} | dense {dense_bits} | {question.note}"
        )

    LAST_RUN_PATH.write_text(
        "\n".join(
            [
                "# Recall@k last run",
                "",
                "```",
                *table,
                "```",
                "",
                "## Disagreements at k=5",
                *(disagreements or ["none"]),
                "",
                "## Per question",
                *detail_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {LAST_RUN_PATH}")


if __name__ == "__main__":
    main()
