"""Chain-of-custody ledger for signed PDF compliance reports.

Every time a PDF is signed via `POST /api/validate/report.pdf` or `/report.sign`
we append a hash-chained entry (`prev_hash → hash`) to the
`compliance_pdf_ledger` collection. The ledger stores only summary metadata
(digest, kid, framework code, verdict, requester fingerprint) — NEVER the
report payload itself — so a public GET is safe.

The chain is verifiable in O(n): each entry.hash = sha256(canonical({prev_hash, meta})).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from database import get_db

COL = "compliance_pdf_ledger"
GENESIS = "0" * 64


def _canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


async def _last_hash() -> str:
    db = get_db()
    doc = await db[COL].find_one({}, sort=[("seq", -1)])
    if not doc:
        return GENESIS
    return str(doc.get("hash", GENESIS))


async def append(
    *,
    digest_sha256: str,
    kid: str,
    algorithm: str,
    framework_code: str,
    status: str,
    score: int | None,
    kind: str,  # 'pdf' | 'sign' | 'bundle'
    requester: str,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    db = get_db()
    seq_doc = await db[COL].find_one({}, sort=[("seq", -1)])
    seq = int(seq_doc.get("seq", 0)) + 1 if seq_doc else 1
    prev = await _last_hash()
    meta: dict[str, Any] = {
        "seq": seq,
        "digest": digest_sha256,
        "kid": kid,
        "algorithm": algorithm,
        "framework": framework_code,
        "status": status,
        "score": score,
        "kind": kind,
        "requester": requester,
        "at": _now_iso(),
    }
    if extras:
        meta["extras"] = extras
    payload = {"prev_hash": prev, "meta": meta}
    h = hashlib.sha256(_canonical(payload)).hexdigest()
    doc = {
        "id": uuid.uuid4().hex,
        "prev_hash": prev,
        "hash": h,
        **meta,
    }
    if extras:
        doc["extras"] = extras
    await db[COL].insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


async def recent(limit: int = 100) -> list[dict[str, Any]]:
    db = get_db()
    return (
        await db[COL].find({}, {"_id": 0}).sort("seq", -1).to_list(min(500, limit))
    )


async def verify_chain(limit: int = 500) -> dict[str, Any]:
    db = get_db()
    entries = await db[COL].find({}, {"_id": 0}).sort("seq", 1).to_list(limit)
    ok = True
    broken_at: int | None = None
    for i, e in enumerate(entries):
        prev = entries[i - 1]["hash"] if i > 0 else GENESIS
        if e.get("prev_hash") != prev:
            ok = False
            broken_at = e.get("seq")
            break
        recompute_meta = {k: e[k] for k in ("seq","digest","kid","algorithm","framework","status","score","kind","requester","at") if k in e}
        if "extras" in e:
            recompute_meta["extras"] = e["extras"]
        payload = {"prev_hash": prev, "meta": recompute_meta}
        h = hashlib.sha256(_canonical(payload)).hexdigest()
        if h != e.get("hash"):
            ok = False
            broken_at = e.get("seq")
            break
    return {
        "ok": ok,
        "entries": len(entries),
        "broken_at": broken_at,
        "head": entries[-1]["hash"] if entries else GENESIS,
        "verified_at": _now_iso(),
    }


async def stats() -> dict[str, Any]:
    db = get_db()
    total = await db[COL].count_documents({})
    return {"total": total}
