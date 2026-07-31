import React, { useEffect, useState } from "react";
import {
  Layers,
  Boxes,
  ListChecks,
  GitBranch,
  Landmark,
  ShieldCheck,
  Info,
  Loader2,
  Milestone,
  Clock,
} from "lucide-react";
import Iso3DStack from "../components/Iso3DStack";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL ||
  (typeof window !== "undefined" ? window.location.origin : "");

export default function Blueprint() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const j = await fetch(`${BACKEND_URL}/api/blueprint/full`).then((r) =>
          r.json()
        );
        setData(j);
      } catch (e) {
        setError(e.message);
      }
    })();
  }, []);

  if (error)
    return (
      <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-16 text-red-400">
        Failed to load blueprint: {error}
      </div>
    );

  if (!data)
    return (
      <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-16 text-slate-400 flex items-center gap-2">
        <Loader2 className="animate-spin" size={14} /> Loading blueprint…
      </div>
    );

  const {
    meta,
    layers,
    building_blocks,
    validation_path,
    data_flows,
    regulatory_refs,
  } = data;

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-10 text-slate-200">
      {/* ---------- Header w/ background video + 3D preview ---------- */}
      <div className="relative border border-white/10 rounded-lg overflow-hidden mb-10">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-0 w-full h-full object-cover opacity-25"
          aria-hidden="true"
          data-testid="blueprint-hero-video"
        >
          <source
            src="https://cdn.pixabay.com/video/2020/08/21/47717-451812833_large.mp4"
            type="video/mp4"
          />
        </video>
        <div className="absolute inset-0 pnia-video-overlay" />
        <div className="relative grid grid-cols-12 gap-6 p-6 lg:p-10">
          <div className="col-span-12 lg:col-span-7">
            <div className="text-[10px] font-mono uppercase tracking-[0.28em] text-amber-500/90 mb-2">
              Architektur-Paper · Version {meta.version} · Stand {meta.asOf}
            </div>
            <h1 className="text-3xl lg:text-5xl font-serif tracking-tight text-white leading-tight">
              {meta.title}
            </h1>
            <p className="text-slate-300 mt-4 max-w-3xl text-sm leading-relaxed">
              {meta.subtitle}
            </p>
            <div className="text-[11px] font-mono text-slate-400 mt-4">
              {meta.initiative} ·{" "}
              <span className="text-amber-400">{meta.author}</span>
            </div>
            <div className="mt-6 grid grid-cols-3 lg:grid-cols-5 gap-3 max-w-2xl">
              {[
                { k: "layers", v: layers.length, l: "Ebenen" },
                { k: "bb", v: building_blocks.length, l: "Building Blocks" },
                { k: "stages", v: validation_path.length, l: "Prüfstufen" },
                { k: "flows", v: data_flows.length, l: "Datenflüsse" },
                { k: "refs", v: regulatory_refs.length, l: "Bezüge" },
              ].map((s) => (
                <div
                  key={s.k}
                  className="border border-white/10 bg-black/40 rounded-md p-3"
                >
                  <div className="text-2xl font-serif text-amber-400">
                    {s.v}
                  </div>
                  <div className="mt-1 text-[9px] font-mono uppercase tracking-wider text-slate-500">
                    {s.l}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="hidden lg:block col-span-5">
            <div className="border border-white/10 bg-black/30 rounded-lg p-2">
              <Iso3DStack
                height={340}
                layers={layers.map((l) => ({ level: l.level, title: l.title }))}
              />
            </div>
          </div>
        </div>
      </div>

      {/* ---------- Section: Layers ---------- */}
      <Section
        icon={Layers}
        title="1. Schichtenmodell"
        subtitle="Fünf konzentrische Ebenen der Public-Goods-Architektur"
        count={layers.length}
      >
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-3">
          {layers.map((l, i) => (
            <div
              key={l.level}
              data-testid={`layer-${i}`}
              className="border border-white/10 bg-black/40 rounded-md p-4 hover:border-amber-500/40 transition-colors"
            >
              <div className="text-[10px] font-mono uppercase tracking-wider text-amber-500">
                {l.level}
              </div>
              <div className="mt-2 text-[13px] font-serif text-white leading-snug">
                {l.title}
              </div>
              <div className="mt-3 text-[11px] text-slate-400 leading-relaxed">
                {l.purpose}
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* ---------- Section: Building Blocks ---------- */}
      <Section
        icon={Boxes}
        title="2. Modulschnitt (Building Blocks)"
        subtitle="Zehn wiederverwendbare, interoperable Bausteine"
        count={building_blocks.length}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {building_blocks.map((b) => (
            <div
              key={b.code}
              data-testid={`bb-${b.code}`}
              className="border border-white/10 bg-black/40 rounded-md p-4 flex gap-4 items-start hover:border-amber-500/40 transition-colors"
            >
              <div className="w-14 shrink-0 text-center">
                <div className="text-[9px] font-mono uppercase tracking-wider text-slate-500">
                  BB
                </div>
                <div className="text-lg font-serif text-amber-400 leading-none mt-1">
                  {b.code.split("-")[1]}
                </div>
              </div>
              <div className="flex-1">
                <div className="font-mono text-[11px] uppercase tracking-wider text-amber-400">
                  {b.code} · {b.title}
                </div>
                <div className="text-[11px] text-slate-400 leading-relaxed mt-2">
                  {b.purpose}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* ---------- Section: Validation path ---------- */}
      <Section
        icon={ListChecks}
        title="3. Validierungs- und Screening-Pfad"
        subtitle="Sechs-stufiger identischer Pfad, adaptive und barrierefreie Zugangswege"
        count={validation_path.length}
      >
        <ol className="space-y-2">
          {validation_path.map((s, idx) => (
            <li
              key={s.stage}
              data-testid={`stage-${idx}`}
              className="relative border border-white/10 bg-black/40 rounded-md p-4 pl-14"
            >
              <span className="absolute left-4 top-4 w-8 h-8 rounded-full border border-amber-500/60 bg-amber-500/10 flex items-center justify-center text-[11px] font-mono text-amber-400">
                {idx + 1}
              </span>
              <div className="font-mono text-[11px] uppercase tracking-wider text-amber-400">
                {s.stage} · {s.title}
              </div>
              <div className="text-[12px] text-slate-400 mt-1">{s.detail}</div>
            </li>
          ))}
        </ol>
      </Section>

      {/* ---------- Section: Data flows ---------- */}
      <Section
        icon={GitBranch}
        title="4. Datenflüsse"
        subtitle="Definierte Flüsse zwischen Barrierefreiheits-Layer, Excellent Hub, Upen-Onboarding und Korrektur-Ledger"
        count={data_flows.length}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {data_flows.map((f) => (
            <div
              key={f.flow}
              data-testid={`flow-${f.flow}`}
              className="border border-white/10 bg-black/40 rounded-md p-4 hover:border-amber-500/40 transition-colors"
            >
              <div className="font-mono text-[11px] uppercase tracking-wider text-amber-400">
                {f.flow}
              </div>
              <div className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                {f.detail}
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* ---------- Section: Regulatory refs ---------- */}
      <Section
        icon={Landmark}
        title="5. Regulatorischer Bezugsrahmen"
        subtitle="Institutionen und Normen, die als Referenz benannt werden (keine Zertifizierung)"
        count={regulatory_refs.length}
      >
        <div className="border border-white/10 bg-black/40 rounded-md divide-y divide-white/5">
          {regulatory_refs.map((r) => (
            <div
              key={r.ref}
              data-testid={`ref-${r.ref}`}
              className="p-4 flex flex-col md:flex-row md:items-start md:gap-6"
            >
              <div className="font-mono text-[11px] uppercase tracking-wider text-amber-400 w-48 shrink-0">
                {r.ref}
              </div>
              <div className="text-[12px] text-slate-400 leading-relaxed">
                {r.meaning}
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* ---------- Section: Architecture Timeline ---------- */}
      <Section
        icon={Milestone}
        title="6. Architektur-Timeline"
        subtitle="Der Weg von der Referenz-Kryptografie zur zustandslosen Compliance-Engine"
        count={7}
      >
        <ArchitectureTimeline />
      </Section>

      {/* ---------- Section: Compliance rail ---------- */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-3">
        <ComplianceCard
          icon={ShieldCheck}
          title="EU AI Act 2024/1689"
          detail="Modulschnitt BB-05 · Art. 12 record-keeping via hash-chained audit log; Art. 50 transparency flag propagates into every AI-touched artefact."
        />
        <ComplianceCard
          icon={ShieldCheck}
          title="Digital Markets Act 2022/1925"
          detail="Ebene 1 GovStack + BB-10 Interop-Layer erfüllen die Vorgabe offener, herstellerneutraler Schnittstellen (keine Vendor-Lock-in-Muster)."
        />
        <ComplianceCard
          icon={ShieldCheck}
          title="Digital Services Act 2022/2065"
          detail="BB-09 Korrektur-Ledger erfüllt Art. 17 (Statement of Reasons) und Art. 16 DSGVO in einer nachvollziehbaren, tamper-evidenten Kette."
        />
      </div>

      {/* ---------- Geltungsvorbehalt ---------- */}
      <div className="mt-10 border border-amber-500/30 bg-amber-500/5 rounded-md p-5">
        <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.24em] text-amber-500 mb-2">
          <Info size={12} /> Geltungsvorbehalt
        </div>
        <div className="text-[11px] leading-relaxed text-slate-300">
          {meta.geltungsvorbehalt}
        </div>
      </div>

      <div className="mt-6 text-[10px] font-mono text-slate-500 leading-relaxed">
        © 2026 {meta.author} · {meta.initiative} · {meta.title} · Version{" "}
        {meta.version} · Stand {meta.asOf}
      </div>
    </div>
  );
}

function Section({ icon: Icon, title, subtitle, count, children }) {
  return (
    <section className="mt-10">
      <div className="flex items-end gap-4 pb-4 border-b border-white/5 mb-4">
        <div className="w-9 h-9 rounded-md border border-amber-500/40 bg-amber-500/10 flex items-center justify-center">
          <Icon size={16} className="text-amber-400" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-serif tracking-tight text-white">
            {title}
          </h2>
          {subtitle && (
            <div className="text-[11px] text-slate-500 mt-0.5">{subtitle}</div>
          )}
        </div>
        <div className="text-[10px] font-mono uppercase tracking-wider text-amber-500">
          {count} Einträge
        </div>
      </div>
      {children}
    </section>
  );
}

function ComplianceCard({ icon: Icon, title, detail }) {
  return (
    <div className="border border-white/10 bg-black/40 rounded-md p-4">
      <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.24em] text-amber-500/80 mb-2">
        <Icon size={12} /> {title}
      </div>
      <div className="text-[12px] text-slate-400 leading-relaxed">{detail}</div>
    </div>
  );
}

const TIMELINE_ITEMS = [
  {
    when: "Sprint 1-5 · Q1",
    title: "Referenz-Kryptografie",
    detail:
      "SD-JWT VC (RFC 9215) + ISO 18013-5 mDoc, persistente 3-Level-CA, LOTL-Parser, X.509-Kettenprüfung nach RFC 5280.",
  },
  {
    when: "Sprint 7-9 · Q2",
    title: "Federation & Compliance-Cockpit",
    detail:
      "11 nationale Adapter (EU/FR/IT/CH/PT/SE/NO/DK/IE/BR/US), Emergent Google Auth, LoA-Downgrade-Detection, DSA-PDF-Export.",
  },
  {
    when: "Iteration 3",
    title: "Admin-Portal & GDPR Art. 17",
    detail:
      "Rollenbasiertes Admin-Portal, idempotentes Seeding, tamper-evidenter Erasure-Ledger, GitHub Live-Sync mit LRU-Cache.",
  },
  {
    when: "Iteration 4",
    title: "PNIA Registry + Concil (CP-01)",
    detail:
      "Gedenktafeln (16) + Ehrenplätze, AES-256-GCM PII-Tokenisierung, DSGVO Art. 17 crypto-shred, 4-Säulen Concil Protokoll, CIH-01 Handshake mit Sovereignty Shield.",
  },
  {
    when: "Iteration 5",
    title: "Stateless Compliance Validator",
    detail:
      "251 echte Frameworks aus regula-quest, 8 spezialisierte Rule-Engines (GDPR/DORA/EU AI Act/DMA/DSA/NIS2/eIDAS 2/CRA), Live-Ticker via Server-Sent Events, zero-DB.",
  },
  {
    when: "Iteration 6",
    title: "Signed PDF + Custom Rules + 3D",
    detail:
      "ES256-signierte PDF-Reports, Web-Audio-Pling + FAIL-Pulse, Admin-Rule-Editor, photorealistische CSS-3D-Architektur-Preview, Promo-Video-Loops.",
  },
  {
    when: "Blaupause v1.0",
    title: "Ganzheitliche Public-Goods-Architektur",
    detail:
      "5 Ebenen · 10 Building Blocks · 6 Prüfstufen · 5 Datenflüsse · 9 regulatorische Bezugsrahmen. Referenz-Konzeptwerk, kein Betriebsclaim.",
  },
];

function ArchitectureTimeline() {
  return (
    <ol className="pnia-timeline-track pl-2 space-y-4">
      {TIMELINE_ITEMS.map((it, idx) => (
        <li
          key={it.when}
          data-testid={`timeline-${idx}`}
          className="relative pl-12"
        >
          <span className="pnia-timeline-dot absolute left-0 top-1">
            <Clock size={11} className="text-amber-400" />
          </span>
          <div className="border border-white/10 bg-black/40 rounded-md p-4 hover:border-amber-500/40 transition-colors">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-amber-500">
                {it.when}
              </span>
              <span className="font-serif text-[15px] text-white">
                {it.title}
              </span>
            </div>
            <div className="text-[12px] text-slate-400 leading-relaxed mt-2">
              {it.detail}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
