import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Github, ExternalLink, Star, GitFork, Clock, Download, Loader2, Wifi, WifiOff } from "lucide-react";
import { listReposLive, postmanCollectionUrl } from "../lib/api";

const CAT_COLOR = {
  ARF: "amber",
  "SD-JWT VC": "blue",
  JMAP: "amber",
  "SPID/CIE": "blue",
  Swiyu: "amber",
  DIDComm: "blue",
  "Status List": "emerald",
  Wallet: "amber",
};

function relative(iso) {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diff = Math.max(0, now - then);
  const d = Math.floor(diff / (24 * 3600e3));
  if (d < 1) return "today";
  if (d < 30) return `${d}d ago`;
  const m = Math.floor(d / 30);
  if (m < 12) return `${m}mo ago`;
  return `${Math.floor(m / 12)}y ago`;
}

export default function DeveloperHub() {
  const { t, i18n } = useTranslation();
  const [repos, setRepos] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listReposLive()
      .then(setRepos)
      .catch(() => setRepos([]))
      .finally(() => setLoading(false));
  }, []);

  const cats = ["all", ...Array.from(new Set(repos.map((r) => r.category)))];
  const visible = filter === "all" ? repos : repos.filter((r) => r.category === filter);
  const isDE = i18n.language === "de";

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12">
      <div className="flex items-start justify-between gap-6 mb-8 flex-wrap">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-3">
            DEVELOPER HUB · OSS REGISTRY · LIVE-SYNC
          </div>
          <h1 className="font-serif font-light text-4xl lg:text-5xl text-white leading-tight mb-3">
            {t("hub.title")}
          </h1>
          <p className="text-slate-400 max-w-2xl">{t("hub.subtitle")}</p>
        </div>
        <a
          href={postmanCollectionUrl()}
          target="_blank"
          rel="noreferrer"
          data-testid="postman-download"
          download="eudi-nexus.postman_collection.json"
          className="flex items-center gap-2 border border-amber-500 hover:bg-amber-500 hover:text-black text-amber-400 rounded-sm px-4 py-2.5 text-[13px] font-medium transition-colors"
        >
          <Download size={14} strokeWidth={1.7} />
          {isDE ? "Postman-Kollektion" : "Postman collection"}
        </a>
      </div>

      <div className="flex flex-wrap gap-2 mb-8 items-center">
        {cats.map((c) => (
          <button
            key={c}
            onClick={() => setFilter(c)}
            data-testid={`hub-filter-${c}`}
            data-active={filter === c}
            className={`text-[11px] font-mono uppercase tracking-wider px-3 py-1.5 rounded-sm border transition-colors ${
              filter === c
                ? "border-amber-500 bg-amber-500/10 text-amber-500"
                : "border-white/10 text-slate-400 hover:text-white hover:border-white/25"
            }`}
          >
            {c}
          </button>
        ))}
        {loading && (
          <span className="ml-3 flex items-center gap-1.5 text-[10px] font-mono text-slate-500">
            <Loader2 size={11} className="animate-spin" />
            {isDE ? "GitHub-Sync läuft…" : "syncing GitHub…"}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {visible.map((r) => {
          const tint = CAT_COLOR[r.category] || "blue";
          const gh = r.github || {};
          return (
            <a
              key={r.slug}
              href={r.url}
              target="_blank"
              rel="noreferrer"
              data-testid={`hub-repo-${r.slug.replace(/[/]/g, "-")}`}
              className={`trace-beam group border border-white/10 bg-[#0a0f19] p-5 rounded-sm hover:border-amber-500/50 transition-colors flex flex-col`}
            >
              <div className="flex items-start justify-between gap-2 mb-3">
                <div
                  className={`text-[9px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-sm border ${
                    tint === "amber"
                      ? "border-amber-500/40 bg-amber-500/[0.06] text-amber-500"
                      : tint === "emerald"
                      ? "border-emerald-500/40 bg-emerald-500/[0.06] text-emerald-400"
                      : "border-blue-500/40 bg-blue-500/[0.06] text-blue-400"
                  }`}
                >
                  {r.category}
                </div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500">
                  {r.role}
                </span>
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Github size={13} strokeWidth={1.7} className="text-slate-500" />
                <div className="font-mono text-[13px] text-white group-hover:text-amber-400 transition-colors truncate">
                  {r.slug}
                </div>
              </div>
              <p className="text-[12px] text-slate-400 leading-relaxed flex-1 mb-4">
                {r.description}
              </p>
              {/* Live GitHub badges */}
              <div className="flex items-center gap-3 text-[10.5px] font-mono">
                {gh.reachable ? (
                  <>
                    <span className="inline-flex items-center gap-1 text-amber-500" data-testid={`stars-${r.slug.replace(/[/]/g, "-")}`}>
                      <Star size={10} strokeWidth={1.7} />
                      {gh.stars ?? 0}
                    </span>
                    <span className="inline-flex items-center gap-1 text-slate-400">
                      <GitFork size={10} strokeWidth={1.7} />
                      {gh.forks ?? 0}
                    </span>
                    <span className="inline-flex items-center gap-1 text-slate-500">
                      <Clock size={10} strokeWidth={1.7} />
                      {relative(gh.last_commit)}
                    </span>
                    <span className="inline-flex items-center gap-1 text-emerald-500 ml-auto">
                      <Wifi size={10} strokeWidth={1.7} />
                    </span>
                  </>
                ) : (
                  <span className="inline-flex items-center gap-1 text-slate-500 ml-auto">
                    <WifiOff size={10} strokeWidth={1.7} />
                    {isDE ? "offline" : "no live data"}
                  </span>
                )}
              </div>
              <div className="mt-3 flex items-center gap-1 text-[11px] text-blue-400 group-hover:text-blue-300">
                {t("hub.open")}
                <ExternalLink size={11} strokeWidth={1.7} />
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
