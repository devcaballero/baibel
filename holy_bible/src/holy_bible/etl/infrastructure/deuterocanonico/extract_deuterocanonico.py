#!/usr/bin/env python3
"""Paso 2: extrae texto OCR crudo de libros deuterocanónicos según un mapa JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from holy_bible.shared.settings import PROJECT_ROOT

DEFAULT_MAPA = PROJECT_ROOT / "mapa_libros_deuterocanonicos.json"
DEFAULT_RAW_DIR = PROJECT_ROOT / "raw"

ARCHIVOS = {
    "T2": PROJECT_ROOT / "tomo2_y_tomo3/La Sagrada Biblia T2.txt",
    "T3": PROJECT_ROOT / "tomo2_y_tomo3/La Sagrada Biblia T3.txt",
    "AT1874": PROJECT_ROOT / "antiguo testamento/labiblia_torres_amat_antiguo_testamento.txt",
}


def cargar_mapa(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data.get("_meta", {})
    archivos_meta = meta.get("archivos", {})
    for clave, rel in archivos_meta.items():
        if clave not in ARCHIVOS:
            ARCHIVOS[clave] = PROJECT_ROOT / rel
    return {k: v for k, v in data.items() if not k.startswith("_")}


def leer_rango(path: Path, inicio: int, fin: int) -> str:
    lineas: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for num, linea in enumerate(f, start=1):
            if num < inicio:
                continue
            if num > fin:
                break
            lineas.append(linea.rstrip("\n"))
    return "\n".join(lineas)


def extraer_libro(clave: str, info: dict) -> tuple[str | None, str | None, str]:
    archivo = ARCHIVOS[info["archivo"]]
    texto = leer_rango(archivo, info["linea_inicio_texto"], info["linea_fin"])

    intro: str | None = None
    prologo: str | None = None
    if info.get("linea_inicio_intro"):
        fin_intro = info["linea_inicio_texto"] - 1
        if info.get("linea_inicio_prologo"):
            fin_intro = info["linea_inicio_prologo"] - 1
            prologo = leer_rango(
                archivo,
                info["linea_inicio_prologo"],
                info["linea_fin_prologo"],
            )
        intro = leer_rango(archivo, info["linea_inicio_intro"], fin_intro)

    return intro, prologo, texto


def main() -> None:
    parser = argparse.ArgumentParser(description="Extraer raw de libros deuterocanónicos")
    parser.add_argument(
        "--mapa",
        type=Path,
        default=DEFAULT_MAPA,
        help="Ruta al mapa JSON (default: mapa_libros_deuterocanonicos.json)",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW_DIR,
        help="Directorio de salida para raw (default: raw/)",
    )
    parser.add_argument(
        "--libro",
        action="append",
        help="Solo extraer clave(s) del mapa (ej. tobias). Repetible.",
    )
    args = parser.parse_args()

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    mapa = cargar_mapa(args.mapa)
    claves = args.libro or sorted(mapa.keys())

    for clave in claves:
        if clave not in mapa:
            raise SystemExit(f"Clave desconocida en mapa: {clave}")
        info = mapa[clave]
        intro, prologo, texto = extraer_libro(clave, info)

        raw_path = args.raw_dir / f"{clave}_raw.txt"
        raw_path.write_text(texto, encoding="utf-8")
        print(f"{clave}: {raw_path} ({len(texto.splitlines())} líneas)")

        if intro:
            intro_path = args.raw_dir / f"{clave}_intro_raw.txt"
            intro_path.write_text(intro, encoding="utf-8")
            print(f"  intro: {intro_path} ({len(intro.splitlines())} líneas)")

        if prologo:
            prologo_path = args.raw_dir / f"{clave}_prologo_raw.txt"
            prologo_path.write_text(prologo, encoding="utf-8")
            print(f"  prologo: {prologo_path} ({len(prologo.splitlines())} líneas)")

    print(f"\nExtracción completada en {args.raw_dir}")


if __name__ == "__main__":
    main()
