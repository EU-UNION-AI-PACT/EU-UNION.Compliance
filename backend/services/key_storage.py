"""AES-256-GCM envelope encryption — fail-fast on missing MASTER_KEY."""
from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class KeyStorageError(RuntimeError):
    pass


class KeyStorageManager:
    """
    Envelope encryption for at-rest private key material.

    MASTER_KEY must be provided via env (32-byte base64). If missing or malformed,
    we fail fast — never fall back to a hardcoded value.
    """

    def __init__(self) -> None:
        raw = os.environ.get("MASTER_KEY")
        if not raw:
            raise KeyStorageError(
                "MASTER_KEY env var is required (32-byte base64). "
                "Refusing to boot without it."
            )
        try:
            key = base64.b64decode(raw)
        except Exception as exc:  # pragma: no cover
            raise KeyStorageError(f"MASTER_KEY is not valid base64: {exc}") from exc
        if len(key) != 32:
            raise KeyStorageError(
                f"MASTER_KEY must decode to 32 bytes (got {len(key)})."
            )
        self._aead = AESGCM(key)

    def wrap(self, plaintext: bytes, aad: bytes = b"") -> str:
        nonce = os.urandom(12)
        ct = self._aead.encrypt(nonce, plaintext, aad)
        return base64.b64encode(nonce + ct).decode()

    def unwrap(self, wrapped: str, aad: bytes = b"") -> bytes:
        blob = base64.b64decode(wrapped)
        if len(blob) < 13:
            raise KeyStorageError("wrapped blob too small")
        nonce, ct = blob[:12], blob[12:]
        return self._aead.decrypt(nonce, ct, aad)
