export function IconDefs() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
      <defs>
        <g id="icn-share">
          <circle cx="18" cy="5" r="3" />
          <circle cx="6" cy="12" r="3" />
          <circle cx="18" cy="19" r="3" />
          <line x1="8.6" y1="10.6" x2="15.4" y2="6.4" />
          <line x1="8.6" y1="13.4" x2="15.4" y2="17.6" />
        </g>
        <g id="icn-chevron">
          <polyline points="6 9 12 15 18 9" />
        </g>
        <g id="icn-copy">
          <rect x="9" y="9" width="11" height="11" rx="2" />
          <path d="M5 15V5a2 2 0 0 1 2-2h10" />
        </g>
        <g id="icn-book">
          <path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v16.5a2.5 2.5 0 0 1-2.5 2.5H6.5A2.5 2.5 0 0 1 4 18.5v-14z" />
          <path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20" />
        </g>
        <g id="icn-whatsapp">
          <path d="M20.5 3.5a11 11 0 0 0-17.4 13.2L2 21l4.5-1.1A11 11 0 0 0 20.5 3.5z" />
          <path
            d="M8.5 8.5c.3-1 1-1.1 1.4-1.1.3 0 .6.2.8.6l.7 1.5c.2.3.1.7-.1 1l-.6.6c-.2.2-.2.5 0 .8.5.9 1.7 2.1 2.6 2.6.3.2.6.2.8 0l.6-.6c.3-.2.7-.3 1-.1l1.5.7c.4.2.6.5.6.8 0 .4-.1 1.1-1.1 1.4-1 .3-2.3.1-4-1-1.4-.9-2.7-2.2-3.6-3.6-1.1-1.7-1.3-3-1-4z"
            fillRule="evenodd"
          />
        </g>
        <g id="icn-x">
          <line x1="5" y1="5" x2="19" y2="19" />
          <line x1="19" y1="5" x2="5" y2="19" />
        </g>
        <g id="icn-facebook">
          <path d="M14 21v-7h2.5l.5-3H14V9c0-.9.2-1.5 1.5-1.5H17V4.9c-.3 0-1.2-.1-2.2-.1-2.2 0-3.8 1.3-3.8 3.8V11H8.5v3H11v7h3z" />
        </g>
      </defs>
    </svg>
  );
}

/** @param {{ id: string; className?: string; size?: number }} props */
export function Icon({ id, className = "icon", size = 16 }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      width={size}
      height={size}
      aria-hidden="true"
    >
      <use href={`#${id}`} />
    </svg>
  );
}
