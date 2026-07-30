import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Loader2, CheckCircle2, XCircle, Copy, Ticket, KeySquare, ShieldCheck, ChevronRight, Lock } from "lucide-react";
import { toast } from "sonner";
import {
  fetchNonce,
  issueCredential,
  verifyPresentation,
  issueMdoc,
  verifyMdoc,
  countryVerify,
  listCountries,
} from "../lib/api";
import { generateHolderKey, signProofJwt } from "../lib/crypto";
import { useAuth } from "../lib/auth";

function CopyButton({ text, testId }) {
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        toast.success("Copied");
      }}
      data-testid={testId}
      className="text-slate-500 hover:text-amber-500 transition-colors"
      title="Copy"
    >
      <Copy size={13} strokeWidth={1.6} />
    </button>
  );
}

function StatusPill({ ok, testId }) {
  return (
    <div
      data-testid={testId}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-mono rounded-sm border ${
        ok
          ? "text-emerald-400 border-emerald-500/40 bg-emerald-500/10 glow-emerald"
          : "text-red-400 border-red-500/40 bg-red-500/10"
      }`}
    >
      {ok ? <CheckCircle2 size={11} strokeWidth={2} /> : <XCircle size={11} strokeWidth={2} />}
      {ok ? "VALID" : "INVALID"}
    </div>
  );
}

function SdJwtFlow() {
  const { t, i18n } = useTranslation();
  const { user, loginWithGoogle } = useAuth();
  const [busy, setBusy] = useState(false);
  const [nonce, setNonce] = useState(null);
  const [holder, setHolder] = useState(null);
  const [claims, setClaims] = useState({
    family_name: "Doe",
    given_name: "John",
    birth_date: "1990-01-01",
    email: "john@example.eu",
  });
  const [vct, setVct] = useState("eu.europa.ec.eudi.pid.1");
  const [country, setCountry] = useState("EU");
  const [credential, setCredential] = useState(null);
  const [verifyResult, setVerifyResult] = useState(null);

  const step1 = async () => {
    setBusy(true);
    try {
      const r = await fetchNonce();
      setNonce(r.c_nonce);
      toast.success("Nonce received");
    } catch (e) {
      toast.error("Nonce failed");
    } finally {
      setBusy(false);
    }
  };

  const step2 = async () => {
    if (!nonce) {
      toast.error("Fetch nonce first");
      return;
    }
    if (!user) {
      toast.error(i18n.language === "de" ? "Bitte einloggen zum Ausstellen" : "Sign in required to issue credentials");
      return;
    }
    setBusy(true);
    try {
      const key = await generateHolderKey();
      setHolder(key);
      const proof = await signProofJwt(key.privateKey, key.publicJwk, {
        audience: process.env.REACT_APP_BACKEND_URL,
        nonce,
      });
      const cred = await issueCredential({
        vct,
        subject_claims: claims,
        holder_jwk: key.publicJwk,
        proof_jwt: proof,
        country_code: country,
      });
      setCredential(cred);
      setVerifyResult(null);
      setNonce(null);
      toast.success("Credential issued");
    } catch (e) {
      if (e?.response?.status === 401) {
        toast.error(i18n.language === "de" ? "Session abgelaufen — bitte erneut einloggen" : "Session expired — sign in again");
      } else {
        toast.error("Issue failed: " + (e?.response?.data?.detail?.error || e.message));
      }
    } finally {
      setBusy(false);
    }
  };

  const step3 = async () => {
    if (!credential) {
      toast.error(t("sandbox.no_credential"));
      return;
    }
    setBusy(true);
    try {
      const r = await verifyPresentation({ presentation: credential.credential });
      setVerifyResult(r);
      toast[r.valid ? "success" : "error"](r.valid ? t("sandbox.valid") : t("sandbox.invalid"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid grid-cols-12 gap-6">
      {/* Left: form */}
      <div className="col-span-12 lg:col-span-5 space-y-5">
        <div className="border border-white/10 bg-[#0a0f19] p-5 rounded-sm">
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-3">
            <Ticket size={11} className="inline mr-1" strokeWidth={1.6} /> {t("sandbox.step1")}
          </div>
          <button
            onClick={step1}
            disabled={busy}
            data-testid="sandbox-get-nonce-btn"
            className="w-full flex items-center justify-center gap-2 border border-amber-500/60 hover:bg-amber-500 hover:text-black text-amber-400 px-4 py-2.5 rounded-sm text-sm font-medium transition-colors disabled:opacity-50"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : null}
            {t("sandbox.get_nonce")}
          </button>
          {nonce && (
            <div className="mt-3 flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-500/[0.06] border border-emerald-500/20 rounded-sm px-2.5 py-1.5" data-testid="sandbox-nonce-display">
              <CheckCircle2 size={11} />
              <span className="truncate">{nonce}</span>
              <CopyButton text={nonce} testId="copy-nonce" />
            </div>
          )}
        </div>

        <div className="border border-white/10 bg-[#0a0f19] p-5 rounded-sm">
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-4">
            <KeySquare size={11} className="inline mr-1" strokeWidth={1.6} /> {t("sandbox.step2")}
          </div>
          <div className="space-y-3">
            <div>
              <Label className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                {t("sandbox.vct")}
              </Label>
              <Select value={vct} onValueChange={setVct}>
                <SelectTrigger data-testid="vct-select" className="mt-1 bg-[#050a12] border-white/10 h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="eu.europa.ec.eudi.pid.1">eu.europa.ec.eudi.pid.1</SelectItem>
                  <SelectItem value="eu.europa.ec.eudi.mdl.1">eu.europa.ec.eudi.mdl.1</SelectItem>
                  <SelectItem value="eu.europa.ec.eudi.email.1">eu.europa.ec.eudi.email.1</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                ["family_name", t("sandbox.family_name")],
                ["given_name", t("sandbox.given_name")],
                ["birth_date", t("sandbox.birth_date")],
                ["email", t("sandbox.email")],
              ].map(([k, l]) => (
                <div key={k}>
                  <Label className="text-[10px] font-mono uppercase tracking-wider text-slate-400">{l}</Label>
                  <Input
                    value={claims[k]}
                    onChange={(e) => setClaims({ ...claims, [k]: e.target.value })}
                    data-testid={`claim-${k}`}
                    className="mt-1 bg-[#050a12] border-white/10 h-9 font-mono text-[13px]"
                  />
                </div>
              ))}
            </div>
            <div>
              <Label className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                {t("sandbox.country")}
              </Label>
              <Select value={country} onValueChange={setCountry}>
                <SelectTrigger data-testid="country-select" className="mt-1 bg-[#050a12] border-white/10 h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["EU", "FR", "IT", "CH", "DE", "PT", "SE"].map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <button
              onClick={step2}
              disabled={busy || !nonce || !user}
              data-testid="sandbox-issue-btn"
              className="w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-black px-4 py-2.5 rounded-sm text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {busy ? <Loader2 size={14} className="animate-spin" /> : !user ? <Lock size={13} /> : null}
              {t("sandbox.issue")}
            </button>
            {!user && (
              <button
                onClick={loginWithGoogle}
                data-testid="sandbox-sign-in-hint"
                className="w-full flex items-center justify-center gap-2 border border-amber-500/40 text-amber-400/90 hover:text-amber-400 rounded-sm py-2 text-[11px] font-mono uppercase tracking-wider transition-colors"
              >
                <Lock size={11} strokeWidth={1.7} />
                {i18n.language === "de"
                  ? "Sign-in erforderlich — Emergent Google Auth"
                  : "Sign in required — Emergent Google Auth"}
              </button>
            )}
          </div>
        </div>

        <div className="border border-white/10 bg-[#0a0f19] p-5 rounded-sm">
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-blue-400 mb-3">
            <ShieldCheck size={11} className="inline mr-1" strokeWidth={1.6} /> {t("sandbox.step3")}
          </div>
          <button
            onClick={step3}
            disabled={busy || !credential}
            data-testid="sandbox-verify-btn"
            className="w-full flex items-center justify-center gap-2 border border-blue-500/60 hover:bg-blue-500 hover:text-black text-blue-400 px-4 py-2.5 rounded-sm text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : null}
            {t("sandbox.verify")}
          </button>
        </div>
      </div>

      {/* Right: results (JSON viewer) */}
      <div className="col-span-12 lg:col-span-7 space-y-5">
        <div className="border border-white/10 bg-[#050a12] rounded-sm">
          <div className="flex items-center justify-between border-b border-white/5 px-4 py-2.5">
            <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-slate-500">
              {t("sandbox.credential_result")}
            </div>
            {credential && <CopyButton text={credential.credential} testId="copy-cred" />}
          </div>
          <pre
            data-testid="credential-result"
            className="p-4 text-[11px] font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap break-all max-h-72"
          >
            {credential
              ? JSON.stringify(credential, null, 2)
              : "// awaiting issuance"}
          </pre>
        </div>
        <div className="border border-white/10 bg-[#050a12] rounded-sm">
          <div className="flex items-center justify-between border-b border-white/5 px-4 py-2.5">
            <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-slate-500">
              {t("sandbox.verify_result")}
            </div>
            {verifyResult && <StatusPill ok={verifyResult.valid} testId="verify-status-pill" />}
          </div>
          <pre
            data-testid="verify-result"
            className="p-4 text-[11px] font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-72"
          >
            {verifyResult
              ? JSON.stringify(verifyResult, null, 2)
              : "// awaiting verification"}
          </pre>
        </div>
      </div>
    </div>
  );
}

function MDocFlow() {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [doctype, setDoctype] = useState("org.iso.18013.5.1.mDL");
  const [ns] = useState("org.iso.18013.5.1");
  const [claims, setClaims] = useState({
    family_name: "Doe",
    given_name: "John",
    birth_date: "1990-01-01",
    issuing_country: "EU",
  });
  const [mdoc, setMdoc] = useState(null);
  const [verifyResult, setVerifyResult] = useState(null);

  const doIssue = async () => {
    setBusy(true);
    try {
      const key = await generateHolderKey();
      const r = await issueMdoc({
        doctype,
        namespaces: { [ns]: claims },
        device_public_key: key.publicJwk,
        country_code: "EU",
      });
      setMdoc(r);
      setVerifyResult(null);
      toast.success("mDoc issued");
    } catch (e) {
      toast.error("Issue failed");
    } finally {
      setBusy(false);
    }
  };

  const doVerify = async () => {
    if (!mdoc) return;
    setBusy(true);
    try {
      const r = await verifyMdoc({ mdoc_hex: mdoc.mdoc_hex });
      setVerifyResult(r);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid grid-cols-12 gap-6">
      <div className="col-span-12 lg:col-span-5 space-y-5">
        <div className="border border-white/10 bg-[#0a0f19] p-5 rounded-sm">
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-4">
            ISO 18013-5 mDoc
          </div>
          <div className="space-y-3">
            <div>
              <Label className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                {t("sandbox.mdoc_doctype")}
              </Label>
              <Input
                value={doctype}
                onChange={(e) => setDoctype(e.target.value)}
                data-testid="mdoc-doctype"
                className="mt-1 bg-[#050a12] border-white/10 h-9 font-mono text-[13px]"
              />
            </div>
            <div>
              <Label className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                {t("sandbox.mdoc_namespace")}
              </Label>
              <Input
                value={ns}
                disabled
                data-testid="mdoc-namespace"
                className="mt-1 bg-[#050a12] border-white/10 h-9 font-mono text-[13px] text-slate-400"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(claims).map(([k, v]) => (
                <div key={k}>
                  <Label className="text-[10px] font-mono uppercase tracking-wider text-slate-400">{k}</Label>
                  <Input
                    value={v}
                    onChange={(e) => setClaims({ ...claims, [k]: e.target.value })}
                    data-testid={`mdoc-claim-${k}`}
                    className="mt-1 bg-[#050a12] border-white/10 h-9 font-mono text-[13px]"
                  />
                </div>
              ))}
            </div>
            <div className="flex gap-3 pt-1">
              <button
                onClick={doIssue}
                disabled={busy}
                data-testid="mdoc-issue-btn"
                className="flex-1 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-black px-4 py-2.5 rounded-sm text-sm font-semibold transition-colors disabled:opacity-40"
              >
                {busy ? <Loader2 size={14} className="animate-spin" /> : null}
                {t("sandbox.issue")}
              </button>
              <button
                onClick={doVerify}
                disabled={busy || !mdoc}
                data-testid="mdoc-verify-btn"
                className="flex-1 flex items-center justify-center gap-2 border border-blue-500/60 hover:bg-blue-500 hover:text-black text-blue-400 px-4 py-2.5 rounded-sm text-sm font-medium transition-colors disabled:opacity-40"
              >
                {t("sandbox.verify")}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="col-span-12 lg:col-span-7 space-y-5">
        <div className="border border-white/10 bg-[#050a12] rounded-sm">
          <div className="flex items-center justify-between border-b border-white/5 px-4 py-2.5">
            <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-slate-500">
              {t("sandbox.mdoc_hex")}
            </div>
            {mdoc && <CopyButton text={mdoc.mdoc_hex} testId="copy-mdoc" />}
          </div>
          <pre
            data-testid="mdoc-hex-view"
            className="p-4 text-[11px] font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap break-all max-h-56"
          >
            {mdoc?.mdoc_hex || "// awaiting issuance"}
          </pre>
        </div>
        <div className="border border-white/10 bg-[#050a12] rounded-sm">
          <div className="flex items-center justify-between border-b border-white/5 px-4 py-2.5">
            <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-slate-500">
              {t("sandbox.verify_result")}
            </div>
            {verifyResult && <StatusPill ok={verifyResult.valid} testId="mdoc-verify-pill" />}
          </div>
          <pre
            data-testid="mdoc-verify-result"
            className="p-4 text-[11px] font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-72"
          >
            {verifyResult ? JSON.stringify(verifyResult, null, 2) : "// awaiting verification"}
          </pre>
        </div>
      </div>
    </div>
  );
}

function CountryFlow() {
  const { t } = useTranslation();
  const [countries, setCountries] = useState([]);
  const [pick, setPick] = useState("EU");
  const [presentation, setPresentation] = useState("");
  const [format, setFormat] = useState("sd-jwt");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  React.useEffect(() => {
    listCountries().then(setCountries).catch(() => setCountries([]));
  }, []);

  const doVerify = async () => {
    if (!presentation) {
      toast.error("Paste a presentation string");
      return;
    }
    setBusy(true);
    try {
      const r = await countryVerify({ country_code: pick, presentation, format });
      setResult(r);
    } catch (e) {
      toast.error("Verify failed");
    } finally {
      setBusy(false);
    }
  };

  const active = countries.find((c) => c.code === pick);

  return (
    <div className="grid grid-cols-12 gap-6">
      <div className="col-span-12 lg:col-span-5 space-y-5">
        <div className="border border-white/10 bg-[#0a0f19] p-5 rounded-sm">
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500 mb-4">
            {t("sandbox.country_pick")}
          </div>
          <div className="grid grid-cols-3 gap-2">
            {countries.map((c) => (
              <button
                key={c.code}
                onClick={() => setPick(c.code)}
                data-testid={`country-btn-${c.code}`}
                data-active={pick === c.code}
                className={`trace-beam text-left p-2.5 border rounded-sm transition-colors ${
                  pick === c.code
                    ? "border-amber-500 bg-amber-500/10"
                    : "border-white/10 hover:border-white/25"
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-lg">{c.flag}</span>
                  <span className="font-mono text-[11px] text-slate-300">{c.code}</span>
                </div>
                <div className="mt-1 text-[10px] text-slate-500 line-clamp-1">{c.name}</div>
              </button>
            ))}
          </div>

          {active && (
            <div className="mt-4 pt-4 border-t border-white/5 text-[11px] font-mono text-slate-400 space-y-1.5">
              <div>
                <span className="text-slate-500">scheme:</span> <span className="text-white">{active.scheme}</span>
              </div>
              <div>
                <span className="text-slate-500">framework:</span> <span className="text-white">{active.trust_framework}</span>
              </div>
              <div>
                <span className="text-slate-500">id_hash:</span> <span className="text-amber-500">{active.id_hash_algorithm}</span>
              </div>
              <div>
                <span className="text-slate-500">status:</span>{" "}
                <span className={active.implemented ? "text-emerald-400" : "text-yellow-500"}>
                  {active.implemented ? t("federation.implemented") : t("federation.stub")}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="border border-white/10 bg-[#0a0f19] p-5 rounded-sm">
          <Label className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Format</Label>
          <Select value={format} onValueChange={setFormat}>
            <SelectTrigger data-testid="country-format" className="mt-1 bg-[#050a12] border-white/10 h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="sd-jwt">sd-jwt</SelectItem>
              <SelectItem value="mdoc">mdoc</SelectItem>
              <SelectItem value="ldp-vc">ldp-vc</SelectItem>
            </SelectContent>
          </Select>
          <Label className="mt-4 block text-[10px] font-mono uppercase tracking-wider text-slate-400">
            Presentation (paste from Sandbox)
          </Label>
          <textarea
            value={presentation}
            onChange={(e) => setPresentation(e.target.value)}
            data-testid="country-presentation"
            rows={6}
            className="mt-1 w-full bg-[#050a12] border border-white/10 rounded-sm p-2 text-[11px] font-mono text-slate-300 outline-none focus:border-amber-500/60"
          />
          <button
            onClick={doVerify}
            disabled={busy}
            data-testid="country-verify-btn"
            className="mt-3 w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-black px-4 py-2.5 rounded-sm text-sm font-semibold transition-colors disabled:opacity-40"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : null}
            {t("sandbox.country_verify")}
          </button>
        </div>
      </div>
      <div className="col-span-12 lg:col-span-7">
        <div className="border border-white/10 bg-[#050a12] rounded-sm">
          <div className="flex items-center justify-between border-b border-white/5 px-4 py-2.5">
            <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-slate-500">
              {t("sandbox.verify_result")}
            </div>
            {result && <StatusPill ok={result.valid} testId="country-status-pill" />}
          </div>
          <pre
            data-testid="country-verify-result"
            className="p-4 text-[11px] font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-[600px]"
          >
            {result ? JSON.stringify(result, null, 2) : "// awaiting verification"}
          </pre>
        </div>
      </div>
    </div>
  );
}

