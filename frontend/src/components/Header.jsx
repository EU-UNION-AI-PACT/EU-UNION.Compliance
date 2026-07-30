import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Shield,
  FileText,
  FlaskConical,
  Gauge,
  GitBranch,
  Globe,
  Languages,
  Github,
  LogIn,
  LogOut,
  ShieldAlert,
  Landmark,
  BadgeCheck,
  Network,
  ScrollText,
  Split,
  Scale,
  Library,
  ShieldCheck,
  ChevronDown,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "./ui/dropdown-menu";
import { useAuth } from "../lib/auth";

const coreItems = [
  { to: "/", labelKey: "landing", icon: Shield, testId: "nav-landing" },
  { to: "/paper", labelKey: "paper", icon: FileText, testId: "nav-paper" },
  { to: "/sandbox", labelKey: "sandbox", icon: FlaskConical, testId: "nav-sandbox" },
  { to: "/compliance", labelKey: "compliance", icon: Gauge, testId: "nav-compliance" },
  { to: "/trust", labelKey: "trust", icon: GitBranch, testId: "nav-trust" },
  { to: "/federation", labelKey: "federation", icon: Globe, testId: "nav-federation" },
  { to: "/hub", labelKey: "hub", icon: Github, testId: "nav-hub" },
];

const pniaItems = [
  { to: "/pnia-registry", labelKey: "pnia_registry", icon: Landmark, testId: "nav-pnia-registry" },
  { to: "/pnia-concept", labelKey: "pnia_concept", icon: ScrollText, testId: "nav-pnia-concept" },
  { to: "/hnoss-bridge", labelKey: "hnoss_bridge", icon: Split, testId: "nav-hnoss-bridge" },
  { to: "/governance", labelKey: "governance", icon: Scale, testId: "nav-governance" },
  { to: "/mesh-catalog", labelKey: "mesh_catalog", icon: Library, testId: "nav-mesh-catalog" },
  { to: "/uce", labelKey: "uce", icon: ShieldCheck, testId: "nav-uce" },
  { to: "/pnia-compliance", labelKey: "pnia_compliance", icon: BadgeCheck, testId: "nav-pnia-compliance" },
  { to: "/identity-broker", labelKey: "identity_broker", icon: Network, testId: "nav-identity-broker" },
];

const adminItem = { to: "/admin", labelKey: "admin", icon: ShieldAlert, testId: "nav-admin" };

function coreClass({ isActive }) {
  return (
    "flex items-center gap-2 px-3 py-2 text-[13px] font-medium rounded-sm transition-colors " +
    (isActive
      ? "text-amber-400 bg-amber-500/10 border-b-2 border-amber-500"
      : "text-slate-400 hover:text-white hover:bg-white/5")
  );
}

