import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  ArrowLeft,
  Flame,
  HeartHandshake,
  Landmark,
  MapPin,
  Lock,
  Sparkles,
  Scale,
  QrCode,
  Languages,
  Loader2,
  ExternalLink,
} from "lucide-react";
import { pniaGetPlaque, pniaPlaqueContext, pniaTranslate } from "../lib/api";
import { useAuth } from "../lib/auth";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function Candle() {
  return (
    <div className="relative flex flex-col items-center" aria-hidden="true">
      <div className="candle-glow absolute -top-6 w-24 h-24 rounded-full bg-amber-400/30 blur-2xl" />
      <svg width="40" height="56" viewBox="0 0 40 56" className="candle-flame relative z-10">
        <ellipse cx="20" cy="20" rx="8" ry="16" fill="url(#flame)" />
        <ellipse cx="20" cy="24" rx="4" ry="9" fill="#fff7ed" opacity="0.9" />
        <defs>
          <linearGradient id="flame" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fde68a" />
            <stop offset="55%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#b45309" />
          </linearGradient>
        </defs>
      </svg>
      <div className="w-6 h-20 rounded-t-sm bg-gradient-to-b from-slate-100/90 to-slate-300/70 -mt-1 z-0" />
      <div className="w-10 h-2 rounded-sm bg-slate-400/40" />
    </div>
  );
}

