import { useRef } from "react";
import { getBooksByTestament, TESTAMENTS } from "../data/books";
import { Icon } from "./Icons";
import { SearchTags } from "./SearchTags";

/**
 * @param {{
 *   value: string;
 *   loading?: boolean;
 *   apiUnavailable?: boolean;
 *   error?: string | null;
 *   testament: string;
 *   book: string;
 *   canRetryQuery?: boolean;
 *   onChange: (value: string) => void;
 *   onTestamentChange: (value: string) => void;
 *   onBookChange: (value: string) => void;
 *   onSubmit: (question: string) => void;
 *   onRetryHealthCheck?: () => void;
 *   onRetryQuery?: () => void;
 * }} props
 */
export function SearchForm({
  value,
  loading,
  apiUnavailable = false,
  error,
  testament,
  book,
  canRetryQuery = false,
  onChange,
  onTestamentChange,
  onBookChange,
  onSubmit,
  onRetryHealthCheck,
  onRetryQuery,
}) {
  const inputRef = useRef(null);
  const books = getBooksByTestament(testament || null);
  const fieldsDisabled = Boolean(loading || apiUnavailable);

  function handleRetryHealthCheck(event) {
    event.preventDefault();
    event.stopPropagation();
    onRetryHealthCheck?.();
  }

  function handleRetryQueryClick(event) {
    event.preventDefault();
    event.stopPropagation();
    if (apiUnavailable) return;
    onRetryQuery?.();
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (fieldsDisabled) return;
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
    <>
      {apiUnavailable && (
        <div className="page-error-banner">
          <p className="page-subtitle page-subtitle-error">
            <Icon id="icn-alert" className="icon icon-error" />
            API no disponible
          </p>
          <button
            type="button"
            className="retry-btn"
            onClick={handleRetryHealthCheck}
          >
            Reintentar
          </button>
        </div>
      )}
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
            disabled={loading || apiUnavailable}
            autoComplete="off"
            required
          />
          <button
            type="submit"
            className="search-btn"
            disabled={loading || apiUnavailable}
          >
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
              disabled={loading || apiUnavailable}
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
              disabled={loading || apiUnavailable}
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
        <SearchTags disabled={fieldsDisabled} onSelect={handlePresetSelect} />
        {error && (
          <div className="search-error-row">
            <p className="search-error">
              <Icon id="icn-alert" className="icon icon-error" />
              {error}
            </p>
            {canRetryQuery && onRetryQuery ? (
              <button
                type="button"
                className="retry-btn"
                onClick={handleRetryQueryClick}
              >
                Reintentar
              </button>
            ) : null}
          </div>
        )}
      </form>
    </>
  );
}
