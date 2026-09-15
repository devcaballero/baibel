from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from holy_bible.shared.settings import (
    LIBROS,
    OUTPUT_DIR,
    OVERLAP,
    VERSICULOS_POR_CHUNK,
)

BIBLIA_COMPLETA_FILE = OUTPUT_DIR / "biblia_completa.json"
CHUNKS_FILE = OUTPUT_DIR / "biblia_chunks.jsonl"
EXCLUDED_FILES = {"biblia_completa.json", "biblia_chunks.jsonl"}


def iter_libros_json() -> Iterator[dict[str, Any]]:
    if BIBLIA_COMPLETA_FILE.exists():
        data = json.loads(BIBLIA_COMPLETA_FILE.read_text(encoding="utf-8"))
        yield from data.get("libros", [])
        return

    slugs = {libro["slug"] for libro in LIBROS}
    for path in sorted(OUTPUT_DIR.glob("*.json")):
        if path.name in EXCLUDED_FILES:
            continue
        slug = path.stem
        if slug not in slugs:
            continue
        yield json.loads(path.read_text(encoding="utf-8"))


def fuente_capitulo(cap: dict[str, Any], libro_data: dict[str, Any]) -> str:
    if cap.get("fuente_ocr"):
        return str(cap["fuente_ocr"])
    if cap.get("fuente"):
        return str(cap["fuente"])
    if libro_data.get("fuente"):
        return str(libro_data["fuente"])
    return "bibliatodo"


def generar_chunks_por_capitulo(
    libro: str,
    testamento: str,
    slug: str,
    capitulo: int,
    versiculos: list[dict[str, Any]],
    fuente: str,
    chunk_size: int = VERSICULOS_POR_CHUNK,
    overlap: int = OVERLAP,
) -> list[dict[str, Any]]:
    if not versiculos:
        return []

    chunks: list[dict[str, Any]] = []
    step = max(1, chunk_size - overlap)
    i = 0

    while i < len(versiculos):
        batch = versiculos[i : i + chunk_size]
        if not batch:
            break

        inicio = batch[0]["versiculo"]
        fin = batch[-1]["versiculo"]
        texto = " ".join(v["texto"] for v in batch)

        chunks.append(
            {
                "id": f"{slug}_{capitulo}_{inicio}_{len(chunks) + 1}",
                "libro": libro,
                "testamento": testamento,
                "capitulo": capitulo,
                "versiculo_inicio": inicio,
                "versiculo_fin": fin,
                "texto": texto,
                "fuente": fuente,
            }
        )

        if i + chunk_size >= len(versiculos):
            break
        i += step

    return chunks


def generar_chunks(
    chunk_size: int = VERSICULOS_POR_CHUNK,
    overlap: int = OVERLAP,
    output_path: Path = CHUNKS_FILE,
) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0

    with output_path.open("w", encoding="utf-8") as out:
        for libro_data in iter_libros_json():
            libro = libro_data["libro"]
            slug = libro_data["libro_slug"]
            testamento = libro_data["testamento"]

            for cap in libro_data.get("capitulos", []):
                chunks = generar_chunks_por_capitulo(
                    libro=libro,
                    testamento=testamento,
                    slug=slug,
                    capitulo=cap["capitulo"],
                    versiculos=cap["versiculos"],
                    fuente=fuente_capitulo(cap, libro_data),
                    chunk_size=chunk_size,
                    overlap=overlap,
                )
                for chunk in chunks:
                    out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                    count += 1

    return count
