#!/usr/bin/env python3
"""Consulta de prueba sobre la colección Chroma."""

from __future__ import annotations

import argparse

import chromadb
from sentence_transformers import SentenceTransformer

from holy_bible.shared.settings import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)

DEFAULT_QUERY = "la compasión de Dios hacia los pecadores"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta semántica sobre la Biblia Torres Amat"
    )
    parser.add_argument("consulta", nargs="?", default=DEFAULT_QUERY)
    parser.add_argument("-n", "--num-resultados", type=int, default=5)
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    coleccion = client.get_collection(name=COLLECTION_NAME)
    modelo = SentenceTransformer(EMBEDDING_MODEL)

    query_embedding = modelo.encode(
        [f"query: {args.consulta}"],
        show_progress_bar=False,
    )

    resultados = coleccion.query(
        query_embeddings=query_embedding.tolist(),
        n_results=args.num_resultados,
    )

    for doc, meta in zip(resultados["documents"][0], resultados["metadatas"][0]):
        print(
            f"{meta['libro']} {meta['capitulo']}:"
            f"{meta['versiculo_inicio']}-{meta['versiculo_fin']} — {doc}"
        )


if __name__ == "__main__":
    main()
