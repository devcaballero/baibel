#!/usr/bin/env python3
"""Paso 5: consolida deuterocanónicos según veredicto Doré/1874 y genera biblia completa."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from holy_bible.etl.chunking import generar_chunks
from holy_bible.shared.settings import LIBROS, OUTPUT_DIR, PROJECT_ROOT
from deuterocanonico_utils import FUENTE_BIBLIATODO

DORE_DIR = OUTPUT_DIR
DIR_1874 = PROJECT_ROOT / "output_1874"
BIBLIA_COMPLETA_FILE = OUTPUT_DIR / "biblia_completa.json"
MANIFEST_FILE = PROJECT_ROOT / "logs" / "deuterocanonico_final_manifest.json"

MAC_DORE_CAPS = {1, 3, 8, 10, 12, 13, 16}


def canon_73_slugs() -> list[str]:
    slugs: list[str] = []
    for libro in LIBROS:
        slug = libro["slug"]
        slugs.append(slug)
        if slug == "nehemias":
            slugs.extend(["tobias", "judit"])
        elif slug == "cantares":
            slugs.extend(["sabiduria", "eclesiastico"])
        elif slug == "lamentaciones":
            slugs.append("baruc")
        elif slug == "malaquias":
            slugs.extend(["1macabeos", "2macabeos"])
    return slugs


def load_book(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def cap_by_num(book: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {c["capitulo"]: c for c in book["capitulos"]}


def annotate_cap(
    cap: dict[str, Any],
    *,
    fuente: str | None = None,
    fuente_ocr: str | None = None,
) -> dict[str, Any]:
    out = deepcopy(cap)
    if fuente is not None:
        out["fuente"] = fuente
    if fuente_ocr is not None:
        out["fuente_ocr"] = fuente_ocr
    return out


def build_book(
    book: dict[str, Any],
    caps: list[dict[str, Any]],
    *,
    fuente_libro: str,
    fuentes_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "libro": book["libro"],
        "libro_slug": book["libro_slug"],
        "testamento": book["testamento"],
        "fuente": fuente_libro,
        "capitulos": caps,
    }
    if fuentes_meta:
        payload["fuentes"] = fuentes_meta
    return payload


def all_ocr_dore(caps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [annotate_cap(c, fuente_ocr="doré") for c in caps]


def all_ocr_1874(caps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [annotate_cap(c, fuente_ocr="1874") for c in caps]


def fix_ester_cap15_verses(versiculos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Quita el bloque duplicado de oración (v11-19) y deja el relato v1-19."""
    reset_idx = None
    for i, verse in enumerate(versiculos):
        if i == 0:
            continue
        if verse["versiculo"] == 1 and versiculos[i - 1]["versiculo"] > 1:
            reset_idx = i
            break

    cleaned = versiculos[reset_idx:] if reset_idx is not None else list(versiculos)

    seen: set[int] = set()
    unique: list[dict[str, Any]] = []
    for verse in cleaned:
        num = verse["versiculo"]
        if num in seen:
            continue
        seen.add(num)
        unique.append(deepcopy(verse))

    unique.sort(key=lambda item: item["versiculo"])
    return unique


