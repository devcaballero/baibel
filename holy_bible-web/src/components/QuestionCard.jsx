import { ensureBibliaCatolica } from "../utils/biblia";

/** @param {{ question: string }} props */
export function QuestionCard({ question }) {
  return (
    <div className="card card-question">
      <p className="card-label">Pregunta</p>
      <p className="card-question-text">{ensureBibliaCatolica(question)}</p>
    </div>
  );
}
