"""Developer hub — OSS repo registry (static + live GitHub badges optional)."""
from __future__ import annotations

from fastapi import APIRouter

from models import OSSRepo

router = APIRouter(prefix="/hub", tags=["Developer Hub"])


REGISTRY: list[OSSRepo] = [
    # === EUDI / eIDAS Core ===
    OSSRepo(
        slug="eu-digital-identity-wallet/architecture-and-reference-framework",
        url="https://github.com/eu-digital-identity-wallet/architecture-and-reference-framework",
        category="ARF",
        description="EUDI Architecture & Reference Framework v1.4",
        role="reference",
    ),
    OSSRepo(
        slug="eu-digital-identity-wallet/eudi-lib-jvm-sdjwt-kt",
        url="https://github.com/eu-digital-identity-wallet/eudi-lib-jvm-sdjwt-kt",
        category="SD-JWT VC",
        description="Kotlin SD-JWT VC library (issuer + verifier)",
        role="library",
    ),
    OSSRepo(
        slug="eu-digital-identity-wallet/eudi-app-android-wallet-ui",
        url="https://github.com/eu-digital-identity-wallet/eudi-app-android-wallet-ui",
        category="Wallet",
        description="EUDI Reference Wallet UI (Android)",
        role="app",
    ),
    OSSRepo(
        slug="openwallet-foundation-labs/sd-jwt-python",
        url="https://github.com/openwallet-foundation-labs/sd-jwt-python",
        category="SD-JWT VC",
        description="Reference SD-JWT Python implementation",
        role="library",
    ),
    # === Standards & Specs ===
    OSSRepo(
        slug="oauth-wg/draft-ietf-oauth-sd-jwt-vc",
        url="https://github.com/oauth-wg/draft-ietf-oauth-sd-jwt-vc",
        category="SD-JWT VC",
        description="IETF OAuth WG — SD-JWT VC draft",
        role="spec",
    ),
    OSSRepo(
        slug="oauth-wg/oauth-status-list",
        url="https://github.com/oauth-wg/oauth-status-list",
        category="Status List",
        description="IETF OAuth Working Group — Token Status List draft",
        role="spec",
    ),
    OSSRepo(
        slug="decentralized-identity/didcomm-messaging",
        url="https://github.com/decentralized-identity/didcomm-messaging",
        category="DIDComm",
        description="DIF DIDComm v2 protocol",
        role="protocol",
    ),
    # === Nationale E-ID / SPID / CIE ===
    OSSRepo(
        slug="italia/spid-sp-access-button",
        url="https://github.com/italia/spid-sp-access-button",
        category="SPID/CIE",
        description="AGID SPID SP access button (official assets)",
        role="reference",
    ),
    OSSRepo(
        slug="e-id-admin/eidch-integration-guides",
        url="https://github.com/e-id-admin/eidch-integration-guides",
        category="Swiyu",
        description="Swiss E-ID (Swiyu) integration guides",
        role="library",
    ),
    # === International Identity Providers ===
    OSSRepo(
        slug="belgianmobileid",
        url="https://github.com/belgianmobileid",
        category="OIDC/eIDAS",
        description="Belgian Mobile ID (itsme) — OIDC & eIDAS integration",
        role="reference",
    ),
    OSSRepo(
        slug="signicat",
        url="https://github.com/signicat",
        category="Trust Services",
        description="Signicat — digital trust, eID & signature orchestration",
        role="reference",
    ),
    OSSRepo(
        slug="yehuthi/israelid",
        url="https://github.com/yehuthi/israelid",
        category="ID Validation",
        description="Israel ID Validation (Teudat Zehut checksum)",
        role="library",
    ),
    OSSRepo(
        slug="singpass",
        url="https://github.com/singpass",
        category="National ID",
        description="Singpass Singapore — digital identity & Identiface",
        role="reference",
    ),
    # === KYC / IDV ===
    OSSRepo(
        slug="SumSubstance",
        url="https://github.com/SumSubstance",
        category="KYC/AML",
        description="Sumsub — KYC/KYB mobile SDK & webhook integrations",
        role="library",
    ),
    OSSRepo(
        slug="veriff",
        url="https://github.com/veriff",
        category="KYC/AML",
        description="Veriff — Web & Mobile SDKs for identity verification",
        role="library",
    ),
    OSSRepo(
        slug="gbgplc",
        url="https://github.com/gbgplc",
        category="KYC/AML",
        description="GBG — global identity verification & location services",
        role="library",
    ),
    # === Compliance & Governance ===
    OSSRepo(
        slug="paperless-ngx/paperless-ngx",
        url="https://github.com/paperless-ngx/paperless-ngx",
        category="DMS",
        description="Paperless-ngx — open-source document management & signature pipeline",
        role="reference",
    ),
    OSSRepo(
        slug="lnlp-open-source",
        url="https://github.com/lnlp-open-source",
        category="Compliance",
        description="LexisNexis Legal & Professional — open-source compliance tools",
        role="reference",
    ),
    # === USA / Federal ===
    OSSRepo(
        slug="GSA-TTS",
        url="https://github.com/GSA-TTS",
        category="Federal ID",
        description="GSA TTS — Login.gov US federal digital identity",
        role="reference",
    ),
    OSSRepo(
        slug="18F/identity-idp",
        url="https://github.com/18f/identity-idp",
        category="Federal ID",
        description="18F Identity IdP — core open-source identity provider",
        role="reference",
    ),
    # === Interpol / Law Enforcement ===
    OSSRepo(
        slug="bundesAPI/interpol-api",
        url="https://github.com/bundesAPI/interpol-api",
        category="Law Enforcement",
        description="Community Interpol Notices API wrapper (German/English)",
        role="library",
    ),
]


@router.get("/repos", response_model=list[OSSRepo])
async def list_repos() -> list[OSSRepo]:
    return REGISTRY
