import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Flame,
  Landmark,
  HeartHandshake,
  Lock,
  ShieldCheck,
  Sparkles,
  Fingerprint,
  ScrollText,
  MapPin,
  Loader2,
  FileText,
  CheckCircle2,
  BadgeCheck,
  Cpu,
} from "lucide-react";
import {
  pniaListPlaques,
  pniaCompliance,
  pniaAiAudit,
  pniaGenerateTribute,
} from "../lib/api";
import { useAuth } from "../lib/auth";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const FILTERS = [
  { key: "ALL", label: "Alle", icon: Landmark },
  { key: "MEMORIAL_BOARD", label: "Gedenktafeln", icon: Flame },
  { key: "HONORARY_PLACE", label: "Ehrenplätze", icon: HeartHandshake },
];

function Stat({ label, value, sub, tone = "amber" }) {
  const toneClass =
    tone === "green"
      ? "text-emerald-400 border-emerald-500/30"
      : tone === "indigo"
      ? "text-indigo-300 border-indigo-500/30"
      : "text-amber-400 border-amber-500/30";
  return (
    <div className={`rounded-sm border ${toneClass} bg-white/[0.02] px-4 py-3`}>
      <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500">
        {label}
      </div>
      <div className={`text-2xl font-serif ${toneClass.split(" ")[0]}`}>{value}</div>
      {sub && <div className="text-[10px] text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}

function TransparencyBadge() {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-sm border border-sky-500/40 bg-sky-500/10 px-2 py-0.5 text-[9px] font-mono uppercase tracking-wider text-sky-300"
      data-testid="ai-transparency-badge"
      title="Dieser Text wurde maschinell kuratiert — EU AI Act Art. 50"
    >
      <Sparkles size={10} /> KI-kuratiert · AI Act Art. 50
    </span>
  );
}

function PlaqueCard({ p, canEdit, onGenerated }) {
  const [busy, setBusy] = useState(false);
  const memorial = p.type === "MEMORIAL_BOARD";
  const cp = p.content_payload || {};
  const accent = memorial ? "indigo" : "amber";
  const border = memorial ? "border-indigo-500/25" : "border-amber-500/25";
  const glow = memorial ? "hover:border-indigo-400/50" : "hover:border-amber-400/50";

  const generate = async () => {
    setBusy(true);
    try {
      const res = await pniaGenerateTribute(p.id, { language: "Deutsch" });
      toast.success("Würdevoller Text generiert (KI-kuratiert, Art. 50 protokolliert)");
      onGenerated(p.id, res.tribute_text);
    } catch (e) {
      const msg = e?.response?.status === 401
        ? "Bitte zuerst anmelden (KI-Aktion ist geschützt)."
        : e?.response?.data?.detail || "KI-Generierung fehlgeschlagen";
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card
      className={`bg-[#0b1120]/80 ${border} ${glow} transition-colors relative overflow-hidden`}
      data-testid={`plaque-card-${p.id}`}
    >
      <div
        className={`absolute inset-x-0 top-0 h-0.5 ${
          memorial ? "bg-indigo-500/50" : "bg-amber-500/60"
        }`}
      />
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            {memorial ? (
              <Flame size={16} className="text-indigo-300" />
            ) : (
              <HeartHandshake size={16} className="text-amber-400" />
            )}
            <span className="text-[9px] font-mono uppercase tracking-[0.22em] text-slate-500">
              {memorial ? "Gedenktafel" : "Ehrenplatz"}
            </span>
          </div>
          {p.locked && (
            <span className="inline-flex items-center gap-1 text-[9px] font-mono text-slate-500" title="Write-Once versiegelt (postmortaler Schutz)">
              <Lock size={10} /> versiegelt
            </span>
          )}
        </div>
        <CardTitle className="font-serif text-xl text-white leading-tight mt-1">
          <Link to={`/pnia-memorial/${p.id}`} className="hover:text-amber-300 transition-colors">
            {cp.display_name || "—"}
          </Link>
        </CardTitle>
        {cp.role && <div className="text-[12px] text-slate-400 mt-1">{cp.role}</div>}
      </CardHeader>
      <CardContent className="space-y-3">
        {cp.institution && (
          <div className="flex items-start gap-2 text-[11px] text-slate-500">
            <Landmark size={12} className="mt-0.5 shrink-0" />
            <span>{cp.institution}</span>
          </div>
        )}
        {cp.resting_place && (
          <div className="flex items-start gap-2 text-[11px] text-slate-500">
            <MapPin size={12} className="mt-0.5 shrink-0" />
            <span>{cp.resting_place}</span>
          </div>
        )}
        {cp.tribute_text && (
          <p className="text-[13px] leading-relaxed text-slate-300 border-l-2 border-white/10 pl-3 italic">
            {cp.tribute_text}
          </p>
        )}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          {p.ai_generated_content ? (
            <TransparencyBadge />
          ) : (
            <Badge variant="outline" className="text-[9px] font-mono border-white/15 text-slate-400">
              manuell kuratiert
            </Badge>
          )}
          <Badge
            variant="outline"
            className={`text-[9px] font-mono ${
              p.risk_classification === "LIMITED_RISK_TRANSPARENCY"
                ? "border-sky-500/40 text-sky-300"
                : "border-emerald-500/30 text-emerald-400"
            }`}
          >
            {p.risk_classification === "LIMITED_RISK_TRANSPARENCY" ? "Limited-Risk" : "Minimal-Risk"}
          </Badge>
        </div>
        {canEdit && !p.locked && (
          <Button
            onClick={generate}
            disabled={busy}
            size="sm"
            variant="outline"
            data-testid={`generate-tribute-${p.id}`}
            className="w-full mt-2 border-sky-500/40 text-sky-300 hover:bg-sky-500/10 text-[11px] font-mono"
          >
            {busy ? <Loader2 size={12} className="animate-spin mr-1" /> : <Sparkles size={12} className="mr-1" />}
            KI-Text neu generieren
          </Button>
        )}
        <Link
          to={`/pnia-memorial/${p.id}`}
          data-testid={`open-detail-${p.id}`}
          className="block w-full mt-2 text-center rounded-sm border border-white/10 hover:border-amber-500/40 text-[11px] font-mono text-slate-400 hover:text-amber-300 py-2 transition-colors"
        >
          Würdigen &amp; Details ansehen
        </Link>
      </CardContent>
    </Card>
  );
}

export default function PNIARegistry() {
  const { user } = useAuth();
  const [plaques, setPlaques] = useState([]);
  const [filter, setFilter] = useState("ALL");
  const [comp, setComp] = useState(null);
  const [audit, setAudit] = useState({ entries: [], count: 0 });
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [pl, c, a] = await Promise.all([
        pniaListPlaques(),
        pniaCompliance(),
        pniaAiAudit(),
      ]);
      setPlaques(pl.plaques || []);
      setComp(c);
      setAudit(a);
    } catch (e) {
      toast.error("Register konnte nicht geladen werden");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onGenerated = (id, text) => {
    setPlaques((prev) =>
      prev.map((p) =>
        p.id === id
          ? {
              ...p,
              content_payload: { ...p.content_payload, tribute_text: text },
              ai_generated_content: true,
              risk_classification: "LIMITED_RISK_TRANSPARENCY",
            }
          : p
      )
    );
    load();
  };

  const shown =
    filter === "ALL" ? plaques : plaques.filter((p) => p.type === filter);

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12">
      {/* Hero */}
      <div className="mb-10">
        <div className="flex items-center gap-2 text-amber-500/90 mb-3">
          <Landmark size={16} />
          <span className="text-[10px] font-mono uppercase tracking-[0.3em]">
            PNIA · Personal Notable Individuals Archive
          </span>
        </div>
        <h1 className="font-serif text-4xl lg:text-5xl text-white leading-tight max-w-3xl">
          Gedenk- &amp; Ehrenregister
        </h1>
        <p className="text-slate-400 max-w-2xl mt-4 leading-relaxed">
          Ein würdevolles Register: <span className="text-indigo-300">Gedenktafeln</span> tragen
          das Andenken verstorbener Schlüsselpersonen im Herzen weiter,
          <span className="text-amber-400"> Ehrenplätze</span> würdigen lebende Persönlichkeiten.
          Vollständig konform mit DSGVO, EU AI Act &amp; Digital Markets Act.
        </p>
        <div className="flex flex-wrap gap-2 mt-5">
          {[
            { icon: Fingerprint, t: "AES-256-GCM PII-Tokenisierung" },
            { icon: ShieldCheck, t: "DSGVO Art. 17 · Right-to-be-Forgotten" },
            { icon: Sparkles, t: "EU AI Act Art. 50 · Transparenz" },
            { icon: BadgeCheck, t: "DMA · offene API" },
          ].map(({ icon: Icon, t }) => (
            <span
              key={t}
              className="inline-flex items-center gap-1.5 rounded-sm border border-white/10 bg-white/[0.02] px-3 py-1.5 text-[10px] font-mono text-slate-300"
            >
              <Icon size={12} className="text-amber-500" /> {t}
            </span>
          ))}
          <a
            href={`${BACKEND_URL || ""}/documents/PNIA_Komplettpaket.pdf`}
            target="_blank"
            rel="noreferrer"
            data-testid="pnia-pdf-link"
            className="inline-flex items-center gap-1.5 rounded-sm border border-amber-500/40 bg-amber-500/10 px-3 py-1.5 text-[10px] font-mono text-amber-300 hover:bg-amber-500/20"
          >
            <FileText size={12} /> PNIA Komplettpaket (PDF)
          </a>
        </div>
      </div>

      {/* Compliance strip */}
      {comp && (
        <div
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-8"
          data-testid="pnia-compliance-strip"
        >
          <Stat label="Gedenktafeln" value={comp.plaques.memorial_boards} tone="indigo" />
          <Stat label="Ehrenplätze" value={comp.plaques.honorary_places} tone="amber" />
          <Stat label="Versiegelt" value={comp.plaques.locked_write_once} sub="Write-Once" tone="indigo" />
          <Stat label="KI-kuratiert" value={comp.ai_act.ai_generated_plaques} sub="Art. 50" tone="amber" />
          <Stat
            label="Consents"
            value={comp.dsgvo.consents_granted}
            sub={`${comp.dsgvo.consents_revoked} widerrufen`}
            tone="green"
          />
          <Stat
            label="Audit-Chain"
            value={comp.ai_act.audit_chain_valid ? "gültig" : "defekt"}
            sub={`${comp.ai_act.audit_entries} Einträge`}
            tone={comp.ai_act.audit_chain_valid ? "green" : "amber"}
          />
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-2 mb-6">
        {FILTERS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            data-testid={`filter-${key}`}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-[12px] font-mono transition-colors border ${
              filter === key
                ? "border-amber-500/60 bg-amber-500/10 text-amber-300"
                : "border-white/10 text-slate-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Icon size={13} /> {label}
          </button>
        ))}
        {!user && (
          <span className="ml-auto text-[10px] font-mono text-slate-500">
            Anmelden für KI-Kuratierung &amp; Verwaltung
          </span>
        )}
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex items-center gap-2 text-slate-500 font-mono text-sm">
          <Loader2 size={16} className="animate-spin" /> lädt …
        </div>
      ) : shown.length === 0 ? (
        <div className="text-slate-500 font-mono text-sm">Keine Einträge.</div>
      ) : (
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
          data-testid="plaque-grid"
        >
          {shown.map((p) => (
            <PlaqueCard key={p.id} p={p} canEdit={!!user} onGenerated={onGenerated} />
          ))}
        </div>
      )}

      {/* AI Audit Trail */}
      <div className="mt-14">
        <div className="flex items-center gap-2 mb-4">
          <ScrollText size={16} className="text-sky-400" />
          <h2 className="font-serif text-2xl text-white">Unveränderliches KI-Audit-Protokoll</h2>
          <Badge
            variant="outline"
            className="ml-2 text-[9px] font-mono border-sky-500/40 text-sky-300"
          >
            EU AI Act Art. 12
          </Badge>
        </div>
        <p className="text-slate-500 text-[12px] mb-4 max-w-2xl">
          Jede KI-Entscheidung wird SHA-256-hash-verkettet und ES256-signiert protokolliert —
          nur Hashes von Prompt/Ausgabe, niemals Klartext.
        </p>
        {audit.entries.length === 0 ? (
          <div className="text-slate-600 font-mono text-[12px] border border-white/5 rounded-sm p-4">
            Noch keine KI-Aktionen protokolliert. Generiere einen Text (nach Anmeldung), um den
            Audit-Trail zu füllen.
          </div>
        ) : (
          <div className="overflow-x-auto border border-white/10 rounded-sm">
            <table className="w-full text-[11px] font-mono" data-testid="ai-audit-table">
              <thead className="bg-white/[0.03] text-slate-500">
                <tr>
                  <th className="text-left px-3 py-2">Zeit</th>
                  <th className="text-left px-3 py-2">Aktion</th>
                  <th className="text-left px-3 py-2">Modell</th>
                  <th className="text-left px-3 py-2">Risiko</th>
                  <th className="text-left px-3 py-2">Hash</th>
                </tr>
              </thead>
              <tbody>
                {audit.entries.map((e) => (
                  <tr key={e.id} className="border-t border-white/5 text-slate-300">
                    <td className="px-3 py-2 whitespace-nowrap">
                      {String(e.executed_at).slice(0, 19).replace("T", " ")}
                    </td>
                    <td className="px-3 py-2">
                      <span className="inline-flex items-center gap-1 text-sky-300">
                        <Cpu size={11} /> {e.action_type}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-slate-400">{e.ai_model_version}</td>
                    <td className="px-3 py-2">
                      <span className="text-sky-300">{e.risk_classification}</span>
                    </td>
                    <td className="px-3 py-2 text-slate-500 max-w-[180px] truncate">
                      {e.hash}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="flex items-center gap-2 mt-3 text-[11px] font-mono text-emerald-400">
          <CheckCircle2 size={13} />
          Kette {comp?.ai_act?.audit_chain_valid ? "verifiziert & unversehrt" : "prüfen"}
        </div>
      </div>
    </div>
  );
}
