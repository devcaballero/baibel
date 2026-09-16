import { CitationItem } from "./CitationItem";

/**
 * @param {{ citations: import("../api/client").Citation[] }} props
 */
export function CitationList({ citations }) {
  if (!citations.length) return null;

  const label =
    citations.length === 1 ? "1 pasaje consultado" : `${citations.length} pasajes consultados`;

  return (
    <section className="citations">
      <p className="citations-label">{label}</p>
      <div className="citations-list">
        {citations.map((citation, index) => (
          <CitationItem
            key={`${citation.book}-${citation.chapter}-${citation.verse_start}-${index}`}
            citation={citation}
            defaultOpen={index === 0}
          />
        ))}
      </div>
    </section>
  );
}
