import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Split,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Loader2,
  Send,
  Lock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import {
  hnossInfo,
  hnossPolicies,
  hnossSetMode,
  hnossTransfer,
  hnossTransfers,
} from "../lib/api";

const STATUS_STYLE = {
  ACCEPTED: { color: "text-emerald-400", border: "border-emerald-500/40", icon: CheckCircle2 },
  REJECTED: { color: "text-red-400", border: "border-red-500/40", icon: XCircle },
  PENDING: { color: "text-amber-400", border: "border-amber-500/40", icon: AlertTriangle },
};

export default function HNOSSBridge() {
  const [info, setInfo] = useState(null);
  const [policies, setPolicies] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    source_domain: "mcci-internal",
    target_domain: "eu-commission",
    data_classification: "RESTRICTED",
    batch_size: 1,
    jurisdiction: "EU",
    identity_whitelisted: true,
  });

  const load = useCallback(async () => {
    try {
      const [i, p, t] = await Promise.all([hnossInfo(), hnossPolicies(), hnossTransfers()]);
      setInfo(i);
      setPolicies(p.policies || []);
      setTransfers(t.transfers || []);
    } catch (e) {
      toast.error("HNOSS Bridge konnte nicht geladen werden");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const changeMode = async (mode) => {
    try {
      await hnossSetMode(mode);
      toast.success(`Modus: ${mode}`);
      load();
    } catch (e) {
      toast.error("Modus-Wechsel fehlgeschlagen");
    }
  };

  const submit = async () => {
    setBusy(true);
    try {
      const res = await hnossTransfer({ ...form, batch_size: Number(form.batch_size) });
      setResult(res);
      toast[res.status === "ACCEPTED" ? "success" : res.status === "PENDING" ? "message" : "error"](
        `Transfer ${res.status}`
      );
      load();
    } catch (e) {
      toast.error("Transfer-Evaluierung fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-amber-500/90 mb-3">
          <Split size={16} />
          <span className="text-[10px] font-mono uppercase tracking-[0.3em]">HNOSS Bridge</span>
        </div>
        <h1 className="font-serif text-4xl lg:text-5xl text-white leading-tight">
          Default-Deny Gateway
        </h1>
        <p className="text-slate-400 max-w-2xl mt-4">
          {info?.principle ||
            "Default-Deny + Whitelisting: jede Transaktion bedarf expliziter, protokollierter Freigabe (PDP/PEP)."}
        </p>
      </div>

      {/* Mode selector */}
      <div className="flex flex-wrap items-center gap-2 mb-8" data-testid="hnoss-modes">
        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 mr-1">
          Betriebsmodus:
        </span>
        {(info?.modes || []).map((m) => (
          <button
            key={m}
            onClick={() => changeMode(m)}
            data-testid={`mode-${m}`}
            className={`px-3 py-1.5 rounded-sm text-[12px] font-mono border transition-colors ${
              info?.current_mode === m
                ? "border-amber-500/60 bg-amber-500/10 text-amber-300"
                : "border-white/10 text-slate-400 hover:text-white hover:bg-white/5"
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Transfer simulator */}
        <Card className="bg-[#0b1120]/80 border-white/10 lg:col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono uppercase tracking-wider text-slate-300">
              Transfer-Simulator
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Field label="Source Domain" value={form.source_domain} onChange={(v) => set("source_domain", v)} testId="f-source" />
            <Field label="Target Domain" value={form.target_domain} onChange={(v) => set("target_domain", v)} testId="f-target" />
            <div>
              <Lbl>Data Classification</Lbl>
              <select
                value={form.data_classification}
                onChange={(e) => set("data_classification", e.target.value)}
                data-testid="f-classification"
                className="w-full bg-black/40 border border-white/10 rounded-sm px-3 py-2 text-[12px] font-mono text-slate-200 outline-none focus:border-amber-500/50"
              >
                {["PUBLIC", "RESTRICTED", "CONFIDENTIAL", "TOP_SECRET"].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <Field label="Batch Size" value={form.batch_size} onChange={(v) => set("batch_size", v)} type="number" testId="f-batch" />
            <div>
              <Lbl>Jurisdiction</Lbl>
              <select
                value={form.jurisdiction}
                onChange={(e) => set("jurisdiction", e.target.value)}
                data-testid="f-jurisdiction"
                className="w-full bg-black/40 border border-white/10 rounded-sm px-3 py-2 text-[12px] font-mono text-slate-200 outline-none focus:border-amber-500/50"
              >
                {["EU", "US", "UK", "CH", "INT"].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <label className="flex items-center gap-2 text-[12px] text-slate-300 cursor-pointer" data-testid="f-whitelist">
              <input
                type="checkbox"
                checked={form.identity_whitelisted}
                onChange={(e) => set("identity_whitelisted", e.target.checked)}
                className="w-4 h-4 accent-amber-500"
              />
              Identity whitelisted (POL-001)
            </label>
            <Button
              onClick={submit}
              disabled={busy}
              data-testid="run-transfer"
              className="w-full bg-amber-500 hover:bg-amber-400 text-black font-mono text-[12px] uppercase tracking-wider"
            >
              {busy ? <Loader2 size={14} className="animate-spin mr-1" /> : <Send size={14} className="mr-1" />}
              Transfer evaluieren
            </Button>

            {result && (
              <ResultBox result={result} />
            )}
          </CardContent>
        </Card>

        {/* Policies + components */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-[#0b1120]/80 border-white/10">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-mono uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <ShieldCheck size={14} className="text-amber-500/80" /> Policy-Regeln
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2" data-testid="hnoss-policies">
                {policies.map((p) => (
                  <div key={p.id} className="rounded-sm border border-white/10 bg-white/[0.02] p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[11px] font-mono text-amber-400">{p.id}</span>
                      <Badge variant="outline" className="text-[8px] font-mono border-white/15 text-slate-400">
                        {p.effect}
                      </Badge>
                    </div>
                    <div className="text-[11px] text-slate-400">{p.desc}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0b1120]/80 border-white/10">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-mono uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Clock size={14} className="text-sky-400" /> Letzte Transfers (Audit)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {transfers.length === 0 ? (
                <div className="text-slate-600 text-[12px] font-mono">Noch keine Transfers.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-[11px] font-mono" data-testid="hnoss-transfers-table">
                    <thead className="text-slate-500">
                      <tr>
                        <th className="text-left py-1.5 pr-3">Zeit</th>
                        <th className="text-left py-1.5 pr-3">Route</th>
                        <th className="text-left py-1.5 pr-3">Status</th>
                        <th className="text-left py-1.5 pr-3">Regeln</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transfers.map((tx) => {
                        const s = STATUS_STYLE[tx.status] || {};
                        return (
                          <tr key={tx.id} className="border-t border-white/5 text-slate-300">
                            <td className="py-1.5 pr-3 whitespace-nowrap">
                              {String(tx.timestamp).slice(11, 19)}
                            </td>
                            <td className="py-1.5 pr-3">{tx.source_domain} → {tx.target_domain}</td>
                            <td className={`py-1.5 pr-3 ${s.color || "text-slate-300"}`}>{tx.status}</td>
                            <td className="py-1.5 pr-3 text-slate-500">{(tx.applied_rules || []).join(", ")}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Lbl({ children }) {
  return (
    <label className="text-[10px] font-mono uppercase tracking-wider text-slate-500">{children}</label>
  );
}

function Field({ label, value, onChange, type = "text", testId }) {
  return (
    <div>
      <Lbl>{label}</Lbl>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        data-testid={testId}
        className="w-full bg-black/40 border border-white/10 rounded-sm px-3 py-2 text-[12px] font-mono text-slate-200 outline-none focus:border-amber-500/50"
      />
    </div>
  );
}

function ResultBox({ result }) {
  const s = STATUS_STYLE[result.status] || STATUS_STYLE.PENDING;
  const Icon = s.icon || ShieldAlert;
  return (
    <div className={`mt-3 rounded-sm border ${s.border} bg-white/[0.02] p-3`} data-testid="transfer-result">
      <div className={`flex items-center gap-2 ${s.color} font-serif text-lg`}>
        <Icon size={18} /> {result.status}
      </div>
      <div className="text-[11px] font-mono text-slate-400 mt-2 space-y-1">
        <div>PDP: <span className={s.color}>{result.decision?.pdp}</span> · PEP: {result.decision?.pep}</div>
        <div>Regeln: <span className="text-slate-300">{(result.applied_rules || []).join(", ")}</span></div>
        <div className="truncate flex items-center gap-1"><Lock size={10} /> {result.audit_ref}</div>
      </div>
      <p className="text-[12px] text-slate-300 mt-2">{result.message}</p>
    </div>
  );
}
