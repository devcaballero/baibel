import { PREDEFINED_SEARCHES } from "../data/predefinedSearches";

/**
 * @param {{ disabled?: boolean; onSelect: (query: string) => void }} props
 */
export function SearchTags({ disabled = false, onSelect }) {
  return (
    <div className="search-tags" role="group" aria-label="Búsquedas sugeridas">
      <p className="search-tags-label">Temas frecuentes</p>
      <div className="search-tags-list">
        {PREDEFINED_SEARCHES.map(({ label, query }) => (
          <button
            key={label}
            type="button"
            className="search-tag"
            disabled={disabled}
            onClick={() => onSelect(query)}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