export function Header() {
  const { t, i18n } = useTranslation();
  const { user, loading, loginWithGoogle, logout } = useAuth();
  const location = useLocation();
  const pniaActive = pniaItems.some((i) => location.pathname.startsWith(i.to));

  const toggleLang = () => {
    const next = i18n.language === "de" ? "en" : "de";
    i18n.changeLanguage(next);
    window.localStorage.setItem("eudi_lang", next);
  };

  return (
    <header
      className="sticky top-0 z-30 backdrop-blur-xl border-b border-white/10 bg-[#090d16]/85"
      data-testid="app-header"
    >
      <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-3 flex items-center gap-6">
        <NavLink to="/" className="flex items-center gap-3 group" data-testid="brand-link">
          <div className="relative w-8 h-8 flex items-center justify-center rounded-sm border border-amber-500/50 bg-amber-500/10 glow-amber">
            <div className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse-amber" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="font-serif text-[1.05rem] font-medium tracking-tight text-white">
              {t("brand")}
            </span>
            <span className="text-[9px] font-mono uppercase tracking-[0.24em] text-amber-500/90">
              {t("brand_tag")}
            </span>
          </div>
        </NavLink>

        <nav className="hidden lg:flex items-center gap-1 flex-1">
          {coreItems.map(({ to, labelKey, icon: Icon, testId }) => (
            <NavLink key={to} to={to} end={to === "/"} data-testid={testId} className={coreClass}>
              <Icon size={14} strokeWidth={1.6} />
              <span>{t(`nav.${labelKey}`)}</span>
            </NavLink>
          ))}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                data-testid="nav-pnia-menu"
                className={
                  "flex items-center gap-2 px-3 py-2 text-[13px] font-medium rounded-sm transition-colors outline-none " +
                  (pniaActive
                    ? "text-amber-400 bg-amber-500/10 border-b-2 border-amber-500"
                    : "text-slate-400 hover:text-white hover:bg-white/5")
                }
              >
                <Landmark size={14} strokeWidth={1.6} />
                <span>PNIA</span>
                <ChevronDown size={12} strokeWidth={1.8} />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="start"
              className="bg-[#0b1120] border border-white/10 text-slate-200 min-w-[230px]"
            >
              <DropdownMenuLabel className="text-[9px] font-mono uppercase tracking-[0.2em] text-amber-500/80">
                PNIA · Concil Suite
              </DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-white/10" />
              {pniaItems.map(({ to, labelKey, icon: Icon, testId }) => (
                <DropdownMenuItem key={to} asChild>
                  <NavLink
                    to={to}
                    data-testid={`menu-${testId}`}
                    className={({ isActive }) =>
                      "flex items-center gap-2.5 cursor-pointer text-[13px] " +
                      (isActive ? "text-amber-400" : "text-slate-300")
                    }
                  >
                    <Icon size={14} strokeWidth={1.6} className="text-amber-500/80" />
                    {t(`nav.${labelKey}`)}
                  </NavLink>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {user?.role === "admin" && (
            <NavLink
              to={adminItem.to}
              data-testid={adminItem.testId}
              className={({ isActive }) =>
                "flex items-center gap-2 px-3 py-2 text-[13px] font-medium rounded-sm transition-colors " +
                (isActive
                  ? "text-red-400 bg-red-500/10 border-b-2 border-red-500"
                  : "text-slate-400 hover:text-white hover:bg-white/5")
              }
            >
              <ShieldAlert size={14} strokeWidth={1.6} />
              <span>Admin</span>
            </NavLink>
          )}
        </nav>

        <div className="flex items-center gap-2">
          {!loading && user ? (
            <div className="flex items-center gap-2" data-testid="auth-user-block">
              {user.picture ? (
                <img src={user.picture} alt="" className="w-7 h-7 rounded-full border border-amber-500/50" />
              ) : (
                <div className="w-7 h-7 rounded-full border border-amber-500/50 bg-amber-500/10 flex items-center justify-center text-[10px] font-mono text-amber-500">
                  {user.name?.[0] || "?"}
                </div>
              )}
              <span className="hidden md:inline text-[11px] font-mono text-slate-300 max-w-[130px] truncate" data-testid="auth-user-email">
                {user.email}
              </span>
              <button
                onClick={logout}
                data-testid="logout-btn"
                className="p-2 rounded-sm border border-white/10 hover:border-red-500/50 text-slate-400 hover:text-red-400 transition-colors"
                title="Logout"
              >
                <LogOut size={12} strokeWidth={1.6} />
              </button>
            </div>
          ) : !loading ? (
            <button
              onClick={loginWithGoogle}
              data-testid="login-btn"
              className="flex items-center gap-2 px-3 py-2 rounded-sm border border-amber-500/50 hover:bg-amber-500 hover:text-black text-amber-400 transition-colors text-xs font-mono uppercase tracking-wider"
            >
              <LogIn size={12} strokeWidth={1.7} />
              Sign in
            </button>
          ) : null}
          <button
            onClick={toggleLang}
            data-testid="lang-toggle"
            className="flex items-center gap-2 px-3 py-2 rounded-sm border border-white/10 text-slate-300 hover:text-white hover:border-amber-500/50 transition-colors text-xs font-mono uppercase tracking-wider"
          >
            <Languages size={14} strokeWidth={1.6} />
            {i18n.language === "de" ? "DE" : "EN"}
          </button>
        </div>
      </div>

      {/* mobile nav */}
      <nav className="lg:hidden flex items-center gap-1 overflow-x-auto px-6 pb-2 border-t border-white/5">
        {[...coreItems, ...pniaItems, ...(user?.role === "admin" ? [adminItem] : [])].map(
          ({ to, labelKey, icon: Icon, testId }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              data-testid={`m-${testId}`}
              className={({ isActive }) =>
                "flex items-center gap-1.5 px-3 py-1.5 text-[11px] rounded-sm transition-colors whitespace-nowrap " +
                (isActive
                  ? labelKey === "admin"
                    ? "text-red-400 bg-red-500/10"
                    : "text-amber-400 bg-amber-500/10"
                  : "text-slate-400 hover:text-white")
              }
            >
              <Icon size={12} strokeWidth={1.6} />
              {labelKey === "admin" ? "Admin" : t(`nav.${labelKey}`)}
            </NavLink>
          )
        )}
      </nav>
    </header>
  );
}
