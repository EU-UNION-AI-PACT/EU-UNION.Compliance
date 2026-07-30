import React from "react";
import { Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Header } from "./Header";

export function Layout() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-[#090d16] text-white grain-overlay relative">
      <Header />
      <main className="relative z-[2]">
        <Outlet />
      </main>
      <footer className="relative z-[2] border-t border-white/5 mt-24 py-10 px-6 lg:px-10 text-slate-500 text-[11px]">
        <div className="mx-auto max-w-[1500px] flex flex-col lg:flex-row lg:justify-between gap-3 font-mono">
          <span>© 2026 EUDI-Nexus · {t("footer.line1")}</span>
          <span>
            {t("footer.line2")} <code className="text-amber-500">/app/stalwart/config/config.toml</code>
          </span>
        </div>
        <div className="mx-auto max-w-[1500px] mt-3 pt-3 border-t border-white/5 text-[10px] text-slate-600 font-mono">
          PNIA · Concil Protokoll (CP-01) · Hnoss® · © 2026 Daniel Pohl, Detmold — Alle Urheber- und Registerrechte vorbehalten.
        </div>
      </footer>
    </div>
  );
}
