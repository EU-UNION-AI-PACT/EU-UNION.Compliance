import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Mermaid } from "./Mermaid";

/**
 * Renders inline or block <code> nodes. Fenced ```mermaid``` blocks are
 * lifted into a Mermaid diagram component; everything else is rendered as
 * a normal <code> element. Kept as a module-level function so React does
 * not tear down / rebuild the subtree on each parent render.
 */
function MarkdownCode({ className, children, ...props }) {
  const match = /language-(\w+)/.exec(className || "");
  const lang = match ? match[1] : "";
  // In react-markdown v9+, `inline` prop is gone. Block code is always
  // wrapped in a <pre> by remark, so we detect block via presence of
  // a language class OR a newline in the content.
  const isBlock = !!lang || /\n/.test(String(children));
  if (isBlock && lang === "mermaid") {
    return <Mermaid chart={String(children).trim()} />;
  }
  return (
    <code className={className} {...props}>
      {children}
    </code>
  );
}

/**
 * Renders paper body markdown, hoisting fenced ```mermaid blocks into a
 * dark-themed Mermaid diagram component. Everything else is standard GFM.
 */
export function PaperMarkdown({ body }) {
  // Memoize the components map so ReactMarkdown does not see a new object
  // identity on every re-render.
  const components = useMemo(() => ({ code: MarkdownCode }), []);
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {body}
    </ReactMarkdown>
  );
}