export default function PNIAMemorial() {
  const { id } = useParams();
  const { user } = useAuth();
  const [plaque, setPlaque] = useState(null);
  const [ctx, setCtx] = useState(null);
  const [loading, setLoading] = useState(true);
  const [target, setTarget] = useState("English");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [p, c] = await Promise.all([pniaGetPlaque(id), pniaPlaqueContext(id)]);
      setPlaque(p);
      setCtx(c);
    } catch (e) {
      toast.error("Eintrag nicht gefunden");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const translate = async () => {
    setBusy(true);
    try {
      await pniaTranslate(id, target);
      toast.success(`Übersetzung (${target}) erstellt — KI-kuratiert, Art. 50 protokolliert`);
      await load();
    } catch (e) {
      const msg =
        e?.response?.status === 401
          ? "Bitte zuerst anmelden (KI-Aktion ist geschützt)."
          : e?.response?.data?.detail || "Übersetzung fehlgeschlagen";
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-[1000px] px-6 py-20 flex items-center gap-2 text-slate-500 font-mono text-sm">
        <Loader2 size={16} className="animate-spin" /> lädt …
      </div>
    );
  }
  if (!plaque) {
    return (
      <div className="mx-auto max-w-[1000px] px-6 py-20 text-slate-500 font-mono">
        Eintrag nicht gefunden.{" "}
        <Link to="/pnia-registry" className="text-amber-400 underline">
          Zurück zum Register
        </Link>
      </div>
    );
  }

  const memorial = plaque.type === "MEMORIAL_BOARD";
  const cp = plaque.content_payload || {};
  const translations = cp.translations || {};

  return (
    <div className="mx-auto max-w-[1000px] px-6 lg:px-10 py-12">
      <Link
        to="/pnia-registry"
        data-testid="back-to-registry"
        className="inline-flex items-center gap-2 text-[12px] font-mono text-slate-400 hover:text-amber-400 mb-8"
      >
        <ArrowLeft size={14} /> Zurück zum Register
      </Link>

      {/* Memorial header with candle */}
      <div className="flex flex-col items-center text-center mb-10" data-testid="memorial-detail">
        {memorial ? (
          <Candle />
        ) : (
          <div className="w-14 h-14 rounded-full border border-amber-500/40 bg-amber-500/10 flex items-center justify-center">
            <HeartHandshake size={24} className="text-amber-400" />
          </div>
        )}
        <span className="mt-5 text-[10px] font-mono uppercase tracking-[0.3em] text-slate-500">
          {memorial ? "Gedenktafel · In Memoriam" : "Ehrenplatz"}
        </span>
        <h1 className="font-serif text-4xl lg:text-5xl text-white mt-2">{cp.display_name}</h1>
        {cp.role && <div className="text-slate-400 mt-3 max-w-xl">{cp.role}</div>}
        <div className="flex items-center gap-3 mt-4">
          {plaque.locked && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono text-slate-500">
              <Lock size={11} /> versiegelt (Write-Once)
            </span>
          )}
          {plaque.ai_generated_content && (
            <span className="inline-flex items-center gap-1 rounded-sm border border-sky-500/40 bg-sky-500/10 px-2 py-0.5 text-[9px] font-mono uppercase tracking-wider text-sky-300">
              <Sparkles size={10} /> KI-kuratiert · Art. 50
            </span>
          )}
        </div>
      </div>

      {/* Tribute */}
      {cp.tribute_text && (
        <blockquote className="relative mx-auto max-w-2xl text-center font-serif text-xl lg:text-2xl leading-relaxed text-slate-200 mb-12">
          <span className="text-amber-500/40 text-5xl absolute -top-6 left-0">“</span>
          {cp.tribute_text}
          <span className="text-amber-500/40 text-5xl absolute -bottom-10 right-0">”</span>
        </blockquote>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Facts + QR */}
        <Card className="bg-[#0b1120]/80 border-white/10">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono uppercase tracking-wider text-slate-300">
              Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-[13px] text-slate-400">
            {cp.institution && (
              <div className="flex items-start gap-2">
                <Landmark size={14} className="mt-0.5 text-amber-500/80 shrink-0" />
                <span>{cp.institution}</span>
              </div>
            )}
            {cp.resting_place && (
              <div className="flex items-start gap-2">
                <MapPin size={14} className="mt-0.5 text-amber-500/80 shrink-0" />
                <span>{cp.resting_place}</span>
              </div>
            )}
            {ctx?.maps_url && (
              <div className="flex items-center gap-4 pt-3 border-t border-white/5">
                <img
                  src={`${BACKEND_URL}${ctx.qr_url}`}
                  alt="QR zur Ruhestätte"
                  data-testid="memorial-qr"
                  className="w-24 h-24 rounded-sm border border-white/10 bg-white p-1"
                />
                <div className="text-[11px] font-mono text-slate-500">
                  <div className="flex items-center gap-1 text-slate-300">
                    <QrCode size={12} /> Ruhestätte
                  </div>
                  <a
                    href={ctx.maps_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 mt-2 text-amber-400 hover:underline"
                  >
                    In Karte öffnen <ExternalLink size={11} />
                  </a>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Governance context */}
        <Card className="bg-[#0b1120]/80 border-white/10">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Scale size={14} className="text-amber-500/80" /> Rechtsgrundlage / Governance
            </CardTitle>
          </CardHeader>
          <CardContent className="text-[13px] text-slate-400" data-testid="governance-context">
            {ctx?.governance ? (
              <div className="space-y-2">
                <div className="font-serif text-lg text-white">{ctx.governance.state}</div>
                <Detail k="ISO-3" v={ctx.governance.iso3} />
                <Detail k="Rechtsform" v={ctx.governance.legal_form} />
                <Detail k="Erste Verfassung" v={ctx.governance.first_constitution} />
                <Detail k="Rechtsgrundlage heute" v={ctx.governance.legal_basis_today} />
                <Link
                  to="/governance"
                  className="inline-flex items-center gap-1 text-[11px] font-mono text-amber-400 hover:underline mt-2"
                >
                  Zur Staatenliste <ExternalLink size={11} />
                </Link>
              </div>
            ) : (
              <span className="text-slate-600 text-[12px]">
                Kein staatlicher Governance-Kontext hinterlegt.
              </span>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Translations */}
      <div className="mt-10">
        <div className="flex items-center gap-2 mb-3">
          <Languages size={16} className="text-sky-400" />
          <h2 className="font-serif text-xl text-white">Übersetzungen</h2>
          <Badge variant="outline" className="ml-1 text-[9px] font-mono border-sky-500/40 text-sky-300">
            KI · Art. 50
          </Badge>
        </div>
        {Object.keys(translations).length > 0 ? (
          <div className="space-y-3">
            {Object.entries(translations).map(([lang, text]) => (
              <div key={lang} className="rounded-sm border border-white/10 bg-white/[0.02] p-4">
                <div className="text-[10px] font-mono uppercase tracking-wider text-sky-300 mb-1">
                  {lang}
                </div>
                <p className="text-[13px] italic text-slate-300">{text}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-600 text-[12px] font-mono">Noch keine Übersetzungen.</p>
        )}
        {user && !plaque.locked && (
          <div className="flex items-center gap-2 mt-4">
            <input
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              data-testid="translate-target"
              placeholder="Zielsprache (z.B. English)"
              className="bg-black/40 border border-white/10 rounded-sm px-3 py-2 text-[12px] font-mono text-slate-200 focus:border-sky-500/50 outline-none"
            />
            <Button
              onClick={translate}
              disabled={busy}
              data-testid="translate-btn"
              size="sm"
              variant="outline"
              className="border-sky-500/40 text-sky-300 hover:bg-sky-500/10 text-[11px] font-mono"
            >
              {busy ? <Loader2 size={12} className="animate-spin mr-1" /> : <Sparkles size={12} className="mr-1" />}
              KI-Übersetzung
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

function Detail({ k, v }) {
  if (!v) return null;
  return (
    <div className="flex gap-2">
      <span className="text-slate-500 font-mono text-[10px] uppercase tracking-wider min-w-[130px]">
        {k}
      </span>
      <span className="text-slate-300">{v}</span>
    </div>
  );
}
