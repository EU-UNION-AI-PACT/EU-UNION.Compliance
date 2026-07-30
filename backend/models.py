"""Pydantic schemas — API contracts for EUDI-Nexus."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uid() -> str:
    return str(uuid.uuid4())


class BaseDoc(BaseModel):
    """Base class — ignores Mongo `_id`, uses UUID `id`."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=_uid)
    created_at: datetime = Field(default_factory=_now)


# ---------- Concept Paper ----------


class PaperChapter(BaseDoc):
    slug: str
    number: int
    title: str
    subtitle: str = ""
    summary: str
    body: str  # markdown + mermaid
    reading_minutes: int = 5
    updated_at: datetime = Field(default_factory=_now)


class PaperSearchResult(BaseModel):
    slug: str
    number: int
    title: str
    excerpt: str
    score: float


# ---------- Issuer / SD-JWT ----------


class NonceResponse(BaseModel):
    c_nonce: str
    c_nonce_expires_in: int


class CredentialOfferRequest(BaseModel):
    vct: Literal[
        "eu.europa.ec.eudi.pid.1",
        "eu.europa.ec.eudi.mdl.1",
        "eu.europa.ec.eudi.email.1",
    ] = "eu.europa.ec.eudi.pid.1"
    subject_claims: dict[str, Any]
    holder_jwk: dict[str, Any]
    proof_jwt: str | None = None
    country_code: str = "EU"


class CredentialResponse(BaseModel):
    format: str = "vc+sd-jwt"
    credential: str  # compact SD-JWT
    disclosures_count: int
    vct: str
    issued_at: datetime = Field(default_factory=_now)


class VerifyRequest(BaseModel):
    presentation: str  # compact SD-JWT[+KB-JWT]
    audience: str | None = None
    nonce: str | None = None


class VerifyResponse(BaseModel):
    valid: bool
    reasons: list[str] = []
    disclosed_claims: dict[str, Any] = {}
    issuer: str | None = None
    vct: str | None = None
    trust_chain: list[str] = []
    loa: Literal["low", "substantial", "high"] | None = None
    status: Literal["active", "suspended", "revoked", "unknown"] = "unknown"


# ---------- mDoc ISO 18013-5 ----------


class MDocIssueRequest(BaseModel):
    doctype: str = "org.iso.18013.5.1.mDL"
    namespaces: dict[str, dict[str, Any]]  # namespace -> {claim: value}
    device_public_key: dict[str, Any]  # COSE_Key as JWK
    country_code: str = "EU"


class MDocIssueResponse(BaseModel):
    format: str = "mso_mdoc"
    doctype: str
    mdoc_hex: str  # CBOR-encoded IssuerSigned
    digest_count: int


class MDocVerifyRequest(BaseModel):
    mdoc_hex: str


class MDocVerifyResponse(BaseModel):
    valid: bool
    reasons: list[str] = []
    doctype: str | None = None
    disclosed_namespaces: dict[str, dict[str, Any]] = {}
    trust_chain: list[str] = []
    device_key_present: bool = False


class EngagementResponse(BaseModel):
    engagement_id: str
    device_engagement_hex: str
    session_key_public_jwk: dict[str, Any]
    expires_at: datetime


# ---------- Trust / LOTL ----------


class TrustAnchor(BaseModel):
    subject: str
    issuer: str
    serial_number: str
    not_before: datetime
    not_after: datetime
    key_use: list[str]
    is_root: bool
    fingerprint_sha256: str
    country_code: str


class LotlSummary(BaseModel):
    territory: str
    scheme_operator: str
    sequence_number: int
    issue_date: datetime
    next_update: datetime
    anchor_count: int
    anchors: list[TrustAnchor]


class LotlParseRequest(BaseModel):
    xml: str


# ---------- Compliance ----------


class AuditEvent(BaseDoc):
    event_type: str
    actor: str
    subject: str | None = None
    payload: dict[str, Any] = {}
    prev_hash: str = ""
    hash: str = ""
    signature: str = ""


class ComplianceMetrics(BaseModel):
    total_credentials_issued: int
    total_presentations_verified: int
    verification_success_rate: float
    active_loa_low: int
    active_loa_substantial: int
    active_loa_high: int
    downgrade_incidents: int
    ai_act_transparency_events: int
    gdpr_erasure_requests: int


class ErasureRequest(BaseModel):
    subject_hash: str
    reason: str = "GDPR Art. 17"


# ---------- Country Adapters ----------


class CountryInfo(BaseModel):
    code: str
    name: str
    flag: str  # emoji flag (used in country code table only, not UI icons)
    scheme: str
    trust_framework: str
    supported_formats: list[str]
    loa_mapping: dict[str, str]
    reference_url: str
    id_hash_algorithm: str
    implemented: bool


class CountryVerifyRequest(BaseModel):
    country_code: str
    presentation: str
    format: Literal["sd-jwt", "mdoc", "ldp-vc"] = "sd-jwt"
    audience: str | None = None
    nonce: str | None = None


# ---------- JMAP (Mock/Bridge) ----------


class JmapAuthRequest(BaseModel):
    sd_jwt_presentation: str


class JmapAuthResponse(BaseModel):
    session_cookie: str
    expires_in: int
    account_email: str
    account_id: str


# ---------- Developer Hub ----------


class OSSRepo(BaseModel):
    slug: str  # owner/repo
    url: str
    category: str
    description: str
    role: str  # e.g. "issuer", "verifier", "trust"
