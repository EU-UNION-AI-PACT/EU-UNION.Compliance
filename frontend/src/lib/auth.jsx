import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { authMe, authLogout, authSession, setSessionToken, getSessionToken } from "../lib/api";

const AuthContext = createContext({
  user: null,
  loading: true,
  loginWithGoogle: () => {},
  logout: async () => {},
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const check = useCallback(async () => {
    if (!getSessionToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const u = await authMe();
      setUser(u);
    } catch (err) {
      // Session expired or invalid — clear it and force re-login.
      // eslint-disable-next-line no-console
      console.warn("Auth /me failed:", err);
      setSessionToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // CRITICAL: If returning from OAuth callback, skip the /me check.
    // AuthCallback will exchange the session_id and establish the session first.
    if (typeof window !== "undefined" && window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return;
    }
    check();
  }, [check]);

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const loginWithGoogle = () => {
    const redirectUrl = window.location.origin + "/compliance";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const logout = async () => {
    try {
      await authLogout();
    } catch (err) {
      // Backend logout errors are non-fatal — we still clear the local session.
      // eslint-disable-next-line no-console
      console.warn("Backend logout failed (clearing local session anyway):", err);
    }
    setSessionToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, loginWithGoogle, logout, refresh: check }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

/**
 * Detects `#session_id=…` in the URL fragment (read reactively from useLocation),
 * exchanges it for a session_token via the backend, then redirects to /compliance.
 * Used at the App-router level BEFORE regular routes render.
 */
export function AuthCallback() {
  const location = useLocation();
  const nav = useNavigate();
  const { refresh } = useAuth();
  const hasProcessed = React.useRef(false);
  const [err, setErr] = React.useState(null);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;
    const hash = location.hash || "";
    const m = hash.match(/session_id=([^&]+)/);
    if (!m) {
      nav("/", { replace: true });
      return;
    }
    (async () => {
      try {
        const result = await authSession(m[1]);
        if (result?.session_token) setSessionToken(result.session_token);
        await refresh();
        window.history.replaceState(null, "", "/compliance");
        nav("/compliance", { replace: true });
      } catch (e) {
        setErr(e?.response?.data?.detail || e.message);
      }
    })();
  }, [location.hash, nav, refresh]);

  return (
    <div className="min-h-screen bg-[#090d16] flex items-center justify-center text-slate-400">
      <div className="text-center">
        <div className="w-8 h-8 mx-auto mb-4 rounded-full border-2 border-amber-500 border-t-transparent animate-spin" />
        <div className="text-xs font-mono uppercase tracking-widest text-amber-500">
          {err ? "AUTH FAILED" : "AUTHENTICATING…"}
        </div>
        {err && <div className="mt-3 text-xs text-red-400 font-mono">{err}</div>}
      </div>
    </div>
  );
}
