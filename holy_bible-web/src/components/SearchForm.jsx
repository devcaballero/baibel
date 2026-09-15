import { useRef } from "react";
import { getBooksByTestament, TESTAMENTS } from "../data/books";
import { SearchTags } from "./SearchTags";

/**
 * @param {{
 *   value: string;
 *   loading?: boolean;
 *   error?: string | null;
 *   testament: string;
 *   book: string;
 *   onChange: (value: string) => void;
 *   onTestamentChange: (value: string) => void;
 *   onBookChange: (value: string) => void;
 *   onSubmit: (question: string) => void;
 * }} props
 */
export function SearchForm({
  value,
  loading,
  error,
  testament,
  book,
  onChange,
  onTestamentChange,
  onBookChange,
  onSubmit,
}) {
  const inputRef = useRef(null);
  const books = getBooksByTestament(testament || null);

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

  function handleTestamentChange(event) {
    const nextTestament = event.target.value;
    onTestamentChange(nextTestament);
    if (!book) return;
    const allowed = getBooksByTestament(nextTestament || null);
    if (!allowed.some((item) => item.name === book)) {
      onBookChange("");
    }
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
      <div className="search-filters">
        <label className="search-filter" htmlFor="testament">
          <span className="search-filter-label">Testamento</span>
          <select
            id="testament"
            name="testament"
            className="search-select"
            value={testament}
            onChange={handleTestamentChange}
            disabled={loading}
          >
            <option value="">Todos</option>
            {TESTAMENTS.map(({ value: optionValue, label }) => (
              <option key={optionValue} value={optionValue}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="search-filter" htmlFor="book">
          <span className="search-filter-label">Libro</span>
          <select
            id="book"
            name="book"
            className="search-select"
            value={book}
            onChange={(event) => onBookChange(event.target.value)}
            disabled={loading}
          >
            <option value="">Todos</option>
            {books.map(({ name }) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <SearchTags disabled={loading} onSelect={handlePresetSelect} />
      {error && <p className="search-error">{error}</p>}
    </form>
  );
}
