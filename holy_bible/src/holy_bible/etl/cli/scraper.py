#!/usr/bin/env python3
"""Scraper principal: descarga Biblia Torres Amat desde bibliatodo.com."""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from holy_bible.etl.chunking import generar_chunks
from holy_bible.etl.infrastructure.scraping.parser import es_capitulo_vacio, parse_capitulo
from holy_bible.etl.infrastructure.scraping.state_manager import StateManager
from holy_bible.shared.settings import (
    BASE_URL,
    BOOK_DELAY,
    CLOUDFLARE_CHALLENGE_MARKER,
    DEUTEROCANONICOS_FALTANTES,
    LIBROS,
    LIBROS_POR_SLUG,
    LOGS_DIR,
    MAX_BOOK_ATTEMPTS,
    MAX_RETRIES,
    OUTPUT_DIR,
    REQUEST_DELAY,
    REQUEST_TIMEOUT,
    USER_AGENT,
)

LOG_FILE = LOGS_DIR / "scraping.log"
LIBROS_CAPITULOS_FILE = LOGS_DIR / "libros_capitulos.json"
REPORTE_FILE = LOGS_DIR / "reporte_validacion.json"
BIBLIA_COMPLETA_FILE = OUTPUT_DIR / "biblia_completa.json"

logger = logging.getLogger("holy_bible")


def setup_logging() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


