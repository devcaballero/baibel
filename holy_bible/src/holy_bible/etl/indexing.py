from __future__ import annotations

import json

import chromadb
from sentence_transformers import SentenceTransformer

from holy_bible.etl.chunking import CHUNKS_FILE
from holy_bible.shared.settings import (
    CHROMA_BATCH_SIZE,
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL,
)


def load_chunks_into_chroma() -> int:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    model = SentenceTransformer(EMBEDDING_MODEL)

    with CHUNKS_FILE.open("r", encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]

    texts = [f"passage: {chunk['texto']}" for chunk in chunks]
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        batch_size=EMBEDDING_BATCH_SIZE,
    )

    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["texto"] for chunk in chunks]
    metadatas = [
        {
            "libro": chunk["libro"],
            "testamento": chunk["testamento"],
            "capitulo": chunk["capitulo"],
            "versiculo_inicio": chunk["versiculo_inicio"],
            "versiculo_fin": chunk["versiculo_fin"],
            "fuente": chunk.get("fuente", "bibliatodo"),
        }
        for chunk in chunks
    ]

    for start in range(0, len(chunks), CHROMA_BATCH_SIZE):
        end = start + CHROMA_BATCH_SIZE
        collection.add(
            ids=ids[start:end],
            embeddings=embeddings[start:end].tolist(),
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

    return len(chunks)
