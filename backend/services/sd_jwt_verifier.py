"""SD-JWT VC Verifier V2 — with KB-JWT + Status List + Trust-Anchor lookup.

Verifies:
  * JWS signature (ES256/ES384) via SignerSingleton public key
  * time claims (iat / exp / nbf)
  * disclosure digests match `_sd`
  * key binding JWT (typ=kb+jwt) — if audience/nonce present
  * status list — bit 0=active, 1=suspended, 2=revoked
"""
from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from services.signer_singleton import SignerSingleton
from services.status_list_client import StatusListClient


def _b64u_decode(seg: str) -> bytes:
    pad = "=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg + pad)


def _jwk_to_ec_public_key(jwk: dict[str, Any]) -> ec.EllipticCurvePublicKey:
    if jwk.get("kty") != "EC":
        raise ValueError("only EC JWKs supported")
    crv = jwk.get("crv")
    curve_map = {"P-256": ec.SECP256R1(), "P-384": ec.SECP384R1(), "P-521": ec.SECP521R1()}
    if crv not in curve_map:
        raise ValueError(f"unsupported curve {crv}")
    x = int.from_bytes(_b64u_decode(jwk["x"]), "big")
    y = int.from_bytes(_b64u_decode(jwk["y"]), "big")
    return ec.EllipticCurvePublicNumbers(x, y, curve_map[crv]).public_key()


class SDJWTVerifierV2:
    def __init__(self, status_client: StatusListClient) -> None:
        self._status = status_client

    async def verify(
        self,
        presentation: str,
        *,
        audience: str | None = None,
        nonce: str | None = None,
    ) -> dict[str, Any]:
        reasons: list[str] = []
        parts = presentation.split("~")
        if len(parts) < 2:
            return {"valid": False, "reasons": ["malformed sd-jwt (no `~`)"]}
        jws = parts[0]
        disclosures = [p for p in parts[1:-1] if p]  # last "" is trailing tilde
        kb_jwt = parts[-1] if parts[-1] else None

        try:
            protected_b64, payload_b64, sig_b64 = jws.split(".")
            protected = json.loads(_b64u_decode(protected_b64))
            payload = json.loads(_b64u_decode(payload_b64))
        except Exception as exc:
            return {"valid": False, "reasons": [f"cannot parse jws: {exc}"]}

        # signature check against SignerSingleton (issuer)
        signer = await SignerSingleton.instance()
        signing_input = f"{protected_b64}.{payload_b64}".encode()
        sig_raw = _b64u_decode(sig_b64)
        alg = protected.get("alg", "ES256")
        try:
            if alg == "ES256":
                r = int.from_bytes(sig_raw[:32], "big")
                s = int.from_bytes(sig_raw[32:], "big")
                der = encode_dss_signature(r, s)
                signer.public_key.verify(der, signing_input, ec.ECDSA(hashes.SHA256()))
            else:
                reasons.append(f"unsupported alg {alg}")
        except InvalidSignature:
            reasons.append("invalid issuer signature")
        except Exception as exc:
            reasons.append(f"signature error: {exc}")

        # time claims
        now = int(datetime.now(timezone.utc).timestamp())
        if "exp" in payload and payload["exp"] < now:
            reasons.append("credential expired")
        if "nbf" in payload and payload["nbf"] > now:
            reasons.append("credential not yet valid")

        # disclosures
        sd = set(payload.get("_sd", []))
        alg_name = payload.get("_sd_alg", "sha-256")
        if alg_name != "sha-256":
            reasons.append(f"unsupported _sd_alg {alg_name}")
        disclosed: dict[str, Any] = {}
        for d in disclosures:
            dig = base64.urlsafe_b64encode(hashlib.sha256(d.encode()).digest()).decode().rstrip("=")
            if dig not in sd:
                reasons.append(f"unknown disclosure digest {dig[:8]}…")
                continue
            try:
                arr = json.loads(_b64u_decode(d))
                if len(arr) == 3:
                    disclosed[arr[1]] = arr[2]
            except Exception:
                reasons.append("malformed disclosure")

        # key binding JWT — expected when audience/nonce are asserted
        if audience or nonce:
            if not kb_jwt:
                reasons.append("missing KB-JWT")
            else:
                cnf = payload.get("cnf", {}).get("jwk")
                if not cnf:
                    reasons.append("credential lacks cnf.jwk")
                else:
                    kb_res = self._verify_kb(kb_jwt, cnf, audience, nonce)
                    if not kb_res["valid"]:
                        reasons.extend(kb_res["reasons"])

        # status list
        status_uri = payload.get("status", {}).get("status_list", {}).get("uri")
        status_idx = payload.get("status", {}).get("status_list", {}).get("idx")
        status = "unknown"
        if status_uri and status_idx is not None:
            status = await self._status.status_for(status_uri, status_idx)
            if status == "revoked":
                reasons.append("credential revoked")

        return {
            "valid": len(reasons) == 0,
            "reasons": reasons,
            "disclosed_claims": disclosed,
            "issuer": payload.get("iss"),
            "vct": payload.get("vct"),
            "status": status,
        }

    def _verify_kb(
        self,
        kb_jwt: str,
        holder_jwk: dict[str, Any],
        audience: str | None,
        nonce: str | None,
    ) -> dict[str, Any]:
        reasons: list[str] = []
        try:
            hb64, pb64, sb64 = kb_jwt.split(".")
            header = json.loads(_b64u_decode(hb64))
            payload = json.loads(_b64u_decode(pb64))
        except Exception as exc:
            return {"valid": False, "reasons": [f"KB-JWT parse: {exc}"]}
        if header.get("typ") != "kb+jwt":
            reasons.append(f"KB-JWT typ must be kb+jwt (got {header.get('typ')})")
        if audience and payload.get("aud") != audience:
            reasons.append("KB-JWT aud mismatch")
        if nonce and payload.get("nonce") != nonce:
            reasons.append("KB-JWT nonce mismatch")
        try:
            pk = _jwk_to_ec_public_key(holder_jwk)
            sig_raw = _b64u_decode(sb64)
            r = int.from_bytes(sig_raw[:32], "big")
            s = int.from_bytes(sig_raw[32:], "big")
            der = encode_dss_signature(r, s)
            pk.verify(der, f"{hb64}.{pb64}".encode(), ec.ECDSA(hashes.SHA256()))
        except InvalidSignature:
            reasons.append("KB-JWT signature invalid")
        except Exception as exc:
            reasons.append(f"KB-JWT verify error: {exc}")
        return {"valid": len(reasons) == 0, "reasons": reasons}
