import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  ScrollText,
  ShieldCheck,
  ShieldAlert,
  KeyRound,
  Landmark,
  Cpu,
  Lock,
  Copyright,
  Fingerprint,
  CheckCircle2,
  XCircle,
  Loader2,
  Sparkles,
  Layers,
} from "lucide-react";
import { pniaConcept, pniaHandshake, pniaOwnership } from "../lib/api";

const INVARIANTS = [
  { key: "peace", label: "Frieden / Peace" },
  { key: "freedom", label: "Freiheit / Freedom" },
  { key: "integrity", label: "Integrität / Integrity" },
  { key: "neighborly_love", label: "Nächstenliebe / Neighborly Love" },
];

export default function PNIAConcept() {
  const [concept, setConcept] = useState(null);
  const [ownership, setOwnership] = useState(null);
  const [selected, setSelected] = useState({
    peace: true,
    freedom: true,
    integrity: true,
    neighborly_love: true,
  });
  const [commitment, setCommitment] = useState("sha256-konstitutionelle-akzeptanz");
  const [hsResult, setHsResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [c, o] = await Promise.all([pniaConcept(), pniaOwnership()]);
        setConcept(c);
        setOwnership(o);
      } catch (e) {
        toast.error("Konzept konnte nicht geladen werden");
      }
    })();
  }, []);

  const runHandshake = async () => {
    setBusy(true);
    setHsResult(null);
    try {
      const accepted = Object.entries(selected)
        .filter(([, v]) => v)
        .map(([k]) => k);
      const res = await pniaHandshake({
        accepted_invariants: accepted,
        commitment: commitment || null,
      });
      setHsResult(res);
      toast.success("Established Access — alle Invarianten erfüllt");
    } catch (e) {
      // A Governance-Mismatch is returned as a real HTTP 403 with the decision
      // envelope in the response body — display it as the isolation result.
      const data = e?.response?.data;
      if (data && data.decision === "GOVERNANCE_MISMATCH") {
        setHsResult(data);
        toast.error("Governance-Mismatch — Sovereignty Shield isoliert");
      } else {
        toast.error("Handshake fehlgeschlagen");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12">
      {/* Hero */}
      <div className="mb-10">
        <div className="flex items-center gap-2 text-amber-500/90 mb-3">
          <ScrollText size={16} />
          <span className="text-[10px] font-mono uppercase tracking-[0.3em]">
            Concil Protokoll · CP-01
          </span>
        </div>
        <h1 className="font-serif text-4xl lg:text-5xl text-white leading-tight max-w-3xl">
          {concept?.acronym || "PNIA — Production Network ID Architecture"}
        </h1>
        <p className="text-slate-400 max-w-3xl mt-4 leading-relaxed">
          {concept?.definition ||
            "Technisches Referenzdesign, das regulatorische und ethische Anforderungen als systemische Invarianten direkt in den Datenstrom einbettet."}
        </p>
        <div className="flex flex-wrap gap-2 mt-5">
          {(concept?.principles || []).map((p) => (
            <span
              key={p}
              className="inline-flex items-center gap-1.5 rounded-sm border border-white/10 bg-white/[0.02] px-3 py-1.5 text-[10px] font-mono text-slate-300"
            >
              <Sparkles size={12} className="text-amber-500" /> {p}
            </span>
          ))}
        </div>
      </div>

      {/* CP-01 Four Pillars */}
      <section className="mb-12">
        <div className="flex items-center gap-2 mb-4">
          <Layers size={16} className="text-amber-400" />
          <h2 className="font-serif text-2xl text-white">Die vier Säulen (CP-01)</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="cp01-pillars">
          {(concept?.cp01_pillars || []).map((p) => (
            <Card key={p.key} className="bg-[#0b1120]/80 border-amber-500/20">
              <CardHeader className="pb-2">
                <CardTitle className="font-serif text-lg text-amber-300">{p.name}</CardTitle>
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                  {p.en}
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-[12px] leading-relaxed text-slate-400">{p.desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Technical pillars + roles */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Cpu size={16} className="text-sky-400" />
            <h2 className="font-serif text-xl text-white">Technische Säulen</h2>
          </div>
          <div className="space-y-3">
            {(concept?.technical_pillars || []).map((tp) => (
              <div key={tp.name} className="rounded-sm border border-white/10 bg-white/[0.02] p-3">
                <div className="text-[13px] text-sky-300 font-medium">{tp.name}</div>
                <div className="text-[11px] text-slate-500 mt-1">{tp.desc}</div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2 mb-4">
            <KeyRound size={16} className="text-amber-400" />
            <h2 className="font-serif text-xl text-white">Governance-Rollen</h2>
          </div>
          <div className="space-y-3">
            {(concept?.governance_roles || []).map((r) => (
              <div key={r.role} className="rounded-sm border border-white/10 bg-white/[0.02] p-3">
                <div className="text-[13px] text-amber-300 font-medium">{r.role}</div>
                <div className="text-[11px] text-slate-500 mt-1">{r.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CIH-01 Handshake live demo */}
      <section className="mb-12">
        <div className="flex items-center gap-2 mb-2">
          <ShieldCheck size={16} className="text-emerald-400" />
          <h2 className="font-serif text-2xl text-white">CIH-01 Handshake · Live</h2>
          <Badge variant="outline" className="ml-2 text-[9px] font-mono border-emerald-500/40 text-emerald-300">
            State-0-Compliance
          </Badge>
        </div>
        <p className="text-slate-500 text-[12px] mb-5 max-w-2xl">
          Ein System erhält nur „Established Access“, wenn es alle hart kodierten Governance-Invarianten
          (Axiome) akzeptiert und ein konstitutionelles Commitment vorlegt. Andernfalls isoliert der
          Sovereignty Shield den Aufrufer (HTTP 403).
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="bg-[#0b1120]/80 border-white/10">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-mono text-slate-300 uppercase tracking-wider">
                Proposed Invariants
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {INVARIANTS.map((inv) => (
                <label
                  key={inv.key}
                  className="flex items-center gap-3 cursor-pointer text-[13px] text-slate-300"
                  data-testid={`inv-${inv.key}`}
                >
                  <input
                    type="checkbox"
                    checked={selected[inv.key]}
                    onChange={(e) =>
                      setSelected((s) => ({ ...s, [inv.key]: e.target.checked }))
                    }
                    className="w-4 h-4 accent-amber-500"
                  />
                  {inv.label}
                </label>
              ))}
              <div className="pt-2">
                <label className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                  Commitment (sha256)
                </label>
                <input
                  value={commitment}
                  onChange={(e) => setCommitment(e.target.value)}
                  data-testid="commitment-input"
                  className="w-full mt-1 bg-black/40 border border-white/10 rounded-sm px-3 py-2 text-[12px] font-mono text-slate-200 focus:border-amber-500/50 outline-none"
                />
              </div>
              <Button
                onClick={runHandshake}
                disabled={busy}
                data-testid="run-handshake"
                className="w-full mt-2 bg-amber-500 hover:bg-amber-400 text-black font-mono text-[12px] uppercase tracking-wider"
              >
                {busy ? <Loader2 size={14} className="animate-spin mr-1" /> : <KeyRound size={14} className="mr-1" />}
                Handshake ausführen
              </Button>
            </CardContent>
          </Card>

          <Card
            className={`bg-[#0b1120]/80 ${
              hsResult
                ? hsResult.status === 200
                  ? "border-emerald-500/40"
                  : "border-red-500/40"
                : "border-white/10"
            }`}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-mono text-slate-300 uppercase tracking-wider">
                Concil-Validierung
              </CardTitle>
            </CardHeader>
            <CardContent data-testid="handshake-result">
              {!hsResult ? (
                <div className="text-slate-600 font-mono text-[12px]">
                  Führe den Handshake aus, um die Antwort zu sehen.
                </div>
              ) : hsResult.status === 200 ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-emerald-400">
                    <CheckCircle2 size={18} />
                    <span className="font-serif text-lg">200 · Established Access</span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400 space-y-1">
                    <div>decision: <span className="text-emerald-300">{hsResult.decision}</span></div>
                    <div>sovereignty_shield: <span className="text-emerald-300">{hsResult.sovereignty_shield}</span></div>
                    <div className="truncate">session_token: <span className="text-slate-500">{hsResult.session_token}</span></div>
                    <div className="truncate">signature: <span className="text-slate-500">{hsResult.concil_signature_header}</span></div>
                  </div>
                  <p className="text-[12px] text-slate-300">{hsResult.message}</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-red-400">
                    <ShieldAlert size={18} />
                    <span className="font-serif text-lg">403 · Governance-Mismatch</span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400 space-y-1">
                    <div>sovereignty_shield: <span className="text-red-300">{hsResult.sovereignty_shield}</span></div>
                    <div>
                      missing:{" "}
                      <span className="text-red-300">
                        {(hsResult.missing_invariants || []).join(", ") || "—"}
                      </span>
                    </div>
                    <div>commitment_present: <span className="text-red-300">{String(hsResult.commitment_present)}</span></div>
                  </div>
                  <p className="text-[12px] text-slate-300 flex items-start gap-1">
                    <XCircle size={13} className="text-red-400 mt-0.5 shrink-0" />
                    {hsResult.message}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Urheberrecht & Register */}
      {ownership && (
        <section
          className="rounded-sm border border-amber-500/30 bg-gradient-to-br from-amber-500/[0.06] to-transparent p-6 lg:p-8"
          data-testid="ownership-block"
        >
          <div className="flex items-center gap-2 mb-4">
            <Copyright size={18} className="text-amber-400" />
            <h2 className="font-serif text-2xl text-white">Urheberrecht &amp; Register</h2>
            <Badge variant="outline" className="ml-2 text-[9px] font-mono border-amber-500/40 text-amber-300">
              geschützt
            </Badge>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <div>
                <div className="font-serif text-xl text-amber-300">{ownership.copyright}</div>
                <div className="text-[12px] text-slate-400">
                  {ownership.holder} · {ownership.location}
                </div>
              </div>
              <p className="text-[13px] leading-relaxed text-slate-300 border-l-2 border-amber-500/40 pl-4">
                {ownership.statement}
              </p>
              <div className="flex flex-wrap gap-2">
                {(ownership.trademarks || []).map((t) => (
                  <span
                    key={t}
                    className="inline-flex items-center gap-1.5 rounded-sm border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[10px] font-mono text-amber-300"
                  >
                    <Lock size={10} /> {t}
                  </span>
                ))}
              </div>
              {ownership.governance && (
                <div className="space-y-2 pt-2">
                  {Object.entries(ownership.governance).map(([k, v]) => (
                    <div key={k} className="text-[11px] text-slate-500">
                      <span className="text-slate-300 font-mono">{k}:</span> {v}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 mb-3 text-slate-400">
                <Fingerprint size={14} />
                <span className="text-[10px] font-mono uppercase tracking-[0.2em]">
                  Register-Nummern
                </span>
              </div>
              <div className="space-y-2" data-testid="register-numbers">
                {(ownership.registers || []).map((r) => (
                  <div
                    key={r.label}
                    className="flex items-center justify-between gap-3 rounded-sm border border-white/10 bg-black/30 px-3 py-2"
                  >
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                      {r.label}
                    </span>
                    <span className="text-[12px] font-mono text-amber-300">{r.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
