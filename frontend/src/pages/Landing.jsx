import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  KeyRound,
  ShieldCheck,
  Landmark,
  Globe2,
  Gauge,
  Fingerprint,
  ArrowUpRight,
} from "lucide-react";

const HERO_LANDING =
  "https://images.unsplash.com/photo-1579567761406-4684ee0c75b6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxOTF8MHwxfHNlYXJjaHwzfHxjeWJlcnB1bmslMjB0ZWNobm9sb2d5JTIwbm9kZSUyMG5ldHdvcmslMjBhYnN0cmFjdHxlbnwwfHx8fDE3ODUzMTI3MDN8MA&ixlib=rb-4.1.0&q=85";
const HERO_SHIELD =
  "https://images.unsplash.com/photo-1744324480866-1794a1bf193c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwzfHxjeWJlcnB1bmslMjBnbG93aW5nJTIwc2VjdXJpdHklMjBzaGllbGQlMjBuZXR3b3JrfGVufDB8fHx8MTc4NTMxMjcwMnww&ixlib=rb-4.1.0&q=85";
const HERO_PIPELINE =
  "https://images.unsplash.com/photo-1597733336794-12d05021d510?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1ODR8MHwxfHNlYXJjaHwzfHxhYnN0cmFjdCUyMGZpYmVyJTIwb3B0aWMlMjBkYXRhJTIwcGlwZWxpbmUlMjBnbG93aW5nfGVufDB8fHx8MTc4NTMxMjcwM3ww&ixlib=rb-4.1.0&q=85";
const HERO_GLOBE =
  "https://images.unsplash.com/photo-1733195296321-b99d129b09cd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjY2NjV8MHwxfHNlYXJjaHwyfHxkaWdpdGFsJTIwd29ybGQlMjBnbG93aW5nJTIwY29ubmVjdGlvbnMlMjBub2Rlc3xlbnwwfHx8fDE3ODUzMTI3MDN8MA&ixlib=rb-4.1.0&q=85";

