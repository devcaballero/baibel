"""Lógica de parsing HTML compartida entre explorar.py y scraper.py."""

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from holy_bible.shared.settings import CAPITULO_VACIO_PATTERN

SELECTOR_CONTENEDOR = "#info_capitulo"
SELECTOR_VERSICULOS = "p.bt-verse"
SELECTOR_NUMERO = "sup > a"
SELECTOR_TEXTO = "span.bt-verse-text"


def es_capitulo_vacio(html: str) -> bool:
    """Detecta si la página no tiene contenido bíblico."""
    if re.search(CAPITULO_VACIO_PATTERN, html, re.IGNORECASE):
        return True
    soup = BeautifulSoup(html, "lxml")
    return len(soup.select(SELECTOR_VERSICULOS)) == 0


def _extraer_notas(verse_el: Tag) -> list[str] | None:
    """Extrae notas al pie si existen, excluyendo el sup del número de versículo."""
    notas: list[str] = []

    for note_el in verse_el.select(".bt-note, .nota, .footnote"):
        texto = note_el.get_text(strip=True)
        if texto:
            notas.append(texto)

    for sup in verse_el.find_all("sup"):
        if sup.find("a"):
            continue
        texto = sup.get_text(strip=True)
        if texto:
            notas.append(texto)

    return notas if notas else None


def parse_versiculo(verse_el: Tag) -> dict[str, Any] | None:
    """Parsea un elemento p.bt-verse individual."""
    num_el = verse_el.select_one(SELECTOR_NUMERO)
    text_el = verse_el.select_one(SELECTOR_TEXTO)

    if not num_el or not text_el:
        return None

    try:
        numero = int(num_el.get_text(strip=True))
    except ValueError:
        return None

    texto = text_el.get_text(strip=True)
    if not texto:
        return None

    return {
        "versiculo": numero,
        "texto": texto,
        "notas": _extraer_notas(verse_el),
    }


def parse_capitulo(html: str) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Parsea todos los versículos de un capítulo.

    Returns:
        Tupla (versiculos, warnings).
    """
    soup = BeautifulSoup(html, "lxml")
    warnings: list[str] = []
    versiculos: list[dict[str, Any]] = []

    for verse_el in soup.select(SELECTOR_VERSICULOS):
        parsed = parse_versiculo(verse_el)
        if parsed is None:
            snippet = verse_el.get_text(strip=True)[:80]
            warnings.append(f"No se pudo parsear versículo: {snippet!r}")
            continue
        versiculos.append(parsed)

    for i, v in enumerate(versiculos):
        expected = i + 1
        if v["versiculo"] != expected:
            warnings.append(
                f"Secuencia irregular: esperado v.{expected}, encontrado v.{v['versiculo']}"
            )
            break

    return versiculos, warnings


def obtener_html_contenedor(html: str) -> str | None:
    """Devuelve outerHTML del contenedor #info_capitulo."""
    soup = BeautifulSoup(html, "lxml")
    contenedor = soup.select_one(SELECTOR_CONTENEDOR)
    return str(contenedor) if contenedor else None
