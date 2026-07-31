import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || (typeof window !== "undefined" ? window.location.origin : "");
export const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// --- Bearer token storage (memory-first, sessionStorage fallback) ---
//
// Kubernetes ingress overrides CORS wildcards, so we cannot rely on
// backend-set HttpOnly cookies from the browser. We therefore keep the token
// in JS-accessible storage, but harden it two ways:
//
//   1. PRIMARY: an in-memory reference — cleared on hard reload / navigation
//      away from the SPA. This is what every request reads from.
//   2. FALLBACK: window.sessionStorage — dies when the tab closes. Used only
//      to survive soft in-app reloads.
//
// We deliberately do NOT use window.localStorage because it survives across
// tabs/windows and browser restarts, expanding the XSS blast radius.
const TOKEN_KEY = "eudi_session_token";
let _memoryToken = null;

function _readSessionStorage() {
  try {
    return typeof window !== "undefined" && window.sessionStorage
      ? window.sessionStorage.getItem(TOKEN_KEY)
      : null;
  } catch {
    return null;
  }
}

function _writeSessionStorage(t) {
  try {
    if (typeof window === "undefined" || !window.sessionStorage) return;
    if (t) window.sessionStorage.setItem(TOKEN_KEY, t);
    else window.sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // sessionStorage may be blocked in private mode — memory fallback still works.
  }
}

