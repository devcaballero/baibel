class ChromaUnavailableError(Exception):
    """Chroma no está disponible (directorio ausente o colección inexistente)."""


class RagSearchError(Exception):
    """Error al buscar contexto en Chroma."""


class RagGenerationError(Exception):
    """Error al generar respuesta con el modelo de lenguaje."""
