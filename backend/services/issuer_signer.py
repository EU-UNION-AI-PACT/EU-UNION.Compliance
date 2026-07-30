"""RFC 7515 JWS signer — ES256 with fixed 64-byte R‖S concat output."""
from __future__ import annotations

import base64
import json
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from services.signer_singleton import SignerSingleton


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64u_json(obj: dict[str, Any]) -> str:
    return _b64u(json.dumps(obj, separators=(",", ":"), sort_keys=True).encode())


def _rs_concat(pk: ec.EllipticCurvePrivateKey, msg: bytes, comp_len: int) -> bytes:
    """Sign msg and return R‖S in the fixed IEEE P1363 layout.

    RFC 7515 §3.4 mandates that ECDSA JWS signatures are the raw R and S values
    concatenated in fixed-length big-endian form, NOT the DER structure that
    OpenSSL emits by default.
    """
    algo = {32: hashes.SHA256, 48: hashes.SHA384, 66: hashes.SHA512}[comp_len]()
    der = pk.sign(msg, ec.ECDSA(algo))
    r, s = decode_dss_signature(der)
    return r.to_bytes(comp_len, "big") + s.to_bytes(comp_len, "big")


async def sign_jws(
    payload: dict[str, Any],
    *,
    typ: str = "vc+sd-jwt",
    extra_header: dict[str, Any] | None = None,
) -> str:
    signer = await SignerSingleton.instance()
    header = {"alg": "ES256", "typ": typ, "kid": signer.kid}
    if extra_header:
        header.update(extra_header)
    protected = _b64u_json(header)
    body = _b64u_json(payload)
    signing_input = f"{protected}.{body}".encode()
    sig = _rs_concat(signer.private_key, signing_input, 32)
    return f"{protected}.{body}.{_b64u(sig)}"
