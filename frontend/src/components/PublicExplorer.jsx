import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ShieldCheck,
  Radio,
  Play,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  ArrowUpRight,
} from "lucide-react";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL ||
  (typeof window !== "undefined" ? window.location.origin : "");

const SAMPLES = [
  {
    key: "gdpr-min",
    label: "GDPR · minimal",
    framework: "GDPR",
    hint: "Only 2 of 7 required fields — expect FAIL",
    payload: {
      controller: "PNIA Reference Ltd.",
      processing_purpose: "user auth",
    },
  },
  {
    key: "dora-full",
    label: "DORA · full",
    framework: "DORA",
    hint: "All 8 required fields — expect PASS",
    payload: {
      ict_governance: "board approved",
      ict_risk_register: "documented",
      incident_classification: "tier1..3",
      incident_reporting_timeline: "4h/1M",
      digital_operational_resilience_testing: "annual",
      third_party_ict_register: "yes",
      critical_third_party_designation: "assessed",
      business_continuity_plan: "RTO 4h",
    },
  },
  {
    key: "aiact-partial",
    label: "EU AI Act · partial",
    framework: "EU AI Act",
    hint: "3 of 8 required covered — expect FAIL",
    payload: {
      ai_system_role: "provider",
      risk_classification: "high-risk",
      technical_documentation: "annex-iv v1.2",
    },
  },
];

