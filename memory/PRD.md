# EUDI-Nexus — Product Requirements Document

## Original Problem Statement
Web-App (React + FastAPI + MongoDB) — eIDAS 2.0 / EUDI-Wallet Referenz-Infrastruktur mit Concept Paper Portal + Reference Sandbox + Compliance Cockpit. SD-JWT VC + ISO 18013-5 mDoc. No-Mocks-Policy strikt. Cyberpunk-Institutional Design.

## Iteration History

### Iteration 1 — Sprint 1-5 MVP (Foundation + SD-JWT + mDoc)
- All crypto services: SD-JWT builder/verifier, mDoc issuer/verifier, persistent 3-level CA, LOTL parser, X.509 chain validator, hash-chained audit log
- 5 concept paper chapters, live sandbox, compliance cockpit, trust pipeline, federation, developer hub
- 4 real country adapters (EU/FR/IT/CH), 7 stubs
- **34/34 backend tests passing**

### Iteration 2 — Sprint 7-9 + Emergent Google Auth
- **Sprint 7**: All 7 stub adapters (PT/SE/NO/DK/IE/BR/US) upgraded to real signature verification with DSGVO-hashing of national IDs (Personnummer, Fødselsnummer, CPR, PPSN, CPF, DL#). All 11 adapters now `implemented=true`.
- **Sprint 8**: LoA-Downgrade-Detection service (`services/oversight.py`) — hooks into every successful verification, maintains per-subject-fingerprint LoA history in Mongo, emits `loa.downgrade` audit events on regression. Human-oversight override endpoint (`POST /api/compliance/oversight/override`) with `accept`/`reject`/`escalate` decisions, audit-logged. Frontend `<DowngradePanel />` in the Compliance page.
- **Sprint 9**: `GET /api/hub/repos/live` — GitHub public-API sync with 1h LRU cache (stars/forks/last_commit/reachability). `GET /api/hub/postman-collection` — on-the-fly OpenAPI → Postman v2.1 conversion. `<DeveloperHub />` shows LIVE badges + a Postman-download button.
- **Emergent Google Auth**: `POST /api/issuer/credential` and `POST /api/compliance/gdpr/erasure` protected via `Depends(require_user)`. Bearer-token flow (Kubernetes ingress overrides CORS wildcards, so we use localStorage + Authorization header instead of cookies). `/api/auth/session` returns `session_token` in JSON body for client-side storage.
- **49/49 backend tests passing** — no critical bugs.
- Code review fixes applied: (1) `/api/auth/logout` now honors Bearer, (2) `create_session` upserts by `session_token`, (3) `OverrideRequest.decision` uses `Literal[...]` → 422 for invalid values (not 500), (4) `subject_fingerprint` uses NFC + casefold() for deterministic locale-independent hashing.

### Iteration 3 — Admin Portal (`/admin`)
- **Role-based access**: `role` field on `users` collection. `require_admin` dependency. Nav-item "Admin" only visible to admin role.
- **Idempotent seeding**: `services/admin_seed.py` reads `ADMIN_EMAILS` env var (comma-separated). Bootstrap: first user to sign in becomes admin if no admins configured and no other users exist.
- **`GET /api/admin/overview`**: aggregate snapshot — adapters, CA docs, audit chain integrity, credential count, downgrade counts, user counts.
- **`GET /api/admin/users`**: user + role listing.
- **Frontend `/admin`** with 4 tabs:
  1. **Overview** — 6 real-time stat cards + user table with role badges
  2. **AI Act Art. 14 Oversight** — reuses `<DowngradePanel />`
  3. **GDPR Art. 17** — real erasure form (Bearer-gated, confirm-before-execute) + tamper-evident history of past erasure events
  4. **GitHub Live-Sync** — 10 repos, per-repo status (LIVE / http-error), aggregate stars, cache-refresh button
- **Every cell** is bound to a real backend endpoint. No hardcoded emails. No fake events. No client-side auth bypass. Complies with the No-Mocks-Policy.

### Iteration 7 — Chain-of-Custody + Bundle + Ops Webhook + Public Explorer + Mermaid Bug Fix (autonom)
- **BUG FIX · Mermaid syntax error on concept paper**: `/paper/jmap-wallet-auth` failed with `Mermaid parse error on line 11` because the sequenceDiagram messages contained `<br/>`, `{ sd_jwt_vp }` curly braces, unicode ellipsis `…` and semicolons. Rewrote the diagram to plain-text messages, defensively hardened the `/paper/architektur` flowchart (removed leading `.env` dot, removed comma inside cylindrical `[( )]` shape), fixed the source in `services/seed_paper.py` and force-updated both chapters in the `paper_chapters` collection via `update_one`. **Frontend-verified**: all 3 mermaid-carrying chapters (`executive-summary`, `architektur`, `jmap-wallet-auth`) now render as SVG with zero parse errors.
- **NEW · Chain-of-Custody Ledger** (`services/compliance_ledger.py`, `routers/compliance_validate.py` `/ledger` + `/ledger/verify`): every call to `POST /report.pdf`, `/report.sign` or `/report-bundle.pdf` appends a hash-chained entry to the `compliance_pdf_ledger` collection (`hash = SHA-256(canonical({prev_hash, meta}))`). Only summary metadata is stored (digest, kid, framework, status, kind, requester, at) — never the report payload. Public read; verifier walks the chain in O(n) and returns `{ok, entries, broken_at, head}`. Live component `ChainOfCustodyLedger.jsx` polls every 30s and shows the chain status badge on the validator page.
- **NEW · Multi-Report Bundle** (`services/compliance_pdf.render_bundle_pdf`, `POST /api/validate/report-bundle.pdf`): combines 1..20 signed reports into a single A4 PDF booklet with a Table of Contents and a bundle-level ES256 signature over the canonical concatenation. Response headers `X-PNIA-Bundle-Count`, `X-PNIA-Signature-Alg`, `X-PNIA-Digest-SHA256`. Frontend adds a checkbox to each framework row and a `signed bundle PDF` action button showing `n / 20` selection counter.
- **NEW · Realtime Ops Alert** (`services/ops_webhook.py`, admin router endpoints `/ops-webhook`, `/ops-webhook/test`, admin portal "Ops Webhook" tab): admin sets a Slack- or Teams-compatible webhook URL, filter (`on_fail_only`, optional `min_score`); `dispatch_bg()` is called fire-and-forget from `_publish()` in the compliance router — never blocks the request path and never raises. In-process 100-entry ring buffer keeps delivery status (HTTP code / ok flag / error) for the admin UI.
- **NEW · Public Explorer tile** (`components/PublicExplorer.jsx`, mounted on Landing between the 3D promo section and the globe CTA): 3 example payloads (GDPR minimal, DORA full, EU AI Act partial) — one-click "Try it" runs a real validation and the live-ticker mini panel lights up (SSE, ephemeral).
- **Backend tests**: 27/27 first-pass (8 bundle + 10 ledger + 6 webhook auth + 3 regression). Total accumulated: **92 tests passing** across iterations 5-7. Frontend Mermaid bug: verified by frontend agent (0 parse errors across 3 chapters).
- **No LLM calls in this iteration** — credits preserved.

### Iteration 6 — Signed PDF + Custom Rules + Photorealistic 3D (autonom)
- **NEW · Signed PDF Compliance Report** (`services/compliance_pdf.py`, `POST /api/validate/report.pdf`, `POST /api/validate/report.sign`):
  - A4 ReportLab layout with framework metadata, verdict, missing / recommended / covered tables, and a cryptographic signature block (ES256 JWS over the SHA-256 of the canonical JSON of the report).
  - Response headers `X-PNIA-Signature-Alg`, `X-PNIA-Signature-KID`, `X-PNIA-Digest-SHA256` expose the signature primitives for machine consumption.
  - Frontend "signed PDF" button on the validator report card triggers a one-shot download.
- **NEW · Custom Rule Editor** (`services/compliance_custom_rules.py`, `routers/compliance_validate.py` custom-rules endpoints, `AdminPortal` Custom Rules tab):
  - Admin-scoped `POST /api/validate/custom-rules/{code}` / `DELETE /api/validate/custom-rules/{id}` / `GET /api/validate/custom-rules` (via `require_admin`).
  - Public read `GET /api/validate/custom-rules/{code}` (transparency principle).
  - Rules stored in Mongo `compliance_custom_rules` collection, merged into `engine.validate()` at call time — the validator remains stateless from the caller's perspective. Every effective report includes `mode=SPECIALISED+CUSTOM(n)` when overrides apply.
- **NEW · Framework Detail Drawer** (`components/FrameworkDrawer.jsx`): slide-in right panel, rule list with severity chips, source link, custom overrides block, and a **Copy as cURL** action generating a ready-to-paste `curl -X POST` command with placeholder payload matching the ruleset.
- **NEW · Live Ticker Sounds + FAIL Pulse** (Web Audio API, no external files): soft sine-wave pling at 880 Hz for PASS, 660 Hz for warnings, 220 Hz sweeping down for FAIL; FAIL ticker rows apply the `pnia-fail-pulse` red-shadow animation for two cycles. Mute toggle in the ticker header.
- **NEW · Photorealistic 3D isometric architecture stack** (`components/Iso3DStack.jsx`, `pnia_iter6.css`): CSS 3D transform (rotateX 58° · rotateZ -38°, translateZ per layer 0/60/120/180/240 px), diagonal repeating-linear-gradient inner texture, pulsing amber nodes on the top plane, 24s gentle rotation loop. Rendered on the landing page and the blueprint hero.
- **NEW · Promo video loops** (Pixabay CDN, royalty-free): looping muted autoplay `<video>` layers on the landing hero, the promo section and the blueprint hero — with a dedicated `.pnia-video-overlay` gradient to keep text legible.
- **NEW · Architecture Timeline** (`pages/Blueprint.jsx` section 6): 7-milestone vertical track from Sprint 1-5 kryptography through Iteration 6 to the Blaupause v1.0 reference concept.
- **Backend tests**: 21/21 first-pass (13 PDF/JWS + 8 custom-rules auth + regression). Total accumulated: 65 tests passing across iterations 5 & 6.
- **No LLM calls in this iteration** — credits preserved.

### Iteration 5 — Stateless Compliance Validator + BLAUPAUSE (autonom)
- **Infra restore v2**: recreated `/app/backend/.env` (fresh MASTER_KEY, EMERGENT_LLM_KEY, MONGO_URL, DB_NAME, ISSUER_URL) + `/app/frontend/.env`. Installed missing `frozendict` + `cachetools` deps for pyld. Backend + frontend operational again.
- **NEW · Stateless Compliance Validation Engine** (`routers/compliance_validate.py`, `services/compliance_engine.py`, `data/frameworks.json`):
  - 251 real compliance frameworks 1:1 from `regula-quest.lovable.app/directory` (MiCA, DORA, GDPR, DSA, DMA, EU AI Act, NIS2, eIDAS 2, CRA, ISO 27001/42001, PCI DSS, HIPAA, SOC 2, NIST CSF/AI RMF, MAS, APRA, MAS, RBI, LGPD, POPIA, PIPL, DPDP, W3C VC, FIDO2, OIDC, EUDI ARF, WCAG 2.2, MITRE ATT&CK/ATLAS, etc.).
  - 8 specialised rule engines: GDPR (9 rules Art. 4-49), DORA (9 rules Art. 5-45), EU AI Act (10 rules Art. 3-72), DMA (7 rules), DSA (6 rules), NIS2 (6 rules), eIDAS 2 (5 rules), CRA (5 rules).
  - All other frameworks -> `GENERIC_GOVERNANCE_SKELETON` (organization, scope, responsible_role, documentation_url, last_review_date, evidence_repository).
  - `POST /api/validate` accepts arbitrary JSON payload + framework code; returns status (PASS / PASS_WITH_WARNINGS / FAIL / UNKNOWN_FRAMEWORK) + score + covered/missing/warnings + suggestions with statement-of-reasons per rule. **Data-minimisation: only field NAMES are echoed back, never values.**
  - `POST /api/validate/batch` — up to 20 frameworks parallel.
  - **Zero MongoDB writes**, no cross-request state, no LLM calls (deterministic rule engine).
  - `GET /api/validate/stream` — Server-Sent Events endpoint with 200-entry in-process ring buffer; disappears on tab close & on process restart. Ticker events carry only outcomes, no payload values.
- **NEW · BLAUPAUSE DER GESAMTARCHITEKTUR** (`routers/blueprint.py`, `pages/Blueprint.jsx`, route `/blueprint`): full 5-layer model, 10 building blocks (BB-01…BB-10), 6-stage validation path, 5 data flows, 9 regulatory references, Geltungsvorbehalt — Version 1.0, Stand 31. Juli 2026, Daniel Pohl / CoE e.V.
- **NEW · Compliance Validation Dashboard** (`pages/ComplianceValidator.jsx`, route `/validator`): sortable framework directory (category + full-text search), JSON payload editor, one-click validation, colour-coded report with covered/missing/warnings breakdown, source-of-truth link per framework, side-panel **Live Ticker** via EventSource (SSE) — ephemeral by design.
- **Compliance mapping**: EU AI Act Art. 12 record-keeping (deterministic + auditable) & Art. 50 transparency (no AI decision surface), DMA (open, machine-readable JSON API, no vendor lock-in, batch up to 20), DSA Art. 17 statement of reasons (rule.hint per finding), GDPR data-minimisation (payload values never echoed).
- **Backend tests**: 44/44 first-pass (23 validator + 21 blueprint). No PNIA regressions.

### Iteration 4 — PNIA (Production Network ID Architecture) build-up
- **Infra restore**: recreated missing backend/.env (MONGO_URL, DB_NAME, generated MASTER_KEY, ISSUER_URL, EMERGENT_LLM_KEY) + frontend/.env (REACT_APP_BACKEND_URL); added missing `pyld` dependency. Backend operational again.
- **Säule B merge (1:1 from user backup)**: `routers/pnia_compliance.py` (EU-ARF/eIDAS BSI report validator via `scripts/eu_arf_compliance_check.py`), `routers/identity_broker.py` (23 global eID providers), frontend `PNIACompliance.jsx` + `IdentityBroker.jsx`, `PNIA_Komplettpaket.pdf`.
- **NEW · Memorial & Honorary Registry** (`/pnia-registry`, `routers/pnia_registry.py`, `services/pnia_registry.py`): Gedenktafeln (DECEASED) + Ehrenplätze (LIVING). DSGVO-compliant — PII **AES-256-GCM tokenized** (reuses `key_storage`), pseudonymous `system_id`, **consent lifecycle** (LIVING requires GRANTED consent to publish), **Art. 17 right-to-be-forgotten** = crypto-shred + cascade deactivate, postmortal **write-once lock**. EU AI Act — **hash-chained + ES256-signed AiAuditLog** (`pnia_ai_audit`), **Art. 50 transparency flag** + risk classification. Real **gpt-5.4** tribute generation via emergentintegrations (`services/pnia_ai.py`). Seeded 16 historical state-founder memorials + 1 honorary place (initiator).
- **NEW · Concil Protokoll CP-01** (`/pnia-concept`, `routers/pnia_concil.py`, `services/pnia_concil.py`): PNIA = Production Network ID Architecture. 4 pillars (Axiom, Immunitas, Governance-Veredelung, Multi-Ewigkeits-Flow), technical pillars, governance roles. Live **CIH-01 handshake** (Discovery→Invariant-Validation→Activation): 200 Established Access vs **403 Sovereignty Shield** on governance mismatch (State-0-Compliance). Protected **Urheberrecht/Register** statement (© 2026 Daniel Pohl, Hnoss®, EU-Expert-ID/D-U-N-S/VAT/LEI/UNGM). Site-wide copyright footer.
- **Compliance mapping**: EU AI Act (Art. 12 record-keeping, Art. 50 transparency), DSGVO (Art. 5/6/7/17 + Erwägungsgrund 27), DMA (open API, no vendor lock-in).
- **Backend tests**: 32/34 first pass; Concil HTTP-403 mismatch fixed + curl-verified (34/34 effective).


## Architecture Locks
- ES256 primary; ES384/ES512 for LoA-High; EdDSA optional for W3C VC-DM 2.0
- SD-JWT VC (RFC 9215) + ISO 18013-5 mDoc parallel
- CBOR Tag 18 (COSE_Sign1) + 24 (bstr.cbor) + 0 (tdate) — strict
- AES-256-GCM Envelope Key Storage — fail-fast on missing `MASTER_KEY`
- Persistent 3-Level CA (Root → Intermediate → Signer) — never regenerated
- c_nonce TTL 300s + `find_one_and_delete` One-Time-Use
- Status List with signature + LRU 5min cache
- Audit log: SHA-256 prev_hash + JWS `typ=audit+jwt` signature per entry

## Backlog (P0 / P1 / P2)

### P0 (production hardening — recommended before real-world use)
- [ ] Populate `ADMIN_EMAILS` in production `.env` (or leverage first-user bootstrap)
- [ ] Rate-limit `/api/issuer/credential` and `/api/compliance/gdpr/erasure`
- [ ] Also protect `/api/issuer/nonce` with `Depends(require_user)` (currently public — flagged in iteration-2 review as nonce-pool-exhaustion vector)
- [ ] `AamvaMdlAdapter` currently trusts platform-local CA for cross-border mDL — document as reference-only or wire real AAMVA trust anchors
- [ ] Sprint 6 (JMAP + Wallet-Auth) on-prem Stalwart deployment testing

### P1 (nice-to-have next)
- [ ] `?download=1` variant of `/api/hub/postman-collection` with `Content-Disposition: attachment`
- [ ] Optional GITHUB_TOKEN env for higher API rate limits (60 → 5000 req/h)
- [ ] Volltextsuche im Concept Paper mit Query-Highlighting
- [ ] QR-Code Renderer für Credential-Offer URIs (`openid-credential-offer://…`)
- [ ] W3C VC-DM 2.0 mit URDNA2015 canonicalization für Swiyu

### P2
- [ ] Playwright E2E test suite (frontend)
- [ ] GitHub Actions CI/CD `.github/workflows/eudi_compliance_gates.yml`
- [ ] Kubernetes Helm-Chart
- [ ] Frontend admin: user role management (promote/demote via UI)

## Test Reports
- `/app/test_reports/iteration_1.json` — Sprint 1-5 MVP (34/34)
- `/app/test_reports/iteration_2.json` — Sprint 7-9 + Auth (49/49)

## Env Vars (`/app/backend/.env`)
- `MONGO_URL` — MongoDB connection
- `DB_NAME` — Mongo database name
- `MASTER_KEY` — 32-byte base64 AES-256 key (fail-fast if missing)
- `ISSUER_URL` — public backend URL (used as `aud` in proof JWTs)
- `ISSUER_ID` — DID / issuer identifier
- `CORS_ORIGINS` — comma-separated (default `*` — production should whitelist)
- `ADMIN_EMAILS` — comma-separated emails to promote to admin on login (empty → first-user bootstrap)
- `STALWART_BASE_URL` — reference-only, on-prem Stalwart JMAP sidecar