export default function Sandbox() {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-[1500px] px-6 lg:px-10 py-12">
      <div className="mb-8 flex items-center gap-3 text-[10px] font-mono uppercase tracking-[0.22em] text-amber-500">
        REFERENCE SANDBOX <ChevronRight size={11} className="text-slate-600" /> Live
      </div>
      <h1 className="font-serif font-light text-4xl lg:text-5xl text-white leading-tight mb-3">
        {t("sandbox.title")}
      </h1>
      <p className="text-slate-400 max-w-2xl mb-10">{t("sandbox.subtitle")}</p>

      <Tabs defaultValue="sdjwt">
        <TabsList
          data-testid="sandbox-tabs"
          className="bg-[#0a0f19] border border-white/10 rounded-sm h-11 p-1"
        >
          <TabsTrigger
            value="sdjwt"
            data-testid="tab-sdjwt"
            className="rounded-sm data-[state=active]:bg-amber-500 data-[state=active]:text-black text-slate-400 px-4"
          >
            {t("sandbox.tabs.sdjwt")}
          </TabsTrigger>
          <TabsTrigger
            value="mdoc"
            data-testid="tab-mdoc"
            className="rounded-sm data-[state=active]:bg-amber-500 data-[state=active]:text-black text-slate-400 px-4"
          >
            {t("sandbox.tabs.mdoc")}
          </TabsTrigger>
          <TabsTrigger
            value="country"
            data-testid="tab-country"
            className="rounded-sm data-[state=active]:bg-amber-500 data-[state=active]:text-black text-slate-400 px-4"
          >
            {t("sandbox.tabs.country")}
          </TabsTrigger>
        </TabsList>
        <TabsContent value="sdjwt" className="mt-6">
          <SdJwtFlow />
        </TabsContent>
        <TabsContent value="mdoc" className="mt-6">
          <MDocFlow />
        </TabsContent>
        <TabsContent value="country" className="mt-6">
          <CountryFlow />
        </TabsContent>
      </Tabs>
    </div>
  );
}
