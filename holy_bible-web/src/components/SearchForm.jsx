import { useRef } from "react";
import { SearchTags } from "./SearchTags";

/**
 * @param {{
 *   value: string;
 *   loading?: boolean;
 *   error?: string | null;
 *   onChange: (value: string) => void;
 *   onSubmit: (question: string) => void;
 * }} props
 */
export function SearchForm({ value, loading, error, onChange, onSubmit }) {
  const inputRef = useRef(null);

  function handleSubmit(event) {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    onChange("");
  }

  function handlePresetSelect(query) {
    onChange(query);
    inputRef.current?.focus();
  }

  return (
    <form className="search-form" onSubmit={handleSubmit}>
      <label className="search-label" htmlFor="question">
        ¿Qué querés consultar en la Biblia Católica?
      </label>
      <div className="search-row">
        <input
          ref={inputRef}
          id="question"
          name="question"
          type="text"
          className="search-input"
          placeholder="Ej.: ¿Qué dice la Biblia Católica sobre la amistad?"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          disabled={loading}
          autoComplete="off"
          required
        />
        <button type="submit" className="search-btn" disabled={loading}>
          {loading ? "Consultando…" : "Consultar"}
        </button>
      </div>
      <SearchTags disabled={loading} onSelect={handlePresetSelect} />
      {error && <p className="search-error">{error}</p>}
    </form>
  );
}
