# Mejoras realizadas en Baibel

Resumen del trabajo de retrieval, filtros y evaluación sobre el backend RAG de Baibel (`holy_bible/`) y el frontend (`holy_bible-web/`). Repo: `devcaballero/baibel`.

Estas mejoras quedaron en `main` en la última iteración (hasta `26975b6`).

---

## 1. Filtros de Testamento y Libro

**Problema**: la API ya soportaba filtrar por testamento (`AT`/`NT`) y libro, pero el frontend no exponía esa capacidad — el usuario no podía acotar su búsqueda.

**Cambios**:
- `holy_bible-web/src/data/books.js` (nuevo): listado completo de los 73 libros del canon católico, con testamento asociado.
- `holy_bible-web/src/api/client.js`: `queryBible` acepta `testament`/`book` opcionales; solo se incluyen en el body del POST si están definidos (evita mandar filtros vacíos al backend).
- `holy_bible-web/src/components/SearchForm.jsx`: selects de Testamento y Libro, con el segundo filtrado dinámicamente según el primero.
- `holy_bible-web/src/pages/HomePage.jsx`: estado de filtros, no se resetea entre búsquedas.

**Verificación manual**: NT + Juan → el body del POST incluyó `{"testament":"NT","book":"Juan"}` correctamente. Selects se deshabilitan durante `loading`; cambiar de testamento resetea el libro si ya no corresponde.

**Commits**: `0aea8ad`, `c65ed99`

---

## 2. Hybrid Retrieval (BM25 + RRF) — implementado, medido, **desactivado por default**

**Objetivo inicial**: sumar retrieval léxico (BM25) al dense retrieval existente (Chroma + E5), fusionando con Reciprocal Rank Fusion (RRF), para mejorar casos con términos específicos (nombres propios, términos técnicos) que el embedding podría no priorizar bien.

**Qué se construyó**:
- `infrastructure/retrieval/bm25.py`: `BM25Retriever` con índice en memoria (rank-bm25), reconstruido desde `biblia_chunks.jsonl` al arrancar. Si el archivo no existe, cae a modo "unavailable" sin romper la API.
- `domain/ranking.py`: `reciprocal_rank_fusion()`, función pura, testeada.
- `application/service.py`: `RagService.retrieve()` orquesta ambos retrievers (pool de 20 resultados cada uno) y fusiona antes de cortar a `num_results`.
- Parámetro `hybrid: bool` en `POST /query` para controlar el comportamiento por request.

**Verificación de que la fusión funciona correctamente**: se confirmó a mano (debug logs + cálculo manual de scores RRF) que:
- La fusión respeta empates y reordena correctamente cuando dos retrievers difieren en el ranking.
- Promueve candidatos que el dense-only no traía (caso "Melquisedec" → Salmos 110:4-7 entró al top-5 vía sparse, algo que dense solo no lograba).

**Resultado de la medición (recall@k, 15 preguntas, dataset curado a mano)**:

| Métrica | hybrid=True | hybrid=False (dense-only) |
|---|---:|---|
| Recall@1 | 20.0% | 40.0% |
| Recall@3 | 20.0% | 60.0% |
| Recall@5 | 33.3% | 73.3% |

**Diagnóstico**: BM25 con tokenizer plano (sin stopwords, sin discriminación semántica) no aporta señal útil en este corpus — el vocabulario bíblico está muy concentrado, y tanto el score agregado como el IDF máximo por token fallan en separar preguntas con término raro (donde BM25 ayudaría) de preguntas genéricas (donde solo mete ruido). Se probaron dos métricas candidatas para un umbral condicional y ninguna separó limpio — evidencia de que el problema es estructural, no de calibración.

**Decisión**: `hybrid` default pasó a `False` en `schemas.py` y `service.py`. El código queda completo, correcto y disponible como opt-in (`hybrid: true` en el request) para cuando el corpus crezca o se mejore el tokenizer.

**Commits**: `f0c716e` (implementación), `b4891b9` (eval), `8723bdf` (default a `False`), `2a40e7a` (documentación de la decisión)

---

## 3. Eval de Retrieval — `recall@k`

Herramienta nueva y reusable: `holy_bible/src/holy_bible/eval/`.

