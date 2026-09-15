import { useCallback, useEffect, useState } from "react";
import { getHealth, queryBible } from "../api/client";
import { AnswerCard } from "../components/AnswerCard";
import { CitationList } from "../components/CitationList";
import { LoadingIndicator } from "../components/LoadingIndicator";
import { QuestionCard } from "../components/QuestionCard";
import { ensureBibliaCatolica } from "../utils/biblia";
import { SearchForm } from "../components/SearchForm";

export function HomePage() {
  const [question, setQuestion] = useState("");
  const [searchDraft, setSearchDraft] = useState("");
  const [testament, setTestament] = useState("");
  const [book, setBook] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);

  useEffect(() => {
    getHealth()
      .then((health) => setApiStatus(health))
      .catch(() => setApiStatus({ status: "error", detail: "API no disponible" }));
  }, []);

  const handleSubmit = useCallback(async (nextQuestion) => {
    const normalizedQuestion = ensureBibliaCatolica(nextQuestion);
    setQuestion(normalizedQuestion);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await queryBible(normalizedQuestion, {
        testament: testament || undefined,
        book: book || undefined,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al consultar");
    } finally {
      setLoading(false);
    }
  }, [testament, book]);

  return (
    <main className="page">
      <header className="page-header">
        <img src="/logo.png" alt="" className="page-logo" width={96} height={96} />
        <h1 className="page-title">Baibel</h1>
        {apiStatus?.status === "error" && (
          <p className="page-subtitle page-subtitle-error">{apiStatus.detail ?? "API no disponible"}</p>
        )}
      </header>

      <SearchForm
        value={searchDraft}
        onChange={setSearchDraft}
        testament={testament}
        book={book}
        onTestamentChange={setTestament}
        onBookChange={setBook}
        loading={loading}
        error={error}
        onSubmit={handleSubmit}
      />

      {loading && <LoadingIndicator />}

      {result && !loading && (
        <div className="results">
          <QuestionCard question={question} />
          <AnswerCard question={question} answer={result.answer} />
          <CitationList key={question} citations={result.citations} />
        </div>
      )}
    </main>
  );
}