// One-time migration: if a legacy token is still sitting in localStorage from
// a previous release, hoist it into sessionStorage + memory and wipe it.
function _migrateLegacyLocalStorage() {
  try {
    if (typeof window === "undefined" || !window.localStorage) return;
    const legacy = window.localStorage.getItem(TOKEN_KEY);
    if (legacy) {
      _memoryToken = legacy;
      _writeSessionStorage(legacy);
      window.localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // ignore quota / access errors
  }
}
_migrateLegacyLocalStorage();

export function setSessionToken(t) {
  _memoryToken = t || null;
  _writeSessionStorage(t || null);
}
export function getSessionToken() {
  if (_memoryToken) return _memoryToken;
  const fromSession = _readSessionStorage();
  if (fromSession) _memoryToken = fromSession;
  return _memoryToken;
}

api.interceptors.request.use((cfg) => {
  const t = getSessionToken();
  if (t) cfg.headers["Authorization"] = `Bearer ${t}`;
  return cfg;
});

// ---- Concept Paper ----
export const listChapters = () => api.get("/paper/chapters").then((r) => r.data);
export const getChapter = (slug) => api.get(`/paper/chapters/${slug}`).then((r) => r.data);
export const searchChapters = (q) => api.get(`/paper/search`, { params: { q } }).then((r) => r.data);

// ---- Issuer / Verifier ----
export const fetchNonce = () => api.post("/issuer/nonce").then((r) => r.data);
export const issueCredential = (body) => api.post("/issuer/credential", body).then((r) => r.data);
export const revokeCredential = (idx) => api.post(`/issuer/status-list/primary/revoke/${idx}`).then((r) => r.data);
export const verifyPresentation = (body) => api.post("/verifier/verify", body).then((r) => r.data);

// ---- mDoc ----
export const issueMdoc = (body) => api.post("/mdoc/issue", body).then((r) => r.data);
export const verifyMdoc = (body) => api.post("/mdoc/verify", body).then((r) => r.data);
export const createEngagement = () => api.post("/mdoc/engagement").then((r) => r.data);

// ---- Trust ----
export const getCaChain = () => api.get("/trust/ca/chain").then((r) => r.data);
export const parseLotl = (xml) => api.post("/trust/lotl/parse", { xml }).then((r) => r.data);

// ---- Compliance ----
export const getMetrics = () => api.get("/compliance/metrics").then((r) => r.data);
export const getAuditLog = () => api.get("/compliance/audit-log").then((r) => r.data);
export const verifyAuditChain = () => api.get("/compliance/audit-log/verify").then((r) => r.data);
export const runErasure = (subject_hash) =>
  api.post("/compliance/gdpr/erasure", { subject_hash, reason: "GDPR Art. 17" }).then((r) => r.data);
export const getAiActTransparency = () => api.get("/compliance/ai-act/transparency").then((r) => r.data);
export const dsaPdfUrl = () => `${API_BASE}/compliance/dsa/report.pdf`;

// ---- Oversight (AI Act Art. 14) ----
export const getDowngrades = () => api.get("/compliance/oversight/downgrades").then((r) => r.data);
export const overrideDecision = (body) => api.post("/compliance/oversight/override", body).then((r) => r.data);

// ---- Countries ----
export const listCountries = () => api.get("/country/list").then((r) => r.data);
export const countryVerify = (body) => api.post("/country/verify", body).then((r) => r.data);

// ---- Hub ----
export const listRepos = () => api.get("/hub/repos").then((r) => r.data);
export const listReposLive = () => api.get("/hub/repos/live").then((r) => r.data);
export const postmanCollectionUrl = () => `${API_BASE}/hub/postman-collection`;

// ---- Discovery ----
export const wellKnown = () => api.get("/.well-known/openid-credential-issuer").then((r) => r.data);
export const jwks = () => api.get("/.well-known/jwks.json").then((r) => r.data);

// ---- Auth ----
export const authMe = () => api.get("/auth/me").then((r) => r.data);
export const authSession = (session_id) => api.post("/auth/session", { session_id }).then((r) => r.data);
export const authLogout = () => api.post("/auth/logout").then((r) => r.data);

// ---- Admin (require_admin) ----
export const adminOverview = () => api.get("/admin/overview").then((r) => r.data);
export const adminListUsers = () => api.get("/admin/users").then((r) => r.data);

// ---- PNIA Memorial & Honorary Registry ----
export const pniaListPlaques = (type) =>
  api.get("/pnia/registry/plaques", { params: type ? { type } : {} }).then((r) => r.data);
export const pniaGetPlaque = (id) => api.get(`/pnia/registry/plaques/${id}`).then((r) => r.data);
export const pniaCompliance = () => api.get("/pnia/registry/compliance").then((r) => r.data);
export const pniaAiAudit = () => api.get("/pnia/registry/ai-audit").then((r) => r.data);
export const pniaVerifyAiAudit = () => api.get("/pnia/registry/ai-audit/verify").then((r) => r.data);
export const pniaGenerateTribute = (id, body) =>
  api.post(`/pnia/registry/plaques/${id}/generate-tribute`, body).then((r) => r.data);
export const pniaTranslate = (id, target_language) =>
  api.post(`/pnia/registry/plaques/${id}/translate`, { target_language }).then((r) => r.data);
export const pniaCreateIndividual = (body) =>
  api.post("/pnia/registry/individuals", body).then((r) => r.data);
export const pniaCreateConsent = (body) =>
  api.post("/pnia/registry/consents", body).then((r) => r.data);
export const pniaRevokeConsent = (individual_id) =>
  api.post(`/pnia/registry/consents/${individual_id}/revoke`).then((r) => r.data);
export const pniaCreatePlaque = (body) =>
  api.post("/pnia/registry/plaques", body).then((r) => r.data);
export const pniaLockPlaque = (id) =>
  api.post(`/pnia/registry/plaques/${id}/lock`).then((r) => r.data);

// ---- PNIA Core · Concil Protokoll (CP-01) ----
export const pniaConcept = () => api.get("/pnia/concil/").then((r) => r.data);
export const pniaDiscovery = () => api.get("/pnia/concil/discovery").then((r) => r.data);
export const pniaOwnership = () => api.get("/pnia/concil/ownership").then((r) => r.data);
export const pniaHandshake = (body) =>
  api.post("/pnia/concil/handshake", body).then((r) => r.data);

// ---- Governance Staatenliste ----
export const govStates = (q) =>
  api.get("/governance/states", { params: q ? { q } : {} }).then((r) => r.data);
export const govInfo = () => api.get("/governance/").then((r) => r.data);

// ---- HNOSS Bridge ----
export const hnossInfo = () => api.get("/hnoss-bridge/").then((r) => r.data);
export const hnossPolicies = () => api.get("/hnoss-bridge/policies").then((r) => r.data);
export const hnossMode = () => api.get("/hnoss-bridge/mode").then((r) => r.data);
export const hnossSetMode = (mode) =>
  api.post("/hnoss-bridge/mode", { mode }).then((r) => r.data);
export const hnossTransfer = (body) =>
  api.post("/hnoss-bridge/transfer", body).then((r) => r.data);
export const hnossTransfers = () => api.get("/hnoss-bridge/transfers").then((r) => r.data);

// ---- PNIA memorial detail context ----
export const pniaPlaqueContext = (id) =>
  api.get(`/pnia/registry/plaques/${id}/context`).then((r) => r.data);

export default api;
