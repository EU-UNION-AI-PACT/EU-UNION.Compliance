import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Mermaid } from "./Mermaid";

/**
 * Renders paper body markdown, hoisting fenced ```mermaid blocks into a
 * dark-themed Mermaid diagram component. Everything else is standard GFM.
 */
export function PaperMarkdown({ body }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ node, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          const lang = match ? match[1] : "";
          // In react-markdown v9+, `inline` prop is gone. Block code is always
          // wrapped in a <pre> by remark, so we detect block via presence of
          // a language class OR a newline in the content.
          const isBlock = !!lang || /\n/.test(String(children));
          if (isBlock && lang === "mermaid") {
            return <Mermaid chart={String(children).trim()} />;
          }
          if (!isBlock) {
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          }
          return (
            <code className={className} {...props}>
              {children}
            </code>
          );
        },
      }}
    >
      {body}
    </ReactMarkdown>
  );
}
