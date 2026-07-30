"""Race-safe singleton for the issuer's signing key.

Persists a single ES256 key across process lifetime. On first access, we
either load the existing wrapped private key from Mongo or generate a fresh
one (P-256), wrap it via KeyStorageManager, and store it. All subsequent calls
resolve the same key in-memory.
"""
from __future__ import annotations

import asyncio
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from database import get_db
from services.key_storage import KeyStorageManager


class SignerSingleton:
    _instance: "SignerSingleton | None" = None
    _lock = asyncio.Lock()

    def __init__(self, private_key: ec.EllipticCurvePrivateKey, kid: str) -> None:
        self._private_key = private_key
        self._kid = kid

    @classmethod
    async def instance(cls) -> "SignerSingleton":
        async with cls._lock:
            if cls._instance is not None:
                return cls._instance
            db = get_db()
            ks = KeyStorageManager()
            existing = await db.issuer_keys.find_one({"role": "primary"})
            if existing:
                pem = ks.unwrap(existing["wrapped_pem"])
                pk = serialization.load_pem_private_key(pem, password=None)
                if not isinstance(pk, ec.EllipticCurvePrivateKey):
                    raise RuntimeError("stored issuer key is not EC")
                cls._instance = cls(pk, existing["kid"])
                return cls._instance
            # generate fresh P-256
            pk = ec.generate_private_key(ec.SECP256R1())
            pem = pk.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption(),
            )
            kid = base64.urlsafe_b64encode(os_urandom(9)).decode().rstrip("=")
            await db.issuer_keys.insert_one(
                {
                    "role": "primary",
                    "kid": kid,
                    "curve": "P-256",
                    "wrapped_pem": ks.wrap(pem),
                }
            )
            cls._instance = cls(pk, kid)
            return cls._instance

    # -- accessors --

    @property
    def kid(self) -> str:
        return self._kid

    @property
    def private_key(self) -> ec.EllipticCurvePrivateKey:
        return self._private_key

    @property
    def public_key(self) -> ec.EllipticCurvePublicKey:
        return self._private_key.public_key()

    def public_pem(self) -> str:
        return self.public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def public_jwk(self) -> dict:
        nums = self.public_key.public_numbers()
        x = nums.x.to_bytes(32, "big")
        y = nums.y.to_bytes(32, "big")
        return {
            "kty": "EC",
            "crv": "P-256",
            "x": base64.urlsafe_b64encode(x).decode().rstrip("="),
            "y": base64.urlsafe_b64encode(y).decode().rstrip("="),
            "kid": self._kid,
            "use": "sig",
            "alg": "ES256",
        }


def os_urandom(n: int) -> bytes:
    import os

    return os.urandom(n)
