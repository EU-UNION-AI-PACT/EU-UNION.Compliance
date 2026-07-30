"""SD-JWT VC Issuer — RFC 9215 / draft-ietf-oauth-sd-jwt-vc.

Builds a compact SD-JWT with per-claim salted disclosures and an `_sd` digest
array in the payload. Also embeds `cnf.jwk` (holder key binding), `vct`, `iss`,
`iat`, `exp`, and — critically — a `status.status_list` pointer.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from services.issuer_signer import sign_jws


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64u_str(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


def _hash_disclosure(disclosure_b64: str) -> str:
    digest = hashlib.sha256(disclosure_b64.encode("ascii")).digest()
    return _b64u(digest)


def _make_disclosure(claim: str, value: Any) -> tuple[str, str]:
    """Return (disclosure_b64, sd_digest)."""
    salt = _b64u(secrets.token_bytes(16))
    array = json.dumps([salt, claim, value], separators=(",", ":"))
    disclosure_b64 = _b64u_str(array)
    return disclosure_b64, _hash_disclosure(disclosure_b64)


class SDJWTBuilder:
    def __init__(self, issuer: str, vct: str, ttl_hours: int = 24 * 30) -> None:
        self.issuer = issuer
        self.vct = vct
        self.ttl = timedelta(hours=ttl_hours)

    async def issue(
        self,
        *,
        claims: dict[str, Any],
        holder_jwk: dict[str, Any],
        status_index: int,
        status_list_uri: str,
    ) -> tuple[str, int]:
        """Return (compact_sd_jwt, disclosure_count)."""
        sd_digests: list[str] = []
        disclosures: list[str] = []
        for k, v in claims.items():
            disc, dig = _make_disclosure(k, v)
            disclosures.append(disc)
            sd_digests.append(dig)
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "iss": self.issuer,
            "vct": self.vct,
            "iat": int(now.timestamp()),
            "exp": int((now + self.ttl).timestamp()),
            "_sd": sd_digests,
            "_sd_alg": "sha-256",
            "cnf": {"jwk": holder_jwk},
            "status": {
                "status_list": {
                    "idx": status_index,
                    "uri": status_list_uri,
                }
            },
        }
        jws = await sign_jws(payload, typ="vc+sd-jwt")
        compact = jws + "~" + "~".join(disclosures) + "~"
        return compact, len(disclosures)
