import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { CheckCircle2, XCircle, Download, RefreshCw, Loader2, Trash2, ScrollText, Brain } from "lucide-react";
import { toast } from "sonner";
import {
  getMetrics,
  getAuditLog,
  verifyAuditChain,
  runErasure,
  getAiActTransparency,
  dsaPdfUrl,
} from "../lib/api";
import { DowngradePanel } from "../components/DowngradePanel";
import { useAuth } from "../lib/auth";

function Stat({ label, value, tint = "amber", testId }) {
  const cls =
    tint === "amber"
      ? "border-amber-500/25 text-amber-500"
      : tint === "blue"
      ? "border-blue-500/25 text-blue-400"
      : tint === "emerald"
      ? "border-emerald-500/25 text-emerald-400"
      : "border-white/10 text-white";
  return (
    <div className={`border ${cls} bg-[#0a0f19] rounded-sm p-5`} data-testid={testId}>
      <div className="text-[9px] font-mono uppercase tracking-[0.2em] text-slate-500 mb-2">{label}</div>
      <div className="font-serif text-4xl font-light text-white">{value}</div>
    </div>
  );
}

export default function Compliance() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [audit, setAudit] = useState([]);
  const [chainRes, setChainRes] = useState(null);
  const [erasureHash, setErasureHash] = useState("");
  const [busy, setBusy] = useState(false);
  const [ai, setAi] = useState(null);

  const refresh = async () => {
    const [m, a, aiT] = await Promise.all([getMetrics(), getAuditLog(), getAiActTransparency()]);
    setMetrics(m);
    setAudit(a);
    setAi(aiT);
  };

  useEffect(() => {
    refresh();
  }, []);

  const doVerifyChain = async () => {
    setBusy(true);
    try {
      const r = await verifyAuditChain();
      setChainRes(r);
      toast[r.valid ? "success" : "error"](r.valid ? t("compliance.chain_ok") : t("compliance.chain_bad"));
    } finally {
      setBusy(false);
    }
  };

  const doErasure = async () => {
    if (!erasureHash) return;
    if (!user) {
      toast.error("Sign in required for GDPR erasure");
      return;
    }
    setBusy(true);
    try {
      const r = await runErasure(erasureHash);
      toast.success(`Deleted ${r.deleted} records`);
      setErasureHash("");
      refresh();
    } catch (e) {
      if (e?.response?.status === 401) toast.error("Authentication required");
      else toast.error("Erasure failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-3">
            COMPLIANCE COCKPIT
          </div>
          <h1 className="font-serif font-light text-4xl lg:text-5xl text-white leading-tight mb-2">
            {t("compliance.title")}
          </h1>
          <p className="text-slate-400 max-w-2xl">{t("compliance.subtitle")}</p>
        </div>
        <button
          onClick={refresh}
          data-testid="compliance-refresh"
          className="p-2.5 border border-white/10 hover:border-amber-500/50 rounded-sm text-slate-300 hover:text-amber-500 transition-colors"
        >
          <RefreshCw size={14} strokeWidth={1.6} />
        </button>
      </div>

      {/* Metric bento */}
      <div className="bento-tight mb-10">
        <div className="col-span-12 md:col-span-4">
          <Stat label={t("compliance.credentials")} value={metrics?.total_credentials_issued ?? "—"} tint="amber" testId="stat-credentials" />
        </div>
        <div className="col-span-12 md:col-span-4">
          <Stat label={t("compliance.verifications")} value={metrics?.total_presentations_verified ?? "—"} tint="blue" testId="stat-verifications" />
        </div>
        <div className="col-span-12 md:col-span-4">
          <Stat
            label={t("compliance.success_rate")}
            value={metrics ? `${(metrics.verification_success_rate * 100).toFixed(1)}%` : "—"}
            tint="emerald"
            testId="stat-success-rate"
          />
        </div>
        <div className="col-span-6 md:col-span-3">
          <Stat label={t("compliance.loa_high")} value={metrics?.active_loa_high ?? 0} tint="amber" testId="stat-loa-high" />
        </div>
        <div className="col-span-6 md:col-span-3">
          <Stat label={t("compliance.loa_sub")} value={metrics?.active_loa_substantial ?? 0} tint="blue" testId="stat-loa-sub" />
        </div>
        <div className="col-span-6 md:col-span-3">
          <Stat label={t("compliance.loa_low")} value={metrics?.active_loa_low ?? 0} testId="stat-loa-low" />
        </div>
        <div className="col-span-6 md:col-span-3">
          <Stat label={t("compliance.downgrades")} value={metrics?.downgrade_incidents ?? 0} testId="stat-downgrades" />
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6 mb-10">
        {/* Audit-log */}
        <div className="col-span-12 lg:col-span-8 border border-white/10 bg-[#0a0f19] rounded-sm">
          <div className="flex items-center justify-between border-b border-white/5 px-5 py-3">
            <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500">
              <ScrollText size={12} strokeWidth={1.6} /> {t("compliance.audit_log")}
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={doVerifyChain}
                disabled={busy}
                data-testid="verify-chain-btn"
                className="text-[11px] font-mono px-3 py-1.5 border border-blue-500/50 hover:bg-blue-500 hover:text-black text-blue-400 rounded-sm transition-colors disabled:opacity-40"
              >
                {busy ? <Loader2 size={11} className="inline animate-spin mr-1" /> : null}
                {t("compliance.verify_chain")}
              </button>
              {chainRes && (
                <div
                  data-testid="chain-verify-badge"
                  className={`inline-flex items-center gap-1 text-[10px] font-mono px-2 py-1 rounded-sm ${
                    chainRes.valid
                      ? "text-emerald-400 border border-emerald-500/40 bg-emerald-500/10"
                      : "text-red-400 border border-red-500/40 bg-red-500/10"
                  }`}
                >
                  {chainRes.valid ? <CheckCircle2 size={10} /> : <XCircle size={10} />}
                  {chainRes.checked} entries
                </div>
              )}
            </div>
          </div>
          <div className="max-h-[440px] overflow-y-auto">
            <table className="w-full text-[11.5px] font-mono">
              <thead className="sticky top-0 bg-[#0a0f19]">
                <tr className="text-slate-500 uppercase text-[9px] tracking-widest">
                  <th className="text-left px-4 py-2 font-medium">Timestamp</th>
                  <th className="text-left px-4 py-2 font-medium">Event</th>
                  <th className="text-left px-4 py-2 font-medium">Actor</th>
                  <th className="text-left px-4 py-2 font-medium">Hash</th>
                </tr>
              </thead>
              <tbody>
                {audit.map((row) => (
                  <tr key={row.hash || row.timestamp} className="border-t border-white/5 hover:bg-white/[0.02]" data-testid={`audit-row-${row.hash?.slice(0, 8)}`}>
                    <td className="px-4 py-2 text-slate-500 whitespace-nowrap">{row.timestamp?.slice(0, 19)}</td>
                    <td className="px-4 py-2 text-amber-400">{row.event_type}</td>
                    <td className="px-4 py-2 text-slate-300">{row.actor}</td>
                    <td className="px-4 py-2 text-blue-400 truncate max-w-[220px]">{row.hash?.slice(0, 18)}…</td>
                  </tr>
                ))}
                {!audit.length && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-slate-500">
                      No audit events yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Side panel */}
        <div className="col-span-12 lg:col-span-4 space-y-4">
          <div className="border border-white/10 bg-[#0a0f19] p-5 rounded-sm">
            <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.22em] text-blue-400 mb-3">
              <Brain size={12} strokeWidth={1.6} /> AI Act Art. 13
            </div>
            <div className="text-xs text-slate-400 mb-4 leading-relaxed">
              {ai?.regulation}
              <br />
              <span className="text-slate-500">System role:</span> {ai?.system_role}
            </div>
            <div data-testid="ai-events-count" className="text-3xl font-serif font-light text-white">
              {ai?.events?.length ?? 0}
              <span className="text-xs font-mono text-slate-500 ml-2 uppercase tracking-wider">events</span>
            </div>
          </div>

          <div className="border border-white/10 bg-[#0a0f19] p-5 rounded-sm">
            <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-3">
              <Trash2 size={12} strokeWidth={1.6} /> GDPR Art. 17
            </div>
            <input
              value={erasureHash}
              onChange={(e) => setErasureHash(e.target.value)}
              placeholder={t("compliance.erasure_hint")}
              data-testid="erasure-input"
              className="w-full bg-[#050a12] border border-white/10 focus:border-amber-500/60 rounded-sm px-2.5 py-1.5 text-xs font-mono text-white outline-none mb-3 transition-colors"
            />
            <button
              onClick={doErasure}
              disabled={busy || !erasureHash}
              data-testid="run-erasure-btn"
              className="w-full text-[11px] font-mono uppercase tracking-wider border border-red-500/50 hover:bg-red-500 hover:text-white text-red-400 rounded-sm py-1.5 transition-colors disabled:opacity-40"
            >
              {t("compliance.run_erasure")}
            </button>
          </div>

          <a
            href={dsaPdfUrl()}
            target="_blank"
            rel="noreferrer"
            data-testid="dsa-pdf-link"
            className="flex items-center justify-center gap-2 border border-amber-500 hover:bg-amber-500 hover:text-black text-amber-400 rounded-sm py-2.5 text-[13px] font-medium transition-colors"
          >
            <Download size={13} strokeWidth={1.7} />
            {t("compliance.dsa_export")}
          </a>
        </div>
      </div>

      {/* AI Act Art. 14 Downgrade Panel */}
      <DowngradePanel />
    </div>
  );
}
