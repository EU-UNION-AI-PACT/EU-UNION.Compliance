"""Admin-scoped custom rule overrides for the stateless compliance engine.

The engine itself remains stateless. Custom rules live in a **separate**
MongoDB collection (`compliance_custom_rules`) and are only *merged in* at
the top of a validate() call — never stored in the request path.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from database import get_db

COL = "compliance_custom_rules"


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


async def list_rules(framework_code: str) -> list[dict[str, Any]]:
    db = get_db()
    docs = await db[COL].find(
        {"framework": framework_code.upper()}, {"_id": 0}
    ).sort("created_at", 1).to_list(200)
    return docs


async def add_rule(
    framework_code: str,
    field: str,
    hint: str,
    severity: str,
    actor: str,
) -> dict[str, Any]:
    if severity not in ("REQUIRED", "RECOMMENDED"):
        raise ValueError("severity must be REQUIRED or RECOMMENDED")
    if not field or not hint:
        raise ValueError("field and hint are required")
    db = get_db()
    doc = {
        "id": uuid.uuid4().hex,
        "framework": framework_code.upper(),
        "field": field,
        "hint": hint,
        "severity": severity,
        "created_at": _now_iso(),
        "created_by": actor,
    }
    await db[COL].insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


async def delete_rule(rule_id: str) -> bool:
    db = get_db()
    r = await db[COL].delete_one({"id": rule_id})
    return r.deleted_count == 1


async def count_by_framework() -> dict[str, int]:
    db = get_db()
    cursor = db[COL].aggregate(
        [{"$group": {"_id": "$framework", "n": {"$sum": 1}}}]
    )
    out: dict[str, int] = {}
    async for row in cursor:
        out[str(row["_id"])] = int(row["n"])
    return out


async def all_rules() -> list[dict[str, Any]]:
    db = get_db()
    return await db[COL].find({}, {"_id": 0}).sort("created_at", 1).to_list(2000)
