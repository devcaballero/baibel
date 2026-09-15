#!/usr/bin/env python3
"""Compara versículos por capítulo entre dos corridas deuterocanónicas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from holy_bible.shared.settings import OUTPUT_DIR, PROJECT_ROOT
from deuterocanonico_utils import BOOK_META

DEUTERO_SLUGS = {
    "tobias",
    "judit",
    "ester",
    "sabiduria",
    "eclesiastico",
    "baruc",
    "daniel",
    "1macabeos",
    "2macabeos",
}

MERGE_CAPS = {
    "ester": list(range(11, 17)),
    "daniel": [13, 14],
}


def caps_versiculos(path: Path, solo: list[int] | None = None) -> dict[int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[int, int] = {}
    for cap in data.get("capitulos", []):
        num = cap["capitulo"]
        if solo is not None and num not in solo:
            continue
        out[num] = len(cap.get("versiculos", []))
    return out


def comparar(
    anterior_dir: Path,
    nueva_dir: Path,
    etiqueta_anterior: str,
    etiqueta_nueva: str,
) -> dict:
    libros = []
    for clave, meta in BOOK_META.items():
        slug = meta["libro_slug"]
        if slug not in DEUTERO_SLUGS:
            continue
        solo = MERGE_CAPS.get(slug)
        prev_path = anterior_dir / f"{slug}.json"
        new_path = nueva_dir / f"{slug}.json"
        if not prev_path.exists() or not new_path.exists():
            continue
        prev = caps_versiculos(prev_path, solo)
        new = caps_versiculos(new_path, solo)
        caps = sorted(set(prev) | set(new))
        filas = []
        mejor_nueva = 0
        mejor_anterior = 0
        iguales = 0
        for cap in caps:
            p = prev.get(cap, 0)
            n = new.get(cap, 0)
            if cap not in prev:
                estado = "solo_nueva"
                mejor_nueva += 1
            elif cap not in new:
                estado = "solo_anterior"
                mejor_anterior += 1
            elif n > p:
                estado = "nueva_mayor"
                mejor_nueva += 1
            elif n < p:
                estado = "anterior_mayor"
                mejor_anterior += 1
            else:
                estado = "igual"
                iguales += 1
            filas.append(
                {
                    "capitulo": cap,
                    f"versiculos_{etiqueta_anterior}": p if cap in prev else None,
                    f"versiculos_{etiqueta_nueva}": n if cap in new else None,
                    "delta": (n - p) if cap in prev and cap in new else None,
                    "estado": estado,
                }
            )
        libros.append(
            {
                "clave": clave,
                "libro": meta["libro"],
                "slug": slug,
                "caps_anterior": len(prev),
                "caps_nueva": len(new),
                "total_versiculos_anterior": sum(prev.values()),
                "total_versiculos_nueva": sum(new.values()),
                "caps_mejor_nueva": mejor_nueva,
                "caps_mejor_anterior": mejor_anterior,
                "caps_iguales": iguales,
                "capitulos": filas,
            }
        )
    return {
        "anterior": str(anterior_dir),
        "nueva": str(nueva_dir),
        "libros": libros,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Comparar corridas deuterocanónicas")
    parser.add_argument("--anterior", type=Path, default=OUTPUT_DIR, help="Salida Doré/previous")
    parser.add_argument("--nueva", type=Path, default=PROJECT_ROOT / "output_1874")
    parser.add_argument(
        "--out",
        type=Path,
        default=PROJECT_ROOT / "logs" / "comparacion_deuterocanonico_1874_vs_dore.json",
    )
    args = parser.parse_args()

    reporte = comparar(args.anterior, args.nueva, "dore", "1874")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Comparación guardada en {args.out}\n")
    for libro in reporte["libros"]:
        print(
            f"{libro['libro']}: caps {libro['caps_anterior']}→{libro['caps_nueva']} | "
            f"versículos {libro['total_versiculos_anterior']}→{libro['total_versiculos_nueva']} | "
            f"mejor 1874: {libro['caps_mejor_nueva']} caps | "
            f"mejor Doré: {libro['caps_mejor_anterior']} caps | "
            f"iguales: {libro['caps_iguales']}"
        )
        faltantes = [
            f["capitulo"]
            for f in libro["capitulos"]
            if f["estado"] in ("solo_anterior", "anterior_mayor")
        ]
        if faltantes:
            print(f"  ⚠ caps donde Doré gana o falta en 1874: {faltantes[:20]}")


if __name__ == "__main__":
    main()
