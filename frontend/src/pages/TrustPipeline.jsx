import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Loader2, ScanText, ShieldAlert, Fingerprint, ChevronDown, ChevronRight } from "lucide-react";
import { toast } from "sonner";
import { getCaChain, parseLotl } from "../lib/api";

function ChainNode({ cert, isLast }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const roleColor =
    cert.role === "root" ? "amber" : cert.role === "intermediate" ? "blue" : "emerald";
  return (
    <div className="relative pl-8" data-testid={`chain-node-${cert.role}`}>
      {/* connector */}
      {!isLast && (
        <div className="absolute left-3 top-8 bottom-0 w-px bg-gradient-to-b from-amber-500/60 via-blue-500/50 to-transparent" />
      )}
      <div
        className={`absolute left-0 top-4 w-6 h-6 flex items-center justify-center rounded-full border ${
          roleColor === "amber"
            ? "border-amber-500 bg-amber-500/15"
            : roleColor === "blue"
            ? "border-blue-500 bg-blue-500/15"
            : "border-emerald-500 bg-emerald-500/15"
        }`}
      >
        <Fingerprint size={11} strokeWidth={1.7} className={`text-${roleColor}-400`} />
      </div>
      <div className="mb-3 border border-white/10 bg-[#0a0f19] rounded-sm trace-beam">
        <button
          onClick={() => setOpen((o) => !o)}
          className="w-full flex items-center justify-between px-4 py-3 text-left"
          data-testid={`chain-toggle-${cert.role}`}
        >
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-0.5">
              {cert.role}
            </div>
            <div className="font-serif text-white text-[15px]">{cert.subject}</div>
            <div className="mt-1 text-[10.5px] font-mono text-slate-500">
              {t("trust.issuer")}: {cert.issuer}
            </div>
          </div>
          {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        {open && (
          <div className="px-4 pb-4 pt-2 border-t border-white/5 grid grid-cols-2 gap-3 text-[11px] font-mono">
            <div>
              <div className="text-slate-500 uppercase text-[9px] tracking-[0.15em]">{t("trust.serial")}</div>
              <div className="text-slate-300 truncate">{cert.serial}</div>
            </div>
            <div>
              <div className="text-slate-500 uppercase text-[9px] tracking-[0.15em]">{t("trust.fingerprint")}</div>
              <div className="text-blue-400 truncate">{cert.fingerprint_sha256.slice(0, 24)}…</div>
            </div>
            <div>
              <div className="text-slate-500 uppercase text-[9px] tracking-[0.15em]">{t("trust.valid_from")}</div>
              <div className="text-slate-300">{cert.not_before?.slice(0, 19)}</div>
            </div>
            <div>
              <div className="text-slate-500 uppercase text-[9px] tracking-[0.15em]">{t("trust.valid_until")}</div>
              <div className="text-slate-300">{cert.not_after?.slice(0, 19)}</div>
            </div>
            <details className="col-span-2 mt-1">
              <summary className="cursor-pointer text-[10px] uppercase tracking-widest text-slate-500 hover:text-white">
                PEM
              </summary>
              <pre className="mt-2 text-[10px] text-slate-400 bg-[#050a12] p-2 rounded-sm overflow-x-auto whitespace-pre-wrap break-all max-h-40">
                {cert.pem}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );
}

export default function TrustPipeline() {
  const { t } = useTranslation();
  const [chain, setChain] = useState([]);
  const [xml, setXml] = useState("");
  const [parsed, setParsed] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getCaChain().then(setChain).catch(() => setChain([]));
  }, []);

  const doParse = async () => {
    setBusy(true);
    try {
      const r = await parseLotl(xml);
      setParsed(r);
      toast.success(`Parsed ${r.anchor_count} anchors`);
    } catch (e) {
      toast.error("Parse failed: " + (e?.response?.data?.detail || e.message));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12">
      <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-3">
        TRUST PIPELINE · RFC 5280 · ETSI TS 119 612
      </div>
      <h1 className="font-serif font-light text-4xl lg:text-5xl text-white leading-tight mb-3">
        {t("trust.title")}
      </h1>
      <p className="text-slate-400 max-w-2xl mb-10">{t("trust.subtitle")}</p>

      <div className="grid grid-cols-12 gap-8">
        <section className="col-span-12 lg:col-span-6">
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-blue-400 mb-4">
            {t("trust.chain_title")}
          </div>
          {chain.length === 0 ? (
            <div className="text-slate-500 text-sm font-mono">Loading…</div>
          ) : (
            <div>
              {chain.map((c, i) => (
                <ChainNode key={c.role} cert={c} isLast={i === chain.length - 1} />
              ))}
            </div>
          )}
        </section>
        <section className="col-span-12 lg:col-span-6">
          <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-4">
            <ScanText size={12} strokeWidth={1.6} /> {t("trust.lotl_title")}
          </div>
          <textarea
            value={xml}
            onChange={(e) => setXml(e.target.value)}
            data-testid="lotl-xml-input"
            placeholder={t("trust.lotl_placeholder")}
            rows={10}
            className="w-full bg-[#050a12] border border-white/10 focus:border-amber-500/60 rounded-sm p-3 text-[11px] font-mono text-slate-300 outline-none transition-colors"
          />
          <button
            onClick={doParse}
            disabled={busy || !xml.trim()}
            data-testid="lotl-parse-btn"
            className="mt-3 flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-black px-4 py-2 rounded-sm text-sm font-semibold transition-colors disabled:opacity-40"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : <ScanText size={14} strokeWidth={1.7} />}
            {t("trust.parse")}
          </button>

          {parsed && (
            <div className="mt-6 border border-blue-500/30 bg-blue-500/[0.04] p-4 rounded-sm" data-testid="lotl-parsed-summary">
              <div className="grid grid-cols-2 gap-3 text-[11.5px] font-mono">
                <div>
                  <div className="text-slate-500 uppercase text-[9px]">Territory</div>
                  <div className="text-white">{parsed.territory}</div>
                </div>
                <div>
                  <div className="text-slate-500 uppercase text-[9px]">Sequence</div>
                  <div className="text-amber-500">#{parsed.sequence_number}</div>
                </div>
                <div className="col-span-2">
                  <div className="text-slate-500 uppercase text-[9px]">Scheme Operator</div>
                  <div className="text-white">{parsed.scheme_operator}</div>
                </div>
                <div>
                  <div className="text-slate-500 uppercase text-[9px]">Anchors</div>
                  <div className="text-emerald-400">{parsed.anchor_count}</div>
                </div>
              </div>
              {parsed.anchors.length > 0 && (
                <div className="mt-4 border-t border-white/5 pt-3 max-h-64 overflow-y-auto">
                  <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-2">
                    {t("trust.anchors")}
                  </div>
                  {parsed.anchors.slice(0, 20).map((a, i) => (
                    <div key={i} className="text-[10.5px] font-mono text-slate-400 py-1 border-b border-white/5 last:border-0">
                      <div className="text-white truncate">{a.subject || a.tsp_name}</div>
                      <div className="text-blue-400 truncate">{a.fingerprint_sha256.slice(0, 20)}…</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {!parsed && (
            <div className="mt-4 text-[11px] text-slate-500 flex items-start gap-2">
              <ShieldAlert size={12} strokeWidth={1.6} className="mt-0.5 shrink-0" />
              <span>
                Paste a real ETSI TS 119 612 LOTL (e.g. from{" "}
                <a
                  className="text-blue-400 underline"
                  href="https://ec.europa.eu/tools/lotl/eu-lotl.xml"
                  target="_blank"
                  rel="noreferrer"
                >
                  ec.europa.eu/tools/lotl/eu-lotl.xml
                </a>
                ).
              </span>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
