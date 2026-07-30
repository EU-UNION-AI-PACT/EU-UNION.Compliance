import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { AlertTriangle, CheckCircle2, XCircle, ArrowRight, Loader2, Users } from "lucide-react";
import { toast } from "sonner";
import { getDowngrades, overrideDecision } from "../lib/api";
import { useAuth } from "../lib/auth";

const LOA_COLOR = {
  high: "text-emerald-400",
  substantial: "text-blue-400",
  low: "text-yellow-500",
};

export function DowngradePanel() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [rows, setRows] = useState([]);
  const [busy, setBusy] = useState(false);
  const [openNote, setOpenNote] = useState({});

  const refresh = async () => {
    try {
      const d = await getDowngrades();
      setRows(d);
    } catch {}
  };

  useEffect(() => {
    refresh();
    const h = setInterval(refresh, 8000);
    return () => clearInterval(h);
  }, []);

  const act = async (subject_fp, decision) => {
    setBusy(true);
    try {
      const note = openNote[subject_fp] || "";
      await overrideDecision({
        subject_fp,
        decision,
        reviewer: user?.email || "anonymous-reviewer",
        note,
      });
      toast.success(`Marked ${decision}`);
      await refresh();
    } catch (e) {
      toast.error("Override failed");
    } finally {
      setBusy(false);
    }
  };

  const isDE = i18n.language === "de";

  return (
    <div className="border border-red-500/25 bg-[#0a0f19] rounded-sm" data-testid="downgrade-panel">
      <div className="flex items-center justify-between border-b border-white/5 px-5 py-3">
        <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.22em] text-red-400">
          <AlertTriangle size={12} strokeWidth={1.7} />
          {isDE ? "LoA-Downgrade-Erkennung (AI Act Art. 14)" : "LoA downgrade detection (AI Act Art. 14)"}
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500">
          <Users size={10} /> {rows.filter((r) => r.status === "pending").length} pending
        </div>
      </div>
      {rows.length === 0 ? (
        <div className="p-6 text-center text-[12px] font-mono text-slate-500">
          {isDE ? "Keine Downgrades erkannt." : "No downgrades detected."}
        </div>
      ) : (
        <div className="max-h-[420px] overflow-y-auto">
          {rows.map((r) => (
            <div
              key={r.subject_fp + r.detected_at}
              className="border-t border-white/5 first:border-0 px-5 py-4"
              data-testid={`downgrade-row-${r.subject_fp?.slice(0, 8)}`}
            >
              <div className="flex items-start justify-between gap-4 mb-2">
                <div>
                  <div className="flex items-center gap-2 text-[13px] font-mono">
                    <span className={LOA_COLOR[r.from_loa] || "text-slate-400"}>{r.from_loa}</span>
                    <ArrowRight size={11} className="text-slate-500" />
                    <span className={LOA_COLOR[r.to_loa] || "text-slate-400"}>{r.to_loa}</span>
                  </div>
                  <div className="mt-1 text-[10.5px] font-mono text-slate-500 truncate max-w-[280px]">
                    subject_fp: {r.subject_fp?.slice(0, 24)}…
                  </div>
                  <div className="text-[10.5px] font-mono text-slate-500">
                    vct: {r.context?.vct || "—"} · detected {String(r.detected_at).slice(0, 19)}
                  </div>
                </div>
                <div>
                  {r.status === "pending" ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-sm border border-yellow-500/40 bg-yellow-500/10 text-yellow-400">
                      PENDING
                    </span>
                  ) : (
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-sm border ${
                        r.status === "accepted"
                          ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                          : r.status === "rejected"
                          ? "border-red-500/40 bg-red-500/10 text-red-400"
                          : "border-blue-500/40 bg-blue-500/10 text-blue-400"
                      }`}
                    >
                      {r.status.toUpperCase()}
                    </span>
                  )}
                </div>
              </div>
              {r.status === "pending" && user && (
                <div className="mt-3 space-y-2">
                  <input
                    type="text"
                    placeholder={isDE ? "Notiz für Prüfer-Log…" : "Reviewer note…"}
                    value={openNote[r.subject_fp] || ""}
                    onChange={(e) => setOpenNote({ ...openNote, [r.subject_fp]: e.target.value })}
                    data-testid={`downgrade-note-${r.subject_fp?.slice(0, 8)}`}
                    className="w-full bg-[#050a12] border border-white/10 focus:border-amber-500/60 rounded-sm px-2.5 py-1.5 text-[11px] font-mono text-white outline-none transition-colors"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => act(r.subject_fp, "accept")}
                      disabled={busy}
                      data-testid={`downgrade-accept-${r.subject_fp?.slice(0, 8)}`}
                      className="flex-1 flex items-center justify-center gap-1 text-[10.5px] font-mono uppercase tracking-wider border border-emerald-500/50 hover:bg-emerald-500 hover:text-black text-emerald-400 py-1.5 rounded-sm transition-colors disabled:opacity-40"
                    >
                      <CheckCircle2 size={10} /> Accept
                    </button>
                    <button
                      onClick={() => act(r.subject_fp, "reject")}
                      disabled={busy}
                      data-testid={`downgrade-reject-${r.subject_fp?.slice(0, 8)}`}
                      className="flex-1 flex items-center justify-center gap-1 text-[10.5px] font-mono uppercase tracking-wider border border-red-500/50 hover:bg-red-500 hover:text-white text-red-400 py-1.5 rounded-sm transition-colors disabled:opacity-40"
                    >
                      <XCircle size={10} /> Reject
                    </button>
                    <button
                      onClick={() => act(r.subject_fp, "escalate")}
                      disabled={busy}
                      data-testid={`downgrade-escalate-${r.subject_fp?.slice(0, 8)}`}
                      className="flex-1 flex items-center justify-center gap-1 text-[10.5px] font-mono uppercase tracking-wider border border-blue-500/50 hover:bg-blue-500 hover:text-black text-blue-400 py-1.5 rounded-sm transition-colors disabled:opacity-40"
                    >
                      Escalate
                    </button>
                  </div>
                </div>
              )}
              {r.status === "pending" && !user && (
                <div className="mt-2 text-[10.5px] font-mono text-slate-500 italic">
                  {isDE ? "Sign in als Reviewer, um zu entscheiden." : "Sign in as a reviewer to decide."}
                </div>
              )}
              {r.human_note && (
                <div className="mt-2 text-[10.5px] font-mono text-slate-400 border-l-2 border-blue-500/40 pl-2">
                  {r.reviewer}: {r.human_note}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
