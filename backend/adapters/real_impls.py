"""Real adapters for PT/SE/NO/DK/IE/BR/US — Sprint 7 + Sprint 10 (LDP-VC).

Every adapter delegates crypto to SDJWTVerifierV2, MDocVerifier, OR
LdpVcVerifier (URDNA2015) depending on the presented `format` and applies a
country-specific normalization + SHA-256 hash of the national identifier before
returning the disclosed claims.
"""
from __future__ import annotations

import re
from typing import Any

from adapters.base import CountryConfig, sha256_hex
from services.ldp_vc_verifier import LdpVcVerifier
from services.sd_jwt_verifier import SDJWTVerifierV2
from services.status_list_client import StatusListClient


def _norm_digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


class _MultiFormatAdapter:
    """Base for adapters that accept SD-JWT (mandatory) and W3C VC-DM 2.0 (optional)."""

    id_claim_keys: tuple[str, ...] = ()
    normalize = staticmethod(lambda s: (s or "").strip().upper())
    loa_default: str | None = None

    def __init__(self, config: CountryConfig) -> None:
        self.config = config
        self._sd_verifier = SDJWTVerifierV2(StatusListClient())
        self._ldp_verifier = LdpVcVerifier()

    async def verify(
        self,
        presentation: str,
        *,
        format: str,
        audience: str | None,
        nonce: str | None,
    ) -> dict[str, Any]:
        if format == "sd-jwt":
            result = await self._sd_verifier.verify(presentation, audience=audience, nonce=nonce)
        elif format == "ldp-vc" and "ldp-vc" in self.config.supported_formats:
            result = await self._ldp_verifier.verify(presentation)
        elif format == "mdoc" and "mdoc" in self.config.supported_formats:
            from services.mdoc_verifier import MDocVerifier

            result = await MDocVerifier().verify(bytes.fromhex(presentation))
            disclosed = {}
            for ns in result.get("disclosed_namespaces", {}).values():
                disclosed.update(ns)
            result["disclosed_claims"] = disclosed
        else:
            return {
                "valid": False,
                "reasons": [f"{self.config.code} adapter does not support format={format}"],
                "disclosed_claims": {},
            }
        disclosed = result.get("disclosed_claims", {})
        # ID hashing — take a copy so we don't mutate cached claims
        disclosed = dict(disclosed)
        for k in self.id_claim_keys:
            if k in disclosed and disclosed[k]:
                disclosed[f"{k}_hash"] = self.hash_national_id(str(disclosed[k]))
                disclosed.pop(k, None)
                break
        result["disclosed_claims"] = disclosed
        if self.loa_default:
            result["loa"] = self.loa_default
        return result

    def hash_national_id(self, national_id: str) -> str:
        return sha256_hex(self.__class__.normalize(national_id))


class PortugalAdapter(_MultiFormatAdapter):
    id_claim_keys = ("nic", "citizen_card_number")
    loa_default = "high"


class BankIdSEAdapter(_MultiFormatAdapter):
    id_claim_keys = ("personnummer", "personal_number")
    normalize = staticmethod(_norm_digits)
    loa_default = "high"


class IdPortenNOAdapter(_MultiFormatAdapter):
    id_claim_keys = ("fodselsnummer", "personal_identity_number")
    normalize = staticmethod(_norm_digits)
    loa_default = "high"


class MitIdDKAdapter(_MultiFormatAdapter):
    id_claim_keys = ("cpr", "cpr_number")
    normalize = staticmethod(_norm_digits)
    loa_default = "substantial"


class MyGovIdIEAdapter(_MultiFormatAdapter):
    id_claim_keys = ("ppsn", "psc_number")
    loa_default = "substantial"


class GovBrAdapter(_MultiFormatAdapter):
    id_claim_keys = ("cpf",)
    normalize = staticmethod(_norm_digits)
    loa_default = "high"


