"""ANSSI France Connect adapter — INSEE-hash for PID identifier."""
from __future__ import annotations

from typing import Any

from adapters.base import CountryConfig, sha256_hex
from services.sd_jwt_verifier import SDJWTVerifierV2
from services.status_list_client import StatusListClient


class FranceConnectAdapter:
    config = CountryConfig(
        code="FR",
        name="France (France Connect+)",
        flag="🇫🇷",
        scheme="France Connect+",
        trust_framework="ANSSI RGS *** / eIDAS High",
        supported_formats=["oidc", "sd-jwt"],
        loa_mapping={"eidas1": "low", "eidas2": "substantial", "eidas3": "high"},
        reference_url="https://franceconnect.gouv.fr/partenaires",
        id_hash_algorithm="SHA-256 over INSEE code",
        implemented=True,
    )

    def __init__(self) -> None:
        self._sd_verifier = SDJWTVerifierV2(StatusListClient())
        from services.ldp_vc_verifier import LdpVcVerifier
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
            return {"valid": False, "reasons": ["France Connect+ requires SD-JWT VC or LDP-VC"]}
        disclosed = dict(result.get("disclosed_claims", {}))
        insee = disclosed.get("insee")
        if insee:
            disclosed["insee_hash"] = self.hash_national_id(insee)
            disclosed.pop("insee", None)
        result["disclosed_claims"] = disclosed
        result["loa"] = "high"
        return result

    def hash_national_id(self, national_id: str) -> str:
        return sha256_hex(national_id.strip().upper())
