/**
 * @param {{ text: string }} props
 */
export function FormattedText({ text }) {
  if (!text) return null;

  const parts = text.split(/(\*\*.+?\*\*)/g);

  return parts.map((part, index) => {
    const boldMatch = part.match(/^\*\*(.+)\*\*$/);
    if (boldMatch) {
      return (
        <strong key={index} className="answer-strong">
          {boldMatch[1]}
        </strong>
      );
    }
    return part;
  });
}