def sort_verses_by_number(versiculos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted((deepcopy(v) for v in versiculos), key=lambda item: item["versiculo"])


def merge_1macabeos() -> dict[str, Any]:
    base = load_book(DIR_1874 / "1macabeos.json")
    dore = load_book(DORE_DIR / "1macabeos.json")
    dore_map = cap_by_num(dore)
    caps_out: list[dict[str, Any]] = []
    audit: dict[str, str] = {}

    for cap in sorted(base["capitulos"], key=lambda c: c["capitulo"]):
        num = cap["capitulo"]
        if num in MAC_DORE_CAPS:
            src = dore_map[num]
            caps_out.append(annotate_cap(src, fuente_ocr="doré"))
            audit[str(num)] = "doré"
        else:
            cap_fixed = deepcopy(cap)
            if num == 14:
                cap_fixed["versiculos"] = sort_verses_by_number(cap["versiculos"])
            caps_out.append(annotate_cap(cap_fixed, fuente_ocr="1874"))
            audit[str(num)] = "1874"

    return build_book(
        base,
        caps_out,
        fuente_libro="mixta_ocr_dore_1874",
        fuentes_meta={
            "base_ocr": "1874",
            "caps_dore": sorted(MAC_DORE_CAPS),
            "fuente_ocr_por_capitulo": audit,
            "post_proceso": {"cap_14": "versiculos_reordenados_por_numero"},
        },
    )


def merge_ester() -> dict[str, Any]:
    base = load_book(DIR_1874 / "ester.json")
    dore = load_book(DORE_DIR / "ester.json")
    dore_map = cap_by_num(dore)
    caps_out: list[dict[str, Any]] = []
    audit: dict[str, str] = {}

    for cap in sorted(base["capitulos"], key=lambda c: c["capitulo"]):
        num = cap["capitulo"]
        if num <= 10:
            caps_out.append(annotate_cap(cap, fuente=FUENTE_BIBLIATODO))
            audit[str(num)] = "bibliatodo"
        elif num == 14:
            caps_out.append(annotate_cap(dore_map[num], fuente_ocr="doré"))
            audit[str(num)] = "doré"
        else:
            cap_fixed = deepcopy(cap)
            if num == 15:
                cap_fixed["versiculos"] = fix_ester_cap15_verses(cap["versiculos"])
            caps_out.append(annotate_cap(cap_fixed, fuente_ocr="1874"))
            audit[str(num)] = "1874"

    return build_book(
        base,
        caps_out,
        fuente_libro="mixta_bibliatodo_ocr",
        fuentes_meta={
            "principal": FUENTE_BIBLIATODO,
            "secciones_adicionales": "1874",
            "caps_dore_override": [14],
            "fuente_por_capitulo": audit,
            "post_proceso": {"cap_15": "bloque_oracion_duplicado_eliminado"},
        },
    )


def merge_daniel() -> dict[str, Any]:
    book = load_book(DIR_1874 / "daniel.json")
    caps_out: list[dict[str, Any]] = []
    audit: dict[str, str] = {}

    for cap in sorted(book["capitulos"], key=lambda c: c["capitulo"]):
        num = cap["capitulo"]
        if num <= 12:
            caps_out.append(annotate_cap(cap, fuente=FUENTE_BIBLIATODO))
            audit[str(num)] = "bibliatodo"
        else:
            caps_out.append(annotate_cap(cap, fuente_ocr="1874"))
            audit[str(num)] = "1874"

    return build_book(
        book,
        caps_out,
        fuente_libro="mixta_bibliatodo_ocr",
        fuentes_meta={
            "principal": FUENTE_BIBLIATODO,
            "secciones_adicionales": "1874",
            "capitulos_ocr": [13, 14],
            "fuente_por_capitulo": audit,
        },
    )


def apply_veredict() -> dict[str, Any]:
    manifest: dict[str, Any] = {"libros": {}}

    # Doré sin cambios de texto, solo metadata
    for slug in ("tobias", "sabiduria", "baruc"):
        book = load_book(DORE_DIR / f"{slug}.json")
        out = build_book(
            book,
            all_ocr_dore(book["capitulos"]),
            fuente_libro="archive_org_dore_ocr_llm_limpieza",
            fuentes_meta={"ocr": "doré", "fuente_ocr_por_capitulo": "doré"},
        )
        path = OUTPUT_DIR / f"{slug}.json"
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest["libros"][slug] = {"accion": "mantener_dore", "fuente_ocr": "doré"}

    # 1874 completo
    for slug in ("judit", "eclesiastico", "2macabeos"):
        book = load_book(DIR_1874 / f"{slug}.json")
        out = build_book(
            book,
            all_ocr_1874(book["capitulos"]),
            fuente_libro="archive_org_1874_ocr_llm_limpieza",
            fuentes_meta={"ocr": "1874", "fuente_ocr_por_capitulo": "1874"},
        )
        path = OUTPUT_DIR / f"{slug}.json"
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest["libros"][slug] = {"accion": "reemplazar_1874", "fuente_ocr": "1874"}

    # Mixtos
    daniel = merge_daniel()
    (OUTPUT_DIR / "daniel.json").write_text(
        json.dumps(daniel, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest["libros"]["daniel"] = {
        "accion": "bibliatodo_1_12_1874_13_14",
        "fuente_por_capitulo": daniel["fuentes"]["fuente_por_capitulo"],
    }

    ester = merge_ester()
    (OUTPUT_DIR / "ester.json").write_text(
        json.dumps(ester, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest["libros"]["ester"] = {
        "accion": "bibliatodo_1_10_1874_11_16_cap14_dore",
        "fuente_por_capitulo": ester["fuentes"]["fuente_por_capitulo"],
    }

    mac1 = merge_1macabeos()
    (OUTPUT_DIR / "1macabeos.json").write_text(
        json.dumps(mac1, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest["libros"]["1macabeos"] = {
        "accion": "1874_base_caps_dore_override",
        "fuente_ocr_por_capitulo": mac1["fuentes"]["fuente_ocr_por_capitulo"],
    }

    return manifest


def cargar_biblia_73() -> list[dict[str, Any]]:
    libros: list[dict[str, Any]] = []
    for slug in canon_73_slugs():
        path = OUTPUT_DIR / f"{slug}.json"
        if not path.exists():
            raise FileNotFoundError(f"Falta {path}")
        libros.append(load_book(path))
    return libros


def consolidar_biblia(libros_data: list[dict[str, Any]]) -> None:
    biblia = {"libros": libros_data}
    BIBLIA_COMPLETA_FILE.write_text(
        json.dumps(biblia, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def validar(libros: list[dict[str, Any]]) -> dict[str, Any]:
    checks: dict[str, Any] = {"libros": len(libros), "detalle": {}}
    expected = {
        "judit": 16,
        "eclesiastico": 51,
        "2macabeos": 15,
        "daniel": 14,
        "ester": 16,
        "1macabeos": 16,
    }
    for slug, n_caps in expected.items():
        book = next(b for b in libros if b["libro_slug"] == slug)
        caps = [c["capitulo"] for c in book["capitulos"]]
        checks["detalle"][slug] = {
            "capitulos": len(caps),
            "esperado": n_caps,
            "ok": len(caps) == n_caps,
            "huecos": [i for i in range(1, n_caps + 1) if i not in caps],
        }
    return checks


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = apply_veredict()
    libros = cargar_biblia_73()
    checks = validar(libros)
    consolidar_biblia(libros)
    chunk_count = generar_chunks()

    manifest["validacion"] = checks
    manifest["biblia_completa"] = str(BIBLIA_COMPLETA_FILE)
    manifest["chunks"] = chunk_count
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Libros en biblia_completa.json: {len(libros)}")
    print(f"Chunks generados: {chunk_count}")
    for slug, info in checks["detalle"].items():
        status = "OK" if info["ok"] else "FALLO"
        print(f"  {slug}: {info['capitulos']} caps [{status}]")
    print(f"Manifest: {MANIFEST_FILE}")


if __name__ == "__main__":
    main()
