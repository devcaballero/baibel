# Biblia Scraper — Torres Amat RAG

Pipeline para scrapear, indexar y consultar la **Biblia Torres Amat** (canon católico, 73 libros) con búsqueda semántica (Chroma + E5) y respuestas generadas por Claude, basadas exclusivamente en los pasajes recuperados.

El repositorio tiene **dos bounded contexts** claramente separados:

| Contexto | Qué hace | Cuándo se corre |
|----------|----------|-----------------|
| **ETL** | Scrapea, genera chunks, carga Chroma | Ocasional (batch) |
| **RAG** | Expone API REST de consulta | Continuo (servicio) |

Comparten datos (`chroma_biblia/`, metadata) y config (`shared/settings.py`), pero no runtime.

## Qué incluye

### ETL (offline)

- Scraper de [bibliatodo.com](https://www.bibliatodo.com/la-biblia/Torres-amat) (Playwright)
- Libros deuterocanónicos desde OCR (Archive.org: Doré y 1874)
- Chunking con overlap → `output/biblia_chunks.jsonl`
- Indexación vectorial en Chroma (`intfloat/multilingual-e5-large`, prefijos E5)

### RAG (online)

- API REST FastAPI con `/health` y `/query`
- Búsqueda semántica + generación con Claude (`claude-haiku-4-5-20251001`)
- Respuestas basadas solo en pasajes recuperados, con citas

## Requisitos

- Python 3.11+
- `ANTHROPIC_API_KEY` en `.env` (solo para la API RAG)
- ~2 GB de disco para el modelo de embeddings (primer uso)

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium   # solo para ETL (scraping)
```

Creá un `.env` en la raíz:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

---

## ETL — Cómo construir el índice

```bash
# 1. Scrapear libros protocanónicos
python scraper.py

# 2. (Opcional) Deuterocanónicos
python finalize_deuterocanonico.py

# 3. Generar chunks
python chunker.py
# → output/biblia_chunks.jsonl  (~11.850 chunks)

# 4. Cargar embeddings en Chroma (~8 min)
python cargar_chroma.py
# → chroma_biblia/
```

Consulta de prueba en terminal (sin API):

```bash
python consultar.py "la compasión de Dios hacia los pecadores"
```

---

## RAG — Cómo servir consultas

```bash
uvicorn holy_bible.rag.api.app:app --reload --port 8000
# shim de compatibilidad:
# uvicorn api.main:app --reload --port 8000
```

Documentación interactiva: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### `GET /health`

```json
{
  "status": "ok",
  "indexed_chunks": 11852
}
```

### `POST /query`

**Request:**

```json
{
  "question": "¿Qué dice la Biblia sobre el perdón?",
  "num_results": 5,
  "testament": "NT",
  "book": "Mateo"
}
```

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `question` | string | sí | Pregunta del usuario |
| `num_results` | int | no | Chunks a recuperar (default 5, max 20) |
| `testament` | `"AT"` \| `"NT"` | no | Filtrar por testamento |
| `book` | string | no | Nombre exacto del libro (ej. `"Eclesiástico"`) |

**Response:**

```json
{
  "answer": "…",
  "citations": [
    {
      "book": "Mateo",
      "chapter": 18,
      "verse_start": 21,
      "verse_end": 22,
      "text": "…",
      "source": "bibliatodo"
    }
  ]
}
```

**Códigos de error:**

| Código | Cuándo |
|--------|--------|
| 400 | `question` vacía o solo espacios |
| 422 | Body ausente o sin campo `question` |
| 502 | Error de la API de Anthropic |
| 503 | Chroma no disponible |

---

## Arquitectura

```
src/holy_bible/
├── shared/                  # Config compartida (settings.py)
├── etl/                     # Bounded context: construir el índice
│   ├── chunking.py
│   ├── indexing.py
│   ├── infrastructure/
│   │   ├── scraping/        # parser, state_manager
│   │   └── deuterocanonico/
│   └── cli/                 # scraper, chunker, cargar_chroma, explorar
└── rag/                     # Bounded context: consultar el índice
    ├── domain/              # BiblicalChunk, excepciones
    ├── application/         # RagService
    ├── infrastructure/      # Chroma, Anthropic, E5
    ├── api/                 # FastAPI (app, schemas)
    └── cli/                 # consultar (debug)
```

Flujo de dependencias:

```
ETL:  cli → etl → shared
RAG:  api → application → domain
              ↓
       infrastructure → shared
```

Los scripts en la raíz (`chunker.py`, `scraper.py`, `api/main.py`, etc.) son **shims de compatibilidad**.

## Datos y metadata

Cada chunk en Chroma tiene:

| Campo | Ejemplo |
|-------|---------|
| `libro` | `"Génesis"` |
| `testamento` | `"AT"` |
| `capitulo` | `1` |
| `versiculo_inicio` / `versiculo_fin` | `1` / `4` |
| `fuente` | `"bibliatodo"`, `"doré"`, `"1874"` |

## Tests

```bash
python tests/test_api.py
```

## Estructura del repositorio

```
holy_bible/
├── src/holy_bible/
│   ├── shared/              # settings.py
│   ├── etl/                 # pipeline offline
│   └── rag/                 # API online
├── tests/
├── output/                  # JSON + biblia_chunks.jsonl
├── chroma_biblia/           # índice vectorial
├── logs/
├── chunker.py               # shims → etl.cli.*
├── api/main.py              # shim → rag.api.app
├── pyproject.toml
└── requirements.txt
```

## Configuración

Todo en `src/holy_bible/shared/settings.py`. El `config.py` de la raíz re-exporta esos valores por compatibilidad.
