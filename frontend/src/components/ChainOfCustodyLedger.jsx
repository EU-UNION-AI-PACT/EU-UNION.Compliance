import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Loader2,
  ExternalLink,
} from "lucide-react";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL ||
  (typeof window !== "undefined" ? window.location.origin : "");

const KIND_COLOR = {
  sign: "text-slate-300 border-slate-500/40 bg-slate-500/10",
  pdf: "text-amber-300 border-amber-500/40 bg-amber-500/10",
  bundle: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10",
};

/**
 * Public tamper-evident chain-of-custody ledger.
 * Shows the last-N ledger entries and verifies the hash chain.
 */
export default function ChainOfCustodyLedger() {
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [chain, setChain] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const load = async () => {
    setBusy(true);
    setError(null);
    try {
      const [le, ch] = await Promise.all([
        fetch(`${BACKEND_URL}/api/validate/ledger?limit=50`).then((r) => r.json()),
        fetch(`${BACKEND_URL}/api/validate/ledger/verify`).then((r) => r.json()),
      ]);
      setEntries(le.entries || []);
      setTotal(le.total || 0);
      setChain(ch);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
    const iv = setInterval(load, 30_000);
    return () => clearInterval(iv);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      className="border border-white/10 bg-black/40 rounded-md"
      data-testid="ledger-panel"
    >
      <div className="p-4 border-b border-white/10 flex items-center gap-3 flex-wrap">
        <ShieldCheck size={14} className="text-amber-400" />
        <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300">
          Chain-of-Custody Ledger
        </span>
        <span className="text-[10px] font-mono text-slate-500">
          public · tamper-evident · SHA-256 hash-chain
        </span>
        {chain && (
          <span
            data-testid="ledger-chain-status"
            className={`ml-auto inline-flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded border ${
              chain.ok
                ? "text-emerald-300 border-emerald-500/40 bg-emerald-500/10"
                : "text-red-300 border-red-500/40 bg-red-500/10"
            }`}
          >
            {chain.ok ? <CheckCircle2 size={11} /> : <XCircle size={11} />}
            {chain.ok ? "chain OK" : "chain BROKEN"} · {chain.entries} entries
          </span>
        )}
        <button
          onClick={load}
          data-testid="ledger-refresh"
          disabled={busy}
          className="text-[10px] font-mono uppercase tracking-wider text-slate-400 hover:text-amber-400 flex items-center gap-1"
        >
          {busy ? <Loader2 size={11} className="animate-spin" /> : <RefreshCw size={11} />}
          refresh
        </button>
      </div>
      {chain && (
        <div className="px-4 py-2 border-b border-white/5 text-[10px] font-mono text-slate-500">
          Total: <span className="text-amber-400">{total}</span> · Head:{" "}
          <span className="text-slate-300">{(chain.head || "").slice(0, 24)}…</span>
        </div>
      )}
      {error && (
        <div className="p-4 text-red-400 text-[11px] font-mono">{error}</div>
      )}
      <div className="max-h-[380px] overflow-y-auto divide-y divide-white/5">
        {entries.length === 0 && (
          <div className="p-6 text-center text-[11px] font-mono text-slate-500">
            no signed reports yet · press "signed PDF" or generate a bundle to fill the ledger
          </div>
        )}
        {entries.map((e) => (
          <div
            key={e.id}
            data-testid={`ledger-entry-${e.seq}`}
            className="px-4 py-2 flex items-center gap-3 hover:bg-white/5 transition-colors"
          >
            <span className="w-10 text-[10px] font-mono text-slate-500">
              #{e.seq}
            </span>
            <span
              className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase tracking-wider ${
                KIND_COLOR[e.kind] || KIND_COLOR.sign
              }`}
            >
              {e.kind}
            </span>
            <span className="text-[11px] font-mono text-amber-400 w-24 truncate">
              {e.framework}
            </span>
            <span className="text-[10px] font-mono text-slate-400 w-24 truncate">
              {e.status}
            </span>
            <span
              className="text-[10px] font-mono text-emerald-300/80 truncate flex-1"
              title={e.digest}
            >
              {(e.digest || "").slice(0, 20)}…
            </span>
            <span className="text-[9px] font-mono text-slate-500 w-32 text-right truncate">
              {(e.at || "").slice(0, 19).replace("T", " ")}
            </span>
          </div>
        ))}
      </div>
      <div className="px-4 py-2 border-t border-white/10 text-[9px] font-mono text-slate-500 flex items-center gap-2">
        <ExternalLink size={10} />
        GET /api/validate/ledger · verify GET /api/validate/ledger/verify
      </div>
    </div>
  );
}
