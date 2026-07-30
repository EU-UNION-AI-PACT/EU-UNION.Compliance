"""CI Gate 2 — validate CBOR tag adherence in emitted mDocs."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import cbor2
from cbor2 import CBORTag


async def _issue_sample() -> bytes:
    from services.mdoc_issuer import MDocIssuerSingleton

    issuer = await MDocIssuerSingleton.instance()
    namespaces = {
        "org.iso.18013.5.1": {
            "family_name": "Doe",
            "given_name": "John",
            "birth_date": "1990-01-01",
            "issuing_country": "EU",
        }
    }
    device_jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": "MKBCTNIcKUSDii11ySs3526iDZ8AiTo7Tu6KPAqv7D4",
        "y": "4Etl6SRW2YiLUrN5vfvVHuhp7x8PxltmWWlbbM4IFyM",
    }
    mdoc, _ = issuer.issue("org.iso.18013.5.1.mDL", namespaces, device_jwk)
    return mdoc


def _find_tags(obj, found: set[int]) -> None:
    if isinstance(obj, CBORTag):
        found.add(obj.tag)
        _find_tags(obj.value, found)
    elif isinstance(obj, dict):
        for v in obj.values():
            _find_tags(v, found)
    elif isinstance(obj, list):
        for v in obj:
            _find_tags(v, found)
    elif isinstance(obj, (bytes, bytearray)):
        try:
            _find_tags(cbor2.loads(bytes(obj)), found)
        except Exception:
            pass


async def main() -> int:
    mdoc = await _issue_sample()
    top = cbor2.loads(mdoc)
    found: set[int] = set()
    _find_tags(top, found)
    # issuerAuth itself is Tag 18 — walk into it
    issuer_auth = top["issuerAuth"]
    tagged = cbor2.loads(issuer_auth)
    _find_tags(tagged, found)
    required = {18, 24, 0}
    missing = required - found
    if missing:
        print(f"[FAIL] missing CBOR tags: {sorted(missing)}", file=sys.stderr)
        return 1
    print(f"[OK] all required tags present: {sorted(required & found)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
