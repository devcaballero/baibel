#!/usr/bin/env python3
"""Paso 3: limpieza OCR y generación de JSON (local por defecto; --api para Claude)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from holy_bible.shared.settings import OUTPUT_DIR, PROJECT_ROOT
from deuterocanonico_utils import (
    BOOK_META,
    CLEAN_PROMPT,
    FUENTE_BIBLIATODO,
    FUENTE_OCR_1874_LLM,
    FUENTE_OCR_LLM,
    FUENTE_OCR_LOCAL,
    LOGS_DIR,
    split_capitulos,
)
from local_ocr_cleaner import parse_capitulo_fragmento, validar_capitulo

DEFAULT_RAW_DIR = PROJECT_ROOT / "raw"
JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")
MODEL = "claude-haiku-4-5-20251001"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cargar_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def guardar_output(
    clave: str,
    meta: dict,
    capitulos_out: list[dict],
    fuente: str,
    output_dir: Path,
    merge_base_dir: Path,
    force: bool = False,
) -> Path:
    if meta["merge"]:
        out_path = output_dir / f"{meta['libro_slug']}.json"
        base_path = merge_base_dir / f"{meta['libro_slug']}.json"
        existente = json.loads(base_path.read_text(encoding="utf-8"))
        existente.setdefault("fuente", FUENTE_BIBLIATODO)
        reemplazar = {cap["capitulo"] for cap in capitulos_out}
        caps_map = {
            c["capitulo"]: c
            for c in existente["capitulos"]
            if c["capitulo"] not in reemplazar
        }
        agregados: list[int] = []
        for cap in capitulos_out:
            caps_map[cap["capitulo"]] = {
                "capitulo": cap["capitulo"],
                "versiculos": cap["versiculos"],
            }
            agregados.append(cap["capitulo"])
        existente["capitulos"] = sorted(caps_map.values(), key=lambda c: c["capitulo"])
        existente["fuentes"] = {
            "principal": FUENTE_BIBLIATODO,
            "secciones_adicionales": fuente,
            "capitulos_adicionales": sorted(agregados),
        }
        out_path.write_text(json.dumps(existente, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_path

    payload = {
        "libro": meta["libro"],
        "libro_slug": meta["libro_slug"],
        "testamento": meta["testamento"],
        "fuente": fuente,
        "capitulos": [
            {"capitulo": c["capitulo"], "versiculos": c["versiculos"]}
            for c in capitulos_out
        ],
    }
    out_path = output_dir / f"{meta['libro_slug']}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def procesar_libro_local(
    clave: str,
    raw_dir: Path,
    output_dir: Path,
    merge_base_dir: Path,
    fuente: str,
    fallidos: list[dict],
    advertencias: list[dict],
    force: bool = False,
) -> dict:
    meta = BOOK_META[clave]
    raw_path = raw_dir / f"{clave}_raw.txt"
    texto = raw_path.read_text(encoding="utf-8")
    capitulos_raw = split_capitulos(texto, meta.get("ocr_capitulo"))

    capitulos_out: list[dict] = []
    stats: dict[int, int] = {}

    for cap_num, fragmento in capitulos_raw:
        try:
            versiculos, _ = parse_capitulo_fragmento(fragmento)
            warns = validar_capitulo(versiculos, cap_num)
            if warns:
                advertencias.append({"clave": clave, "capitulo": cap_num, "warnings": warns})
            if not versiculos:
                raise ValueError("Sin versículos tras limpieza local")
        except Exception as exc:  # noqa: BLE001
            fallidos.append(
                {
                    "libro_clave": clave,
                    "libro": meta["libro"],
                    "capitulo": cap_num,
                    "error": str(exc),
                    "modo": "local",
                    "fragmento_crudo": fragmento[:8000],
                    "timestamp": utc_now(),
                }
            )
            print(f"  ERROR cap {cap_num}: {exc}", file=sys.stderr)
            continue

        capitulos_out.append({"capitulo": cap_num, "versiculos": versiculos})
        stats[cap_num] = len(versiculos)

    out_path = guardar_output(
        clave, meta, capitulos_out, fuente, output_dir, merge_base_dir, force=force
    )
    return {
        "clave": clave,
        "libro": meta["libro"],
        "modo": "local",
        "output": out_path.name,
        "capitulos": stats,
        "total_versiculos": sum(stats.values()),
    }


def extraer_json(texto: str) -> dict:
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    match = JSON_BLOCK_RE.search(texto)
    if not match:
        raise ValueError("Respuesta sin JSON")
    raw = match.group()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        fixed = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", raw)
        return json.loads(fixed)


def procesar_libro_api(
    clave: str,
    raw_dir: Path,
    output_dir: Path,
    merge_base_dir: Path,
    fuente: str,
    cache_dir: Path,
    force: bool,
    fallidos: list[dict],
) -> dict:
    import anthropic

    meta = BOOK_META[clave]
    raw_path = raw_dir / f"{clave}_raw.txt"
    texto = raw_path.read_text(encoding="utf-8")
    capitulos_raw = split_capitulos(texto, meta.get("ocr_capitulo"))
    cache_path = cache_dir / f"deuterocanonico_cache_{clave}.json"
    cache: dict = {}
    if cache_path.exists() and not force:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Modo --api requiere ANTHROPIC_API_KEY en .env o entorno")
    client = anthropic.Anthropic(api_key=api_key)

    capitulos_out: list[dict] = []
    stats: dict[int, int] = {}

    for cap_num, fragmento in capitulos_raw:
        cache_key = str(cap_num)
        if cache_key in cache and not force:
            versiculos = cache[cache_key]["versiculos"]
        else:
            try:
                prompt = CLEAN_PROMPT.format(
                    libro=meta["libro"], capitulo=cap_num, fragmento=fragmento
                )
                msg = client.messages.create(
                    model=MODEL,
                    max_tokens=8192,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}],
                )
                data = extraer_json(msg.content[0].text)
                versiculos = [
                    {
                        "versiculo": int(v["versiculo"]),
                        "texto": str(v["texto"]).strip(),
                        "notas": v.get("notas"),
                    }
                    for v in data["versiculos"]
                ]
                cache[cache_key] = {"versiculos": versiculos, "procesado_en": utc_now()}
                cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
                time.sleep(0.5)
            except Exception as exc:  # noqa: BLE001
                fallidos.append(
                    {
                        "libro_clave": clave,
                        "libro": meta["libro"],
                        "capitulo": cap_num,
                        "error": str(exc),
                        "modo": "api",
                        "fragmento_crudo": fragmento[:8000],
                        "timestamp": utc_now(),
                    }
                )
                continue
        capitulos_out.append({"capitulo": cap_num, "versiculos": versiculos})
        stats[cap_num] = len(versiculos)

    out_path = guardar_output(
        clave, meta, capitulos_out, fuente, output_dir, merge_base_dir, force=force
    )
    return {
        "clave": clave,
        "libro": meta["libro"],
        "modo": "api",
        "output": out_path.name,
        "capitulos": stats,
        "total_versiculos": sum(stats.values()),
    }


def imprimir_muestras(clave: str, output_dir: Path, caps_nuevos: list[int] | None = None) -> None:
    meta = BOOK_META[clave]
    path = output_dir / f"{meta['libro_slug']}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    todos: list[dict] = []
    for cap in data["capitulos"]:
        if caps_nuevos and cap["capitulo"] not in caps_nuevos:
            continue
        for v in cap["versiculos"]:
            todos.append({"capitulo": cap["capitulo"], **v})
    if not todos:
        return
    label = f"caps {caps_nuevos}" if caps_nuevos else "libro completo"
    print(f"\n=== {meta['libro']} ({clave}, {label}) — primeros 3 versículos ===")
    for v in todos[:3]:
        print(f"  {v['capitulo']}:{v['versiculo']}  {v['texto'][:120]}...")
    print(f"=== {meta['libro']} — últimos 3 versículos ===")
    for v in todos[-3:]:
        print(f"  {v['capitulo']}:{v['versiculo']}  {v['texto'][:120]}...")


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpiar OCR deuterocanónico")
    parser.add_argument("--libro", action="append", help="Procesar solo clave(s) del mapa")
    parser.add_argument("--api", action="store_true", help="Usar Claude API en lugar de limpieza local")
    parser.add_argument("--force", action="store_true", help="Reprocesar cache API")
    parser.add_argument("--muestras", action="store_true", help="Imprimir primeros/últimos 3 versículos")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help="Directorio raw de entrada")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directorio JSON de salida (default: output/)",
    )
    parser.add_argument(
        "--merge-base-dir",
        type=Path,
        default=None,
        help="Base para merge Daniel/Ester (default: output-dir o output/ si difiere)",
    )
    parser.add_argument(
        "--fuente",
        default=None,
        help="Valor del campo fuente en JSON (default según modo/edición)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Directorio de cache API (default: logs/)",
    )
    parser.add_argument(
        "--fragmentos-fallidos",
        type=Path,
        default=None,
        help="Ruta logs/fragmentos_fallidos.json alternativa",
    )
    parser.add_argument(
        "--resumen",
        type=Path,
        default=None,
        help="Ruta logs/deuterocanonico_resumen.json alternativa",
    )
    args = parser.parse_args()

    cargar_env()
    cache_dir = args.cache_dir or LOGS_DIR
    fragmentos_path = args.fragmentos_fallidos or LOGS_DIR / "fragmentos_fallidos.json"
    resumen_path = args.resumen or LOGS_DIR / "deuterocanonico_resumen.json"
    merge_base_dir = args.merge_base_dir or (
        OUTPUT_DIR if args.output_dir != OUTPUT_DIR else args.output_dir
    )

    if args.fuente:
        fuente = args.fuente
    elif args.output_dir.name == "output_1874" or "1874" in str(args.output_dir):
        fuente = FUENTE_OCR_1874_LLM
    else:
        fuente = FUENTE_OCR_LLM if args.api else FUENTE_OCR_LOCAL

    cache_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    claves = args.libro or list(BOOK_META.keys())
    fallidos: list[dict] = []
    advertencias: list[dict] = []
    if fragmentos_path.exists():
        fallidos = json.loads(fragmentos_path.read_text(encoding="utf-8"))

    resumenes: list[dict] = []
    modo = "api" if args.api else "local"
    print(f"Modo: {modo} | fuente: {fuente} | raw: {args.raw_dir} | out: {args.output_dir}")

    for clave in claves:
        if clave not in BOOK_META:
            raise SystemExit(f"Clave desconocida: {clave}")
        raw_path = args.raw_dir / f"{clave}_raw.txt"
        if not raw_path.exists():
            raise SystemExit(f"Falta {raw_path}; ejecutá extract_deuterocanonico.py primero")

        print(f"\nProcesando {clave}...")
        if args.api:
            resumen = procesar_libro_api(
                clave,
                args.raw_dir,
                args.output_dir,
                merge_base_dir,
                fuente,
                cache_dir,
                args.force,
                fallidos,
            )
        else:
            resumen = procesar_libro_local(
                clave,
                args.raw_dir,
                args.output_dir,
                merge_base_dir,
                fuente,
                fallidos,
                advertencias,
                force=args.force,
            )
        resumenes.append(resumen)
        print(
            f"  {resumen['total_versiculos']} versículos en "
            f"{len(resumen['capitulos'])} capítulos → {args.output_dir}/{resumen['output']}"
        )
        if args.muestras:
            caps_muestra = (
                list(resumen["capitulos"].keys()) if BOOK_META[clave].get("merge") else None
            )
            imprimir_muestras(clave, args.output_dir, caps_muestra)

    fragmentos_path.write_text(
        json.dumps(fallidos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    resumen_path.write_text(
        json.dumps(resumenes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    adv_path = cache_dir / "deuterocanonico_advertencias.json"
    adv_path.write_text(json.dumps(advertencias, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nResumen → {resumen_path}")
    if advertencias:
        print(f"Advertencias de validación → {adv_path} ({len(advertencias)} caps)")
    if fallidos:
        print(f"Fragmentos fallidos → {fragmentos_path} ({len(fallidos)})")


if __name__ == "__main__":
    main()
