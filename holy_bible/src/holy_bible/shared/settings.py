"""Configuración central del proyecto."""

from pathlib import Path

# src/holy_bible/shared/settings.py -> repo root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# --- Scraper ---
BASE_URL = "https://www.bibliatodo.com/la-biblia/Torres-amat"
VERSION_SLUG = "Torres-amat"
USER_AGENT = "BibliaScraper/1.0 (RAG research)"

REQUEST_DELAY = (1.0, 2.0)
BOOK_DELAY = (2.0, 5.0)
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
MAX_BOOK_ATTEMPTS = 3

VERSICULOS_POR_CHUNK = 4
OVERLAP = 1

OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

LIBROS = [
    {"slug": "genesis", "nombre": "Génesis", "testamento": "AT"},
    {"slug": "exodo", "nombre": "Éxodo", "testamento": "AT"},
    {"slug": "levitico", "nombre": "Levítico", "testamento": "AT"},
    {"slug": "numeros", "nombre": "Números", "testamento": "AT"},
    {"slug": "deuteronomio", "nombre": "Deuteronomio", "testamento": "AT"},
    {"slug": "josue", "nombre": "Josué", "testamento": "AT"},
    {"slug": "jueces", "nombre": "Jueces", "testamento": "AT"},
    {"slug": "rut", "nombre": "Rut", "testamento": "AT"},
    {"slug": "1samuel", "nombre": "1 Samuel", "testamento": "AT"},
    {"slug": "2samuel", "nombre": "2 Samuel", "testamento": "AT"},
    {"slug": "1reyes", "nombre": "1 Reyes", "testamento": "AT"},
    {"slug": "2reyes", "nombre": "2 Reyes", "testamento": "AT"},
    {"slug": "1cronicas", "nombre": "1 Crónicas", "testamento": "AT"},
    {"slug": "2cronicas", "nombre": "2 Crónicas", "testamento": "AT"},
    {"slug": "esdras", "nombre": "Esdras", "testamento": "AT"},
    {"slug": "nehemias", "nombre": "Nehemías", "testamento": "AT"},
    {"slug": "ester", "nombre": "Ester", "testamento": "AT"},
    {"slug": "job", "nombre": "Job", "testamento": "AT"},
    {"slug": "salmos", "nombre": "Salmos", "testamento": "AT"},
    {"slug": "proverbios", "nombre": "Proverbios", "testamento": "AT"},
    {"slug": "eclesiastes", "nombre": "Eclesiastés", "testamento": "AT"},
    {"slug": "cantares", "nombre": "Cantares", "testamento": "AT"},
    {"slug": "isaias", "nombre": "Isaías", "testamento": "AT"},
    {"slug": "jeremias", "nombre": "Jeremías", "testamento": "AT"},
    {"slug": "lamentaciones", "nombre": "Lamentaciones", "testamento": "AT"},
    {"slug": "ezequiel", "nombre": "Ezequiel", "testamento": "AT"},
    {"slug": "daniel", "nombre": "Daniel", "testamento": "AT"},
    {"slug": "oseas", "nombre": "Oseas", "testamento": "AT"},
    {"slug": "joel", "nombre": "Joel", "testamento": "AT"},
    {"slug": "amos", "nombre": "Amós", "testamento": "AT"},
    {"slug": "abdias", "nombre": "Abdías", "testamento": "AT"},
    {"slug": "jonas", "nombre": "Jonás", "testamento": "AT"},
    {"slug": "miqueas", "nombre": "Miqueas", "testamento": "AT"},
    {"slug": "nahum", "nombre": "Nahúm", "testamento": "AT"},
    {"slug": "habacuc", "nombre": "Habacuc", "testamento": "AT"},
    {"slug": "sofonias", "nombre": "Sofonías", "testamento": "AT"},
    {"slug": "hageo", "nombre": "Hageo", "testamento": "AT"},
    {"slug": "zacarias", "nombre": "Zacarías", "testamento": "AT"},
    {"slug": "malaquias", "nombre": "Malaquías", "testamento": "AT"},
    {"slug": "mateo", "nombre": "Mateo", "testamento": "NT"},
    {"slug": "marcos", "nombre": "Marcos", "testamento": "NT"},
    {"slug": "lucas", "nombre": "Lucas", "testamento": "NT"},
    {"slug": "juan", "nombre": "Juan", "testamento": "NT"},
    {"slug": "hechos", "nombre": "Hechos", "testamento": "NT"},
    {"slug": "romanos", "nombre": "Romanos", "testamento": "NT"},
    {"slug": "1corintios", "nombre": "1 Corintios", "testamento": "NT"},
    {"slug": "2corintios", "nombre": "2 Corintios", "testamento": "NT"},
    {"slug": "galatas", "nombre": "Gálatas", "testamento": "NT"},
    {"slug": "efesios", "nombre": "Efesios", "testamento": "NT"},
    {"slug": "filipenses", "nombre": "Filipenses", "testamento": "NT"},
    {"slug": "colosenses", "nombre": "Colosenses", "testamento": "NT"},
    {"slug": "1tesalonicenses", "nombre": "1 Tesalonicenses", "testamento": "NT"},
    {"slug": "2tesalonicenses", "nombre": "2 Tesalonicenses", "testamento": "NT"},
    {"slug": "1timoteo", "nombre": "1 Timoteo", "testamento": "NT"},
    {"slug": "2timoteo", "nombre": "2 Timoteo", "testamento": "NT"},
    {"slug": "tito", "nombre": "Tito", "testamento": "NT"},
    {"slug": "filemon", "nombre": "Filemón", "testamento": "NT"},
    {"slug": "hebreos", "nombre": "Hebreos", "testamento": "NT"},
    {"slug": "santiago", "nombre": "Santiago", "testamento": "NT"},
    {"slug": "1pedro", "nombre": "1 Pedro", "testamento": "NT"},
    {"slug": "2pedro", "nombre": "2 Pedro", "testamento": "NT"},
    {"slug": "1juan", "nombre": "1 Juan", "testamento": "NT"},
    {"slug": "2juan", "nombre": "2 Juan", "testamento": "NT"},
    {"slug": "3juan", "nombre": "3 Juan", "testamento": "NT"},
    {"slug": "judas", "nombre": "Judas", "testamento": "NT"},
    {"slug": "apocalipsis", "nombre": "Apocalipsis", "testamento": "NT"},
]