- `dataset.py`: 15 preguntas curadas a mano (genéricas, doctrinales, narrativas, términos propios/técnicos raros), cada una con el pasaje esperado.
- `recall_at_k.py`: mide, para `hybrid=True` y `hybrid=False`, si el pasaje esperado aparece en el top-k recuperado. No llama a Anthropic — mide retrieval puro, sin costo de generación.

Fue la herramienta que permitió detectar que hybrid empeoraba el retrieval antes de que llegara a producción con ese comportamiento por default.

**Comando**: `holy-bible-eval-recall`

---

## 4. Eval de Generación — `faithfulness` (Ragas)

**Objetivo**: medir si las respuestas de Claude son fieles a los pasajes recuperados (sin alucinar), no solo si el retrieval trae el pasaje correcto.

**Herramienta**: `holy_bible/src/holy_bible/eval/faithfulness_eval.py` — corre las 15 preguntas del dataset a través de `RagService.query()` completo (con generación real), arma un `EvaluationDataset` de Ragas y evalúa con la métrica `faithfulness`, usando el mismo modelo Claude ya configurado como juez.

**Iteración 1 — bug de instrumentación**: la primera corrida dio un promedio de **0.693**, pero `retrieved_contexts` se armaba solo con el texto plano de los chunks, sin la referencia bíblica (libro/capítulo/versículo). El juez no podía verificar precisión de citas. Corregido para usar el mismo formato de contexto que ya usa `AnthropicGenerator` en producción (`[n] Libro cap:inicio-fin\ntexto`).

**Iteración 2 — baseline correcto**: con el contexto bien formado, el promedio subió a **0.840**. Esto confirmó que gran parte del score bajo original era ruido de medición, no fidelidad real — aunque `AnthropicGenerator` en producción nunca tuvo el bug (el bug era solo del script de eval).

**Iteración 3 — fix real de producción**: el detalle de casos individuales reveló un patrón: Claude a veces cita un número de versículo distinto al que realmente aparece en el chunk recuperado (ej. citó "Hebreos 7:1" cuando el chunk real era "Hebreos 6:19-20" — un número que recuerda de ediciones bíblicas comunes, no del contexto que efectivamente recibió). Se agregó una regla explícita al `SYSTEM_PROMPT` (`shared/settings.py`) instruyendo a usar únicamente la referencia tal como aparece en el contexto dado, nunca una numeración distinta recordada de memoria.

**Resultado final**:

| Corrida | Promedio faithfulness | Nota |
|---|---:|---|
| Inicial (bug de contexto) | 0.693 | No confiable — contexto sin referencias |
| Contexto corregido | 0.840 | Baseline real |
| + regla anti-alucinación de citas | **0.879** | Melquisedec: 0.727 → 0.900 |

El caso remanente más bajo (`salmo del buen pastor`, 0.700) no es un problema de generación — la respuesta es honesta sobre no tener el Salmo 23 en el contexto recuperado. Es un miss de retrieval, no de fidelidad.

**Comando**: `holy-bible-eval-faithfulness` (costo aprox. USD 0.25-0.30 por corrida, ~15 llamadas de generación + evaluación con juez)

Eval, dependencias de Ragas (`ragas`, `langchain-anthropic`) y la regla del `SYSTEM_PROMPT` están en `main` (`26975b6`).

---

## Estado final

| Frente | Estado |
|---|---|
| Filtros testamento/libro | ✅ En producción |
| Hybrid retrieval | ✅ Código correcto, apagado por default con evidencia documentada |
| Eval recall@k | ✅ Herramienta reusable en el repo |
| Eval faithfulness | ✅ Herramienta reusable; fix de citas aplicado a `SYSTEM_PROMPT` |

## Lecciones para la próxima vez

- Medir antes de asumir: la hipótesis de que hybrid retrieval mejora resultados era razonable a priori y resultó falsa en este corpus — el eval la refutó en minutos en vez de descubrirse en producción.
- Los evals quedaron como herramientas permanentes en el repo (`holy_bible/src/holy_bible/eval/`), no como scripts descartables — cualquier cambio futuro a retrieval o al prompt de generación se puede validar contra el mismo dataset antes de mergear.
