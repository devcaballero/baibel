from __future__ import annotations

import re
from pathlib import Path

from holy_bible.eval.dataset import EVAL_DATASET
from holy_bible.eval.recall_at_k import _UnusedGenerator
from holy_bible.rag.application.service import RagService
from holy_bible.shared.settings import PROJECT_ROOT, RETRIEVAL_POOL_SIZE

THRESHOLDS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
LAST_RUN_PATH = PROJECT_ROOT / "eval" / "last_run.md"
OUTPUT_PATH = PROJECT_ROOT / "eval" / "threshold_sweep.md"

_HYBRID_AT_5 = re.compile(
    r"^- (?P<question>.+)\n  hybrid @1=. @3=. @5=(?P<hit>[YN])",
    re.MULTILINE,
)


def _hybrid_hits_at_5(path: Path) -> dict[str, bool]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    return {
        match.group("question").strip(): match.group("hit") == "Y"
        for match in _HYBRID_AT_5.finditer(text)
    }


def main() -> None:
    service = RagService(generator=_UnusedGenerator())
    hybrid_hits = _hybrid_hits_at_5(LAST_RUN_PATH)
    rows: list[tuple[str, float, str, str]] = []

    for question in EVAL_DATASET:
        scored = service._bm25_retriever.search_with_scores(
            question.question,
            n_results=RETRIEVAL_POOL_SIZE,
        )
        top_score = scored[0][1] if scored else 0.0
        if question.question not in hybrid_hits:
            hybrid_label = "hybrid@5 n/a"
        elif hybrid_hits[question.question]:
            hybrid_label = "hybrid@5 hit"
        else:
            hybrid_label = "hybrid@5 miss"
        rows.append((question.question, top_score, question.note, hybrid_label))

    rows.sort(key=lambda item: item[1], reverse=True)

    question_width = max(len(row[0]) for row in rows)
    print()
    header = (
        f"{'question':<{question_width}}  {'top_sparse_score':>16}  "
        f"{'note':<36}  hybrid last_run"
    )
    print(header)
    print("-" * len(header))
    for question, score, note, hybrid_label in rows:
        print(
            f"{question:<{question_width}}  {score:16.4f}  {note:<36}  {hybrid_label}"
        )

    print()
    print(f"{'umbral':>8}  {'activarían hybrid':>18}  (de {len(EVAL_DATASET)})")
    threshold_lines: list[str] = []
    for threshold in THRESHOLDS:
        count = sum(1 for _, score, _, _ in rows if score >= threshold)
        line = f"{threshold:8.1f}  {count:18d}  / {len(EVAL_DATASET)}"
        threshold_lines.append(line)
        print(line)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    md_rows = [
        "| question | top_sparse_score | note | hybrid last_run |",
        "|---|---:|---|---|",
    ]
    for question, score, note, hybrid_label in rows:
        md_rows.append(
            f"| {question} | {score:.4f} | {note} | {hybrid_label} |"
        )
    md_thresholds = [
        "| umbral | activarían hybrid |",
        "|---:|---:|",
    ]
    for threshold in THRESHOLDS:
        count = sum(1 for _, score, _, _ in rows if score >= threshold)
        md_thresholds.append(f"| {threshold:.1f} | {count} / {len(EVAL_DATASET)} |")

    OUTPUT_PATH.write_text(
        "\n".join(
            [
                "# BM25 top-score threshold sweep",
                "",
                "## Scores por pregunta",
                "",
                *md_rows,
                "",
                "## Umbrales candidatos",
                "",
                *md_thresholds,
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
