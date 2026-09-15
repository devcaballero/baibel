# Baibel

Frontend SPA (Vite + React) para consultar la Biblia Católica vía la API RAG del proyecto [`holy_bible`](../holy_bible).

## Requisitos

- Node.js 18+
- API RAG corriendo en `http://localhost:8000`

## Instalación

```bash
cd holy_bible-web
npm install
cp .env.example .env   # opcional si ya existe .env
```

## Desarrollo

Terminal 1 — API:

```bash
cd ../holy_bible
source .venv/bin/activate
uvicorn holy_bible.rag.api.app:app --reload --port 8000
```

Terminal 2 — front:

```bash
npm run dev
```

Abrí [http://localhost:5173](http://localhost:5173).

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | URL base de la API RAG |

## Estructura

```
src/
├── api/           # cliente /query y /health
├── components/    # SearchForm, AnswerCard, CitationList, ShareMenu…
├── pages/         # HomePage
└── utils/         # compartir, formato de citas
```

## v1

- Formulario de consulta → `POST /query`
- Vista de respuesta y citas (estilo mockup)
- Compartir (copiar, WhatsApp, X, Facebook)
- Health check al cargar

## Próxima versión

- Filtros por testamento y libro

## Build

```bash
npm run build
npm run preview
```
