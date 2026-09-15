from __future__ import annotations

from holy_bible.rag.domain.entities import BiblicalChunk


def reciprocal_rank_fusion(
    rankings: list[list[BiblicalChunk]],
    k: int = 60,
) -> list[BiblicalChunk]:
    scores: dict[str, float] = {}
    first_seen: dict[str, BiblicalChunk] = {}
    for ranking in rankings:
        for index, chunk in enumerate(ranking):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + index + 1)
            if chunk.id not in first_seen:
                first_seen[chunk.id] = chunk
    return sorted(
        first_seen.values(),
        key=lambda chunk: scores[chunk.id],
        reverse=True,
    )
