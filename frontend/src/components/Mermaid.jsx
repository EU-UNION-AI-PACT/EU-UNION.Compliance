import React, { useEffect, useRef } from "react";
import mermaid from "mermaid";
import DOMPurify from "dompurify";

let initialized = false;

// DOMPurify config that KEEPS SVG structure but drops any script/handler.
// Applied as a defense-in-depth layer even though mermaid runs with
// securityLevel:'strict' (no <foreignObject>, no inline event handlers).
const SVG_SANITIZE_CONFIG = {
  USE_PROFILES: { svg: true, svgFilters: true },
  ADD_TAGS: ["foreignObject"], // allowed but harmless under strict mermaid
  FORBID_TAGS: ["script"],
  FORBID_ATTR: ["onclick", "onerror", "onload", "onmouseover", "onfocus"],
};

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

/**
 * Parse a sanitized SVG string into a live DOM element WITHOUT using
 * innerHTML. Uses DOMParser on image/svg+xml, which:
 *   1. Does NOT execute any <script> tag it encounters (per spec).
 *   2. Cannot fire inline event handlers.
 *   3. Rejects malformed markup — the caller sees a parse error tag it
 *      can inspect and handle explicitly.
 * DOMPurify is still applied first as a defense-in-depth belt.
 */
function svgNodeFromString(rawSvg) {
  const clean = DOMPurify.sanitize(rawSvg, SVG_SANITIZE_CONFIG);
  const doc = new DOMParser().parseFromString(clean, "image/svg+xml");
  const err = doc.querySelector("parsererror");
  if (err) {
    throw new Error("mermaid SVG parse failed");
  }
  return doc.documentElement;
}

/**
 * Build a safe <pre> node with textContent-only error message. Never
 * touches innerHTML, so it is inherently XSS-safe.
 */
function errorNode(message) {
  const pre = document.createElement("pre");
  pre.style.color = "#f87171";
  pre.style.fontSize = "11px";
  pre.style.whiteSpace = "pre-wrap";
  pre.textContent = `Mermaid parse error: ${message}`;
  return pre;
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
        // handlers or <foreignObject>. We then run DOMPurify + DOMParser to
        // produce a live SVG DOM node and mount it via replaceChildren, so
        // NO innerHTML assignment is ever performed anywhere in this file.
        const { svg } = await mermaid.render(targetId, chartRef.current);
        const node = svgNodeFromString(svg);
        if (!cancel && ref.current) {
          ref.current.replaceChildren(node);
        }
      } catch (e) {
        if (ref.current) {
          ref.current.replaceChildren(errorNode(e?.message || String(e)));
        }
        console.error("Mermaid render failed:", e);
      }
    })();
    return () => {
      cancel = true;
    };
  }, [chart, id]);

  return <div className="mermaid-wrap" data-testid="mermaid-diagram" ref={ref} />;
}
