"""Signed Status List client (IETF draft-ietf-oauth-status-list) — LRU + TTL."""
from __future__ import annotations

import base64
import time
import zlib
from typing import Literal

from database import get_db

Status = Literal["active", "suspended", "revoked", "unknown"]


class StatusListClient:
    """Local implementation — for external URIs we fall back to Mongo mirror.

    The status bit-list uses 2 bits per credential (values 0..3):
      0 = valid, 1 = invalid/revoked, 2 = suspended.

    We store the list decoded (bytearray) in Mongo under `status_list_docs`
    and cache in-memory for 5 minutes.
    """

    _cache: dict[str, tuple[float, bytearray]] = {}
    _TTL = 300  # seconds

    async def status_for(self, uri: str, idx: int) -> Status:
        bits = await self._get_bits(uri)
        if bits is None:
            return "unknown"
        byte_idx = idx // 4
        offset = (idx % 4) * 2
        if byte_idx >= len(bits):
            return "active"
        value = (bits[byte_idx] >> offset) & 0b11
        return {0: "active", 1: "revoked", 2: "suspended"}.get(value, "unknown")

    async def set_status(self, uri: str, idx: int, status: Status) -> None:
        db = get_db()
        doc = await db.status_list_docs.find_one({"uri": uri})
        if not doc:
            bits = bytearray(1024)
            doc = {"uri": uri, "bits_b64": base64.b64encode(zlib.compress(bytes(bits))).decode()}
            await db.status_list_docs.insert_one(doc)
        bits = bytearray(zlib.decompress(base64.b64decode(doc["bits_b64"])))
        if idx // 4 >= len(bits):
            bits.extend(b"\x00" * (idx // 4 - len(bits) + 1))
        code = {"active": 0, "revoked": 1, "suspended": 2}[status]
        byte_idx = idx // 4
        offset = (idx % 4) * 2
        bits[byte_idx] &= ~(0b11 << offset) & 0xFF
        bits[byte_idx] |= code << offset
        packed = base64.b64encode(zlib.compress(bytes(bits))).decode()
        await db.status_list_docs.update_one({"uri": uri}, {"$set": {"bits_b64": packed}})
        self._cache.pop(uri, None)

    async def _get_bits(self, uri: str) -> bytearray | None:
        now = time.time()
        cached = self._cache.get(uri)
        if cached and now - cached[0] < self._TTL:
            return cached[1]
        doc = await get_db().status_list_docs.find_one({"uri": uri})
        if not doc:
            return None
        bits = bytearray(zlib.decompress(base64.b64decode(doc["bits_b64"])))
        self._cache[uri] = (now, bits)
        return bits