class AamvaMdlAdapter:
    """US AAMVA mDL — ISO 18013-5 only. DL number hash.

    NOTE: This adapter uses the platform-local MDocVerifier which trusts the
    EUDI-Nexus CA. Cross-border trust anchors (AAMVA root list) must be wired
    for production — this is out of scope for the reference platform.
    """

    def __init__(self, config: CountryConfig) -> None:
        self.config = config

    async def verify(
        self,
        presentation: str,
        *,
        format: str,
        audience: str | None,
        nonce: str | None,
    ) -> dict[str, Any]:
        if format != "mdoc":
            return {"valid": False, "reasons": ["AAMVA mDL requires ISO 18013-5 mdoc"]}
        from services.mdoc_verifier import MDocVerifier

        try:
            raw = bytes.fromhex(presentation)
        except ValueError as exc:
            return {"valid": False, "reasons": [f"mdoc hex parse: {exc}"]}
        result = await MDocVerifier().verify(raw)
        disclosed: dict[str, Any] = {}
        for ns in result.get("disclosed_namespaces", {}).values():
            disclosed.update(ns)
        dl = disclosed.get("document_number") or disclosed.get("driving_licence_number")
        if dl:
            disclosed["document_number_hash"] = self.hash_national_id(str(dl))
            disclosed.pop("document_number", None)
            disclosed.pop("driving_licence_number", None)
        result["disclosed_claims"] = disclosed
        result["loa"] = "substantial"
        return result

    def hash_national_id(self, national_id: str) -> str:
        return sha256_hex((national_id or "").strip().upper())


# ---------------------------------------------------------------------------
# Stub-Adapter für internationale Provider (vorher PortugalAdapter-Reuse)
# ---------------------------------------------------------------------------

class _GenericStubAdapter(_MultiFormatAdapter):
    """Fallback-Stub für Länder ohne echte native Integration.

    Nutzt das generische Multi-Format-Protokoll, aber mit
    länderspezifischem ID-Claim-Key und Normalisierung.
    """


# --- Mittlerer Osten & Afrika ---
class UaePassAdapter(_GenericStubAdapter):
    id_claim_keys = ("emirates_id", "national_id")
    normalize = staticmethod(lambda s: (s or "").strip().upper())


# --- Europa ---
class EvrotrustAdapter(_GenericStubAdapter):
    id_claim_keys = ("egn", "national_id")
    normalize = staticmethod(lambda s: (s or "").strip().upper())


class BelgianMobileIdAdapter(_GenericStubAdapter):
    id_claim_keys = ("national_number", "national_id")
    normalize = staticmethod(lambda s: (s or "").strip().upper())


class LuxTrustAdapter(_GenericStubAdapter):
    id_claim_keys = ("national_identifier", "national_id")
    normalize = staticmethod(lambda s: (s or "").strip().upper())


# --- Ostasien ---
class ChinaCtidAdapter(_GenericStubAdapter):
    id_claim_keys = ("resident_id", "national_id")
    normalize = staticmethod(lambda s: (s or "").strip().upper())


class KoreaMobileIdAdapter(_GenericStubAdapter):
    id_claim_keys = ("resident_registration", "national_id")
    normalize = staticmethod(lambda s: (s or "").strip())


class JapanMyNumberAdapter(_GenericStubAdapter):
    id_claim_keys = ("individual_number", "national_id")
    normalize = staticmethod(lambda s: (s or "").strip())


# --- Taiwan & Estland & Indien & Nordamerika & Ozeanien & Skandinavien ---
class TaiwanDigitalIdAdapter(_GenericStubAdapter):
    id_claim_keys = ("national_id",)
    normalize = staticmethod(lambda s: (s or "").strip().upper())


class EstoniaEResidencyAdapter(_GenericStubAdapter):
    id_claim_keys = ("e_residency_id", "personal_code")
    normalize = staticmethod(lambda s: (s or "").strip().upper())


class AadhaarAdapter(_GenericStubAdapter):
    id_claim_keys = ("aadhaar_uid", "uid")
    normalize = staticmethod(_norm_digits)


class CanadaInteracAdapter(_GenericStubAdapter):
    id_claim_keys = ("provincial_id",)
    normalize = staticmethod(lambda s: (s or "").strip().upper())


class AustraliaMyGovIdAdapter(_GenericStubAdapter):
    id_claim_keys = ("mygovid",)
    normalize = staticmethod(lambda s: (s or "").strip())


class NewZealandRealMeAdapter(_GenericStubAdapter):
    id_claim_keys = ("realme_id",)
    normalize = staticmethod(lambda s: (s or "").strip())


class IcelandIslandisAdapter(_GenericStubAdapter):
    id_claim_keys = ("kennitala",)
    normalize = staticmethod(_norm_digits)


class FinlandTrustNetworkAdapter(_GenericStubAdapter):
    id_claim_keys = ("finnish_personal_id",)
    normalize = staticmethod(_norm_digits)


class IsraelIdAdapter(_GenericStubAdapter):
    id_claim_keys = ("id_number",)
    normalize = staticmethod(lambda s: (s or "").strip().upper())
