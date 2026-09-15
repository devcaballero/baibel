from __future__ import annotations

from holy_bible.eval.dataset import EVAL_DATASET
from holy_bible.eval.recall_at_k import _UnusedGenerator
from holy_bible.rag.application.service import RagService
from holy_bible.shared.settings import PROJECT_ROOT

OUTPUT_PATH = PROJECT_ROOT / "eval" / "idf_sweep.md"

HYBRID_AT_5 = {
    "¿Quién era Melquisedec?": "miss",
    "¿Cuál es el mandamiento más importante según Jesús?": "hit",
    "¿Cómo describe Pablo el amor en su carta a los Corintios?": "miss",
    "¿Cómo empieza el evangelio de Juan?": "miss",
    "¿Qué le pasó a Jonás en el mar?": "hit",
    "¿Cuáles son las bienaventuranzas?": "hit",
    "¿Qué le prometió Dios a Abraham?": "miss",
    "¿Quién traicionó a Jesús y cómo?": "miss",
    "¿Qué dice el salmo del buen pastor?": "miss",
    "¿Qué le pasó a la esposa de Lot?": "miss",
    "¿Cuál es el fruto del espíritu según Pablo?": "miss",
    "¿Cómo define la fe la carta a los Hebreos?": "miss",
    "¿Quién fue Onán y qué hizo?": "hit",
    "¿Qué le pasó a Job y a su familia?": "miss",
    "¿Qué era el efod que usaban los sacerdotes?": "hit",
}


def main() -> None:
    service = RagService(generator=_UnusedGenerator())
    rows: list[tuple[str, float, str, str]] = []
    for question in EVAL_DATASET:
        max_idf = service._bm25_retriever.max_question_idf(question.question)
        hybrid = HYBRID_AT_5[question.question]
        rows.append((question.question, max_idf, question.note, hybrid))

    rows.sort(key=lambda item: item[1], reverse=True)

    question_width = max(len(row[0]) for row in rows)
    print()
    header = (
        f"{'question':<{question_width}}  {'max_idf':>8}  "
        f"{'note':<40}  hybrid@5"
    )
    print(header)
    print("-" * len(header))
    for question, max_idf, note, hybrid in rows:
        print(
            f"{question:<{question_width}}  {max_idf:8.4f}  {note:<40}  {hybrid}"
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    md = [
        "# Max question IDF sweep",
        "",
        "| question | max_idf | note | hybrid@5 |",
        "|---|---:|---|---|",
    ]
    for question, max_idf, note, hybrid in rows:
        md.append(f"| {question} | {max_idf:.4f} | {note} | {hybrid} |")
    md.append("")
    OUTPUT_PATH.write_text("\n".join(md), encoding="utf-8")
    print(f"\nWrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
