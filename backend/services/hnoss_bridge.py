"""HNOSS Bridge — controlled, auditable Default-Deny gateway.

Derived 1:1 from the archive spec ``HNOSS_Bridge_Spezifikation.md``:
Default-Deny + Whitelisting, Policy Decision Point (PDP) / Policy Enforcement
Point (PEP), immutable audit logging, and four operating modes
(Normal / Quarantäne / Read-Only / Fail-Closed).

Every evaluated transfer is written to the platform's SHA-256 hash-chained
audit log (``append_event``) — POL-005: "Jede Transaktion muss signiert und
audit-logged sein".
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from database import get_db
from services.audit_log import append_event

COL_STATE = "hnoss_bridge_state"
COL_TX = "hnoss_transfers"

MODES = ["Normal", "Quarantäne", "Read-Only", "Fail-Closed"]
BATCH_DUAL_CONTROL_THRESHOLD = 10000

COMPONENTS = [
    {"id": "hnoss-bridge-ingress", "name": "Ingress Gateway", "fn": "TLS/mTLS, Auth, DDoS-Protection"},
    {"id": "hnoss-pep", "name": "Policy Enforcement Point (PEP)", "fn": "Durchsetzung der PDP-Entscheidungen"},
    {"id": "hnoss-pdp", "name": "Policy Decision Point (PDP)", "fn": "Whitelisting: Identity, Data, Operation, Geo"},
    {"id": "hnoss-sanitizer", "name": "Sanitization Layer", "fn": "Schema, Integrität, Klassifizierung"},
    {"id": "hnoss-audit-log", "name": "Audit Bridge Logger", "fn": "Hash, Signatur, Timestamp (append-only)"},
    {"id": "hnoss-bridge-egress", "name": "Egress Gateway", "fn": "Policy-Enforcement, Rate-Limiting"},
]

POLICIES = [
    {"id": "POL-001", "desc": "Nur identitäts-whitelistete Dienste dürfen an die Bridge", "effect": "Default-Deny"},
    {"id": "POL-002", "desc": "Daten der Klasse TOP SECRET dürfen nicht in öffentliche Domänen", "effect": "Block"},
    {"id": "POL-003", "desc": "Batch-Transfers > 10.000 Datensätze erfordern Dual-Control", "effect": "PENDING"},
    {"id": "POL-004", "desc": "Transfers außerhalb der EU erfordern Geo-Whitelist + DSB-Freigabe", "effect": "PENDING"},
    {"id": "POL-005", "desc": "Jede Transaktion muss signiert und audit-logged sein", "effect": "Enforce"},
    {"id": "POL-006", "desc": "Privilegierte Aktionen (Whitelist-Änderung) erfordern 4-Augen-Prinzip", "effect": "Enforce"},
]

PUBLIC_DOMAINS = {"internet", "public", "internet-of-science", "öffentlich"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def get_mode() -> str:
    db = get_db()
    doc = await db[COL_STATE].find_one({"_id": "singleton"})
    return doc["mode"] if doc else "Normal"


async def set_mode(mode: str) -> str:
    if mode not in MODES:
        raise ValueError(f"invalid mode: {mode}")
    db = get_db()
    await db[COL_STATE].update_one(
        {"_id": "singleton"}, {"$set": {"mode": mode, "updated_at": _now()}}, upsert=True
    )
    await append_event(event_type="hnoss.bridge.mode_changed", actor="operator", subject=mode, payload={})
    return mode


async def evaluate_transfer(
    *,
    source_domain: str,
    target_domain: str,
    data_classification: str = "RESTRICTED",
    batch_size: int = 1,
    jurisdiction: str = "EU",
    identity_whitelisted: bool = False,
) -> dict[str, Any]:
    """PDP evaluation → ACCEPTED / REJECTED / PENDING with applied policy rules."""
    tx_id = str(uuid.uuid4())
    mode = await get_mode()
    applied: list[str] = []
    status = "ACCEPTED"
    classification = (data_classification or "").upper().replace(" ", "_")
    target = (target_domain or "").strip().lower()

    # Mode gating first
    if mode == "Fail-Closed":
        status, applied = "REJECTED", ["MODE:Fail-Closed"]
    elif mode == "Quarantäne":
        status, applied = "PENDING", ["MODE:Quarantäne"]
    elif mode == "Read-Only":
        status, applied = "REJECTED", ["MODE:Read-Only (keine ausgehenden Transfers)"]
    else:
        # POL-001 Default-Deny
        if not identity_whitelisted:
            status = "REJECTED"
            applied.append("POL-001")
        # POL-002 classification vs public domain
        if classification in ("TOP_SECRET", "TOPSECRET") and target in PUBLIC_DOMAINS:
            status = "REJECTED"
            applied.append("POL-002")
        # POL-004 non-EU geo
        if status != "REJECTED" and jurisdiction.strip().upper() != "EU":
            status = "PENDING"
            applied.append("POL-004")
        # POL-003 large batch
        if status != "REJECTED" and batch_size > BATCH_DUAL_CONTROL_THRESHOLD:
            status = "PENDING"
            applied.append("POL-003")
        if not applied:
            applied.append("POL-005 (signiert & auditiert)")

    pdp = "ALLOW" if status == "ACCEPTED" else ("DEFER" if status == "PENDING" else "DENY")
    pep = "ENFORCED"
    audit_ref = "audit-sha256:" + hashlib.sha256(f"{tx_id}:{status}".encode()).hexdigest()

    doc = {
        "id": tx_id,
        "tx_id": tx_id,
        "source_domain": source_domain,
        "target_domain": target_domain,
        "data_classification": data_classification,
        "batch_size": batch_size,
        "jurisdiction": jurisdiction,
        "identity_whitelisted": identity_whitelisted,
        "status": status,
        "decision": {"pdp": pdp, "pep": pep, "policy_ref": ",".join(applied)},
        "applied_rules": applied,
        "audit_ref": audit_ref,
        "mode": mode,
        "timestamp": _now(),
    }
    await get_db()[COL_TX].insert_one(dict(doc))
    doc.pop("_id", None)
    await append_event(
        event_type="hnoss.bridge.transfer",
        actor=source_domain,
        subject=target_domain,
        payload={"status": status, "rules": applied, "tx_id": tx_id},
    )
    messages = {
        "ACCEPTED": "Transfer akzeptiert und protokolliert.",
        "REJECTED": "Transfer durch Policy verweigert (Default-Deny).",
        "PENDING": "Transfer erfordert manuelle Freigabe (Dual-Control / DSB).",
    }
    doc["message"] = messages[status]
    return doc


async def recent_transfers(limit: int = 25) -> list[dict[str, Any]]:
    db = get_db()
    return await db[COL_TX].find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
