const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/**
 * @typedef {Object} Citation
 * @property {string} book
 * @property {number} chapter
 * @property {number} verse_start
 * @property {number} verse_end
 * @property {string} text
 * @property {string} source
 */

/**
 * @typedef {Object} QueryResponse
 * @property {string} answer
 * @property {Citation[]} citations
 */

/**
 * @typedef {Object} HealthResponse
 * @property {string} status
 * @property {number | null} [indexed_chunks]
 * @property {string | null} [detail]
 */

/**
 * @param {string} question
 * @param {{ numResults?: number; testament?: string | null; book?: string | null }} [options]
 * @returns {Promise<QueryResponse>}
 */
export async function queryBible(
  question,
  { numResults = 5, testament, book } = {},
) {
  /** @type {{ question: string; num_results: number; testament?: string; book?: string }} */
  const payload = { question, num_results: numResults };
  if (testament) payload.testament = testament;
  if (book) payload.book = book;

  const response = await fetch(`${API_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : Array.isArray(body.detail)
          ? body.detail.map((e) => e.msg ?? JSON.stringify(e)).join("; ")
          : `Error ${response.status}`;
    throw new Error(detail);
  }

  return response.json();
}

/** @returns {Promise<HealthResponse>} */
export async function getHealth() {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }
  return response.json();
}

export { API_URL };
