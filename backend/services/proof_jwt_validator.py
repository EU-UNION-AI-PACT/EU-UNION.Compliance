"""OpenID4VCI Proof-of-Possession JWT validator — c_nonce one-time-use."""
from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from database import get_db


def _b64u_decode(seg: str) -> bytes:
    pad = "=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg + pad)


def _jwk_to_pub(jwk: dict[str, Any]) -> ec.EllipticCurvePublicKey:
    if jwk.get("kty") != "EC":
        raise ValueError("only EC JWKs supported in proof-of-possession")
    curve_map = {"P-256": ec.SECP256R1(), "P-384": ec.SECP384R1()}
    curve = curve_map[jwk["crv"]]
    x = int.from_bytes(_b64u_decode(jwk["x"]), "big")
    y = int.from_bytes(_b64u_decode(jwk["y"]), "big")
    return ec.EllipticCurvePublicNumbers(x, y, curve).public_key()


class ProofJWTValidator:
    """
    Validates OpenID4VCI proof JWTs (typ=openid4vci-proof+jwt).

    c_nonce enforcement: the nonce is read from Mongo and *atomically*
    deleted via `find_one_and_delete` so it cannot be replayed.
    """

    def __init__(self, expected_audience: str, nonce_ttl_seconds: int = 300) -> None:
        self._aud = expected_audience
        self._ttl = nonce_ttl_seconds

    async def issue_nonce(self) -> tuple[str, int]:
        import secrets

        nonce = base64.urlsafe_b64encode(secrets.token_bytes(24)).decode().rstrip("=")
        exp = datetime.now(timezone.utc) + timedelta(seconds=self._ttl)
        await get_db().c_nonces.insert_one({"value": nonce, "expires_at": exp})
        return nonce, self._ttl

    async def validate(self, proof_jwt: str, expected_holder_jwk: dict[str, Any]) -> dict[str, Any]:
        reasons: list[str] = []
        try:
            hb64, pb64, sb64 = proof_jwt.split(".")
            header = json.loads(_b64u_decode(hb64))
            payload = json.loads(_b64u_decode(pb64))
        except Exception as exc:
            return {"valid": False, "reasons": [f"proof jwt parse: {exc}"]}
        if header.get("typ") != "openid4vci-proof+jwt":
            reasons.append(f"typ must be openid4vci-proof+jwt (got {header.get('typ')})")
        if header.get("alg") not in ("ES256", "ES384"):
            reasons.append(f"alg must be ES256/ES384 (got {header.get('alg')})")
        if "jwk" not in header:
            reasons.append("proof jwt header must include jwk")
        elif header["jwk"] != expected_holder_jwk:
            reasons.append("jwk mismatch with holder key")
        if payload.get("aud") != self._aud:
            reasons.append(f"aud mismatch (expected {self._aud})")
        iat = payload.get("iat", 0)
        now = int(datetime.now(timezone.utc).timestamp())
        if abs(now - iat) > 600:
            reasons.append("iat skew > 10min")
        nonce = payload.get("nonce")
        if not nonce:
            reasons.append("nonce missing")
        else:
            consumed = await get_db().c_nonces.find_one_and_delete({"value": nonce})
            if not consumed:
                reasons.append("nonce unknown or already used (one-time-use)")

        # signature verify with declared jwk
        if "jwk" in header:
            try:
                pk = _jwk_to_pub(header["jwk"])
                sig_raw = _b64u_decode(sb64)
                comp = 32 if header.get("alg") == "ES256" else 48
                r = int.from_bytes(sig_raw[:comp], "big")
                s = int.from_bytes(sig_raw[comp:], "big")
                der = encode_dss_signature(r, s)
                hash_algo = hashes.SHA256() if header.get("alg") == "ES256" else hashes.SHA384()
                pk.verify(der, f"{hb64}.{pb64}".encode(), ec.ECDSA(hash_algo))
            except InvalidSignature:
                reasons.append("proof jwt signature invalid")
            except Exception as exc:
                reasons.append(f"proof verify error: {exc}")
        return {"valid": len(reasons) == 0, "reasons": reasons}
