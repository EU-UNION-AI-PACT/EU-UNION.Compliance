"""Cryptographically chained audit-log (SHA-256 hash chain + issuer signature)."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from database import get_db
from services.issuer_signer import sign_jws

_append_lock = asyncio.Lock()


async def append_event(
    event_type: str,
    actor: str,
    subject: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with _append_lock:
        db = get_db()
        last = await db.audit_log.find_one(sort=[("timestamp", -1)])
        prev_hash = last["hash"] if last else ""
        body = {
            "event_type": event_type,
            "actor": actor,
            "subject": subject,
            "payload": payload or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prev_hash": prev_hash,
        }
        body_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        h = hashlib.sha256(body_bytes).hexdigest()
        signature = await sign_jws({"h": h}, typ="audit+jwt")
        doc = {**body, "hash": h, "signature": signature}
        await db.audit_log.insert_one(doc)
        doc.pop("_id", None)
        return doc


async def verify_chain(limit: int = 200) -> dict[str, Any]:
    db = get_db()
    docs = await db.audit_log.find({}, {"_id": 0}).sort("timestamp", 1).to_list(limit)
    reasons: list[str] = []
    prev = ""
    for d in docs:
        body = {k: d[k] for k in ("event_type", "actor", "subject", "payload", "timestamp", "prev_hash")}
        body_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        h = hashlib.sha256(body_bytes).hexdigest()
        if h != d["hash"]:
            reasons.append(f"hash mismatch at {d['timestamp']}")
        if d["prev_hash"] != prev:
            reasons.append(f"prev_hash mismatch at {d['timestamp']}")
        prev = d["hash"]
    return {"valid": len(reasons) == 0, "reasons": reasons, "checked": len(docs)}
