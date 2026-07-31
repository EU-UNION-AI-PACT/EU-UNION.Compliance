import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Terminal,
  AlertTriangle,
  Trash2,
  GitBranch,
  Unlock,
  Lock,
  RefreshCw,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Star,
  Clock,
  Users,
  Fingerprint,
  Zap,
  Send,
} from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../lib/auth";
import {
  adminOverview,
  adminListUsers,
  runErasure,
  listReposLive,
  getAuditLog,
} from "../lib/api";
import { DowngradePanel } from "../components/DowngradePanel";

function TabButton({ id, label, icon: Icon, active, onClick, testId }) {
  return (
    <button
      onClick={onClick}
      data-testid={testId}
      data-active={active}
      className={`flex items-center gap-2 px-4 py-2 text-[11.5px] font-mono uppercase tracking-wider rounded-sm border transition-colors ${
        active
          ? "bg-amber-500/10 border-amber-500 text-amber-500"
          : "bg-[#0a0f19]/60 border-white/10 text-slate-400 hover:text-white hover:border-white/25"
      }`}
    >
      <Icon size={13} strokeWidth={1.7} />
      <span>{label}</span>
    </button>
  );
}

function StatCard({ label, value, sub, tint = "amber", testId }) {
  const cls =
    tint === "amber"
      ? "border-amber-500/25"
      : tint === "blue"
      ? "border-blue-500/25"
      : tint === "emerald"
      ? "border-emerald-500/25"
      : "border-white/10";
  return (
    <div className={`bg-[#0a0f19] border ${cls} p-5 rounded-sm`} data-testid={testId}>
      <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500 mb-2">{label}</div>
      <div className="font-serif text-3xl font-light text-white">{value}</div>
      {sub && <div className="mt-2 text-[10px] text-emerald-400 font-mono">{sub}</div>}
    </div>
  );
}

