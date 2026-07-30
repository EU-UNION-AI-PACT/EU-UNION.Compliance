"""LoA downgrade detection + Human Oversight (EU AI Act Art. 14).

For every verifier decision, we look up the last-known LoA for the subject
(identified by SHA-256 of family_name+given_name+birth_date — no cleartext PII
is ever persisted). If the newly asserted LoA is *lower* than the previous one,
we emit an `loa.downgrade` audit event and store an oversight record that a
human reviewer can accept / reject / escalate.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from database import get_db
from services.audit_log import append_event


LOA_RANK = {"low": 1, "substantial": 2, "high": 3}


def subject_fingerprint(disclosed: dict[str, Any]) -> str | None:
    import unicodedata

    parts = [
        str(disclosed.get("family_name") or ""),
        str(disclosed.get("given_name") or ""),
        str(disclosed.get("birth_date") or ""),
    ]
    if not any(parts):
        return None
    # NFC + casefold so 'Ä', 'ß' etc normalize deterministically across locales
    normalized = "|".join(unicodedata.normalize("NFC", p).casefold() for p in parts)
    return hashlib.sha256(normalized.encode()).hexdigest()


async def track_and_detect(
    disclosed: dict[str, Any],
    new_loa: str | None,
    context: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the created downgrade record (or None if no downgrade)."""
    if new_loa not in LOA_RANK:
        return None
    fp = subject_fingerprint(disclosed)
    if not fp:
        return None
    db = get_db()
    prev = await db.loa_history.find_one({"subject_fp": fp})
    old_loa = prev.get("loa") if prev else None
    await db.loa_history.update_one(
        {"subject_fp": fp},
        {"$set": {"subject_fp": fp, "loa": new_loa, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    if old_loa and LOA_RANK.get(old_loa, 0) > LOA_RANK.get(new_loa, 0):
        record = {
            "subject_fp": fp,
            "from_loa": old_loa,
            "to_loa": new_loa,
            "detected_at": datetime.now(timezone.utc),
            "context": context,
            "status": "pending",  # pending | accepted | rejected | escalated
            "human_note": None,
            "reviewer": None,
        }
        await db.loa_downgrades.insert_one(record)
        await append_event(
            event_type="loa.downgrade",
            actor="oversight-monitor",
            subject=fp,
            payload={"from": old_loa, "to": new_loa, "vct": context.get("vct")},
        )
        record.pop("_id", None)
        return record
    return None


async def list_downgrades(limit: int = 100) -> list[dict[str, Any]]:
    cur = get_db().loa_downgrades.find({}, {"_id": 0}).sort("detected_at", -1).limit(limit)
    return await cur.to_list(limit)


async def override(subject_fp: str, decision: str, reviewer: str, note: str) -> dict[str, Any]:
    """Human oversight action per EU AI Act Art. 14."""
    if decision not in ("accept", "reject", "escalate"):
        raise ValueError("decision must be accept | reject | escalate")
    db = get_db()
    updated = await db.loa_downgrades.find_one_and_update(
        {"subject_fp": subject_fp, "status": "pending"},
        {
            "$set": {
                "status": {"accept": "accepted", "reject": "rejected", "escalate": "escalated"}[decision],
                "reviewer": reviewer,
                "human_note": note,
                "reviewed_at": datetime.now(timezone.utc),
            }
        },
        return_document=True,
    )
    if not updated:
        return {"ok": False, "reason": "no pending record found"}
    updated.pop("_id", None)
    await append_event(
        event_type="ai_act.human_oversight",
        actor=reviewer,
        subject=subject_fp,
        payload={"decision": decision, "note": note},
    )
    return {"ok": True, "record": updated}
