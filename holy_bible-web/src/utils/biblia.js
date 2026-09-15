/**
 * Asegura que toda mención a "Biblia" incluya "Católica".
 * @param {string} text
 */
export function ensureBibliaCatolica(text) {
  return text.replace(/\b(Biblia)(?!\s+[Cc]at[oó]lica)\b/g, "Biblia Católica");
}
