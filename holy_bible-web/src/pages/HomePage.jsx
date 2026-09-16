import { useCallback, useEffect, useState } from "react";
import { getHealth, queryBible } from "../api/client";
import { AnswerCard } from "../components/AnswerCard";
import { CitationList } from "../components/CitationList";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { QuestionCard } from "../components/QuestionCard";
import { TESTAMENTS } from "../data/books";
import { ensureBibliaCatolica } from "../utils/biblia";
import { SearchForm } from "../components/SearchForm";

function searchScopeLabel(testament, book) {
  const parts = [];
  if (testament) {
    const match = TESTAMENTS.find((item) => item.value === testament);
    parts.push(match?.label ?? testament);
  }
  if (book) {
    parts.push(book);
  }
  if (parts.length === 0) {
    return null;
  }
  return `Buscando en: ${parts.join(" · ")}`;
}

export function HomePage() {
  const [question, setQuestion] = useState("");
  const [searchDraft, setSearchDraft] = useState("");
  const [testament, setTestament] = useState("");
  const [book, setBook] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);
  const [lastAttemptedQuestion, setLastAttemptedQuestion] = useState("");

  const retryHealthCheck = useCallback(() => {
    getHealth()
      .then((health) => {
        setApiStatus(health);
        setError(null);
      })
      .catch(() => setApiStatus({ status: "error", detail: "API no disponible" }));
  }, []);

  useEffect(() => {
    retryHealthCheck();
  }, [retryHealthCheck]);

  const handleSubmit = useCallback(async (nextQuestion) => {
    if (apiStatus?.status === "error") return;
    const normalizedQuestion = ensureBibliaCatolica(nextQuestion);
    setQuestion(normalizedQuestion);
    setLastAttemptedQuestion(normalizedQuestion);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await queryBible(normalizedQuestion, {
        testament: testament || undefined,
        book: book || undefined,
      });
      setResult({
        ...data,
        appliedTestament: testament,
        appliedBook: book,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al consultar");
    } finally {
      setLoading(false);
    }
  }, [apiStatus?.status, testament, book]);

  const handleRetryQuery = useCallback(() => {
    if (!lastAttemptedQuestion || apiStatus?.status === "error") return;
    handleSubmit(lastAttemptedQuestion);
  }, [apiStatus?.status, handleSubmit, lastAttemptedQuestion]);

  const apiUnavailable = apiStatus?.status === "error";
  const formError = apiUnavailable ? null : error;

  const resultScope = result
    ? searchScopeLabel(result.appliedTestament, result.appliedBook)
    : null;

  return (
    <main className="page">
      <header className="page-header">
        <img src="/logo.png" alt="" className="page-logo" width={96} height={96} />
        <h1 className="page-title">Baibel</h1>
      </header>

      <SearchForm
        value={searchDraft}
        onChange={setSearchDraft}
        testament={testament}
        book={book}
        onTestamentChange={setTestament}
        onBookChange={setBook}
        loading={loading}
        apiUnavailable={apiUnavailable}
        error={formError}
        onSubmit={handleSubmit}
        onRetryHealthCheck={retryHealthCheck}
        onRetryQuery={handleRetryQuery}
        canRetryQuery={Boolean(lastAttemptedQuestion)}
      />

      {loading && <LoadingIndicator />}

      {result && !loading && (
        <div className="results">
          <QuestionCard question={question} />
          {resultScope ? <p className="result-scope">{resultScope}</p> : null}
          <AnswerCard question={question} answer={result.answer} />
          <CitationList key={question} citations={result.citations} />
        </div>
      )}
    </main>
  );
}
