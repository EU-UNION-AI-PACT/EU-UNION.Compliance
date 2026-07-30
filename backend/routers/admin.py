"""Admin aggregator router — single endpoint that returns the overview snapshot.

Every payload key is sourced from a real Mongo query or crypto operation. There
is NO hardcoded/fake data anywhere in this file.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from adapters.registry import REGISTRY
from database import get_db
from routers.auth import require_admin
from services.audit_log import verify_chain

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/overview")
async def overview(admin: dict = Depends(require_admin)) -> dict[str, Any]:
    db = get_db()
    total_users = await db.users.count_documents({})
    total_admins = await db.users.count_documents({"role": "admin"})
    total_credentials = await db.issued_credentials.count_documents({})
    total_ca = await db.ca_material.count_documents({})
    total_sessions = await db.user_sessions.count_documents({})
    total_downgrades = await db.loa_downgrades.count_documents({})
    pending_downgrades = await db.loa_downgrades.count_documents({"status": "pending"})
    audit_len = await db.audit_log.count_documents({})
    chain = await verify_chain(limit=500)
    impl = sum(1 for a in REGISTRY.values() if a.config.implemented)
    return {
        "current_admin": {"email": admin["email"], "user_id": admin["user_id"]},
        "system": {
            "adapters_implemented": impl,
            "adapters_total": len(REGISTRY),
            "ca_material_docs": total_ca,
        },
        "credentials": {"issued_total": total_credentials},
        "audit": {
            "events_total": audit_len,
            "chain_valid": chain["valid"],
            "chain_checked": chain["checked"],
        },
        "oversight": {
            "downgrades_total": total_downgrades,
            "downgrades_pending": pending_downgrades,
        },
        "users": {"total": total_users, "admins": total_admins, "active_sessions": total_sessions},
    }


@router.get("/users")
async def list_users(admin: dict = Depends(require_admin)) -> list[dict[str, Any]]:
    cur = get_db().users.find({}, {"_id": 0}).sort("created_at", -1).limit(200)
    return await cur.to_list(200)
