"""RFC 5280 X.509 chain validator — signature + time + name-chaining."""
from __future__ import annotations

from datetime import datetime, timezone

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey


def _verify_signed_by(child: x509.Certificate, parent: x509.Certificate) -> str | None:
    """Return None on success, else a human-readable reason string."""
    pub = parent.public_key()
    try:
        if isinstance(pub, ec.EllipticCurvePublicKey):
            pub.verify(
                child.signature,
                child.tbs_certificate_bytes,
                ec.ECDSA(child.signature_hash_algorithm),
            )
        elif isinstance(pub, RSAPublicKey):
            pub.verify(
                child.signature,
                child.tbs_certificate_bytes,
                padding.PKCS1v15(),
                child.signature_hash_algorithm,
            )
        else:
            return "unsupported parent key type"
    except InvalidSignature:
        return "invalid signature"
    if child.issuer != parent.subject:
        return "issuer/subject name mismatch"
    return None


class TrustValidator:
    """RFC 5280 chain check: signer → intermediate → root anchor."""

    def __init__(self, trust_anchors: list[x509.Certificate]) -> None:
        self._anchors_by_subject = {a.subject: a for a in trust_anchors}

    def validate_chain(self, chain: list[x509.Certificate]) -> dict[str, object]:
        reasons: list[str] = []
        if not chain:
            return {"valid": False, "reasons": ["empty chain"]}
        now = datetime.now(timezone.utc)
        # time checks
        for cert in chain:
            if cert.not_valid_before_utc > now:
                reasons.append(f"cert not yet valid: {cert.subject.rfc4514_string()}")
            if cert.not_valid_after_utc < now:
                reasons.append(f"cert expired: {cert.subject.rfc4514_string()}")
        # chain checks — each child MUST be signed by next
        for i in range(len(chain) - 1):
            err = _verify_signed_by(chain[i], chain[i + 1])
            if err:
                reasons.append(
                    f"link {i}→{i+1} ({chain[i].subject.rfc4514_string()}): {err}"
                )
        # anchor check: the last cert must either BE an anchor or be signed by one
        top = chain[-1]
        anchor = self._anchors_by_subject.get(top.subject) or self._anchors_by_subject.get(top.issuer)
        if not anchor:
            reasons.append("top-of-chain not present in trust anchor set")
        else:
            if top.subject != anchor.subject:
                err = _verify_signed_by(top, anchor)
                if err:
                    reasons.append(f"anchor verification failed: {err}")
        chain_repr = [c.subject.rfc4514_string() for c in chain]
        return {"valid": len(reasons) == 0, "reasons": reasons, "chain": chain_repr}
