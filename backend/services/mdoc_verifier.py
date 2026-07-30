"""ISO 18013-5 mDoc Verifier — validates issuerAuth chain + digest matches."""
from __future__ import annotations

import hashlib
from typing import Any

import cbor2
from cbor2 import CBORTag
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from services.ca_generator import CAGenerator
from services.trust_validator import TrustValidator


def _verify_cose_sign1(cose_bytes: bytes, signer_cert_der: bytes) -> tuple[bool, str]:
    tagged = cbor2.loads(cose_bytes)
    if not isinstance(tagged, CBORTag) or tagged.tag != 18:
        return False, "issuerAuth missing Tag 18 (COSE_Sign1)"
    prot, _unprot, payload, sig = tagged.value
    sig_structure = cbor2.dumps(["Signature1", prot, b"", payload])
    cert = x509.load_der_x509_certificate(signer_cert_der)
    pk = cert.public_key()
    if not isinstance(pk, ec.EllipticCurvePublicKey):
        return False, "signer key is not EC"
    if len(sig) != 64:
        return False, f"expected 64-byte ES256 signature, got {len(sig)}"
    r = int.from_bytes(sig[:32], "big")
    s = int.from_bytes(sig[32:], "big")
    der = encode_dss_signature(r, s)
    try:
        pk.verify(der, sig_structure, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return False, "issuerAuth signature invalid"
    return True, ""


class MDocVerifier:
    async def verify(self, mdoc_bytes: bytes) -> dict[str, Any]:
        reasons: list[str] = []
        try:
            issuer_signed = cbor2.loads(mdoc_bytes)
        except Exception as exc:
            return {"valid": False, "reasons": [f"cbor parse: {exc}"]}
        if not isinstance(issuer_signed, dict):
            return {"valid": False, "reasons": ["issuerSigned is not a map"]}
        namespaces = issuer_signed.get("nameSpaces", {})
        issuer_auth = issuer_signed.get("issuerAuth")
        if not issuer_auth:
            return {"valid": False, "reasons": ["missing issuerAuth"]}

        # unwrap COSE_Sign1 to fetch x5chain
        cose = cbor2.loads(issuer_auth)
        _prot, unprot, payload, _sig = cose.value
        x5chain_der = unprot.get(33)
        if isinstance(x5chain_der, list):
            x5chain_der = x5chain_der[0]
        if not x5chain_der:
            return {"valid": False, "reasons": ["issuerAuth lacks x5chain"]}

        # signature check
        ok, err = _verify_cose_sign1(issuer_auth, x5chain_der)
        if not ok:
            reasons.append(err)

        # chain check against CA
        mat = await CAGenerator.get_material()
        signer_cert = x509.load_der_x509_certificate(x5chain_der)
        chain = [signer_cert, mat["intermediate"]["cert"], mat["root"]["cert"]]
        tv = TrustValidator([mat["root"]["cert"]])
        chain_res = tv.validate_chain(chain)
        if not chain_res["valid"]:
            reasons.extend(chain_res["reasons"])

        # decode MSO from Tag 24
        payload_tag = cbor2.loads(payload)
        if not isinstance(payload_tag, CBORTag) or payload_tag.tag != 24:
            reasons.append("issuerAuth payload lacks Tag 24")
            mso = {}
        else:
            mso = cbor2.loads(payload_tag.value)

        # validate digests
        disclosed: dict[str, dict[str, Any]] = {}
        value_digests = mso.get("valueDigests", {})
        for ns, items in namespaces.items():
            ns_digests = value_digests.get(ns, {})
            disclosed[ns] = {}
            for item_bytes in items:
                actual = hashlib.sha256(item_bytes).digest()
                item = cbor2.loads(item_bytes)
                if isinstance(item, CBORTag) and item.tag == 24:
                    elem = cbor2.loads(item.value)
                    if ns_digests.get(elem["digestID"]) != actual:
                        reasons.append(f"digest mismatch in {ns}/{elem.get('elementIdentifier')}")
                        continue
                    disclosed[ns][elem["elementIdentifier"]] = elem["elementValue"]
        device_key_present = bool(mso.get("deviceKeyInfo", {}).get("deviceKey"))
        return {
            "valid": len(reasons) == 0,
            "reasons": reasons,
            "doctype": mso.get("docType"),
            "disclosed_namespaces": disclosed,
            "trust_chain": chain_res.get("chain", []),
            "device_key_present": device_key_present,
        }
