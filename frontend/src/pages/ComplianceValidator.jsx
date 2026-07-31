import React, { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ShieldCheck,
  Activity,
  Play,
  Radio,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Info,
  Trash2,
  Filter,
  Server,
  Volume2,
  VolumeX,
  FileDown,
  ChevronRight,
  Package,
} from "lucide-react";
import FrameworkDrawer from "../components/FrameworkDrawer";
import ChainOfCustodyLedger from "../components/ChainOfCustodyLedger";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL ||
  (typeof window !== "undefined" ? window.location.origin : "");

const DEFAULT_PAYLOAD = {
  controller: "PNIA Reference Ltd.",
  processing_purpose: "Provide EUDI Wallet reference services",
  legal_basis: "Art. 6(1)(b) GDPR — contract",
  data_categories: ["identity_attributes", "audit_hash"],
  retention_period: "P90D",
  subject_rights_endpoint: "/api/gdpr/rights",
  breach_notification_process: "72h to lead DPA + downstream controllers",
};

const STATUS_COLOR = {
  PASS: "text-emerald-400 border-emerald-500/50 bg-emerald-500/10",
  PASS_WITH_WARNINGS: "text-amber-400 border-amber-500/50 bg-amber-500/10",
  FAIL: "text-red-400 border-red-500/50 bg-red-500/10",
  UNKNOWN_FRAMEWORK: "text-slate-400 border-slate-500/50 bg-slate-500/10",
};