class BibliaFetcher:
    """Cliente Playwright reutilizable para fetch de páginas."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def __enter__(self) -> BibliaFetcher:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._context = self._browser.new_context(user_agent=USER_AGENT)
        self._page = self._context.new_page()
        return self

    def __exit__(self, *args: object) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def fetch(self, url: str) -> str:
        assert self._page is not None
        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._page.goto(
                    url,
                    timeout=REQUEST_TIMEOUT * 1000,
                    wait_until="domcontentloaded",
                )
                status = response.status if response else 0

                if status in (429, 500, 503):
                    raise RuntimeError(f"HTTP {status} en {url}")

                try:
                    self._page.wait_for_selector(
                        "#info_capitulo, body",
                        timeout=REQUEST_TIMEOUT * 1000,
                    )
                except Exception:
                    pass

                html = self._page.content()

                if CLOUDFLARE_CHALLENGE_MARKER in html:
                    raise RuntimeError("Challenge Cloudflare detectado")

                return html

            except Exception as exc:
                last_error = exc
                wait = 2 ** attempt
                logger.warning(
                    "Intento %d/%d falló para %s: %s. Reintento en %ds",
                    attempt,
                    MAX_RETRIES,
                    url,
                    exc,
                    wait,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(wait)

        raise RuntimeError(f"No se pudo obtener {url}: {last_error}")


def delay_entre_requests() -> None:
    time.sleep(random.uniform(*REQUEST_DELAY))


def delay_entre_libros() -> None:
    delay = random.uniform(*BOOK_DELAY)
    logger.info("Pausa entre libros: %.1fs", delay)
    time.sleep(delay)


def libro_output_path(slug: str) -> Path:
    return OUTPUT_DIR / f"{slug}.json"


def libro_ya_scrapeado(slug: str) -> bool:
    path = libro_output_path(slug)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return bool(data.get("capitulos"))
    except (json.JSONDecodeError, OSError):
        return False


def cargar_libros_capitulos() -> dict[str, int]:
    if LIBROS_CAPITULOS_FILE.exists():
        try:
            return json.loads(LIBROS_CAPITULOS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def guardar_libros_capitulos(data: dict[str, int]) -> None:
    LIBROS_CAPITULOS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def scrape_libro(
    fetcher: BibliaFetcher,
    libro: dict[str, str],
    force: bool,
    stats: dict[str, Any],
) -> dict[str, Any] | None:
    slug = libro["slug"]
    nombre = libro["nombre"]
    testamento = libro["testamento"]

    if not force and libro_ya_scrapeado(slug):
        logger.info("Omitiendo %s (ya existe en output/)", slug)
        existing = json.loads(libro_output_path(slug).read_text(encoding="utf-8"))
        stats["libros_scrapeados"] += 1
        stats["total_capitulos"] += len(existing.get("capitulos", []))
        for cap in existing.get("capitulos", []):
            stats["total_versiculos"] += len(cap.get("versiculos", []))
        return existing

    logger.info("Iniciando libro: %s (%s)", nombre, slug)
    capitulos: list[dict[str, Any]] = []
    capitulo_num = 1

    while True:
        url = f"{BASE_URL}/{slug}-{capitulo_num}"
        logger.info("  Procesando %s capítulo %d — %s", nombre, capitulo_num, url)

        delay_entre_requests()
        html = fetcher.fetch(url)

        if es_capitulo_vacio(html):
            logger.info("  Fin de %s en capítulo %d (sin contenido)", nombre, capitulo_num)
            break

        versiculos, warnings = parse_capitulo(html)
        for w in warnings:
            logger.warning("  %s cap %d: %s", nombre, capitulo_num, w)
            stats["warnings_parsing"].append(
                {"libro": nombre, "capitulo": capitulo_num, "warning": w}
            )

        if not versiculos:
            logger.warning(
                "  %s cap %d: sin versículos parseables — posible error",
                nombre,
                capitulo_num,
            )
            stats["capitulos_vacios"].append(
                {"libro": nombre, "slug": slug, "capitulo": capitulo_num}
            )
            break

        capitulos.append({"capitulo": capitulo_num, "versiculos": versiculos})
        stats["total_versiculos"] += len(versiculos)
        capitulo_num += 1

    if not capitulos:
        logger.error("No se obtuvo ningún capítulo para %s", nombre)
        return None

    libro_data = {
        "libro": nombre,
        "libro_slug": slug,
        "testamento": testamento,
        "capitulos": capitulos,
    }

    libro_output_path(slug).write_text(
        json.dumps(libro_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "Guardado %s — %d capítulos, %d versículos",
        slug,
        len(capitulos),
        sum(len(c["versiculos"]) for c in capitulos),
    )

    libros_capitulos = cargar_libros_capitulos()
    libros_capitulos[slug] = len(capitulos)
    guardar_libros_capitulos(libros_capitulos)

    stats["libros_scrapeados"] += 1
    stats["total_capitulos"] += len(capitulos)
    return libro_data


def cargar_todos_los_libros() -> list[dict[str, Any]] | None:
    """Carga los 66 JSON por libro si todos existen."""
    libros_data: list[dict[str, Any]] = []
    for libro in LIBROS:
        path = libro_output_path(libro["slug"])
        if not path.exists():
            return None
        try:
            libros_data.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            return None
    return libros_data


def consolidar_biblia(libros_data: list[dict[str, Any]]) -> None:
    biblia = {"libros": libros_data}
    BIBLIA_COMPLETA_FILE.write_text(
        json.dumps(biblia, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Consolidado en %s (%d libros)", BIBLIA_COMPLETA_FILE, len(libros_data))


def generar_reporte(stats: dict[str, Any]) -> None:
    reporte = {
        "libros_scrapeados": stats["libros_scrapeados"],
        "total_capitulos": stats["total_capitulos"],
        "total_versiculos": stats["total_versiculos"],
        "capitulos_vacios": stats["capitulos_vacios"],
        "warnings_parsing": stats["warnings_parsing"],
        "deuterocanonicos_faltantes": DEUTEROCANONICOS_FALTANTES,
    }
    REPORTE_FILE.write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Reporte de validación: %s", REPORTE_FILE)


def run_orchestrator(
    state: StateManager,
    slugs: list[str] | None,
    force: bool,
    stats: dict[str, Any],
) -> None:
    """Procesa libros secuencialmente según state.json."""
    if force and slugs:
        for slug in slugs:
            state.reset_book(slug)
    elif force:
        for libro in LIBROS:
            state.reset_book(libro["slug"])

    pending = state.get_books_to_process(
        max_attempts=MAX_BOOK_ATTEMPTS,
        slugs=slugs,
    )

    if not pending:
        summary = state.summary()
        logger.info(
            "No hay libros pendientes. Estado: %s",
            summary,
        )
        return

    init_summary = state.summary()
    logger.info(
        "Libros a procesar: %d (pending=%d, failed=%d)",
        len(pending),
        init_summary.get("pending", 0),
        init_summary.get("failed", 0),
    )

    with BibliaFetcher() as fetcher:
        for index, entry in enumerate(pending):
            slug = entry["id"]
            libro = LIBROS_POR_SLUG[slug]

            state.mark_processing(slug)
            logger.info(
                "=== [%d/%d] %s (%s) — intento %d ===",
                index + 1,
                len(pending),
                libro["nombre"],
                slug,
                entry["attempts"] + 1,
            )

            try:
                result = scrape_libro(fetcher, libro, force, stats)
                if result is None:
                    raise RuntimeError(
                        f"No se obtuvo ningún capítulo para {libro['nombre']}"
                    )
                state.mark_completed(slug)
                logger.info("Libro completado: %s", slug)
            except Exception as exc:
                error_msg = f"{type(exc).__name__}: {exc}"
                logger.error("Error en %s: %s", slug, error_msg)
                state.mark_failed(slug, error_msg)

            if index < len(pending) - 1:
                delay_entre_libros()


def main() -> None:
    parser = argparse.ArgumentParser(description="Scraper Biblia Torres Amat")
    parser.add_argument(
        "--libro",
        action="append",
        dest="libros",
        help="Slug del libro a scrapear (puede repetirse). Default: todos pendientes.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-scrapear aunque el JSON del libro ya exista.",
    )
    parser.add_argument(
        "--skip-chunks",
        action="store_true",
        help="No generar biblia_chunks.jsonl al finalizar.",
    )
    args = parser.parse_args()

    setup_logging()

    if args.libros:
        for slug in args.libros:
            if slug not in LIBROS_POR_SLUG:
                logger.error("Libro desconocido: %s", slug)
                sys.exit(1)

    state = StateManager.load_or_create()
    summary = state.summary()
    logger.info(
        "Estado inicial — completed: %d, pending: %d, failed: %d, processing: %d",
        summary.get("completed", 0),
        summary.get("pending", 0),
        summary.get("failed", 0),
        summary.get("processing", 0),
    )

    stats: dict[str, Any] = {
        "libros_scrapeados": 0,
        "total_capitulos": 0,
        "total_versiculos": 0,
        "capitulos_vacios": [],
        "warnings_parsing": [],
    }

    run_orchestrator(state, args.libros, args.force, stats)

    all_data = cargar_todos_los_libros()
    if all_data:
        consolidar_biblia(all_data)
        if not args.skip_chunks:
            count = generar_chunks()
            logger.info("Generados %d chunks en output/biblia_chunks.jsonl", count)

    generar_reporte(stats)
    final_summary = state.summary()
    logger.info(
        "Finalizado — completed: %d, pending: %d, failed: %d | "
        "Esta sesión: %d capítulos, %d versículos scrapeados",
        final_summary.get("completed", 0),
        final_summary.get("pending", 0),
        final_summary.get("failed", 0),
        stats["total_capitulos"],
        stats["total_versiculos"],
    )


if __name__ == "__main__":
    main()
