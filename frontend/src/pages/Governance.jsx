import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Card, CardContent } from "../components/ui/card";
import { Scale, Search, Loader2, ChevronRight, Landmark } from "lucide-react";
import { govStates, govInfo } from "../lib/api";

export default function Governance() {
  const [q, setQ] = useState("");
  const [states, setStates] = useState([]);
  const [count, setCount] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(null);

  const load = useCallback(async (query) => {
    setLoading(true);
    try {
      const d = await govStates(query);
      setStates(d.states || []);
      setCount(d.count || 0);
    } catch (e) {
      toast.error("Staatenliste konnte nicht geladen werden");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const i = await govInfo();
        setTotal(i.count || 0);
      } catch (e) {
        /* noop */
      }
    })();
    load("");
  }, [load]);

  useEffect(() => {
    const id = setTimeout(() => load(q), 250);
    return () => clearTimeout(id);
  }, [q, load]);

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-amber-500/90 mb-3">
          <Scale size={16} />
          <span className="text-[10px] font-mono uppercase tracking-[0.3em]">
            Governance &amp; Rechtsgrundlagen
          </span>
        </div>
        <h1 className="font-serif text-4xl lg:text-5xl text-white leading-tight">Staatenliste</h1>
        <p className="text-slate-400 max-w-2xl mt-4">
          Rechtsgrundlagen, Verfassungen und Schlüsselfiguren von {total || "…"} Staaten — die
          Governance-Grundlage der PNIA-Gedenktafeln.
        </p>
      </div>

      <div className="relative max-w-md mb-6">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          data-testid="gov-search"
          placeholder="Suche: Staat, ISO-3, Hauptstadt, Schlüsselfigur …"
          className="w-full bg-black/40 border border-white/10 rounded-sm pl-9 pr-3 py-2.5 text-[13px] text-slate-200 outline-none focus:border-amber-500/50"
        />
      </div>

      <div className="text-[11px] font-mono text-slate-500 mb-3" data-testid="gov-count">
        {count} Treffer
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-slate-500 font-mono text-sm">
          <Loader2 size={16} className="animate-spin" /> lädt …
        </div>
      ) : (
        <div className="space-y-2" data-testid="gov-list">
          {states.map((s) => (
            <Card
              key={s.state}
              className="bg-[#0b1120]/70 border-white/10 hover:border-amber-500/30 transition-colors cursor-pointer"
              onClick={() => setOpen(open === s.state ? null : s.state)}
              data-testid={`gov-row-${s.iso3 || s.state}`}
            >
              <CardContent className="py-3">
                <div className="flex items-center gap-4">
                  <Landmark size={15} className="text-amber-500/70 shrink-0" />
                  <div className="font-serif text-lg text-white min-w-[180px]">{s.state}</div>
                  <div className="text-[11px] font-mono text-slate-500">{s.iso3}</div>
                  <div className="text-[12px] text-slate-400 flex-1 truncate hidden md:block">
                    {s.legal_form}
                  </div>
                  <ChevronRight
                    size={16}
                    className={`text-slate-600 transition-transform ${
                      open === s.state ? "rotate-90" : ""
                    }`}
                  />
                </div>
                {open === s.state && (
                  <div className="mt-3 pt-3 border-t border-white/5 grid grid-cols-1 md:grid-cols-2 gap-2 text-[12px]">
                    <Detail k="Hauptstadt" v={s.capital} />
                    <Detail k="Unabhängigkeit" v={s.independence} />
                    <Detail k="Erste Verfassung" v={s.first_constitution} />
                    <Detail k="Rechtsgrundlage heute" v={s.legal_basis_today} />
                    <Detail k="Schlüsselfiguren" v={s.key_figures} />
                    <Detail k="Anmerkungen" v={s.notes} />
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function Detail({ k, v }) {
  if (!v) return null;
  return (
    <div className="flex gap-2">
      <span className="text-slate-500 font-mono text-[10px] uppercase tracking-wider min-w-[150px] shrink-0">
        {k}
      </span>
      <span className="text-slate-300">{v}</span>
    </div>
  );
}