export default function Landing() {
  const { t } = useTranslation();
  const pillars = [
    { icon: KeyRound, tK: "p1_t", dK: "p1_d", tint: "amber" },
    { icon: Fingerprint, tK: "p2_t", dK: "p2_d", tint: "blue" },
    { icon: Landmark, tK: "p3_t", dK: "p3_d", tint: "amber" },
    { icon: Globe2, tK: "p4_t", dK: "p4_d", tint: "blue" },
    { icon: Gauge, tK: "p5_t", dK: "p5_d", tint: "emerald" },
    { icon: ShieldCheck, tK: "p6_t", dK: "p6_d", tint: "blue" },
  ];
  return (
    <div>
      {/* HERO */}
      <section className="relative overflow-hidden border-b border-white/5">
        <div className="absolute inset-0">
          <img
            src={HERO_LANDING}
            alt="Cyberpunk institutional network"
            className="w-full h-full object-cover opacity-30 mix-blend-luminosity"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-[#090d16] via-[#090d16]/95 to-[#0e1521]/80" />
          <div className="absolute inset-0" style={{
            background: "radial-gradient(ellipse at 20% 30%, rgba(245,158,11,0.12), transparent 60%), radial-gradient(ellipse at 80% 70%, rgba(59,130,246,0.10), transparent 55%)"
          }} />
        </div>
        <div className="relative mx-auto max-w-[1500px] px-6 lg:px-10 py-24 lg:py-32 grid grid-cols-12 gap-8">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.2, 0.7, 0.3, 1] }}
            className="col-span-12 lg:col-span-8"
          >
            <div className="inline-flex items-center gap-3 text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 border border-amber-500/30 bg-amber-500/5 px-3 py-1.5 rounded-sm mb-8" data-testid="hero-eyebrow">
              <div className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse-amber" />
              {t("hero.eyebrow")}
            </div>
            <h1 className="font-serif font-light text-4xl sm:text-5xl lg:text-6xl leading-[1.05] tracking-tight text-white max-w-3xl">
              {t("hero.title")}
            </h1>
            <p className="mt-6 text-base lg:text-lg text-slate-400 max-w-2xl leading-relaxed">
              {t("hero.subtitle")}
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-3">
              <Link
                to="/paper"
                data-testid="hero-cta-paper"
                className="group inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-black px-5 py-3 rounded-sm text-sm font-semibold transition-colors"
              >
                {t("hero.cta_paper")}
                <ArrowUpRight size={16} className="transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" strokeWidth={2} />
              </Link>
              <Link
                to="/sandbox"
                data-testid="hero-cta-sandbox"
                className="inline-flex items-center gap-2 border border-white/15 hover:border-blue-500/70 hover:text-blue-400 text-slate-200 px-5 py-3 rounded-sm text-sm font-medium transition-colors"
              >
                {t("hero.cta_sandbox")}
              </Link>
            </div>

            {/* metrics */}
            <div className="mt-16 grid grid-cols-2 lg:grid-cols-4 gap-6 max-w-3xl">
              {[
                { n: "11", k: "adapters" },
                { n: "2", k: "formats" },
                { n: "3", k: "ci_gates" },
                { n: "9", k: "sprints" },
              ].map((m) => (
                <div key={m.k} data-testid={`metric-${m.k}`} className="border-l border-amber-500/40 pl-4">
                  <div className="font-serif text-4xl text-white font-light">{m.n}</div>
                  <div className="mt-1 text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">
                    {t(`hero.metrics.${m.k}`)}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="hidden lg:block col-span-4"
          >
            <div className="relative border border-white/10 rounded-md overflow-hidden bg-[#0a0f19] trace-beam">
              <img src={HERO_SHIELD} alt="Compliance shield" className="w-full h-72 object-cover opacity-70" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#090d16] via-transparent to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-amber-500/20">
                <div className="text-[9px] font-mono uppercase tracking-[0.2em] text-amber-500">
                  EU AI Act · Art. 13 / 14
                </div>
                <div className="mt-1 text-sm text-white font-serif">
                  Human-oversight hooks in every verifier decision
                </div>
              </div>
            </div>
            <div className="mt-4 relative border border-white/10 rounded-md overflow-hidden bg-[#0a0f19] trace-beam">
              <img src={HERO_PIPELINE} alt="Trust pipeline" className="w-full h-40 object-cover opacity-70" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#090d16] via-transparent to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-blue-500/20">
                <div className="text-[9px] font-mono uppercase tracking-[0.2em] text-blue-400">
                  ETSI TS 119 612 · RFC 5280
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* PILLARS */}
      <section className="relative">
        <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-24">
          <div className="grid grid-cols-12 gap-10 mb-12">
            <div className="col-span-12 lg:col-span-4">
              <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-4">
                ARCHITECTURE OVERVIEW
              </div>
              <h2 className="font-serif font-light text-3xl lg:text-4xl text-white leading-tight">
                {t("pillars.title")}
              </h2>
            </div>
            <div className="col-span-12 lg:col-span-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {pillars.map((p, i) => (
                  <motion.div
                    key={p.tK}
                    initial={{ opacity: 0, y: 12 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: "-80px" }}
                    transition={{ delay: i * 0.05, duration: 0.4 }}
                    className={`trace-beam group relative bg-[#0a0f19] border border-white/[0.07] p-6 rounded-md hover:border-${p.tint === "amber" ? "amber-500" : p.tint === "blue" ? "blue-500" : "emerald-500"}/50 transition-colors cursor-default`}
                    data-testid={`pillar-${p.tK}`}
                  >
                    <div className={`inline-flex w-9 h-9 items-center justify-center rounded-sm border ${p.tint === "amber" ? "border-amber-500/30 bg-amber-500/10 text-amber-500" : p.tint === "blue" ? "border-blue-500/30 bg-blue-500/10 text-blue-400" : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"} mb-4`}>
                      <p.icon size={18} strokeWidth={1.5} />
                    </div>
                    <h3 className="font-serif text-lg text-white mb-1.5">{t(`pillars.${p.tK}`)}</h3>
                    <p className="text-sm text-slate-400 leading-relaxed font-mono text-[12.5px]">
                      {t(`pillars.${p.dK}`)}
                    </p>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* GLOBE CTA */}
      <section className="relative border-t border-white/5">
        <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-24 grid grid-cols-12 gap-10">
          <div className="col-span-12 lg:col-span-6 order-2 lg:order-1">
            <div className="relative border border-white/10 rounded-md overflow-hidden bg-[#0a0f19]">
              <img src={HERO_GLOBE} alt="Digital globe" className="w-full h-80 object-cover opacity-80" />
              <div className="absolute inset-0" style={{
                background: "radial-gradient(circle at 40% 60%, transparent 40%, rgba(9,13,22,0.85))"
              }} />
            </div>
          </div>
          <div className="col-span-12 lg:col-span-6 order-1 lg:order-2">
            <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-blue-400 mb-4">
              CROSS-BORDER FEDERATION
            </div>
            <h2 className="font-serif font-light text-3xl lg:text-4xl text-white leading-tight mb-4">
              27 nations. One <span className="text-amber-500">CountryAdapter</span> Protocol.
            </h2>
            <p className="text-slate-400 leading-relaxed mb-6 max-w-lg">
              From France Connect+ (INSEE) to Swiss Swiyu (AHV) to AAMVA mDL (US) — every jurisdiction
              speaks the same interface, with GDPR-compliant SHA-256 pseudonymisation of national IDs at
              the boundary.
            </p>
            <Link
              to="/federation"
              data-testid="cta-federation"
              className="inline-flex items-center gap-2 text-amber-500 hover:text-amber-400 text-sm font-mono uppercase tracking-wider"
            >
              Explore federation
              <ArrowUpRight size={14} strokeWidth={2} />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
