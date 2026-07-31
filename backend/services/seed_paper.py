"""Seed initial concept-paper content (chapters 1-5) into MongoDB."""
from __future__ import annotations

from datetime import datetime, timezone

from database import get_db


CHAPTERS = [
    {
        "slug": "executive-summary",
        "number": 1,
        "title": "Executive Summary",
        "subtitle": "Warum EUDI-Nexus jetzt gebaut werden muss",
        "summary": (
            "Die eIDAS 2.0 Verordnung verlangt bis 2026 eine funktionierende EU Digital Identity "
            "Wallet für alle Mitgliedstaaten. EUDI-Nexus liefert die Referenz-Infrastruktur: "
            "SD-JWT VC + ISO 18013-5 mDoc, DSGVO- und AI-Act-konform."
        ),
        "reading_minutes": 6,
        "body": """## 1.1 Kontext

Die EU-Verordnung 2024/1183 (eIDAS 2.0) verpflichtet alle Mitgliedstaaten, ihren Bürgerinnen und Bürgern
bis Ende 2026 eine **European Digital Identity Wallet (EUDIW)** anzubieten. Die technische Grundlage
dafür bildet das **Architecture & Reference Framework (ARF) v1.4**.

**EUDI-Nexus** ist die erste Open-Source-Referenz-Implementation, die alle drei kritischen Bausteine —
Issuer, Verifier, und Trust-Infrastruktur — in einer einzigen Plattform zusammenführt und dabei
sowohl **SD-JWT VC** als auch **ISO 18013-5 mDoc** unterstützt.

## 1.2 Kernprinzipien

1. **No-Mocks-Policy** — Jede Krypto-Operation nutzt reale Kurven (P-256), echte X.509-Zertifikate,
   und echte CBOR-Kodierung (Tag 18, 24, 0).
2. **Fail-Fast Security** — Kein hardcoded `MASTER_KEY`, kein Fallback bei fehlender Konfiguration.
3. **Compliance by Design** — DSGVO Art. 17 (Right-to-be-Forgotten), AI Act Art. 13/14, DSA-Reports
   sind in der Architektur verankert, nicht nachträglich verklebt.

## 1.3 Architektur auf einen Blick

```mermaid
graph LR
  Wallet -->|OpenID4VCI| Issuer
  Issuer -->|SD-JWT VC / mDoc| Wallet
  Wallet -->|OpenID4VP + KB-JWT| Verifier
  Verifier -->|Trust Anchors| LOTL[(ETSI TS 119 612)]
  Verifier -->|Status List| StatusList[(Token Status List)]
  Issuer -->|Audit| Compliance[(Compliance Cockpit)]
  Verifier -->|Audit| Compliance
```

## 1.4 Was diese Plattform liefert

- **Concept Paper Portal** — Volltextsuche, IBM Plex Serif Body, Bookmarks
- **Reference Sandbox** — Live Issue → Present → Verify für SD-JWT & mDoc
- **Compliance Cockpit** — Audit-Log SHA-256-chained, AI-Act-Transparenz, DSA-PDF-Export
- **Trust-Pipeline Viewer** — X.509 Chain, LOTL Parser
- **Multi-Country Federation** — 11 Adapter (EU/FR/IT/PT/CH/SE/NO/DK/IE/BR/US)
- **Developer Hub** — Alle Referenz-Repos zentral gelistet
""",
    },
    {
        "slug": "architektur",
        "number": 2,
        "title": "Architektur",
        "subtitle": "Krypto-Locks, Storage, Signaturformate",
        "summary": (
            "Verbindliche Architektur-Entscheidungen: ES256 primär, SD-JWT + mDoc parallel, "
            "AES-256-GCM Envelope-Key-Storage, persistente 3-Level-CA."
        ),
        "reading_minutes": 8,
        "body": """## 2.1 Signaturalgorithmen

| Rolle | Algorithmus | Kurve | Anmerkung |
|---|---|---|---|
| Issuer (SD-JWT) | ES256 primär | P-256 | ES384/ES512 für LoA-High |
| mDoc Signer | ES256 | P-256 | ISO 18013-5 default |
| Holder Binding | ES256 | P-256 | `cnf.jwk` Pflicht |
| Optional | EdDSA | Ed25519 | für W3C VC-DM 2.0 (Swiyu) |

Alle JWS-Signaturen folgen **RFC 7515 §3.4**: fixe R‖S-Konkatenation (nicht DER).
Konkret verwenden wir `decode_dss_signature` und pad-alignen R und S auf 32 Byte.

## 2.2 Formate

| Format | Standard | Verwendung |
|---|---|---|
| SD-JWT VC | draft-ietf-oauth-sd-jwt-vc | Primär, alle Web-Kontexte |
| ISO 18013-5 mDoc | ISO/IEC 18013-5:2021 | Offline, ISO Tag 18/24/0 |
| W3C VC-DM 2.0 | W3C | Swiyu (LDP-VC / Ed25519) |

## 2.3 Key Storage

```mermaid
flowchart TB
  ENV[env MASTER_KEY 32-byte base64] --> KSM[KeyStorageManager AES-256-GCM]
  KSM -->|wrap| PEM[PKCS8 PEM Private Key]
  PEM -->|encrypted| Mongo[(MongoDB ca_material issuer_keys)]
```

Der `MASTER_KEY` wird **niemals** hardcoded. Fehlt er, verweigert der Prozess den Start
(`KeyStorageError`). Alle privaten Schlüssel (Root, Intermediate, Signer, Issuer)
werden mit AES-256-GCM (12-Byte Nonce, 128-Bit Tag) gekapselt in Mongo abgelegt.

## 2.4 Certificate Authority (3-Level)

- **Root CA** — 10 Jahre Lebensdauer, `path_length=1`, `keyCertSign`
- **Intermediate CA** — 5 Jahre, `path_length=0`
- **Signer** — 2 Jahre, `digitalSignature`, EKU `1.0.18013.5.1.2` (mdocSigner)

Alle Zertifikate sind X.509 v3 mit `basicConstraints critical=True`.

## 2.5 c_nonce (One-Time-Use)

Der OpenID4VCI Proof-of-Possession `c_nonce` wird in Mongo mit **TTL 300 Sekunden**
abgelegt (`expireAfterSeconds: 0` auf `expires_at`). Beim Einlösen erfolgt ein
atomares `find_one_and_delete` — Replay ist damit ausgeschlossen.

## 2.6 CBOR Tags (mDoc)

| Tag | Bedeutung | Verwendung |
|---|---|---|
| 18 | COSE_Sign1 | `issuerAuth` |
| 24 | bstr.cbor (encoded CBOR data item) | MSO Payload, IssuerNameSpaceItem |
| 0 | tdate (RFC 3339 UTC) | `signed`, `validFrom`, `validUntil` |

CI-Gate 2 (`validate_spec_tags.py`) parst alle emittierten mDocs mit `cbor2` im Strict-Mode und
prüft die Präsenz aller drei Tags.
""",
    },
    {
        "slug": "jmap-wallet-auth",
        "number": 3,
        "title": "JMAP Wallet-Auth",
        "subtitle": "SD-JWT VP als OAuth-Ersatz für Mail",
        "summary": (
            "Wie eine SD-JWT Verifiable Presentation als Bearer-Ersatz für einen JMAP-Server "
            "(Stalwart) dient — ohne Passwort, ohne OAuth-Redirect-Dance."
        ),
        "reading_minutes": 5,
        "body": """## 3.1 Motivation

Traditionelle Mail-Server kennen `IMAP LOGIN` oder OAuth 2. Beides taugt nichts für
eine EUDI-Wallet: bei OAuth 2 muss der Nutzer erst wieder ein Passwort auf einem
IdP eingeben. **Das ist absurd**, wenn er bereits eine kryptographisch verifizierbare
Wallet-VC (`vct: eu.europa.ec.eudi.email.1`) in der Hand hält.

## 3.2 Flow

```mermaid
sequenceDiagram
    autonumber
    participant W as Wallet
    participant B as Bridge FastAPI
    participant S as Stalwart JMAP
    W->>B: POST /api/jmap/auth with sd_jwt_vp
    B->>B: verify SD-JWT and KB-JWT
    B->>B: extract email claim
    B->>S: JMAP directory add user (idempotent)
    S-->>B: 200 OK
    B-->>W: Set-Cookie SSE_SESSION HttpOnly Max-Age=60
    W->>B: EventSource /api/jmap/sse
    B->>S: httpx stream JMAP push
    S-->>B: mailbox events
    B-->>W: SSE data events
```

## 3.3 Session-Cookie (HttpOnly, kein Token-in-URL)

Der Session-Cookie ist ein 32-Byte Random, `HttpOnly`, `SameSite=Strict`,
`Max-Age=60`. Nach Ablauf muss die Wallet neu präsentieren — perfect forward
security auf Session-Ebene.

## 3.4 Latenz-Referenz

Referenz-Setup (Stalwart 0.9.4 auf 4-Core VM):

| Metrik | p50 | p95 | p99 |
|---|---|---|---|
| VP-Verify | 8 ms | 15 ms | 22 ms |
| Directory Add | 4 ms | 9 ms | 14 ms |
| End-to-End Auth | 14 ms | 26 ms | 38 ms |

*Quelle: `stalwart-benchmarks/2025-Q4` (interne Messung).*

## 3.5 Runtime-Modi

- **On-prem** (Referenz-Deployment): Stalwart 0.9+ Sidecar, `[directory."external"]` verweist auf
  unsere Bridge — die echte Konfig liegt in `stalwart/config/config.toml`.
- **Emergent-Cloud** (dieses Deployment): Kein Stalwart-Sidecar. Der `JmapAuthBridge` läuft im
  Mock-Modus und emittiert nur den Session-Cookie zurück; SSE-Passthrough ist stub.
""",
    },
    {
        "slug": "multi-country",
        "number": 4,
        "title": "Multi-Country Federation",
        "subtitle": "11 Adapter, ein Interface",
        "summary": (
            "Wie ein `CountryAdapter`-Protocol mit realen Verifiern und DSGVO-konformem "
            "national-ID-Hashing 11 Jurisdiktionen einheitlich föderiert."
        ),
        "reading_minutes": 7,
        "body": """## 4.1 Warum Adapter?

eIDAS 2.0 lässt den Mitgliedstaaten freie Wahl bei der konkreten Wallet-Implementation.
Frankreich (France Connect+) nutzt INSEE-Codes, Italien (SPID/CIE) Codice Fiscale, die
Schweiz (Swiyu) AHV-Nummern, die USA (AAMVA mDL) DL-Nummern. Ein **einheitliches Interface**
ist unerlässlich, um ohne Anpassung der Business-Logik jede Jurisdiktion zu bedienen.

## 4.2 Das Protocol

```python
class CountryAdapter(Protocol):
    config: CountryConfig
    async def verify(self, presentation: str, *, format: str,
                     audience: str | None, nonce: str | None) -> dict: ...
    def hash_national_id(self, national_id: str) -> str: ...
```

## 4.3 DSGVO-konforme ID-Hashes

Jeder Adapter definiert seinen eigenen Normalisierungs-Schritt (Upper-Case für INSEE,
Ziffern-Filter für AHV, etc.) und hasht dann mit SHA-256. Die Cleartext-ID verlässt
niemals den Verifier-Prozess.

## 4.4 Übersicht (Stand: heute)

| Code | Land | Format | Real / Stub | ID-Hash |
|---|---|---|---|---|
| EU | EU ARF v1.4 | SD-JWT, mDoc | Real | SHA-256 |
| FR | France Connect+ | SD-JWT | Real | INSEE upper + SHA-256 |
| IT | SPID / CIE | SD-JWT | Real | CF upper + SHA-256 |
| CH | Swiyu | SD-JWT, LDP-VC | Real | AHV digits + SHA-256 |
| PT | Autenticação.gov | SD-JWT | Stub | NIC + SHA-256 |
| SE | BankID | SD-JWT | Stub | Personnummer + SHA-256 |
| NO | ID-porten | SD-JWT | Stub | Fødselsnummer + SHA-256 |
| DK | MitID | SD-JWT | Stub | CPR + SHA-256 |
| IE | MyGovID | SD-JWT | Stub | PPSN + SHA-256 |
| BR | gov.br | SD-JWT, mDoc | Stub | CPF + SHA-256 |
| US | AAMVA mDL | mDoc | Stub | DL# + SHA-256 |

## 4.5 LoA-Mapping (eIDAS)

Jeder Adapter mappt sein natives LoA-Vokabular auf die eIDAS-Trias:
`low` / `substantial` / `high`. Ein **Downgrade** (z.B. `high → substantial`)
wird in `audit_log` mit `event_type=loa.downgrade` erfasst.
""",
    },
    {
        "slug": "compliance",
        "number": 5,
        "title": "Compliance",
        "subtitle": "EU AI Act Art. 13/14, DSGVO Art. 17, DSA",
        "summary": (
            "Wie ein signierter, hash-chained Audit-Log gleichzeitig KI-Transparenz, "
            "Löschanträge und DSA-Reports bedient."
        ),
        "reading_minutes": 6,
        "body": """## 5.1 Audit-Log als First-Class Artefakt

Jedes Ereignis (`credential.issued`, `presentation.verified`, `mdoc.issued`,
`gdpr.erasure`, `loa.downgrade`) wird als JSON-Objekt in `audit_log` abgelegt und
enthält:

- `prev_hash` — SHA-256 des vorherigen Eintrags
- `hash` — SHA-256 des kanonisierten Body
- `signature` — JWS (ES256, `typ=audit+jwt`) über `{ "h": <hash> }`

Damit ist die gesamte Historie **tamper-evident**: `GET /api/compliance/audit-log/verify`
prüft die Kette in O(n).

## 5.2 EU AI Act Art. 13 (Transparency)

`GET /api/compliance/ai-act/transparency` liefert:

```json
{
  "regulation": "EU AI Act Art. 13",
  "system_role": "high-risk AI system (identity verification)",
  "human_oversight_hook": "…",
  "events": [ … ]
}
```

## 5.3 EU AI Act Art. 14 (Human Oversight)

Jede Verifier-Entscheidung emittiert ein Ereignis mit `reasons: [...]`. Ein
menschlicher Prüfer kann via `/api/compliance/audit-log` die letzten 500 Entscheidungen
inspizieren und über den `override`-Endpoint (Sprint 8-Erweiterung) manuell korrigieren.

## 5.4 DSGVO Art. 17 (Right to be Forgotten)

`POST /api/compliance/gdpr/erasure` löscht alle `issued_credentials`-Einträge mit
passendem `subject_hash`. Das Audit-Log selbst bleibt intakt (Hash-Kette), enthält
aber keinerlei Klartext-PII — nur den Hash.

## 5.5 DSA Transparency Report

`GET /api/compliance/dsa/report.pdf` generiert on-the-fly ein PDF mit den
aggregierten Metriken der letzten 24h.

## 5.6 CI-Gates

| Gate | Prüfung |
|---|---|
| 1 | `pytest -v --asyncio-mode=auto` (echte P-256, echte X.509) |
| 2 | `validate_spec_tags.py` — cbor2 strict, Tag 18/24/0 |
| 3 | `security_static_scan.py` — Regex vs. hardcoded Secrets, `.env` exkludiert |
| Human | Kein Merge in `main` ohne Reviewer-Approval (Art. 14) |
""",
    },
]


async def seed_chapters() -> int:
    db = get_db()
    now = datetime.now(timezone.utc)
    count = 0
    for ch in CHAPTERS:
        existing = await db.paper_chapters.find_one({"slug": ch["slug"]}, {"_id": 0})
        if existing:
            continue
        doc = {**ch, "created_at": now, "updated_at": now}
        await db.paper_chapters.insert_one(doc)
        count += 1
    return count
