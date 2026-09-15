/** @param {import("../api/client").Citation} citation */
export function formatCitationRef(citation) {
  const { book, chapter, verse_start, verse_end } = citation;
  const verses =
    verse_end !== verse_start ? `${verse_start}-${verse_end}` : `${verse_start}`;
  return `${book} ${chapter}:${verses}`;
}

/** @param {string} text */
export function copyToClipboard(text) {
  return navigator.clipboard.writeText(text);
}

/** @param {string} text */
export function shareWhatsApp(text) {
  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank");
}

/** @param {string} text */
export function shareX(text) {
  window.open(
    `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`,
    "_blank",
  );
}

export function shareFacebook() {
  window.open(
    `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(location.href)}`,
    "_blank",
  );
}

/**
 * @typedef {{ type: "h1" | "h2" | "h3" | "p"; heading?: string; body: string }} AnswerBlock
 */

/**
 * Parse markdown-ish answer text into renderable blocks.
 * @param {string} answer
 * @returns {AnswerBlock[]}
 */
export function parseAnswerBlocks(answer) {
  return answer
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block) => {
      if (block.startsWith("### ")) {
        return { type: "h3", body: block.slice(4).trim() };
      }
      if (block.startsWith("## ")) {
        return { type: "h2", body: block.slice(3).trim() };
      }
      if (block.startsWith("# ")) {
        return { type: "h1", body: block.slice(2).trim() };
      }

      const match = block.match(/^\*\*(.+?)\*\*\s*(.*)$/s);
      if (match) {
        const heading = match[1].replace(/\s*-\s*$/, "").trim();
        return {
          type: "p",
          heading,
          body: match[2].trim(),
        };
      }

      return { type: "p", body: block };
    });
}