function OverviewTab() {
  const [snap, setSnap] = useState(null);
  const [users, setUsers] = useState([]);
  const [busy, setBusy] = useState(false);
  const refresh = async () => {
    setBusy(true);
    try {
      const [o, u] = await Promise.all([adminOverview(), adminListUsers()]);
      setSnap(o);
      setUsers(u);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    refresh();
  }, []);
  if (!snap) return <div className="text-slate-500 text-sm font-mono">Loading system snapshot…</div>;
  return (
    <div className="space-y-6" data-testid="admin-overview-tab">
      <div className="flex items-center justify-between">
        <div className="text-[11px] font-mono uppercase tracking-widest text-slate-500">
          real-time snapshot · every metric backed by a mongo query
        </div>
        <button
          onClick={refresh}
          disabled={busy}
          data-testid="admin-refresh-overview"
          className="p-2 rounded-sm border border-white/10 hover:border-amber-500/50 text-slate-300 hover:text-amber-500 transition-colors disabled:opacity-40"
        >
          <RefreshCw size={12} className={busy ? "animate-spin" : ""} strokeWidth={1.7} />
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          label="Adapters implemented"
          value={`${snap.system.adapters_implemented} / ${snap.system.adapters_total}`}
          sub={snap.system.adapters_implemented === snap.system.adapters_total ? "✓ every jurisdiction wired" : "gaps remain"}
          tint="amber"
          testId="admin-stat-adapters"
        />
        <StatCard
          label="CA hierarchy"
          value={`${snap.system.ca_material_docs}-level`}
          sub="AES-256-GCM wrapped"
          tint="emerald"
          testId="admin-stat-ca"
        />
        <StatCard
          label="Audit chain"
          value={snap.audit.chain_valid ? "INTACT" : "BROKEN"}
          sub={`${snap.audit.chain_checked} events checked`}
          tint={snap.audit.chain_valid ? "emerald" : "amber"}
          testId="admin-stat-chain"
        />
        <StatCard label="Credentials issued" value={snap.credentials.issued_total} tint="amber" testId="admin-stat-cred" />
        <StatCard label="Audit events" value={snap.audit.events_total} tint="blue" testId="admin-stat-audit" />
        <StatCard
          label="Downgrades pending"
          value={snap.oversight.downgrades_pending}
          sub={`${snap.oversight.downgrades_total} total`}
          tint={snap.oversight.downgrades_pending > 0 ? "amber" : "emerald"}
          testId="admin-stat-downgrades"
        />
      </div>

      <div className="border border-white/10 bg-[#0a0f19] rounded-sm">
        <div className="border-b border-white/5 px-5 py-3 flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500">
          <Users size={12} strokeWidth={1.7} /> Users & sessions ({snap.users.total} total, {snap.users.admins} admins, {snap.users.active_sessions} active sessions)
        </div>
        <table className="w-full text-[11.5px] font-mono">
          <thead className="text-slate-500 text-[9px] uppercase tracking-widest">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Email</th>
              <th className="text-left px-4 py-2 font-medium">Name</th>
              <th className="text-left px-4 py-2 font-medium">Role</th>
              <th className="text-left px-4 py-2 font-medium">User ID</th>
              <th className="text-left px-4 py-2 font-medium">Created</th>
            </tr>
          </thead>
          <tbody>
            {users.slice(0, 20).map((u) => (
              <tr key={u.user_id} className="border-t border-white/5 hover:bg-white/[0.02]" data-testid={`admin-user-${u.user_id}`}>
                <td className="px-4 py-2 text-white truncate max-w-[240px]">{u.email}</td>
                <td className="px-4 py-2 text-slate-300">{u.name}</td>
                <td className="px-4 py-2">
                  {u.role === "admin" ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-sm border border-amber-500/40 bg-amber-500/10 text-amber-500">
                      ADMIN
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-500">user</span>
                  )}
                </td>
                <td className="px-4 py-2 text-slate-500 truncate max-w-[160px]">{u.user_id}</td>
                <td className="px-4 py-2 text-slate-500">{String(u.created_at || "").slice(0, 19)}</td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                  No users yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function GdprTab() {
  const [hash, setHash] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState([]);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const refresh = async () => {
    const log = await getAuditLog();
    setHistory(log.filter((e) => e.event_type === "gdpr.erasure").slice(0, 25));
  };
  useEffect(() => {
    refresh();
  }, []);

  const execute = async () => {
    setBusy(true);
    try {
      const r = await runErasure(hash);
      toast.success(`Erased ${r.deleted} records for subject_hash=${hash.slice(0, 12)}…`);
      setHash("");
      setConfirmOpen(false);
      await refresh();
    } catch (e) {
      toast.error("Erasure failed: " + (e?.response?.data?.detail || e.message));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-gdpr-tab">
      <div className="border border-red-500/25 bg-[#0a0f19] p-6 rounded-sm">
        <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.22em] text-red-400 mb-4">
          <Trash2 size={12} strokeWidth={1.7} /> GDPR Art. 17 · Right-to-be-forgotten
        </div>
        <p className="text-slate-400 text-sm mb-5 max-w-2xl">
          Executes a signed erasure event: deletes matching{" "}
          <code className="text-blue-400">issued_credentials</code> rows by <code className="text-blue-400">subject_hash</code>,
          then appends a hash-chained audit event with your admin identity as the actor. Cleartext PII never enters
          the system — only its SHA-256 hash.
        </p>
        <div className="grid grid-cols-12 gap-3 items-end">
          <div className="col-span-12 md:col-span-8">
            <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">
              subject_hash (SHA-256 hex)
            </label>
            <input
              value={hash}
              onChange={(e) => setHash(e.target.value)}
              data-testid="admin-gdpr-hash"
              placeholder="e.g. 5b3f8c2a…"
              className="w-full bg-[#050a12] border border-white/10 focus:border-red-500/60 rounded-sm px-3 py-2 text-[12px] font-mono text-white outline-none transition-colors"
            />
          </div>
          <div className="col-span-12 md:col-span-4">
            <button
              onClick={() => (confirmOpen ? execute() : setConfirmOpen(true))}
              disabled={busy || !hash || hash.length < 8}
              data-testid="admin-gdpr-execute"
              className={`w-full py-2 px-4 rounded-sm text-[12px] font-mono uppercase tracking-wider transition-colors ${
                confirmOpen
                  ? "bg-red-500 hover:bg-red-400 text-white"
                  : "border border-red-500/50 text-red-400 hover:bg-red-500 hover:text-white"
              } disabled:opacity-40 disabled:cursor-not-allowed`}
            >
              {busy ? "Running…" : confirmOpen ? "Confirm — Execute erasure" : "Execute cryptographic erasure"}
            </button>
            {confirmOpen && (
              <button
                onClick={() => setConfirmOpen(false)}
                className="w-full mt-1.5 text-[10px] text-slate-500 hover:text-white font-mono uppercase tracking-widest"
              >
                cancel
              </button>
            )}
          </div>
        </div>
      </div>
      <div className="border border-white/10 bg-[#0a0f19] rounded-sm">
        <div className="border-b border-white/5 px-5 py-3 flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500">
          <Fingerprint size={12} strokeWidth={1.7} /> Recent GDPR erasure events (audit-log, tamper-evident)
        </div>
        {history.length === 0 ? (
          <div className="p-6 text-center text-[12px] font-mono text-slate-500">
            No erasure events yet.
          </div>
        ) : (
          <div className="max-h-[360px] overflow-y-auto">
            <table className="w-full text-[11px] font-mono">
              <thead className="sticky top-0 bg-[#0a0f19]">
                <tr className="text-slate-500 text-[9px] uppercase tracking-widest">
                  <th className="text-left px-4 py-2 font-medium">Time</th>
                  <th className="text-left px-4 py-2 font-medium">Actor</th>
                  <th className="text-left px-4 py-2 font-medium">Subject Hash</th>
                  <th className="text-left px-4 py-2 font-medium">Deleted</th>
                  <th className="text-left px-4 py-2 font-medium">Hash</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.hash} className="border-t border-white/5">
                    <td className="px-4 py-2 text-slate-400">{h.timestamp?.slice(0, 19)}</td>
                    <td className="px-4 py-2 text-amber-400 truncate max-w-[200px]">{h.actor}</td>
                    <td className="px-4 py-2 text-slate-300 truncate max-w-[200px]">{h.subject?.slice(0, 16)}…</td>
                    <td className="px-4 py-2 text-emerald-400">{h.payload?.records_deleted ?? 0}</td>
                    <td className="px-4 py-2 text-blue-400 truncate max-w-[180px]">{h.hash?.slice(0, 18)}…</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function relative(iso) {
  if (!iso) return "—";
  const d = Math.max(0, Date.now() - new Date(iso).getTime());
  const day = Math.floor(d / 86400e3);
  if (day < 1) return "today";
  if (day < 30) return `${day}d ago`;
  const mo = Math.floor(day / 30);
  return mo < 12 ? `${mo}mo ago` : `${Math.floor(mo / 12)}y ago`;
}

function SyncTab() {
  const [repos, setRepos] = useState([]);
  const [busy, setBusy] = useState(false);
  const refresh = async () => {
    setBusy(true);
    try {
      const r = await listReposLive();
      setRepos(r);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    refresh();
  }, []);
  const reachable = repos.filter((r) => r.github?.reachable);
  const totalStars = reachable.reduce((s, r) => s + (r.github?.stars || 0), 0);
  return (
    <div className="space-y-6" data-testid="admin-sync-tab">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Repos tracked" value={repos.length} tint="amber" />
        <StatCard label="Live GitHub sync" value={`${reachable.length}/${repos.length}`} sub="1h LRU cache" tint="blue" />
        <StatCard label="Aggregate stars" value={totalStars} tint="emerald" />
      </div>
      <div className="border border-white/10 bg-[#0a0f19] rounded-sm">
        <div className="flex items-center justify-between border-b border-white/5 px-5 py-3">
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 flex items-center gap-2">
            <GitBranch size={12} strokeWidth={1.7} /> OSS repo live-sync (GitHub public API)
          </div>
          <button
            onClick={refresh}
            disabled={busy}
            data-testid="admin-sync-refresh"
            className="text-[10px] font-mono uppercase tracking-wider text-slate-400 hover:text-amber-500 flex items-center gap-1"
          >
            <RefreshCw size={11} className={busy ? "animate-spin" : ""} strokeWidth={1.7} />
            refresh
          </button>
        </div>
        <table className="w-full text-[11.5px] font-mono">
          <thead className="text-slate-500 text-[9px] uppercase tracking-widest">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Slug</th>
              <th className="text-left px-4 py-2 font-medium">Category</th>
              <th className="text-left px-4 py-2 font-medium">Stars</th>
              <th className="text-left px-4 py-2 font-medium">Last commit</th>
              <th className="text-left px-4 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {repos.map((r) => (
              <tr key={r.slug} className="border-t border-white/5 hover:bg-white/[0.02]" data-testid={`admin-sync-row-${r.slug.replace(/[/]/g, "-")}`}>
                <td className="px-4 py-2 text-white truncate max-w-[280px]">
                  <a href={r.url} target="_blank" rel="noreferrer" className="hover:text-amber-400">
                    {r.slug}
                  </a>
                </td>
                <td className="px-4 py-2 text-slate-400">{r.category}</td>
                <td className="px-4 py-2 text-amber-500 inline-flex items-center gap-1">
                  <Star size={10} strokeWidth={1.7} /> {r.github?.stars ?? "—"}
                </td>
                <td className="px-4 py-2 text-slate-400 inline-flex items-center gap-1">
                  <Clock size={10} strokeWidth={1.7} /> {relative(r.github?.last_commit)}
                </td>
                <td className="px-4 py-2">
                  {r.github?.reachable ? (
                    <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-sm border border-emerald-500/40 bg-emerald-500/10 text-emerald-400">
                      <CheckCircle2 size={9} /> LIVE
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-sm border border-slate-500/30 bg-slate-500/5 text-slate-500">
                      <XCircle size={9} /> {r.github?.error || "unreachable"}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function AdminPortal() {
  const { user, loading, loginWithGoogle, logout } = useAuth();
  const [tab, setTab] = useState("overview");
  const nav = useNavigate();
  const { t, i18n } = useTranslation();
  const isDE = i18n.language === "de";

  if (loading) {
    return (
      <div className="mx-auto max-w-[1500px] px-6 py-12 text-slate-500 text-sm font-mono">
        Loading…
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-lg px-6 py-24 text-center">
        <div className="border border-amber-500/30 bg-[#0a0f19] rounded-sm p-8">
          <div className="w-12 h-12 mx-auto mb-4 rounded-sm border border-amber-500/50 bg-amber-500/10 flex items-center justify-center glow-amber">
            <Lock size={22} className="text-amber-500" strokeWidth={1.7} />
          </div>
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-2">
            {isDE ? "Zugang beschränkt" : "Restricted access"}
          </div>
          <h1 className="font-serif text-2xl text-white mb-3">EUDI-Nexus Admin Portal</h1>
          <p className="text-[13px] text-slate-400 mb-6">
            {isDE
              ? "Bitte melde dich per Emergent Google Auth an. Deine E-Mail muss in ADMIN_EMAILS gelistet sein oder du bist der erste registrierte Nutzer (Bootstrap)."
              : "Sign in with Emergent Google Auth. Your email must be listed in ADMIN_EMAILS or you must be the first registered user (bootstrap)."}
          </p>
          <button
            onClick={loginWithGoogle}
            data-testid="admin-signin-btn"
            className="w-full bg-amber-500 hover:bg-amber-400 text-black font-semibold py-2.5 rounded-sm text-sm transition-colors"
          >
            {isDE ? "Mit Google anmelden" : "Sign in with Google"}
          </button>
        </div>
      </div>
    );
  }

  if (user.role !== "admin") {
    return (
      <div className="mx-auto max-w-lg px-6 py-24 text-center">
        <div className="border border-red-500/30 bg-[#0a0f19] rounded-sm p-8" data-testid="admin-forbidden">
          <ShieldAlert size={22} className="text-red-400 mx-auto mb-4" strokeWidth={1.7} />
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-red-400 mb-2">
            HTTP 403 · Forbidden
          </div>
          <h1 className="font-serif text-2xl text-white mb-3">Admin role required</h1>
          <p className="text-[13px] text-slate-400 mb-4 leading-relaxed">
            {isDE
              ? "Du bist eingeloggt als"
              : "You are signed in as"}{" "}
            <code className="text-amber-500">{user.email}</code>{" — "}
            {isDE
              ? "aber diese E-Mail ist nicht in ADMIN_EMAILS registriert. Setze ADMIN_EMAILS in backend/.env oder logge dich mit einer autorisierten Adresse ein."
              : "but this email is not present in ADMIN_EMAILS. Set ADMIN_EMAILS in backend/.env or sign in with an authorized address."}
          </p>
          <button
            onClick={() => nav("/")}
            className="text-[11px] font-mono uppercase tracking-wider text-slate-400 hover:text-white"
          >
            {isDE ? "← Zurück zur Übersicht" : "← Back to overview"}
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "overview", label: isDE ? "System-Übersicht" : "System overview", icon: Terminal, testId: "admin-tab-overview" },
    { id: "downgrade", label: isDE ? "AI Act Art. 14 Aufsicht" : "AI Act Art. 14 Oversight", icon: AlertTriangle, testId: "admin-tab-downgrade" },
    { id: "gdpr", label: "GDPR Art. 17", icon: Trash2, testId: "admin-tab-gdpr" },
    { id: "sync", label: "GitHub Live-Sync", icon: GitBranch, testId: "admin-tab-sync" },
    { id: "rules", label: isDE ? "Custom Rules" : "Custom Rules", icon: ShieldAlert, testId: "admin-tab-rules" },
    { id: "webhook", label: isDE ? "Ops-Webhook" : "Ops Webhook", icon: Zap, testId: "admin-tab-webhook" },
  ];

  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12">
      <div className="flex items-start justify-between gap-6 mb-8 flex-wrap">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-3 flex items-center gap-2">
            <ShieldAlert size={11} /> EUDI-NEXUS // ADMIN PORTAL
          </div>
          <h1 className="font-serif font-light text-4xl lg:text-5xl text-white leading-tight mb-2">
            {isDE ? "Aufsichts-Deck" : "Supervisory deck"}
          </h1>
          <p className="text-slate-400 max-w-2xl">
            {isDE
              ? "EU AI Act Art. 13/14 Human-Oversight, DSGVO Art. 17 Erasure, GitHub Live-Sync — jede Zelle an einen echten Endpoint gebunden."
              : "EU AI Act Art. 13/14 human oversight, GDPR Art. 17 erasure, GitHub live sync — every cell bound to a real endpoint."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-[10.5px] font-mono px-3 py-1.5 rounded-sm border border-emerald-500/40 bg-emerald-500/10 text-emerald-400" data-testid="admin-session-badge">
            <Unlock size={11} strokeWidth={1.7} />
            {isDE ? "Admin-Session aktiv" : "Admin session active"} · {user.email}
          </div>
          <button
            onClick={logout}
            data-testid="admin-logout"
            className="text-[10.5px] font-mono uppercase tracking-wider text-slate-400 hover:text-white px-3 py-1.5 rounded-sm border border-white/10 hover:border-red-500/50"
          >
            {isDE ? "Sperren" : "Lock session"}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-8">
        {tabs.map((tabItem) => (
          <TabButton
            key={tabItem.id}
            id={tabItem.id}
            label={tabItem.label}
            icon={tabItem.icon}
            active={tab === tabItem.id}
            onClick={() => setTab(tabItem.id)}
            testId={tabItem.testId}
          />
        ))}
      </div>

      {tab === "overview" && <OverviewTab />}
      {tab === "downgrade" && <DowngradePanel />}
      {tab === "gdpr" && <GdprTab />}
      {tab === "sync" && <SyncTab />}
      {tab === "rules" && <CustomRulesTab />}
      {tab === "webhook" && <OpsWebhookTab />}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Custom Rule Editor tab                                                      //
// --------------------------------------------------------------------------- //
function CustomRulesTab() {
  const [frameworks, setFrameworks] = React.useState([]);
  const [selected, setSelected] = React.useState("GDPR");
  const [rules, setRules] = React.useState([]);
  const [allRules, setAllRules] = React.useState([]);
  const [byFw, setByFw] = React.useState({});
  const [field, setField] = React.useState("");
  const [hint, setHint] = React.useState("");
  const [severity, setSeverity] = React.useState("REQUIRED");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);

  const BE = process.env.REACT_APP_BACKEND_URL || window.location.origin;
  const tokenHeader = () => {
    const t = window.localStorage.getItem("eudi_session_token");
    return t ? { Authorization: `Bearer ${t}` } : {};
  };

  const loadFrameworks = async () => {
    try {
      const j = await fetch(`${BE}/api/validate/frameworks?limit=500`).then((r) => r.json());
      setFrameworks(j.frameworks || []);
    } catch (e) {
      setError(e.message);
    }
  };
  const loadAll = async () => {
    try {
      const j = await fetch(`${BE}/api/validate/custom-rules`, { headers: tokenHeader() });
      if (!j.ok) throw new Error(`HTTP ${j.status}`);
      const data = await j.json();
      setAllRules(data.rules || []);
      setByFw(data.by_framework || {});
    } catch (e) {
      setError(`load: ${e.message}`);
    }
  };
  const loadRules = async (code) => {
    try {
      const j = await fetch(`${BE}/api/validate/custom-rules/${encodeURIComponent(code)}`).then((r) => r.json());
      setRules(j.rules || []);
    } catch (e) {
      setError(e.message);
    }
  };

  React.useEffect(() => {
    loadFrameworks();
    loadAll();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  React.useEffect(() => {
    if (selected) loadRules(selected);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  const addRule = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${BE}/api/validate/custom-rules/${encodeURIComponent(selected)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json", ...tokenHeader() },
          body: JSON.stringify({ field, hint, severity }),
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setField("");
      setHint("");
      setSeverity("REQUIRED");
      await Promise.all([loadRules(selected), loadAll()]);
    } catch (e) {
      setError(`add: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };
  const deleteRule = async (id) => {
    setBusy(true);
    try {
      const res = await fetch(`${BE}/api/validate/custom-rules/${id}`, {
        method: "DELETE",
        headers: tokenHeader(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await Promise.all([loadRules(selected), loadAll()]);
    } catch (e) {
      setError(`del: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[300px_minmax(0,1fr)] gap-4" data-testid="custom-rules-tab">
      <div className="border border-white/10 bg-[#0a0f19]/60 rounded-md p-3">
        <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
          Frameworks · {frameworks.length}
        </div>
        <div className="max-h-[520px] overflow-y-auto space-y-1">
          {frameworks.map((f) => (
            <button
              key={f.code}
              data-testid={`rules-pick-${f.code}`}
              onClick={() => setSelected(f.code)}
              className={`w-full text-left px-2 py-1.5 text-[11px] font-mono flex items-center justify-between rounded hover:bg-white/5 ${
                selected === f.code ? "bg-amber-500/10 text-amber-300" : "text-slate-300"
              }`}
            >
              <span className="truncate">{f.code}</span>
              {byFw[f.code.toUpperCase()] > 0 && (
                <span className="ml-2 text-[9px] text-emerald-400">
                  +{byFw[f.code.toUpperCase()]}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <div className="border border-white/10 bg-[#0a0f19]/60 rounded-md p-4">
          <div className="flex items-center gap-3 mb-3">
            <ShieldAlert size={14} className="text-amber-400" />
            <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300">
              Add rule to {selected}
            </span>
            {error && (
              <span className="ml-auto text-[10px] font-mono text-red-400">
                {error}
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-[1fr_2fr_140px_120px] gap-2">
            <input
              value={field}
              onChange={(e) => setField(e.target.value)}
              placeholder="field (e.g. dpia_reference)"
              data-testid="rule-field"
              className="px-3 py-2 bg-black/60 border border-white/10 rounded font-mono text-[11px] text-emerald-300 outline-none focus:border-amber-500/60"
            />
            <input
              value={hint}
              onChange={(e) => setHint(e.target.value)}
              placeholder="hint / statement of reasons"
              data-testid="rule-hint"
              className="px-3 py-2 bg-black/60 border border-white/10 rounded font-mono text-[11px] text-slate-200 outline-none focus:border-amber-500/60"
            />
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              data-testid="rule-severity"
              className="px-3 py-2 bg-black/60 border border-white/10 rounded font-mono text-[11px] text-slate-200 outline-none focus:border-amber-500/60"
            >
              <option value="REQUIRED">REQUIRED</option>
              <option value="RECOMMENDED">RECOMMENDED</option>
            </select>
            <button
              onClick={addRule}
              disabled={busy || !field || !hint}
              data-testid="rule-add"
              className="px-3 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-mono text-[11px] uppercase tracking-wider rounded"
            >
              {busy ? "…" : "add"}
            </button>
          </div>
        </div>

        <div className="border border-white/10 bg-[#0a0f19]/60 rounded-md">
          <div className="p-3 border-b border-white/10 font-mono text-[11px] uppercase tracking-wider text-slate-300">
            {selected} · custom rules ({rules.length})
          </div>
          {rules.length === 0 && (
            <div className="p-6 text-center text-[11px] font-mono text-slate-500">
              no custom rules for {selected} — add one above.
            </div>
          )}
          {rules.map((r) => (
            <div
              key={r.id}
              data-testid={`rule-row-${r.id}`}
              className="p-3 border-b border-white/5 flex items-start gap-3"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-emerald-300">
                    {r.field}
                  </span>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                      r.severity === "REQUIRED"
                        ? "bg-red-500/15 text-red-300 border border-red-500/30"
                        : "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                    }`}
                  >
                    {r.severity}
                  </span>
                  <span className="ml-auto text-[9px] font-mono text-slate-500">
                    by {r.created_by}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-1">{r.hint}</div>
              </div>
              <button
                onClick={() => deleteRule(r.id)}
                data-testid={`rule-del-${r.id}`}
                className="p-1 text-slate-500 hover:text-red-400 border border-white/10 hover:border-red-500/40 rounded"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


// --------------------------------------------------------------------------- //
// Ops Webhook admin tab                                                       //
// --------------------------------------------------------------------------- //
function OpsWebhookTab() {
  const [settings, setSettings] = React.useState({
    webhook_url: "",
    on_fail_only: true,
    min_score: "",
  });
  const [history, setHistory] = React.useState([]);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [saved, setSaved] = React.useState(null);

  const BE = process.env.REACT_APP_BACKEND_URL || window.location.origin;
  const tokenHeader = () => {
    const t = window.localStorage.getItem("eudi_session_token");
    return t ? { Authorization: `Bearer ${t}` } : {};
  };

  const load = async () => {
    setError(null);
    try {
      const j = await fetch(`${BE}/api/validate/ops-webhook`, {
        headers: tokenHeader(),
      });
      if (!j.ok) throw new Error(`HTTP ${j.status}`);
      const data = await j.json();
      setSettings({
        webhook_url: data.settings.webhook_url || "",
        on_fail_only: data.settings.on_fail_only !== false,
        min_score:
          data.settings.min_score === null || data.settings.min_score === undefined
            ? ""
            : String(data.settings.min_score),
      });
      setHistory(data.history || []);
    } catch (e) {
      setError(e.message);
    }
  };

  React.useEffect(() => {
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      const body = {
        webhook_url: settings.webhook_url || null,
        on_fail_only: !!settings.on_fail_only,
        min_score: settings.min_score === "" ? null : parseInt(settings.min_score, 10),
      };
      const res = await fetch(`${BE}/api/validate/ops-webhook`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...tokenHeader() },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSaved(new Date().toISOString());
      await load();
    } catch (e) {
      setError(`save: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const sendTest = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${BE}/api/validate/ops-webhook/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...tokenHeader() },
        body: JSON.stringify({ webhook_url: settings.webhook_url }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await load();
    } catch (e) {
      setError(`test: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4" data-testid="ops-webhook-tab">
      <div className="border border-white/10 bg-[#0a0f19]/60 rounded-md p-4">
        <div className="flex items-center gap-3 mb-4">
          <Zap size={14} className="text-amber-400" />
          <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300">
            Realtime Ops Alert
          </span>
          <span className="text-[10px] font-mono text-slate-500 ml-auto">
            Slack / Teams compatible payload
          </span>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_180px_180px] gap-3">
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">
              Webhook URL
            </label>
            <input
              value={settings.webhook_url}
              onChange={(e) => setSettings({ ...settings, webhook_url: e.target.value })}
              placeholder="https://hooks.slack.com/services/... or https://outlook.office.com/webhook/..."
              data-testid="webhook-url"
              className="w-full px-3 py-2 bg-black/60 border border-white/10 rounded font-mono text-[11px] text-slate-200 outline-none focus:border-amber-500/60"
            />
          </div>
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">
              Trigger
            </label>
            <select
              value={settings.on_fail_only ? "fail" : "any"}
              onChange={(e) =>
                setSettings({ ...settings, on_fail_only: e.target.value === "fail" })
              }
              data-testid="webhook-trigger"
              className="w-full px-3 py-2 bg-black/60 border border-white/10 rounded font-mono text-[11px] text-slate-200 outline-none focus:border-amber-500/60"
            >
              <option value="fail">Only FAIL</option>
              <option value="any">Any status</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">
              Min score (opt.)
            </label>
            <input
              value={settings.min_score}
              onChange={(e) => setSettings({ ...settings, min_score: e.target.value.replace(/[^0-9]/g, "") })}
              placeholder="e.g. 50"
              data-testid="webhook-min-score"
              className="w-full px-3 py-2 bg-black/60 border border-white/10 rounded font-mono text-[11px] text-slate-200 outline-none focus:border-amber-500/60"
            />
          </div>
        </div>
        <div className="flex items-center gap-2 mt-4">
          <button
            onClick={save}
            disabled={busy}
            data-testid="webhook-save"
            className="px-3 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-mono text-[10px] uppercase tracking-wider rounded"
          >
            save
          </button>
          <button
            onClick={sendTest}
            disabled={busy || !settings.webhook_url}
            data-testid="webhook-test"
            className="px-3 py-2 border border-emerald-500/50 text-emerald-400 hover:bg-emerald-500 hover:text-black disabled:opacity-40 font-mono text-[10px] uppercase tracking-wider rounded inline-flex items-center gap-1.5"
          >
            <Send size={11} />
            send test
          </button>
          {saved && (
            <span className="text-[10px] font-mono text-emerald-400 ml-2">
              saved {saved.slice(11, 19)}
            </span>
          )}
          {error && (
            <span className="ml-auto text-[10px] font-mono text-red-400">{error}</span>
          )}
        </div>
      </div>

      <div className="border border-white/10 bg-[#0a0f19]/60 rounded-md">
        <div className="p-3 border-b border-white/10 font-mono text-[11px] uppercase tracking-wider text-slate-300">
          Delivery history · in-process ring buffer · {history.length}
        </div>
        {history.length === 0 && (
          <div className="p-6 text-center text-[11px] font-mono text-slate-500">
            no deliveries yet — press "send test" or wait for a FAIL validation
          </div>
        )}
        {history.map((h, idx) => (
          <div
            key={idx}
            data-testid={`webhook-history-${idx}`}
            className="px-3 py-2 border-b border-white/5 flex items-center gap-3"
          >
            <span
              className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase tracking-wider ${
                h.ok
                  ? "text-emerald-300 border-emerald-500/40 bg-emerald-500/10"
                  : "text-red-300 border-red-500/40 bg-red-500/10"
              }`}
            >
              {h.ok ? "OK" : "FAIL"}
            </span>
            <span className="text-[11px] font-mono text-amber-400 w-24 truncate">
              {h.event?.framework || "—"}
            </span>
            <span className="text-[10px] font-mono text-slate-400 w-16">
              {h.http !== null && h.http !== undefined ? `HTTP ${h.http}` : "err"}
            </span>
            <span className="text-[10px] font-mono text-slate-500 flex-1 truncate">
              {h.error || h.url}
            </span>
            <span className="text-[9px] font-mono text-slate-500 w-32 text-right">
              {(h.at || "").slice(11, 19)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

