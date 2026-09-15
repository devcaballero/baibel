from holy_bible.rag.domain.entities import BiblicalChunk
from holy_bible.rag.domain.ranking import reciprocal_rank_fusion


def _chunk(chunk_id: str) -> BiblicalChunk:
    return BiblicalChunk(
        id=chunk_id,
        text=chunk_id,
        book="Génesis",
        chapter=1,
        verse_start=1,
        verse_end=1,
        source="test",
        testament="AT",
    )


def test_reciprocal_rank_fusion_promotes_overlap() -> None:
    chunk_a = _chunk("A")
    chunk_b = _chunk("B")
    chunk_c = _chunk("C")
    fused = reciprocal_rank_fusion(
        [
            [chunk_a, chunk_b],
            [chunk_c, chunk_a],
        ]
    )
    assert [chunk.id for chunk in fused][0] == "A"
    assert {chunk.id for chunk in fused} == {"A", "B", "C"}
    print("\n=== RRF overlap ===\nOK: A rankea primero por aparecer en ambas listas")


if __name__ == "__main__":
    test_reciprocal_rank_fusion_promotes_overlap()
