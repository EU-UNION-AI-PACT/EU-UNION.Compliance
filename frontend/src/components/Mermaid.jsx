import React, { useEffect, useRef } from "react";
import mermaid from "mermaid";

let initialized = false;

function init() {
  if (initialized) return;
  mermaid.initialize({
    startOnLoad: false,
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
    flowchart: { curve: "basis", htmlLabels: true },
    sequence: { actorFontFamily: "Inter", noteFontFamily: "Inter", messageFontFamily: "JetBrains Mono" },
  });
  initialized = true;
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
        const { svg } = await mermaid.render(targetId, chartRef.current);
        if (!cancel && ref.current) ref.current.innerHTML = svg;
      } catch (e) {
        if (ref.current) {
          ref.current.innerHTML = `<pre style="color:#f87171;font-size:11px">Mermaid parse error: ${e?.message || e}</pre>`;
        }
      }
    })();
    return () => {
      cancel = true;
    };
  }, [chart, id]);

  return <div className="mermaid-wrap" data-testid="mermaid-diagram" ref={ref} />;
}
