#!/usr/bin/env python3
"""Script exploratorio: inspecciona HTML de Génesis 1 y valida selectores."""

import sys

from playwright.sync_api import sync_playwright

from holy_bible.shared.settings import BASE_URL, REQUEST_TIMEOUT, USER_AGENT
from holy_bible.etl.infrastructure.scraping.parser import (
    SELECTOR_CONTENEDOR,
    SELECTOR_NUMERO,
    SELECTOR_TEXTO,
    SELECTOR_VERSICULOS,
    parse_capitulo,
    obtener_html_contenedor,
)

URL = f"{BASE_URL}/genesis-1"


def main() -> None:
    print(f"Descargando: {URL}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        page.goto(URL, timeout=REQUEST_TIMEOUT * 1000, wait_until="domcontentloaded")
        page.wait_for_selector(SELECTOR_VERSICULOS, timeout=REQUEST_TIMEOUT * 1000)
        html = page.content()
        browser.close()

    contenedor_html = obtener_html_contenedor(html)
    if not contenedor_html:
        print(f"ERROR: No se encontró el contenedor {SELECTOR_CONTENEDOR}")
        sys.exit(1)

    print("=" * 80)
    print(f"HTML CRUDO — contenedor {SELECTOR_CONTENEDOR}")
    print("=" * 80)
    print(contenedor_html[:3000])
    if len(contenedor_html) > 3000:
        print(f"\n... (truncado, total {len(contenedor_html)} chars)")

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    verse_elements = soup.select(SELECTOR_VERSICULOS)

    print("\n" + "=" * 80)
    print("PRIMEROS 3 ELEMENTOS p.bt-verse (outerHTML)")
    print("=" * 80)
    for i, el in enumerate(verse_elements[:3], 1):
        print(f"\n--- Versículo elemento #{i} ---")
        print(str(el))

    versiculos, warnings = parse_capitulo(html)

    print("\n" + "=" * 80)
    print("TABLA DE VERSÍCULOS PARSEADOS")
    print("=" * 80)
    print(f"{'versiculo':>10} | {'texto (primeros 80 chars)'}")
    print("-" * 95)
    for v in versiculos:
        texto_preview = v["texto"][:80]
        if len(v["texto"]) > 80:
            texto_preview += "..."
        print(f"{v['versiculo']:>10} | {texto_preview}")

    print("\n" + "=" * 80)
    print("RESUMEN DE SELECTORES")
    print("=" * 80)
    print(f"  Contenedor:  {SELECTOR_CONTENEDOR}")
    print(f"  Versículos:  {SELECTOR_VERSICULOS}")
    print(f"  Número:      {SELECTOR_VERSICULOS} > {SELECTOR_NUMERO}  → int(text.strip())")
    print(f"  Texto:       {SELECTOR_VERSICULOS} > {SELECTOR_TEXTO}  → get_text(strip=True)")
    print(f"\n  Total versículos detectados: {len(versiculos)}")

    if warnings:
        print("\n  Advertencias:")
        for w in warnings:
            print(f"    - {w}")


if __name__ == "__main__":
    main()