LIBROS_POR_SLUG = {libro["slug"]: libro for libro in LIBROS}

DEUTEROCANONICOS_FALTANTES = [
    {"slug": "tobias", "nombre": "Tobías"},
    {"slug": "judit", "nombre": "Judit"},
    {"slug": "sabiduria", "nombre": "Sabiduría"},
    {"slug": "eclesiastico", "nombre": "Eclesiástico (Sirácide)"},
    {"slug": "baruc", "nombre": "Baruc"},
    {"slug": "1macabeos", "nombre": "1 Macabeos"},
    {"slug": "2macabeos", "nombre": "2 Macabeos"},
]

CAPITULO_VACIO_PATTERN = r"no posee informaci[oó]n"
CLOUDFLARE_CHALLENGE_MARKER = "Just a moment"

# --- RAG / API ---
CHROMA_DIR = PROJECT_ROOT / "chroma_biblia"
COLLECTION_NAME = "biblia_torres_amat"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_N_RESULTS = 5
MAX_N_RESULTS = 20
RRF_K = 60
RETRIEVAL_POOL_SIZE = 20
CHROMA_BATCH_SIZE = 500
EMBEDDING_BATCH_SIZE = 32

SYSTEM_PROMPT = """\
Sos un asistente que responde preguntas sobre la Biblia católica usando EXCLUSIVAMENTE \
los pasajes bíblicos que se te proporcionan como contexto. No agregues interpretación \
teológica, doctrina, ni conocimiento externo que no esté sustentado en el texto proporcionado.

Reglas:
- Citá siempre el libro, capítulo y versículo de cada pasaje que uses en tu respuesta.
- Si los pasajes proporcionados no contienen información suficiente para responder la \
pregunta, decilo explícitamente en vez de inventar una respuesta.
- Mantené un tono respetuoso y claro.
- Cuando te refieras a las Escrituras, decí siempre "Biblia Católica" (nunca solo "Biblia").
- No cites textualmente pasajes completos más allá de lo necesario; podés parafrasear \
el contenido citando la referencia.\
"""
