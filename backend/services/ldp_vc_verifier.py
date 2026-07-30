"""W3C VC-DM 2.0 Linked-Data-Proof verifier with URDNA2015 canonicalization.

Supports the two DataIntegrity cryptosuites relevant to EU/CH/US wallet stacks:

  * `eddsa-rdfc-2022` — Ed25519 keys, URDNA2015 canonicalization of both the
    document (minus proof) and the proof options (minus proofValue).
  * `ecdsa-rdfc-2019` — P-256 keys, same layout, SHA-256.

Both suites hash the two canonicalized N-Quads streams separately, concatenate
them, and sign / verify the concatenation.

References:
  - W3C VC Data Model 2.0 (Rec, Nov 2024)
  - W3C Data Integrity 1.0 (Rec, Nov 2024) §3.1
  - VC-DI-EDDSA 1.0 / VC-DI-ECDSA 1.0 cryptosuites
  - RDF Dataset Canonicalization 1.0 (URDNA2015 → RDFC-1.0)
"""
from __future__ import annotations

import base64
import copy
import hashlib
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from pyld import jsonld

_DOC_LOADER_CACHE: dict[str, dict[str, Any]] = {}


def _multibase_decode(mb: str) -> bytes:
    """Handle base58btc (z…) and base64url (u…) multibase prefixes."""
    if not mb:
        raise ValueError("empty multibase")
    prefix, rest = mb[0], mb[1:]
    if prefix == "z":
        # base58btc
        import base58  # optional lightweight import

        return base58.b58decode(rest)
    if prefix == "u":
        pad = "=" * (-len(rest) % 4)
        return base64.urlsafe_b64decode(rest + pad)
    raise ValueError(f"unsupported multibase prefix {prefix!r}")


def _canonicalize(doc: dict[str, Any]) -> str:
    """URDNA2015 (aka RDFC-1.0) canonicalization of a JSON-LD document.

    Pyld's `normalize` with `URDNA2015` returns a deterministic string of sorted
    N-Quads (one triple per line).
    """
    return jsonld.normalize(
        doc, {"algorithm": "URDNA2015", "format": "application/n-quads"}
    )


def _hash_two_streams(proof_options: dict[str, Any], document: dict[str, Any]) -> bytes:
    proof_canon = _canonicalize(proof_options)
    doc_canon = _canonicalize(document)
    h1 = hashlib.sha256(proof_canon.encode()).digest()
    h2 = hashlib.sha256(doc_canon.encode()).digest()
    return h1 + h2


class LdpVcVerifier:
    """Verify a W3C VC-DM 2.0 credential with a DataIntegrity proof."""

    SUPPORTED_SUITES = {"eddsa-rdfc-2022", "ecdsa-rdfc-2019", "Ed25519Signature2020"}

    async def verify(
        self,
        presentation: str | dict[str, Any],
    ) -> dict[str, Any]:
        reasons: list[str] = []
        try:
            doc = presentation if isinstance(presentation, dict) else self._parse(presentation)
        except Exception as exc:
            return {"valid": False, "reasons": [f"ldp-vc parse: {exc}"], "disclosed_claims": {}}

        proof = doc.get("proof")
        if not proof:
            return {"valid": False, "reasons": ["ldp-vc missing proof"], "disclosed_claims": {}}
        if isinstance(proof, list):
            proof = proof[0]
        suite = proof.get("cryptosuite") or proof.get("type")
        if suite not in self.SUPPORTED_SUITES:
            reasons.append(f"unsupported cryptosuite '{suite}' (supported: {sorted(self.SUPPORTED_SUITES)})")

        # Build the two canonicalization inputs
        proof_options = {k: v for k, v in proof.items() if k not in ("proofValue", "jws")}
        document = {k: v for k, v in doc.items() if k != "proof"}
        try:
            payload = _hash_two_streams(proof_options, document)
        except Exception as exc:
            return {
                "valid": False,
                "reasons": reasons + [f"URDNA2015 canonicalization failed: {exc}"],
                "disclosed_claims": {},
            }

        # Extract signature + public key from verificationMethod (minimal — for
        # a full deployment resolve DID → key document via did-resolver).
        vm = proof.get("verificationMethod", "")
        pub_multibase = proof.get("publicKeyMultibase") or _extract_key_from_vm(vm)
        proof_value = proof.get("proofValue")
        if not proof_value or not pub_multibase:
            reasons.append("proof must include proofValue and a resolvable public key")
        else:
            try:
                sig = _multibase_decode(proof_value)
                pub = _multibase_decode(pub_multibase)
                if suite in ("eddsa-rdfc-2022", "Ed25519Signature2020"):
                    # multicodec prefix for Ed25519 pub is 0xed01 (2 bytes)
                    if pub.startswith(b"\xed\x01"):
                        pub = pub[2:]
                    ed25519.Ed25519PublicKey.from_public_bytes(pub).verify(sig, payload)
                elif suite == "ecdsa-rdfc-2019":
                    if pub.startswith(b"\x80\x24"):  # P-256 multicodec 0x1200
                        pub = pub[2:]
                    # P-256 uncompressed = 0x04 || X(32) || Y(32)
                    if len(pub) != 65 or pub[0] != 0x04:
                        raise ValueError("P-256 pub must be 65-byte uncompressed")
                    x = int.from_bytes(pub[1:33], "big")
                    y = int.from_bytes(pub[33:], "big")
                    ec_pub = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()
                    r = int.from_bytes(sig[:32], "big")
                    s = int.from_bytes(sig[32:], "big")
                    der = encode_dss_signature(r, s)
                    ec_pub.verify(der, payload, ec.ECDSA(hashes.SHA256()))
            except InvalidSignature:
                reasons.append("DataIntegrity proof signature invalid")
            except Exception as exc:
                reasons.append(f"proof verification error: {exc}")

        # Extract subject claims from credentialSubject
        subject = doc.get("credentialSubject") or {}
        if isinstance(subject, list):
            subject = subject[0] if subject else {}
        disclosed = {k: v for k, v in subject.items() if k != "id"}

        return {
            "valid": len(reasons) == 0,
            "reasons": reasons,
            "disclosed_claims": disclosed,
            "issuer": doc.get("issuer") if isinstance(doc.get("issuer"), str) else (doc.get("issuer") or {}).get("id"),
            "vct": "w3c-vc-dm-2.0",
            "status": "unknown",
        }

    def _parse(self, s: str) -> dict[str, Any]:
        import json

        return json.loads(s)


def _extract_key_from_vm(vm: str) -> str | None:
    """`did:key:z6Mk…#z6Mk…` → z6Mk…"""
    if not vm:
        return None
    if "#" in vm:
        _, frag = vm.rsplit("#", 1)
        return frag
    if vm.startswith("did:key:"):
        return vm[len("did:key:"):]
    return None
