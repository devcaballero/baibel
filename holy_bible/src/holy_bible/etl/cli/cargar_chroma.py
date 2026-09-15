#!/usr/bin/env python3
"""Entry point: cargar chunks en ChromaDB."""

from holy_bible.etl.indexing import load_chunks_into_chroma


def main() -> None:
    count = load_chunks_into_chroma()
    print(f"Cargados {count} chunks en Chroma")


if __name__ == "__main__":
    main()