function StatusPill({ status }) {
  const cls = STATUS_COLOR[status] || STATUS_COLOR.UNKNOWN_FRAMEWORK;
  const Icon =
    status === "PASS"
      ? CheckCircle2
      : status === "PASS_WITH_WARNINGS"
      ? AlertTriangle
      : status === "FAIL"
      ? XCircle
      : Info;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm border font-mono text-[10px] uppercase tracking-wider ${cls}`}
    >
      <Icon size={12} strokeWidth={1.8} />
      {status || "—"}
    </span>
  );
}

export default function ComplianceValidator() {
  const { t } = useTranslation();
  const [frameworks, setFrameworks] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedFramework, setSelectedFramework] = useState("GDPR");
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [payloadText, setPayloadText] = useState(
    JSON.stringify(DEFAULT_PAYLOAD, null, 2)
  );
  const [report, setReport] = useState(null);
  const [running, setRunning] = useState(false);
  const [ticker, setTicker] = useState([]); // ephemeral, lives only in this tab
  const [sseState, setSseState] = useState("connecting"); // connecting|open|closed
  const [error, setError] = useState(null);
  const esRef = useRef(null);
  const [drawerCode, setDrawerCode] = useState(null);
  const [soundOn, setSoundOn] = useState(true);
  const [pdfBusy, setPdfBusy] = useState(false);
  const [bundleBusy, setBundleBusy] = useState(false);
  const [bundleFrameworks, setBundleFrameworks] = useState([]); // codes selected for bundle
  const audioCtxRef = useRef(null);
  const soundOnRef = useRef(true);
  useEffect(() => {
    soundOnRef.current = soundOn;
  }, [soundOn]);

  // ---- Web Audio API pling (no external file) ----
  const playTone = (status) => {
    if (!soundOnRef.current) return;
    try {
      if (!audioCtxRef.current) {
        // eslint-disable-next-line no-undef
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        audioCtxRef.current = new AC();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === "suspended") ctx.resume();
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      const isFail = status === "FAIL";
      osc.type = "sine";
      // soft, professional plings — different pitch per outcome
      const freq = isFail ? 220 : status === "PASS" ? 880 : 660;
      osc.frequency.setValueAtTime(freq, now);
      if (isFail) osc.frequency.linearRampToValueAtTime(180, now + 0.35);
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.linearRampToValueAtTime(0.14, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.45);
      osc.start(now);
      osc.stop(now + 0.5);
    } catch (err) {
      // Audio context can fail in unsupported browsers or when user hasn't
      // interacted with the page yet — non-fatal.
      // eslint-disable-next-line no-console
      console.warn("Ticker tone failed:", err);
    }
  };

  // ---- initial data ----
  useEffect(() => {
    (async () => {
      try {
        const [fr, st] = await Promise.all([
          fetch(`${BACKEND_URL}/api/validate/frameworks?limit=500`).then((r) =>
            r.json()
          ),
          fetch(`${BACKEND_URL}/api/validate/stats`).then((r) => r.json()),
        ]);
        setFrameworks(fr.frameworks || []);
        setStats(st);
      } catch (e) {
        setError(`Failed to load frameworks: ${e.message}`);
      }
    })();
  }, []);

  // ---- SSE live ticker (ephemeral: no localStorage, no persistence) ----
  useEffect(() => {
    const url = `${BACKEND_URL}/api/validate/stream`;
    const es = new EventSource(url);
    esRef.current = es;
    setSseState("connecting");
    es.addEventListener("hello", () => setSseState("open"));
    es.addEventListener("validation", (e) => {
      try {
        const evt = JSON.parse(e.data);
        playTone(evt.status);
        setTicker((prev) =>
          [{ ...evt, _rx: Date.now(), _pulse: evt.status === "FAIL" }, ...prev].slice(0, 50)
        );
      } catch (err) {
        // eslint-disable-next-line no-console
        console.warn("Ticker validation event parse failed:", err);
      }
    });
    es.addEventListener("replay", (e) => {
      try {
        const evt = JSON.parse(e.data);
        setTicker((prev) =>
          [...prev, { ...evt, _rx: Date.now(), _replay: true }].slice(0, 50)
        );
      } catch (err) {
        // eslint-disable-next-line no-console
        console.warn("Ticker replay event parse failed:", err);
      }
    });
    es.onerror = () => setSseState("closed");
    return () => {
      es.close();
      esRef.current = null;
    };
    // The SSE connection must be established exactly ONCE per mount. `playTone`
    // is intentionally captured via closure; it reads the latest `soundOn` via
    // `soundOnRef.current`, so no stale-closure bug exists. Setters (setTicker,
    // setSseState) are stable per React's contract.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- categories for the filter dropdown ----
  const categories = useMemo(() => {
    const set = new Set(frameworks.map((f) => f.category));
    return ["all", ...Array.from(set).sort()];
  }, [frameworks]);

  const filteredFrameworks = useMemo(() => {
    const q = search.trim().toLowerCase();
    return frameworks
      .filter((f) => category === "all" || f.category === category)
      .filter(
        (f) =>
          !q ||
          f.code.toLowerCase().includes(q) ||
          f.name.toLowerCase().includes(q) ||
          f.regulator.toLowerCase().includes(q)
      );
  }, [frameworks, category, search]);

  const specialised = new Set(stats?.specialised_validators || []);

  // ---- validate ----
  const runValidate = async () => {
    setRunning(true);
    setError(null);
    try {
      let payload;
      try {
        payload = JSON.parse(payloadText || "{}");
      } catch (e) {
        throw new Error(`Payload is not valid JSON: ${e.message}`);
      }
      const res = await fetch(`${BACKEND_URL}/api/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          framework: selectedFramework,
          payload,
          source: "dashboard",
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const j = await res.json();
      setReport(j);
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  };

  const clearTicker = () => setTicker([]);

  const downloadPdf = async () => {
    if (!report) return;
    setPdfBusy(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/validate/report.pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const code = report?.framework?.code || "framework";
      a.download = `pnia-compliance-${code}-${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    } catch (e) {
      setError(`PDF export failed: ${e.message}`);
    } finally {
      setPdfBusy(false);
    }
  };

  const toggleBundle = (code) => {
    setBundleFrameworks((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code].slice(0, 20)
    );
  };

  const downloadBundle = async () => {
    if (bundleFrameworks.length === 0) return;
    setBundleBusy(true);
    setError(null);
    try {
      let payload;
      try {
        payload = JSON.parse(payloadText || "{}");
      } catch (e) {
        throw new Error(`Payload is not valid JSON: ${e.message}`);
      }
      // 1) batch-validate to get real reports
      const batch = await fetch(`${BACKEND_URL}/api/validate/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          frameworks: bundleFrameworks,
          payload,
          source: "bundle-download",
        }),
      }).then((r) => r.json());
      // 2) send them to the bundle PDF renderer
      const res = await fetch(`${BACKEND_URL}/api/validate/report-bundle.pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reports: batch.reports || [] }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pnia-compliance-bundle-${bundleFrameworks.length}-${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    } catch (e) {
      setError(`Bundle failed: ${e.message}`);
    } finally {
      setBundleBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-10 text-slate-200">
      {/* --------- Header --------- */}
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6 pb-6 border-b border-white/10">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.28em] text-amber-500/80 mb-2">
            PNIA · Stateless · Zero Storage
          </div>
          <h1 className="text-3xl lg:text-4xl font-serif tracking-tight">
            Compliance Validation Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-2 max-w-3xl">
            Real-time, database-less validation of arbitrary JSON payloads
            against{" "}
            <span className="text-amber-400 font-mono">
              {stats?.total || "…"}
            </span>{" "}
            real compliance frameworks. Specialised rule engines for GDPR,
            DORA, EU AI Act, DMA, DSA, NIS2, eIDAS 2 and CRA — every other
            framework receives a generic Governance Skeleton. The Live Ticker
            below streams validations via Server-Sent Events; closing this tab
            wipes the entire history.
          </p>
        </div>
        <div className="flex flex-col gap-2 items-end">
          <div className="flex items-center gap-2 text-[11px] font-mono">
            <span className="text-slate-500">SSE</span>
            <span
              className={
                sseState === "open"
                  ? "text-emerald-400"
                  : sseState === "connecting"
                  ? "text-amber-400"
                  : "text-red-400"
              }
            >
              ● {sseState.toUpperCase()}
            </span>
          </div>
          <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500">
            <Server size={12} /> stateless • no DB • Art. 12 EU AI Act
          </div>
        </div>
      </div>

      {/* --------- Stat strip --------- */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
          <StatCard label="Frameworks total" value={stats.total} />
          <StatCard
            label="Specialised validators"
            value={stats.specialised_validators.length}
          />
          <StatCard
            label="Categories"
            value={Object.keys(stats.categories).length}
          />
          <StatCard
            label="Jurisdictions"
            value={Object.keys(stats.jurisdictions).length}
          />
        </div>
      )}

      {/* --------- Two-column: form + ticker --------- */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_400px] gap-6 mt-8">
        {/* -- Left: framework picker + payload -- */}
        <div className="space-y-4">
          <div className="border border-white/10 bg-black/40 backdrop-blur rounded-md">
            <div className="p-4 border-b border-white/10 flex items-center gap-3 flex-wrap">
              <ShieldCheck size={16} className="text-amber-400" />
              <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300">
                Framework Selection
              </span>
              <div className="ml-auto flex items-center gap-2">
                <div className="relative">
                  <Filter
                    size={11}
                    className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-500"
                  />
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    data-testid="fw-category-select"
                    className="pl-6 pr-3 py-1.5 bg-black/50 border border-white/10 rounded text-[11px] font-mono text-slate-200 focus:border-amber-500/60 outline-none"
                  >
                    {categories.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search 251 frameworks…"
                  data-testid="fw-search"
                  className="px-3 py-1.5 bg-black/50 border border-white/10 rounded text-[11px] font-mono text-slate-200 w-52 focus:border-amber-500/60 outline-none"
                />
              </div>
            </div>
            <div className="max-h-72 overflow-y-auto divide-y divide-white/5">
              {filteredFrameworks.slice(0, 200).map((f) => (
                <div
                  key={f.code + f.name}
                  className={`w-full flex items-center gap-3 hover:bg-white/5 transition-colors ${
                    selectedFramework === f.code ? "bg-amber-500/10" : ""
                  }`}
                >
                  <button
                    data-testid={`fw-row-${f.code}`}
                    onClick={() => setSelectedFramework(f.code)}
                    className="flex-1 text-left px-4 py-2 flex items-center gap-3"
                  >
                    <span
                      className={`inline-block w-1 h-6 rounded-full ${
                        specialised.has(f.code.toUpperCase())
                          ? "bg-amber-500"
                          : "bg-slate-600"
                      }`}
                    />
                    <span className="font-mono text-[11px] text-amber-400 w-24 truncate">
                      {f.code}
                    </span>
                    <span className="flex-1 text-[12px] text-slate-300 truncate">
                      {f.name}
                    </span>
                    <span className="hidden md:inline text-[10px] font-mono text-slate-500 w-28 text-right truncate">
                      {f.regulator}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 w-24 text-right">
                      {f.category}
                    </span>
                  </button>
                  <label
                    className="inline-flex items-center px-2 cursor-pointer select-none"
                    title="Add to bundle"
                  >
                    <input
                      type="checkbox"
                      checked={bundleFrameworks.includes(f.code)}
                      onChange={() => toggleBundle(f.code)}
                      data-testid={`fw-bundle-${f.code}`}
                      className="h-3 w-3 accent-emerald-500"
                    />
                  </label>
                  <button
                    onClick={() => setDrawerCode(f.code)}
                    data-testid={`fw-detail-${f.code}`}
                    title="Open detail drawer"
                    className="pr-3 py-2 text-slate-500 hover:text-amber-400"
                  >
                    <ChevronRight size={14} />
                  </button>
                </div>
              ))}
              {filteredFrameworks.length === 0 && (
                <div className="p-6 text-center text-slate-500 text-sm">
                  no framework matches
                </div>
              )}
            </div>
            <div className="p-3 border-t border-white/10 text-[10px] font-mono text-slate-500 flex items-center gap-3 flex-wrap">
              <span>
                Selected:{" "}
                <span className="text-amber-400">{selectedFramework}</span>{" "}
                {specialised.has(selectedFramework.toUpperCase())
                  ? "· SPECIALISED rule engine"
                  : "· generic Governance Skeleton"}
              </span>
              <span className="ml-auto flex items-center gap-2">
                <span>
                  Bundle:{" "}
                  <span className="text-emerald-400">
                    {bundleFrameworks.length}
                  </span>{" "}
                  / 20
                </span>
                <button
                  onClick={downloadBundle}
                  disabled={bundleBusy || bundleFrameworks.length === 0}
                  data-testid="btn-download-bundle"
                  className="inline-flex items-center gap-1.5 px-2 py-1 border border-emerald-500/50 text-emerald-400 hover:bg-emerald-500 hover:text-black disabled:opacity-40 text-[10px] font-mono uppercase tracking-wider rounded"
                  title="Combined signed PDF booklet with TOC"
                >
                  <Package size={11} />
                  {bundleBusy ? "building…" : "signed bundle PDF"}
                </button>
                {bundleFrameworks.length > 0 && (
                  <button
                    onClick={() => setBundleFrameworks([])}
                    data-testid="btn-clear-bundle"
                    className="text-[10px] font-mono uppercase tracking-wider text-slate-500 hover:text-red-400"
                  >
                    clear
                  </button>
                )}
              </span>
            </div>
          </div>

          {/* Payload editor */}
          <div className="border border-white/10 bg-black/40 rounded-md">
            <div className="p-4 border-b border-white/10 flex items-center gap-3">
              <Play size={14} className="text-amber-400" />
              <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300">
                JSON Payload (in-memory only)
              </span>
              <button
                onClick={() =>
                  setPayloadText(JSON.stringify(DEFAULT_PAYLOAD, null, 2))
                }
                data-testid="payload-reset"
                className="ml-auto text-[10px] font-mono uppercase tracking-wider text-slate-400 hover:text-amber-400 flex items-center gap-1"
              >
                <RefreshCw size={11} /> reset
              </button>
            </div>
            <textarea
              value={payloadText}
              onChange={(e) => setPayloadText(e.target.value)}
              data-testid="payload-editor"
              rows={14}
              spellCheck={false}
              className="w-full bg-black/60 p-4 font-mono text-[11px] text-emerald-300 outline-none"
            />
            <div className="p-3 border-t border-white/10 flex items-center gap-3">
              <button
                onClick={runValidate}
                disabled={running}
                data-testid="btn-validate"
                className="px-4 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-mono text-[11px] uppercase tracking-wider rounded flex items-center gap-2"
              >
                <Play size={12} />
                {running ? "validating…" : `Validate against ${selectedFramework}`}
              </button>
              <span className="text-[10px] font-mono text-slate-500">
                POST /api/validate · stateless passthrough
              </span>
              {error && (
                <span className="ml-auto text-[11px] text-red-400 font-mono">
                  {error}
                </span>
              )}
            </div>
          </div>

          {/* Report */}
          {report && (
            <div
              data-testid="report-card"
              className="border border-white/10 bg-black/40 rounded-md"
            >
              <div className="p-4 border-b border-white/10 flex items-center gap-3 flex-wrap">
                <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300">
                  Validation Report
                </span>
                <StatusPill status={report.status} />
                <span className="text-[11px] font-mono text-slate-400">
                  score {report.score}%
                </span>
                <button
                  onClick={downloadPdf}
                  disabled={pdfBusy}
                  data-testid="btn-download-pdf"
                  className="ml-auto inline-flex items-center gap-1.5 px-2 py-1 border border-amber-500/50 text-amber-400 hover:bg-amber-500 hover:text-black text-[10px] font-mono uppercase tracking-wider rounded"
                  title="Signed A4 PDF · ES256 JWS"
                >
                  <FileDown size={11} />
                  {pdfBusy ? "signing…" : "signed PDF"}
                </button>
                <span className="text-[10px] font-mono text-slate-500 basis-full mt-1">
                  {report.mode} · {report.engine}
                </span>
              </div>
              <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-wider text-emerald-400/80 mb-2">
                    Covered ({report.covered?.length || 0})
                  </div>
                  <ul className="space-y-1">
                    {(report.covered || []).map((c) => (
                      <li
                        key={c.field}
                        className="flex items-center gap-2 text-[11px] font-mono text-emerald-300"
                      >
                        <CheckCircle2 size={11} /> {c.field}
                      </li>
                    ))}
                    {(!report.covered || report.covered.length === 0) && (
                      <li className="text-[11px] text-slate-500">—</li>
                    )}
                  </ul>
                </div>
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-wider text-red-400/80 mb-2">
                    Missing required ({report.missing?.length || 0})
                  </div>
                  <ul className="space-y-1">
                    {(report.missing || []).map((c) => (
                      <li
                        key={c.field}
                        className="flex items-start gap-2 text-[11px] font-mono text-red-300"
                      >
                        <XCircle size={11} className="mt-0.5" />
                        <span>
                          <span className="text-red-400">{c.field}</span>{" "}
                          <span className="text-slate-500">— {c.hint}</span>
                        </span>
                      </li>
                    ))}
                    {(!report.missing || report.missing.length === 0) && (
                      <li className="text-[11px] text-slate-500">—</li>
                    )}
                  </ul>
                </div>
              </div>
              {report.warnings && report.warnings.length > 0 && (
                <div className="px-4 pb-4">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-amber-400/80 mb-2">
                    Recommended ({report.warnings.length})
                  </div>
                  <ul className="space-y-1">
                    {report.warnings.map((c) => (
                      <li
                        key={c.field}
                        className="flex items-start gap-2 text-[11px] font-mono text-amber-300"
                      >
                        <AlertTriangle size={11} className="mt-0.5" />
                        <span>
                          <span className="text-amber-400">{c.field}</span>{" "}
                          <span className="text-slate-500">— {c.hint}</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {report.framework && (
                <div className="px-4 pb-4 pt-3 border-t border-white/5 text-[10px] font-mono text-slate-500 flex flex-wrap items-center gap-x-4 gap-y-1">
                  <span>{report.framework.code}</span>
                  <span>{report.framework.regulator}</span>
                  <span>{report.framework.jurisdiction}</span>
                  <a
                    href={report.framework.source}
                    target="_blank"
                    rel="noreferrer"
                    className="ml-auto text-amber-400 hover:text-amber-300"
                  >
                    Source ↗
                  </a>
                </div>
              )}
            </div>
          )}
        </div>

        {/* -- Right: Live Ticker -- */}
        <div className="border border-white/10 bg-black/40 rounded-md flex flex-col h-[560px]">
          <div className="p-4 border-b border-white/10 flex items-center gap-3">
            <Radio
              size={14}
              className={`${
                sseState === "open"
                  ? "text-emerald-400 animate-pulse"
                  : "text-slate-500"
              }`}
            />
            <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300">
              Live Ticker (ephemeral)
            </span>
            <button
              onClick={() => setSoundOn((s) => !s)}
              data-testid="btn-toggle-sound"
              title={soundOn ? "Mute pling" : "Unmute pling"}
              className="ml-auto p-1 rounded text-slate-400 hover:text-amber-400 border border-white/10 hover:border-amber-500/50"
            >
              {soundOn ? <Volume2 size={11} /> : <VolumeX size={11} />}
            </button>
            <button
              onClick={clearTicker}
              data-testid="btn-clear-ticker"
              className="text-[10px] font-mono uppercase tracking-wider text-slate-500 hover:text-red-400 flex items-center gap-1"
            >
              <Trash2 size={11} /> clear
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {ticker.length === 0 && (
              <div className="text-[11px] font-mono text-slate-500 text-center py-8">
                <Activity size={20} className="mx-auto mb-2 opacity-50" />
                Waiting for validations… close this tab to wipe history.
              </div>
            )}
            {ticker.map((evt, idx) => (
              <div
                key={idx}
                data-testid={`ticker-row-${idx}`}
                className={`border border-white/5 rounded p-2 hover:border-amber-500/30 transition-colors ${
                  evt._pulse ? "pnia-fail-pulse" : ""
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <StatusPill status={evt.status} />
                  <span className="text-[10px] font-mono text-amber-400">
                    {evt.framework || "—"}
                  </span>
                  {evt._replay && (
                    <span className="text-[9px] font-mono text-slate-500">
                      REPLAY
                    </span>
                  )}
                  <span className="ml-auto text-[9px] font-mono text-slate-500">
                    {(evt.at || "").slice(11, 19) || ""}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[10px] font-mono text-slate-400">
                  <span>score {evt.score}</span>
                  <span>· missing {evt.missing_required}</span>
                  <span>· warn {evt.recommended_warnings}</span>
                  <span className="ml-auto text-slate-500">{evt.source}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="p-3 border-t border-white/10 text-[9px] font-mono text-slate-500 flex items-center gap-2">
            <Info size={11} /> in-process buffer · no DB · disappears on tab close
          </div>
        </div>
      </div>

      {/* --------- Compliance footer --------- */}
      <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-3">
        <ComplianceCard
          title="EU AI Act (2024/1689)"
          detail="Art. 12 record-keeping · Art. 50 transparency. No AI decision in the engine — pure rule-based, deterministic."
        />
        <ComplianceCard
          title="Digital Markets Act (2022/1925)"
          detail="Open API surface, machine-readable JSON, no vendor lock-in. Batch endpoint supports up to 20 frameworks in parallel."
        />
        <ComplianceCard
          title="Digital Services Act (2022/2065)"
          detail="Every report carries a statement of reasons (hint field per rule) — Art. 17 DSA style."
        />
      </div>
      {/* --------- Chain-of-Custody Ledger --------- */}
      <div className="mt-8">
        <ChainOfCustodyLedger />
      </div>

      {/* --------- Framework Detail Drawer --------- */}
      {drawerCode && (
        <FrameworkDrawer code={drawerCode} onClose={() => setDrawerCode(null)} />
      )}
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="border border-white/10 bg-black/40 rounded-md p-4">
      <div className="text-[9px] font-mono uppercase tracking-[0.24em] text-slate-500">
        {label}
      </div>
      <div className="text-2xl font-serif tracking-tight text-amber-400 mt-1">
        {value}
      </div>
    </div>
  );
}

function ComplianceCard({ title, detail }) {
  return (
    <div className="border border-white/10 bg-black/40 rounded-md p-4">
      <div className="text-[10px] font-mono uppercase tracking-[0.24em] text-amber-500/80 mb-2">
        {title}
      </div>
      <div className="text-[12px] text-slate-400 leading-relaxed">{detail}</div>
    </div>
  );
}
