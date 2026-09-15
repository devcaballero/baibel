import { Icon } from "./Icons";
import { ShareMenu } from "./ShareMenu";
import { FormattedText } from "./FormattedText";
import { ensureBibliaCatolica } from "../utils/biblia";
import { parseAnswerBlocks } from "../utils/share";

function withTrailingColon(text) {
  const trimmed = text.trim();
  return trimmed.endsWith(":") ? trimmed : `${trimmed}:`;
}

/**
 * @param {{ question: string; answer: string }} props
 */
export function AnswerCard({ question, answer }) {
  const normalizedAnswer = ensureBibliaCatolica(answer);
  const blocks = parseAnswerBlocks(normalizedAnswer);
  const shareText = `${ensureBibliaCatolica(question)}\n\n${normalizedAnswer}`;
  const lastParagraphIndex = blocks.reduce(
    (last, block, index) => (block.type === "p" ? index : last),
    -1,
  );

  return (
    <div className="card card-answer">
      <div className="answer-header">
        <div className="answer-title">
          <Icon id="icn-book" className="icon icon-muted" />
          <span>Respuesta</span>
        </div>
        <ShareMenu text={shareText} />
      </div>

      <div className="answer-body">
        {blocks.map((block, index) => {
          if (block.type === "h1") {
            return (
              <h2 key={index} className="answer-h1">
                <FormattedText text={withTrailingColon(block.body)} />
              </h2>
            );
          }

          if (block.type === "h2") {
            return (
              <h3 key={index} className="answer-section-title">
                <FormattedText text={block.body} />
              </h3>
            );
          }

          if (block.type === "h3") {
            return (
              <h4 key={index} className="answer-section-subtitle">
                <FormattedText text={block.body} />
              </h4>
            );
          }

          const isSummary = index === lastParagraphIndex && blocks.length > 1;

          if (block.heading) {
            return (
              <div key={index} className="answer-section">
                <h3 className="answer-section-title">
                  <FormattedText text={block.heading} />
                </h3>
                <p className={isSummary ? "answer-summary" : undefined}>
                  <FormattedText text={block.body} />
                </p>
              </div>
            );
          }

          return (
            <p
              key={index}
              className={isSummary ? "answer-summary" : undefined}
            >
              <FormattedText text={block.body} />
            </p>
          );
        })}
      </div>
    </div>
  );
}
