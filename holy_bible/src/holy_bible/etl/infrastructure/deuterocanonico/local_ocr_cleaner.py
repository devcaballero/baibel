"""Limpieza y estructuración local de texto OCR Torres Amat (sin LLM)."""

from __future__ import annotations

import re

# Líneas a descartar por completo
SKIP_LINE_RES = [
    re.compile(r"^CAPITULO\s+", re.I),
    re.compile(r"^[IVXLC]+\.\s*—\s*\d+\s*$"),
    re.compile(r"^\d{1,4}\s*$"),
    re.compile(r"^[A-ZÁÉÍÓÚÜÑ\. ]+\.\s*$"),
    re.compile(r"^ESTHER\.\s*$", re.I),
    re.compile(r"^TOBIAS\.\s*$", re.I),
    re.compile(r"^JUDIT\.\s*$", re.I),
]

FOOTNOTE_START = re.compile(
    r"^\d+\s+(Año|Antes|Véase|El texto|En los|En la|Nabuchodonosor|"
    r"Copia|Estas expresiones|Aaron|Tertul|San |Según|Num\.|Exod\.|Deuter\.|"
    r"Prov\.|Psalm|Job |Rom\.|Cor\.|Levit\.|Gen\.|Paral|Isai|Ezech|Jerem\.|"
    r"Judith|Sap\.|Cant\.|Mac\.|Oseas|Joel|Amos|Daniel|Esther|Christ|Josepho|"
    r"También|Mas no|Realmente|Probablemente|O sea|Es decir|De aquí|"
    r"Llámanse|Probable|Nota|En los códices|En la Vulgata|El espíritu)",
    re.I,
)

FOOTNOTE_INLINE = re.compile(
    r"(Reg\.|Paral\.|Exod\.|Deuter\.|Prov\.|Psalm\.|Job |cap\.| v\.| v,|"
    r"Antes cap\.|— Véase|—Véase|texto griego|Synopsi|Concilio|"
    r"El texto griego|Ya otra vez|Había hecho|Estas expresiones|"
    r"De la ignominia|cía de la salvación|jesuíta P\.|Según el griego)",
    re.I,
)

VERSE_WITH_DOT = re.compile(r"^(\d+)\.\s*(.*)$")
VERSE_SLASH = re.compile(r"^(\d+)\/\s*(.*)$")
VERSE_NO_DOT = re.compile(r"^(\d+)\s+([A-ZÁÉÍÓÚÜÑ\"'¿¡(].*)$")


def is_illustration_caption(line: str) -> bool:
    """Pies de grabado Doré: mayúsculas, descriptivos, sin numeración de versículo."""
    if re.match(r"^\d+\.", line):
        return False
    letters = [c for c in line if c.isalpha()]
    if len(letters) < 12:
        return False
    upper = sum(1 for c in letters if c.isupper())
    if upper / len(letters) < 0.82:
        return False
    if FOOTNOTE_START.match(line) or FOOTNOTE_INLINE.search(line):
        return False
    return len(line) < 140


def should_skip_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    for pat in SKIP_LINE_RES:
        if pat.match(stripped):
            return True
    if is_illustration_caption(stripped):
        return True
    return False


def is_footnote_line(line: str, last_verse: int | None) -> bool:
    stripped = line.strip()
    if re.match(r"^\d+\s+(Ya otra|Había hecho|El texto griego)", stripped, re.I):
        return True
    if FOOTNOTE_START.match(stripped):
        return True
    if FOOTNOTE_INLINE.search(stripped) and len(stripped) < 260:
        return True
    m = re.match(r"^(\d+)\s+(.*)$", stripped)
    if not m:
        return False
    num = int(m.group(1))
    body = m.group(2)
    if re.match(r"^(Deuter|Exod|Num|Gen|Prov|Paral|Antes|El texto|Ya otra|Había|Estas|De la|cía de)", body, re.I):
        return True
    if last_verse and num <= 12 and num != last_verse + 1:
        if len(body) < 180 and FOOTNOTE_INLINE.search(body):
            return True
        if len(body) < 160 and re.match(r"^(Año|Antes|El |En |Según|Mas |También|San )", body, re.I):
            return True
    return False


def fix_ocr_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^L\s+", "1. ", line)
    line = re.sub(r"^L\.\s*", "1. ", line)
    line = re.sub(r"^\. a-\s*", "1. ", line, flags=re.I)
    line = re.sub(r"^\.?\s*(\d+)\-\s*", r"\1. ", line)
    line = re.sub(r"^(\d+)\s*-\s*", r"\1. ", line)
    line = re.sub(r"^\.\s*(\d+)\-\s*", r"\1. ", line)
    return line


