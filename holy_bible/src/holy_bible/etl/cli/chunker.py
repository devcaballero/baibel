#!/usr/bin/env python3
"""Entry point: generar biblia_chunks.jsonl."""

from holy_bible.etl.chunking import CHUNKS_FILE, generar_chunks


def main() -> None:
    count = generar_chunks()
    print(f"Generados {count} chunks en {CHUNKS_FILE}")


if __name__ == "__main__":
    main()
