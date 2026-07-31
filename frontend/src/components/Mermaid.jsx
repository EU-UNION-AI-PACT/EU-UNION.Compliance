import React, { useEffect, useRef } from "react";
import mermaid from "mermaid";

let initialized = false;

function init() {
  if (initialized) return;
  mermaid.initialize({
    startOnLoad: false,
    // Defense-in-depth: strictest security level — no HTML in labels, no
    // <foreignObject>, no user-provided JS. Applies to all subsequent renders.
    securityLevel: "strict",
    theme: "dark",
    fontFamily: "JetBrains Mono, monospace",
    themeVariables: {
      background: "#090d16",
      primaryColor: "#1a2333",
      primaryTextColor: "#e5e7eb",
      primaryBorderColor: "#f59e0b",
      lineColor: "#3b82f6",
      secondaryColor: "#111827",
      tertiaryColor: "#0e1521",
      textColor: "#e5e7eb",
      fontSize: "13px",
    },
    flowchart: { curve: "basis", htmlLabels: false },
    sequence: {
      actorFontFamily: "Inter",
      noteFontFamily: "Inter",
      messageFontFamily: "JetBrains Mono",
    },
  });
  initialized = true;
}

// Simple, safe HTML escaper used to render parse-error messages.
function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function Mermaid({ chart, id }) {
  const ref = useRef(null);
  const chartRef = useRef(chart);
  chartRef.current = chart;

  useEffect(() => {
    init();
    let cancel = false;
    const targetId = id || `mmd-${Math.random().toString(36).slice(2, 9)}`;
    (async () => {
      try {
        // mermaid.render returns a trusted SVG produced from the input diagram
        // definition. With securityLevel:'strict' it strips any inline event
        // handlers or <foreignObject> nodes, so assigning to innerHTML is safe.
        const { svg } = await mermaid.render(targetId, chartRef.current);
        if (!cancel && ref.current) {
          ref.current.innerHTML = svg;
        }
      } catch (e) {
        // Never inject the raw error message as HTML — always HTML-escape it.
        if (ref.current) {
          const safe = escapeHtml(e?.message || String(e));
          ref.current.innerHTML =
            `<pre style="color:#f87171;font-size:11px">Mermaid parse error: ${safe}</pre>`;
        }
        // eslint-disable-next-line no-console
        console.error("Mermaid render failed:", e);
      }
    })();
    return () => {
      cancel = true;
    };
  }, [chart, id]);

  return <div className="mermaid-wrap" data-testid="mermaid-diagram" ref={ref} />;
}
