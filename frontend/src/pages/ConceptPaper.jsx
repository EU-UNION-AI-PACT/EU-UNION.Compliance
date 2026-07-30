import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import { Bookmark, BookmarkCheck, Search, Clock, ChevronRight } from "lucide-react";
import { listChapters, searchChapters } from "../lib/api";
import { PaperMarkdown } from "../components/PaperMarkdown";

function useBookmarks() {
  const [bm, setBm] = useState(() => {
    try {
      return JSON.parse(window.localStorage.getItem("eudi_bookmarks") || "[]");
    } catch {
      return [];
    }
  });
  const toggle = (slug) => {
    const next = bm.includes(slug) ? bm.filter((s) => s !== slug) : [...bm, slug];
    setBm(next);
    window.localStorage.setItem("eudi_bookmarks", JSON.stringify(next));
  };
  return [bm, toggle];
}

export default function ConceptPaper() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { slug } = useParams();
  const [chapters, setChapters] = useState([]);
  const [bookmarks, toggleBm] = useBookmarks();
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);

  useEffect(() => {
    listChapters().then(setChapters).catch(() => setChapters([]));
  }, []);

  const active = useMemo(() => {
    if (slug) return chapters.find((c) => c.slug === slug);
    return chapters[0];
  }, [chapters, slug]);

  useEffect(() => {
    if (!q || q.length < 2) {
      setResults([]);
      return;
    }
    const h = setTimeout(() => {
      searchChapters(q).then(setResults).catch(() => setResults([]));
    }, 200);
    return () => clearTimeout(h);
  }, [q]);

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12 grid grid-cols-12 gap-10">
      {/* Sidebar */}
      <aside className="col-span-12 lg:col-span-3 order-2 lg:order-1">
        <div className="lg:sticky lg:top-24">
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-5">
            {t("chapters.title")}
          </div>
          <div className="relative mb-5">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" strokeWidth={1.6} />
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("chapters.search_placeholder")}
              data-testid="paper-search-input"
              className="w-full pl-9 pr-3 py-2 bg-[#0a0f19] border border-white/10 focus:border-amber-500/60 rounded-sm text-[13px] text-white placeholder:text-slate-500 outline-none transition-colors"
            />
          </div>
          {results.length > 0 && (
            <div className="mb-6 border border-blue-500/20 bg-blue-500/[0.03] p-3 rounded-sm">
              <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-blue-400 mb-2">
                {results.length} results
              </div>
              {results.map((r) => (
                <button
                  key={r.slug}
                  onClick={() => nav(`/paper/${r.slug}`)}
                  data-testid={`search-hit-${r.slug}`}
                  className="w-full text-left py-2 border-b border-white/5 last:border-0 hover:text-amber-500 transition-colors"
                >
                  <div className="text-[13px] text-white">{r.title}</div>
                  <div className="text-[11px] text-slate-500 font-mono line-clamp-2">{r.excerpt}</div>
                </button>
              ))}
            </div>
          )}
          <nav className="flex flex-col gap-1">
            {chapters.map((c) => {
              const isActive = active?.slug === c.slug;
              const isBm = bookmarks.includes(c.slug);
              return (
                <div
                  key={c.slug}
                  onClick={() => nav(`/paper/${c.slug}`)}
                  data-testid={`chapter-nav-${c.slug}`}
                  data-active={isActive}
                  className={`group cursor-pointer flex items-start gap-3 px-3 py-3 rounded-sm border trace-beam transition-colors ${
                    isActive
                      ? "border-amber-500/60 bg-amber-500/[0.05]"
                      : "border-transparent hover:border-white/10 hover:bg-white/[0.02]"
                  }`}
                >
                  <div className={`font-mono text-xs mt-0.5 ${isActive ? "text-amber-500" : "text-slate-600"}`}>
                    {String(c.number).padStart(2, "0")}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-[13px] leading-tight ${isActive ? "text-white" : "text-slate-300 group-hover:text-white"}`}>
                      {c.title}
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-[10px] font-mono text-slate-500">
                      <Clock size={9} strokeWidth={1.6} /> {c.reading_minutes} {t("chapters.min")}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleBm(c.slug);
                    }}
                    data-testid={`bookmark-${c.slug}`}
                    className={`opacity-0 group-hover:opacity-100 ${isBm ? "opacity-100 text-amber-500" : "text-slate-500 hover:text-amber-400"} transition-all`}
                    title={isBm ? t("chapters.bookmarked") : t("chapters.bookmark")}
                  >
                    {isBm ? <BookmarkCheck size={13} strokeWidth={1.6} /> : <Bookmark size={13} strokeWidth={1.6} />}
                  </button>
                </div>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Body */}
      <article className="col-span-12 lg:col-span-9 order-1 lg:order-2">
        {active ? (
          <div key={active.slug} className="animate-fade-up" data-testid={`chapter-body-${active.slug}`}>
            <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-4">
              CHAPTER {String(active.number).padStart(2, "0")}
              <ChevronRight size={11} strokeWidth={1.6} className="text-slate-600" />
              <Clock size={11} strokeWidth={1.6} /> {active.reading_minutes} {t("chapters.min")}
            </div>
            <h1 className="font-serif font-light text-4xl lg:text-5xl text-white leading-tight mb-3">
              {active.title}
            </h1>
            <p className="font-serif italic text-slate-400 text-lg mb-8 max-w-3xl">{active.subtitle}</p>
            <div className="max-w-3xl paper-prose">
              <PaperMarkdown body={active.body} />
            </div>
          </div>
        ) : (
          <div className="text-slate-500 font-mono text-sm">{t("chapters.empty")}</div>
        )}
      </article>
    </div>
  );
}
