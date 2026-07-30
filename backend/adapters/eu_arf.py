"""EU ARF v1.4 reference adapter — SD-JWT + mDoc + LDP-VC."""
from __future__ import annotations

from typing import Any

from adapters.base import CountryConfig, sha256_hex
from services.ldp_vc_verifier import LdpVcVerifier
from services.sd_jwt_verifier import SDJWTVerifierV2
from services.status_list_client import StatusListClient


class EUARFAdapter:
    config = CountryConfig(
        code="EU",
        name="EU (ARF v1.4)",
        flag="🇪🇺",
        scheme="EUDI ARF",
        trust_framework="eIDAS 2.0 + ARF v1.4",
        supported_formats=["sd-jwt", "mdoc", "ldp-vc"],
        loa_mapping={"low": "low", "substantial": "substantial", "high": "high"},
        reference_url="https://github.com/eu-digital-identity-wallet/architecture-and-reference-framework",
        id_hash_algorithm="SHA-256",
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
            return await self._sd_verifier.verify(presentation, audience=audience, nonce=nonce)
        if format == "mdoc":
            from services.mdoc_verifier import MDocVerifier

            return await MDocVerifier().verify(bytes.fromhex(presentation))
        if format == "ldp-vc":
            return await self._ldp_verifier.verify(presentation)
        return {"valid": False, "reasons": [f"format {format} not supported by EU ARF adapter"]}

    def hash_national_id(self, national_id: str) -> str:
        return sha256_hex(national_id.strip())
