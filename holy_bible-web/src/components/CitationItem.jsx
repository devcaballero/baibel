import { useState } from "react";
import { Icon } from "./Icons";
import { ShareMenu } from "./ShareMenu";
import { formatCitationRef } from "../utils/share";

/**
 * @param {{ citation: import("../api/client").Citation; defaultOpen?: boolean }} props
 */
export function CitationItem({ citation, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const ref = formatCitationRef(citation);
  const shareText = `${ref} — ${citation.text}`;

  return (
    <div className="cita" data-ref={ref}>
      <details
        open={open}
        onToggle={(event) => setOpen(event.currentTarget.open)}
      >
        <summary aria-expanded={open}>
          <span className="cita-ref-wrap">
            <span className="cita-ref">{ref}</span>
            <span className="cita-source">{citation.source}</span>
          </span>
          <span className="cita-actions">
            <ShareMenu text={shareText} compact />
            <Icon id="icn-chevron" className="icon chev icon-muted" />
          </span>
        </summary>
        <p className="cita-text">{citation.text}</p>
      </details>
    </div>
  );
}
