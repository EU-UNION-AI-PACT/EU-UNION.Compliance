"""Swiss E-ID (Swiyu) adapter — AHV hash, real LDP-VC W3C VC-DM 2.0 with URDNA2015."""
from __future__ import annotations

from typing import Any

from adapters.base import CountryConfig, sha256_hex
from services.ldp_vc_verifier import LdpVcVerifier
from services.sd_jwt_verifier import SDJWTVerifierV2
from services.status_list_client import StatusListClient


class SwiyuAdapter:
    config = CountryConfig(
        code="CH",
        name="Switzerland (Swiyu)",
        flag="🇨🇭",
        scheme="Swiss E-ID (Swiyu)",
        trust_framework="Swiss Federal Trust Infrastructure",
        supported_formats=["sd-jwt", "ldp-vc"],
        loa_mapping={"low": "low", "substantial": "substantial", "high": "high"},
        reference_url="https://github.com/e-id-admin",
        id_hash_algorithm="SHA-256 over AHV number (digits only)",
        implemented=True,
    )

    def __init__(self) -> None:
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
        elif format == "ldp-vc":
            result = await self._ldp_verifier.verify(presentation)
        else:
            return {"valid": False, "reasons": [f"Swiyu adapter does not support format={format}"]}
        disclosed = dict(result.get("disclosed_claims", {}))
        ahv = disclosed.get("ahv") or disclosed.get("ahv_number")
        if ahv:
            disclosed["ahv_hash"] = self.hash_national_id(str(ahv))
            disclosed.pop("ahv", None)
            disclosed.pop("ahv_number", None)
        result["disclosed_claims"] = disclosed
        return result

    def hash_national_id(self, national_id: str) -> str:
        norm = "".join(ch for ch in national_id if ch.isdigit())
        return sha256_hex(norm)