function Pill({ status }) {
  const map = {
    PASS: { c: "text-emerald-400 border-emerald-500/40 bg-emerald-500/10", I: CheckCircle2 },
    PASS_WITH_WARNINGS: { c: "text-amber-400 border-amber-500/40 bg-amber-500/10", I: AlertTriangle },
    FAIL: { c: "text-red-400 border-red-500/40 bg-red-500/10", I: XCircle },
  };
  const m = map[status] || { c: "text-slate-400 border-slate-500/40 bg-slate-500/10", I: Info };
  const I = m.I;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm border font-mono text-[10px] uppercase tracking-wider ${m.c}`}>
      <I size={11} /> {status || "—"}
    </span>
  );
}

export default function PublicExplorer() {
  const [ticker, setTicker] = useState([]);
  const [sseState, setSseState] = useState("connecting");
  const [busy, setBusy] = useState(null);
  const [lastReport, setLastReport] = useState(null);
  const esRef = useRef(null);

  useEffect(() => {
    const es = new EventSource(`${BACKEND_URL}/api/validate/stream`);
    esRef.current = es;
    setSseState("connecting");
    es.addEventListener("hello", () => setSseState("open"));
    es.addEventListener("validation", (e) => {
      try {
        const evt = JSON.parse(e.data);
        setTicker((prev) => [{ ...evt, _rx: Date.now() }, ...prev].slice(0, 8));
      } catch (err) {
        // eslint-disable-next-line no-console
        console.warn("PublicExplorer ticker parse failed:", err);
      }
    });
    es.onerror = () => setSseState("closed");
    return () => es.close();
  }, []);

  const runSample = async (sample) => {
    setBusy(sample.key);
    try {
      const res = await fetch(`${BACKEND_URL}/api/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          framework: sample.framework,
          payload: sample.payload,
          source: `explorer:${sample.key}`,
        }),
      });
      const j = await res.json();
      setLastReport(j);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("PublicExplorer sample validation failed:", err);
    }
    finally {
      setBusy(null);
    }
  };

  return (
    <section className="border-t border-white/5 relative overflow-hidden">
      <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-20">
        <div className="flex items-end justify-between gap-6 flex-wrap mb-10">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-2">
              PUBLIC EXPLORER · NO SIGN-IN · NO STORAGE
            </div>
            <h2 className="font-serif font-light text-3xl lg:text-4xl text-white leading-tight max-w-3xl">
              Klick, valide, sieh den Live-Ticker leuchten.
            </h2>
            <p className="text-slate-400 mt-3 max-w-2xl">
              Drei sofort einsatzbereite Beispiel-Payloads gegen GDPR, DORA und
              den EU AI Act. Jede Validierung erscheint sofort im flüchtigen
              Live-Ticker rechts — schließe den Tab, und alles ist weg.
            </p>
          </div>
          <div className="flex items-center gap-3 text-[11px] font-mono">
            <Radio
              size={12}
              className={sseState === "open" ? "text-emerald-400 animate-pulse" : "text-slate-500"}
            />
            <span className="text-slate-500">SSE</span>
            <span className={sseState === "open" ? "text-emerald-400" : "text-slate-500"}>
              {sseState.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {SAMPLES.map((s) => (
              <div
                key={s.key}
                data-testid={`explorer-sample-${s.key}`}
                className="border border-white/10 bg-black/40 rounded-md p-5 flex flex-col hover:border-amber-500/40 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <ShieldCheck size={13} className="text-amber-400" />
                  <span className="font-mono text-[11px] uppercase tracking-wider text-amber-400">
                    {s.framework}
                  </span>
                </div>
                <div className="mt-2 text-[15px] font-serif text-white">{s.label}</div>
                <div className="mt-2 text-[11px] text-slate-500 leading-relaxed">
                  {s.hint}
                </div>
                <pre className="mt-3 flex-1 text-[10px] font-mono text-emerald-300/80 bg-black/60 border border-white/10 rounded p-2 overflow-hidden max-h-32">
                  {JSON.stringify(s.payload, null, 2)}
                </pre>
                <button
                  onClick={() => runSample(s)}
                  disabled={busy === s.key}
                  data-testid={`explorer-run-${s.key}`}
                  className="mt-3 inline-flex items-center justify-center gap-2 px-3 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-mono text-[10px] uppercase tracking-wider rounded"
                >
                  <Play size={11} />
                  {busy === s.key ? "validating…" : "Try it"}
                </button>
              </div>
            ))}
          </div>

          {/* Live Ticker mini */}
          <div className="border border-white/10 bg-black/40 rounded-md">
            <div className="p-4 border-b border-white/10 flex items-center gap-3">
              <Radio
                size={13}
                className={sseState === "open" ? "text-emerald-400 animate-pulse" : "text-slate-500"}
              />
              <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300">
                Live Ticker
              </span>
              <Link
                to="/validator"
                className="ml-auto text-[10px] font-mono uppercase tracking-wider text-slate-400 hover:text-amber-400 flex items-center gap-1"
                data-testid="explorer-open-validator"
              >
                open full validator <ArrowUpRight size={11} />
              </Link>
            </div>
            <div className="p-3 space-y-2 min-h-[280px]">
              {ticker.length === 0 && (
                <div className="text-[11px] font-mono text-slate-500 text-center py-10">
                  press <span className="text-amber-400">Try it</span> to see this ticker light up
                </div>
              )}
              {ticker.map((evt, idx) => (
                <div
                  key={idx}
                  data-testid={`explorer-ticker-${idx}`}
                  className={`border border-white/5 rounded p-2 ${
                    evt.status === "FAIL" ? "pnia-fail-pulse" : ""
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Pill status={evt.status} />
                    <span className="text-[10px] font-mono text-amber-400">
                      {evt.framework || "—"}
                    </span>
                    <span className="ml-auto text-[9px] font-mono text-slate-500">
                      {(evt.at || "").slice(11, 19)}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] font-mono text-slate-400">
                    <span>score {evt.score}</span>
                    <span>· missing {evt.missing_required}</span>
                    <span className="ml-auto text-slate-500 truncate max-w-[120px]">{evt.source}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {lastReport && (
          <div className="mt-6 border border-white/10 bg-black/40 rounded-md p-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300">
                Last result
              </span>
              <Pill status={lastReport.status} />
              <span className="text-[11px] font-mono text-amber-400">
                {lastReport.framework?.code || "—"}
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                score {lastReport.score}%
              </span>
              <span className="text-[10px] font-mono text-slate-500 ml-auto">
                {lastReport.mode} · {lastReport.counts?.missing_required || 0} missing ·{" "}
                {lastReport.counts?.recommended_warnings || 0} warnings
              </span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
