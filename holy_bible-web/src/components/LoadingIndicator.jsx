import { useEffect, useState } from "react";

export function LoadingIndicator() {
  const [dots, setDots] = useState(1);

  useEffect(() => {
    const timer = setInterval(() => {
      setDots((current) => (current % 3) + 1);
    }, 500);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="loading" role="status" aria-live="polite">
      <img
        src="/loading-dove.gif"
        alt=""
        className="loading-dove-gif"
        width={120}
        height={86}
      />
      <p
        className="loading-text"
        aria-label="Buscando pasajes y generando respuesta"
      >
        Buscando pasajes y generando respuesta
        <span className="loading-dots" aria-hidden="true">
          {".".repeat(dots)}
        </span>
      </p>
    </div>
  );
}
