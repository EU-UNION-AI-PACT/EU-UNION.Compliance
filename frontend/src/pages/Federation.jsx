import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ExternalLink, CheckCircle2, MinusCircle } from "lucide-react";
import { listCountries } from "../lib/api";

export default function Federation() {
  const { t } = useTranslation();
  const [countries, setCountries] = useState([]);
  const [active, setActive] = useState(null);

  useEffect(() => {
    listCountries().then((cs) => {
      setCountries(cs);
      setActive(cs[0]);
    });
  }, []);

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12">
      <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-3">
        MULTI-COUNTRY FEDERATION
      </div>
      <h1 className="font-serif font-light text-4xl lg:text-5xl text-white leading-tight mb-3">
        {t("federation.title")}
      </h1>
      <p className="text-slate-400 max-w-2xl mb-10">{t("federation.subtitle")}</p>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-7">
          <div className="border border-white/10 bg-[#0a0f19] rounded-sm overflow-hidden">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="text-slate-500 uppercase text-[9px] tracking-[0.18em] border-b border-white/5">
                  <th className="text-left px-4 py-3 font-medium">Flag</th>
                  <th className="text-left px-4 py-3 font-medium">{t("federation.code")}</th>
                  <th className="text-left px-4 py-3 font-medium">Name</th>
                  <th className="text-left px-4 py-3 font-medium">{t("federation.formats")}</th>
                  <th className="text-left px-4 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {countries.map((c) => (
                  <tr
                    key={c.code}
                    onClick={() => setActive(c)}
                    data-testid={`federation-row-${c.code}`}
                    data-active={active?.code === c.code}
                    className={`cursor-pointer border-b border-white/5 last:border-0 hover:bg-white/[0.02] trace-beam ${
                      active?.code === c.code ? "bg-amber-500/[0.05]" : ""
                    }`}
                  >
                    <td className="px-4 py-3 text-xl">{c.flag}</td>
                    <td className="px-4 py-3 font-mono text-amber-500 text-[13px]">{c.code}</td>
                    <td className="px-4 py-3 text-slate-200">{c.name}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1.5 flex-wrap">
                        {c.supported_formats.map((f) => (
                          <span
                            key={f}
                            className="text-[9px] font-mono uppercase tracking-wider border border-blue-500/30 bg-blue-500/5 text-blue-400 px-2 py-0.5 rounded-sm"
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {c.implemented ? (
                        <span className="inline-flex items-center gap-1 text-[10.5px] font-mono text-emerald-400 border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 rounded-sm">
                          <CheckCircle2 size={9} strokeWidth={2} /> {t("federation.implemented")}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[10.5px] font-mono text-yellow-500 border border-yellow-500/30 bg-yellow-500/5 px-2 py-0.5 rounded-sm">
                          <MinusCircle size={9} strokeWidth={2} /> {t("federation.stub")}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="col-span-12 lg:col-span-5">
          {active && (
            <div className="border border-amber-500/30 bg-[#0a0f19] rounded-sm p-6 sticky top-24" data-testid="federation-detail">
              <div className="flex items-center gap-3 mb-5">
                <div className="text-4xl">{active.flag}</div>
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-500">
                    {active.code}
                  </div>
                  <div className="font-serif text-xl text-white">{active.name}</div>
                </div>
              </div>
              <dl className="space-y-3 text-[13px]">
                <div>
                  <dt className="text-[10px] font-mono uppercase tracking-widest text-slate-500">
                    {t("federation.scheme")}
                  </dt>
                  <dd className="text-slate-200 mt-0.5">{active.scheme}</dd>
                </div>
                <div>
                  <dt className="text-[10px] font-mono uppercase tracking-widest text-slate-500">
                    {t("federation.framework")}
                  </dt>
                  <dd className="text-slate-200 mt-0.5">{active.trust_framework}</dd>
                </div>
                <div>
                  <dt className="text-[10px] font-mono uppercase tracking-widest text-slate-500">
                    {t("federation.id_hash")}
                  </dt>
                  <dd className="text-amber-400 font-mono text-[12px] mt-0.5">{active.id_hash_algorithm}</dd>
                </div>
                <div>
                  <dt className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1">
                    {t("federation.loa")}
                  </dt>
                  <dd className="grid grid-cols-2 gap-1 font-mono text-[11px]">
                    {Object.entries(active.loa_mapping).map(([k, v]) => (
                      <div key={k} className="flex items-center gap-2 border border-white/5 bg-[#050a12] px-2 py-1 rounded-sm">
                        <span className="text-slate-400">{k}</span>
                        <span className="text-slate-600">→</span>
                        <span className="text-blue-400">{v}</span>
                      </div>
                    ))}
                  </dd>
                </div>
              </dl>
              <a
                href={active.reference_url}
                target="_blank"
                rel="noreferrer"
                data-testid="federation-ref-link"
                className="mt-6 inline-flex items-center gap-1.5 text-blue-400 hover:text-blue-300 text-[12.5px] font-mono"
              >
                {t("federation.reference")}
                <ExternalLink size={12} strokeWidth={1.7} />
              </a>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
