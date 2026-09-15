"""Utilidades compartidas para procesamiento de libros deuterocanónicos."""

from __future__ import annotations

import json
import re
from pathlib import Path

from holy_bible.shared.settings import PROJECT_ROOT

MAPA_PATH = PROJECT_ROOT / "mapa_libros_deuterocanonicos.json"
RAW_DIR = PROJECT_ROOT / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

FUENTE_OCR_LLM = "archive_org_ocr_llm_limpieza"
FUENTE_OCR_1874_LLM = "archive_org_1874_ocr_llm_limpieza"
FUENTE_OCR_LOCAL = "archive_org_ocr_local_limpieza"
FUENTE_BIBLIATODO = "bibliatodo"

BOOK_META: dict[str, dict] = {
    "tobias": {
        "libro": "Tobías",
        "libro_slug": "tobias",
        "testamento": "AT",
        "merge": False,
    },
    "judit": {
        "libro": "Judit",
        "libro_slug": "judit",
        "testamento": "AT",
        "merge": False,
    },
    "ester": {
        "libro": "Ester",
        "libro_slug": "ester",
        "testamento": "AT",
        "merge": True,
        "ocr_capitulo": {"XY": 15},
    },
    "sabiduria": {
        "libro": "Sabiduría",
        "libro_slug": "sabiduria",
        "testamento": "AT",
        "merge": False,
        "ocr_capitulo": {"XY": 16, "XYII": 17},
    },
    "eclesiastico": {
        "libro": "Eclesiástico",
        "libro_slug": "eclesiastico",
        "testamento": "AT",
        "merge": False,
    },
    "baruc": {
        "libro": "Baruc",
        "libro_slug": "baruc",
        "testamento": "AT",
        "merge": False,
    },
    "daniel_13_14": {
        "libro": "Daniel",
        "libro_slug": "daniel",
        "testamento": "AT",
        "merge": True,
    },
    "1macabeos": {
        "libro": "1 Macabeos",
        "libro_slug": "1macabeos",
        "testamento": "AT",
        "merge": False,
    },
    "2macabeos": {
        "libro": "2 Macabeos",
        "libro_slug": "2macabeos",
        "testamento": "AT",
        "merge": False,
    },
}

ORDINALES = {
    "PRIMERO": 1,
    "PKIMERO": 1,
    "SEGUNDO": 2,
    "TERCERO": 3,
    "CUARTO": 4,
    "QUINTO": 5,
    "SEXTO": 6,
    "SEPTIMO": 7,
    "SÉPTIMO": 7,
    "OCTAVO": 8,
    "NOVENO": 9,
    "DECIMO": 10,
    "DÉCIMO": 10,
}

OCR_CAPITULO = {
    "IY": 4,
    "Y": 5,
    "IN": 9,
    "VIH": 8,
    "XIY": 14,
    "XIV": 14,
    "XV": 15,
}

ROMAN = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
    "XVI": 16,
    "XVII": 17,
    "XVIII": 18,
    "XIX": 19,
    "XX": 20,
    "XXI": 21,
    "XXII": 22,
    "XXIII": 23,
    "XXIV": 24,
    "XXV": 25,
    "XXVI": 26,
    "XXVII": 27,
    "XXVIII": 28,
    "XXIX": 29,
    "XXX": 30,
    "XXXI": 31,
    "XXXII": 32,
    "XXXIII": 33,
    "XXXIV": 34,
    "XXXV": 35,
    "XXXVI": 36,
    "XXXVII": 37,
    "XXXVIII": 38,
    "XXXIX": 39,
    "XL": 40,
    "XLI": 41,
    "XLII": 42,
    "XLIII": 43,
    "XLIV": 44,
    "XLV": 45,
    "XLVI": 46,
    "XLVII": 47,
    "XLVIII": 48,
    "XLIX": 49,
    "L": 50,
    "LI": 51,
    "XIY": 14,  # OCR frecuente en Daniel XIV
    "YI": 6,  # CAPITULO YI en Baruc
}

CHAPTER_HEAD = (
    r"PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|SEPTIMO|OCTAVO|NOVENO|"
    r"DÉCIMO|DECIMO|[IVXLCDM]+|\d+"
)
CHAPTER_RE = re.compile(
    rf"(?im)^\s*(?:\d+\s+)?CAP[ÍI]TULO\s+({CHAPTER_HEAD})\b"
)


def parse_capitulo(raw: str, overrides: dict[str, int] | None = None) -> int | None:
    token = re.split(r"\s+", raw.strip().upper())[0].rstrip(".,;:")
    if overrides and token in overrides:
        return overrides[token]
    if token.isdigit():
        return int(token)
    if token in OCR_CAPITULO:
        return OCR_CAPITULO[token]
    if token in ORDINALES:
        return ORDINALES[token]
    if token in ROMAN:
        return ROMAN[token]
    return None


def split_capitulos(texto: str, ocr_capitulo: dict[str, int] | None = None) -> list[tuple[int, str]]:
    matches = list(CHAPTER_RE.finditer(texto))
    if not matches:
        raise ValueError("No se encontraron marcadores CAPITULO en el texto")

    fragmentos_por_cap: dict[int, list[str]] = {}
    for i, match in enumerate(matches):
        num = parse_capitulo(match.group(1), ocr_capitulo)
        if num is None:
            continue
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        fragmento = texto[start:end].strip()
        if fragmento:
            fragmentos_por_cap.setdefault(num, []).append(fragmento)

    return [
        (num, "\n\n".join(partes))
        for num, partes in sorted(fragmentos_por_cap.items())
    ]


def cargar_mapa() -> dict:
    data = json.loads(MAPA_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


CLEAN_PROMPT = """Eres un asistente de limpieza de OCR para una edición antigua de la Biblia Torres Amat (español, 1883-1884).

TAREA: Reconstruir el texto limpio corrigiendo SOLO ruido de OCR (espaciado irregular, caracteres mal reconocidos, palabras partidas, números de nota mezclados en el flujo). NO traduzcas, NO parafrasees, NO modernices el español, NO agregues ni quites contenido bíblico.

DESCARTAR EXPLÍCITAMENTE (no incluir en ningún versículo):
- Pies de ilustración / títulos de grabados Doré intercalados en el flujo (ej. "JUDAS MACABEO EN PRESENCIA DEL EJÉRCITO DE NICANOR", líneas en mayúsculas que describen una escena ilustrada). Son leyendas de grabado, NO versículos ni títulos de capítulo/libro.
- Encabezados de página, números de página sueltos, marcas de sección editorial ("II.— 44", etc.).
- Notas al pie y comentarios editoriales de Torres Amat: extraer aparte en `notas_del_fragmento`, no mezclarlos en el texto del versículo.

MANTENER:
- Títulos de capítulo bíblico si aparecen (ej. "CAPITULO PRIMERO") solo como referencia; el JSON pide versículos numerados.
- Numeración de versículos tal como en el original (1., 2., etc.).

Libro: {libro}
Capítulo: {capitulo}

Devuelve ÚNICAMENTE JSON válido (sin markdown) con esta forma:
{{
  "versiculos": [{{"versiculo": 1, "texto": "..."}}, {{"versiculo": 2, "texto": "..."}}],
  "notas_del_fragmento": null
}}

Si hay notas al pie claramente separadas, pon el texto reunido en `notas_del_fragmento` (string o null).

TEXTO OCR DEL FRAGMENTO:
---
{fragmento}
---"""
