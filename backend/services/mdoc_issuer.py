"""ISO 18013-5 mDoc Issuer — Tag 18 (COSE_Sign1), Tag 24 (bstr.cbor), Tag 0 (tdate).

Emits IssuerSigned per ISO 18013-5 §9.1.2:

    IssuerSigned = {
      "nameSpaces": IssuerNameSpaces,
      "issuerAuth": IssuerAuth,           ; COSE_Sign1 (Tag 18)
    }

    IssuerAuth payload = Tag 24 <MobileSecurityObjectBytes>
    MSO carries digestAlgorithm, valueDigests, deviceKeyInfo, docType, validityInfo.
"""
from __future__ import annotations

import asyncio
import hashlib
import os
from datetime import datetime, timezone, timedelta
from typing import Any

import cbor2
from cbor2 import CBORTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from services.ca_generator import CAGenerator


COSE_ES256 = -7


def _cose_sign1(protected: dict, unprotected: dict, payload: bytes, tbs_signer: ec.EllipticCurvePrivateKey) -> bytes:
    prot_bstr = cbor2.dumps(protected) if protected else b""
    sig_structure = cbor2.dumps(["Signature1", prot_bstr, b"", payload])
    der = tbs_signer.sign(sig_structure, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return cbor2.dumps(CBORTag(18, [prot_bstr, unprotected, payload, sig]))


def _cose_key_from_ec_jwk(jwk: dict[str, Any]) -> dict[int, Any]:
    import base64

    def _b64u_decode(s: str) -> bytes:
        pad = "=" * (-len(s) % 4)
        return base64.urlsafe_b64decode(s + pad)

    x = _b64u_decode(jwk["x"])
    y = _b64u_decode(jwk["y"])
    return {1: 2, -1: 1, -2: x, -3: y}  # kty EC2, crv P-256, x, y


class MDocIssuerSingleton:
    _instance: "MDocIssuerSingleton | None" = None
    _lock = asyncio.Lock()

    def __init__(self, signer_key: ec.EllipticCurvePrivateKey, signer_cert_pem: str) -> None:
        self._signer = signer_key
        self._cert_pem = signer_cert_pem
        # DER for x5chain header
        from cryptography import x509

        self._cert_der = x509.load_pem_x509_certificate(signer_cert_pem.encode()).public_bytes(
            serialization.Encoding.DER
        )

    @classmethod
    async def instance(cls) -> "MDocIssuerSingleton":
        async with cls._lock:
            if cls._instance is not None:
                return cls._instance
            mat = await CAGenerator.get_material()
            cls._instance = cls(mat["signer"]["key"], mat["signer"]["pem"])
            return cls._instance

    def issue(
        self,
        doctype: str,
        namespaces: dict[str, dict[str, Any]],
        device_public_jwk: dict[str, Any],
        ttl_days: int = 365,
    ) -> tuple[bytes, int]:
        issuer_name_spaces: dict[str, list[bytes]] = {}
        value_digests: dict[str, dict[int, bytes]] = {}
        total = 0
        for ns, claims in namespaces.items():
            digests: dict[int, bytes] = {}
            items: list[bytes] = []
            for claim_id, (claim_name, value) in enumerate(claims.items()):
                random = os.urandom(16)
                elem = {
                    "digestID": claim_id,
                    "random": random,
                    "elementIdentifier": claim_name,
                    "elementValue": value,
                }
                encoded = cbor2.dumps(elem)
                # Tag 24 — bstr containing CBOR bytes
                tagged = CBORTag(24, encoded)
                items.append(cbor2.dumps(tagged))
                digests[claim_id] = hashlib.sha256(cbor2.dumps(tagged)).digest()
                total += 1
            issuer_name_spaces[ns] = items
            value_digests[ns] = digests

        now = datetime.now(timezone.utc)
        mso = {
            "version": "1.0",
            "digestAlgorithm": "SHA-256",
            "valueDigests": value_digests,
            "deviceKeyInfo": {"deviceKey": _cose_key_from_ec_jwk(device_public_jwk)},
            "docType": doctype,
            "validityInfo": {
                "signed": CBORTag(0, now.strftime("%Y-%m-%dT%H:%M:%SZ")),
                "validFrom": CBORTag(0, now.strftime("%Y-%m-%dT%H:%M:%SZ")),
                "validUntil": CBORTag(
                    0, (now + timedelta(days=ttl_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
                ),
            },
        }
        mso_bytes = cbor2.dumps(mso)
        # Tag 24 payload
        payload_tag24 = cbor2.dumps(CBORTag(24, mso_bytes))
        issuer_auth = _cose_sign1(
            protected={1: COSE_ES256},
            unprotected={33: self._cert_der},  # x5chain
            payload=payload_tag24,
            tbs_signer=self._signer,
        )
        issuer_signed = {"nameSpaces": issuer_name_spaces, "issuerAuth": issuer_auth}
        return cbor2.dumps(issuer_signed), total
