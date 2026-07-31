import React, { useEffect, useState } from "react";
import { X, Copy, ExternalLink, Check, Loader2 } from "lucide-react";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL ||
  (typeof window !== "undefined" ? window.location.origin : "");

/**
 * Slide-in right drawer for a compliance framework.
 * Shows: metadata, all rules (specialised OR generic), source link,
 * copy-as-cURL button, and a "prefill payload" hint block.
 */
export default function FrameworkDrawer({ code, onClose }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [customRules, setCustomRules] = useState([]);

  useEffect(() => {
    if (!code) return;
    setData(null);
    setError(null);
    (async () => {
      try {
        const [rb, cr] = await Promise.all([
          fetch(`${BACKEND_URL}/api/validate/rules/${encodeURIComponent(code)}`).then((r) => {
            if (!r.ok) throw new Error(`rules HTTP ${r.status}`);
            return r.json();
          }),
          fetch(
            `${BACKEND_URL}/api/validate/custom-rules/${encodeURIComponent(code)}`
          ).then((r) => (r.ok ? r.json() : { rules: [] })),
        ]);
        setData(rb);
        setCustomRules(cr.rules || []);
      } catch (e) {
        setError(e.message);
      }
    })();
  }, [code]);

  useEffect(() => {
    const onEsc = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onEsc);
    return () => window.removeEventListener("keydown", onEsc);
  }, [onClose]);

  if (!code) return null;

  const fw = data?.framework;

  const curlCmd = fw
    ? `curl -X POST '${BACKEND_URL}/api/validate' \\
  -H 'content-type: application/json' \\
  -d '${JSON.stringify(
    {
      framework: fw.code,
      source: "cli",
      payload: (data?.rules || []).reduce((acc, r) => {
        acc[r.field] = `<${r.field}>`;
        return acc;
      }, {}),
    },
    null,
    2
  )}'`
    : "";

  const doCopy = async () => {
    try {
      await navigator.clipboard.writeText(curlCmd);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn("Clipboard copy failed:", err);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end"
      data-testid="fw-drawer"
      role="dialog"
      aria-modal="true"
    >
      <div
        className="pnia-drawer-scrim absolute inset-0 bg-black/70"
        onClick={onClose}
      />
      <div className="pnia-drawer relative w-full max-w-[560px] h-full bg-[#0a0f19] border-l border-white/10 overflow-y-auto">
        <div className="sticky top-0 z-10 backdrop-blur bg-[#0a0f19]/90 border-b border-white/10 px-5 py-3 flex items-center gap-3">
          <span className="font-mono text-[10px] uppercase tracking-[0.24em] text-amber-500">
            Framework
          </span>
          <span className="font-mono text-[11px] text-amber-400">{code}</span>
          <button
            onClick={onClose}
            data-testid="drawer-close"
            className="ml-auto p-1.5 border border-white/10 rounded text-slate-400 hover:text-white hover:border-amber-500/50"
          >
            <X size={13} />
          </button>
        </div>

        {error && (
          <div className="p-5 text-red-400 font-mono text-[11px]">{error}</div>
        )}
        {!data && !error && (
          <div className="p-5 flex items-center gap-2 text-slate-500 font-mono text-[11px]">
            <Loader2 size={12} className="animate-spin" /> loading rules…
          </div>
        )}
        {data && fw && (
          <div className="px-5 pb-8 space-y-5">
            <div>
              <div className="text-xl font-serif tracking-tight text-white mt-2">
                {fw.name}
              </div>
              <div className="mt-1 text-[11px] font-mono text-slate-500 flex flex-wrap gap-x-4 gap-y-1">
                <span>{fw.regulator}</span>
                <span>{fw.jurisdiction}</span>
                <span>{fw.category}</span>
                <span>{fw.status}</span>
              </div>
              <a
                href={fw.source}
                target="_blank"
                rel="noreferrer"
                data-testid="drawer-source-link"
                className="inline-flex items-center gap-1.5 mt-3 text-[11px] font-mono text-amber-400 hover:text-amber-300"
              >
                <ExternalLink size={11} /> Open primary regulator publication
              </a>
            </div>

            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="text-[10px] font-mono uppercase tracking-[0.24em] text-amber-500/80">
                  Ruleset · {data.mode}
                </div>
                <div className="ml-auto text-[10px] font-mono text-slate-500">
                  {data.rules?.length || 0} rules
                </div>
              </div>
              <ul className="space-y-2">
                {(data.rules || []).map((r) => (
                  <li
                    key={r.field}
                    data-testid={`drawer-rule-${r.field}`}
                    className="border border-white/10 bg-black/40 rounded p-3"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-[11px] text-amber-400">
                        {r.field}
                      </span>
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                          r.severity === "REQUIRED"
                            ? "bg-red-500/15 text-red-300 border border-red-500/30"
                            : "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                        }`}
                      >
                        {r.severity}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 leading-relaxed">
                      {r.hint}
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {customRules.length > 0 && (
              <div>
                <div className="text-[10px] font-mono uppercase tracking-[0.24em] text-emerald-400/80 mb-2">
                  Custom overrides · {customRules.length}
                </div>
                <ul className="space-y-2">
                  {customRules.map((r) => (
                    <li
                      key={r.id}
                      className="border border-emerald-500/30 bg-emerald-500/5 rounded p-3"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-[11px] text-emerald-300">
                          {r.field}
                        </span>
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                          {r.severity}
                        </span>
                        <span className="ml-auto text-[9px] font-mono text-slate-500">
                          by {r.created_by}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 leading-relaxed">
                        {r.hint}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="text-[10px] font-mono uppercase tracking-[0.24em] text-amber-500/80">
                  Copy as cURL
                </div>
                <button
                  onClick={doCopy}
                  data-testid="drawer-copy-curl"
                  className="ml-auto inline-flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-300 border border-white/10 hover:border-amber-500/50 px-2 py-1 rounded"
                >
                  {copied ? (
                    <>
                      <Check size={11} /> copied
                    </>
                  ) : (
                    <>
                      <Copy size={11} /> copy
                    </>
                  )}
                </button>
              </div>
              <pre className="text-[10px] leading-snug font-mono text-emerald-300 bg-black/60 border border-white/10 rounded p-3 overflow-x-auto whitespace-pre-wrap">
                {curlCmd}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