def normalize_spaces(text: str) -> str:
    text = text.replace("¬", "")
    text = text.replace("\u00ad", "")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([,.;:])\s*", r"\1 ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_verse_text(text: str) -> str:
    text = normalize_spaces(text)
    text = re.sub(r"[\^~#|\\<>]", "", text)
    text = re.sub(r"\s+\d+\s*2:\s*$", "", text)
    text = re.sub(r"\s+\d+\s+\d+:\s*$", "", text)
    text = re.sub(r"\s+\d+\s*$", "", text)  # nota volada suelta al final
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_verse_start(line: str) -> tuple[int, str] | None:
    for pat in (VERSE_WITH_DOT, VERSE_SLASH, VERSE_NO_DOT):
        m = pat.match(line.strip())
        if m:
            return int(m.group(1)), m.group(2).strip()
    return None


def strip_chapter_header(lines: list[str]) -> list[str]:
    """Elimina título/sumario del capítulo antes del versículo 1."""
    for i, line in enumerate(lines):
        start = parse_verse_start(fix_ocr_line(line.strip()))
        if start and start[0] == 1:
            return lines[i:]
    return lines


def split_multi_verse_line(line: str) -> list[str]:
    """Parte líneas OCR con dos versículos pegados (ej. '1. Foo 2. Bar')."""
    parts = re.split(r"\s+(?=\d+\.\s)", line)
    if len(parts) <= 1:
        parts = re.split(r"(?<=\s)(?<=[^0-9])(?=\d+\.\s)", line)
    return [p.strip() for p in parts if p.strip()]


def remove_late_footnote_verses(versiculos: list[dict], notas: list[str]) -> list[dict]:
    if not versiculos:
        return versiculos
    max_n = max(v["versiculo"] for v in versiculos)
    kept: list[dict] = []
    for v in versiculos:
        if v["versiculo"] < max_n and (
            FOOTNOTE_INLINE.search(v["texto"]) or len(v["texto"]) < 100
        ):
            if FOOTNOTE_INLINE.search(v["texto"]) or re.match(
                r"^(Ya otra|Había|El texto|Estas|De la|cía de|Según)", v["texto"], re.I
            ):
                notas.append(v["texto"])
                continue
        kept.append(v)
    return kept


def strip_trailing_footnote_verses(versiculos: list[dict]) -> list[dict]:
    while versiculos:
        texto = versiculos[-1]["texto"]
        if len(texto) < 150 and FOOTNOTE_INLINE.search(texto):
            versiculos.pop()
            continue
        if re.match(
            r"^(El texto|Ya otra|Había hecho|Estas expresiones|De la ignominia|"
            r"cía de la|Según el griego|\. Finalmente cumplidos)",
            texto,
            re.I,
        ):
            versiculos.pop()
            continue
        break
    return versiculos


def parse_capitulo_fragmento(fragmento: str) -> tuple[list[dict], str | None]:
    raw_lines = fragmento.splitlines()
    lines = [ln.rstrip() for ln in raw_lines if ln.strip()]
    lines = strip_chapter_header(lines)

    versiculos: list[dict] = []
    notas: list[str] = []
    current_num: int | None = None
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_num, current_parts
        if current_num is None:
            return
        texto = clean_verse_text(" ".join(current_parts))
        if texto:
            versiculos.append({"versiculo": current_num, "texto": texto, "notas": None})
        current_num = None
        current_parts = []

    i = 0
    while i < len(lines):
        line = fix_ocr_line(lines[i].strip())
        i += 1
        if should_skip_line(line):
            continue
        for subline in split_multi_verse_line(line):
            if should_skip_line(subline):
                continue
            if is_footnote_line(subline, current_num):
                notas.append(normalize_spaces(subline))
                continue

            start = parse_verse_start(subline)
            if start:
                num, text = start
                flush()
                current_num = num
                current_parts = [text] if text else []
                continue

            if current_num is not None:
                if subline.endswith("¬") or subline.endswith("-"):
                    current_parts.append(subline.rstrip("-¬"))
                else:
                    current_parts.append(subline)

    flush()
    versiculos = remove_late_footnote_verses(versiculos, notas)
    versiculos = strip_trailing_footnote_verses(versiculos)
    notas_text = "\n".join(notas).strip() if notas else None
    if notas_text and versiculos:
        versiculos[0]["notas"] = notas_text
    return versiculos, notas_text


def validar_capitulo(versiculos: list[dict], capitulo: int) -> list[str]:
    warnings: list[str] = []
    if not versiculos:
        warnings.append(f"cap {capitulo}: sin versículos")
        return warnings
    nums = [v["versiculo"] for v in versiculos]
    if nums[0] != 1:
        warnings.append(f"cap {capitulo}: no empieza en v.1 (empieza en {nums[0]})")
    gaps = []
    for a, b in zip(nums, nums[1:]):
        if b <= a:
            warnings.append(f"cap {capitulo}: numeración no creciente {a}→{b}")
        elif b - a > 1:
            gaps.extend(range(a + 1, b))
    if gaps:
        warnings.append(f"cap {capitulo}: saltos {gaps[:8]}{'...' if len(gaps)>8 else ''}")
    return warnings
