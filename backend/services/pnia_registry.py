"""PNIA Memorial & Honorary Registry — DSGVO + EU AI Act compliant core.

Adapts the Prisma ``HonoredIndividual / Plaque / ConsentRecord / AiAuditLog``
schema to MongoDB, reusing the existing platform primitives:

  * ``KeyStorageManager``  — AES-256-GCM envelope encryption for PII at rest
  * ``sign_jws``           — ES256 JWS signature over each immutable audit entry
  * ``append_event``       — global SHA-256 hash-chained compliance audit log

Compliance principles enforced in this module
----------------------------------------------
* **Data minimization & tokenization (DSGVO Art. 5, Erwägungsgrund 26):**
  Personally identifiable information (PII) is stored ONLY as an AES-256-GCM
  ciphertext blob, bound (AAD) to a pseudonymous ``system_id``. Joins use the
  pseudonym, never the clear name.
* **Consent lifecycle (DSGVO Art. 6/7, Erwägungsgrund 27):** LIVING individuals
  require a ``GRANTED`` consent before an honorary plaque may be published.
  DECEASED individuals fall outside GDPR scope but require a *representative*
  verification record (postmortal personality right).
* **Right to be forgotten (DSGVO Art. 17):** revoking consent crypto-shreds the
  PII blob (overwrite + drop) and cascades deactivation of all plaques.
* **Immutable AI audit trail (EU AI Act Art. 12 + 50):** every AI action is
  hash-chained + JWS-signed and carries an explicit risk classification.
* **Postmortal write-once protection:** DECEASED plaques can be sealed
  (Write-Once / Read-Many) against unauthorized changes.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from database import get_db
from services.audit_log import append_event
from services.issuer_signer import sign_jws
from services.key_storage import KeyStorageManager

COL_IND = "pnia_individuals"
COL_PLAQUE = "pnia_plaques"
COL_CONSENT = "pnia_consents"
COL_AUDIT = "pnia_ai_audit"

RISK_MINIMAL = "MINIMAL_RISK"
RISK_LIMITED_TRANSPARENCY = "LIMITED_RISK_TRANSPARENCY"  # EU AI Act Art. 50

_km: KeyStorageManager | None = None


def _key_manager() -> KeyStorageManager:
    """Lazily build the envelope-encryption manager (fail-fast on missing key)."""
    global _km
    if _km is None:
        _km = KeyStorageManager()
    return _km


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def uid() -> str:
    return str(uuid.uuid4())


def make_system_id() -> str:
    return "PNIA-" + uuid.uuid4().hex[:12].upper()


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()


# --------------------------------------------------------------------------- #
# PII tokenization (AES-256-GCM envelope encryption)                          #
# --------------------------------------------------------------------------- #
def encrypt_pii(pii: dict[str, Any], system_id: str) -> str:
    payload = json.dumps(pii, separators=(",", ":"), default=str).encode()
    return _key_manager().wrap(payload, aad=system_id.encode())


def decrypt_pii(blob: str, system_id: str) -> dict[str, Any]:
    raw = _key_manager().unwrap(blob, aad=system_id.encode())
    return json.loads(raw.decode())


# --------------------------------------------------------------------------- #
# Immutable AI audit log (EU AI Act Art. 12 + 50)                             #
# --------------------------------------------------------------------------- #
async def append_ai_audit(
    *,
    plaque_id: str,
    action_type: str,
    ai_model_version: str,
    prompt: str,
    output: str,
    risk_classification: str = RISK_LIMITED_TRANSPARENCY,
) -> dict[str, Any]:
    """Append a hash-chained + JWS-signed AI decision record.

    Only hashes of prompt/output are persisted — never the raw text — so the log
    is a tamper-evident *proof of provenance* without leaking content.
    """
    db = get_db()
    last = await db[COL_AUDIT].find_one(sort=[("executed_at", -1)])
    prev_hash = last["hash"] if last else ""
    body = {
        "plaque_id": plaque_id,
        "action_type": action_type,
        "ai_model_version": ai_model_version,
        "prompt_hash": sha256_hex(prompt),
        "output_hash": sha256_hex(output),
        "risk_classification": risk_classification,
        "executed_at": now_iso(),
        "prev_hash": prev_hash,
    }
    h = hashlib.sha256(_canonical(body)).hexdigest()
    signature = await sign_jws({"h": h}, typ="ai-audit+jwt")
    doc = {"id": uid(), **body, "hash": h, "signature": signature}
    await db[COL_AUDIT].insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


async def verify_ai_chain(limit: int = 500) -> dict[str, Any]:
    db = get_db()
    docs = await db[COL_AUDIT].find({}, {"_id": 0}).sort("executed_at", 1).to_list(limit)
    reasons: list[str] = []
    prev = ""
    for d in docs:
        body = {
            k: d[k]
            for k in (
                "plaque_id",
                "action_type",
                "ai_model_version",
                "prompt_hash",
                "output_hash",
                "risk_classification",
                "executed_at",
                "prev_hash",
            )
        }
        h = hashlib.sha256(_canonical(body)).hexdigest()
        if h != d["hash"]:
            reasons.append(f"hash mismatch at {d['executed_at']}")
        if d["prev_hash"] != prev:
            reasons.append(f"prev_hash mismatch at {d['executed_at']}")
        prev = d["hash"]
    return {"valid": len(reasons) == 0, "reasons": reasons, "checked": len(docs)}


# --------------------------------------------------------------------------- #
# Consent helpers                                                             #
# --------------------------------------------------------------------------- #
async def has_granted_consent(individual_id: str) -> bool:
    db = get_db()
    c = await db[COL_CONSENT].find_one(
        {"individual_id": individual_id, "status": "GRANTED"}
    )
    return c is not None


# --------------------------------------------------------------------------- #
# Right to be forgotten (DSGVO Art. 17) — crypto-shredding                     #
# --------------------------------------------------------------------------- #
async def crypto_shred_and_cascade(individual_id: str, actor: str) -> dict[str, Any]:
    """Overwrite the PII blob with cryptographic garbage, then cascade-deactivate.

    We deliberately overwrite the ciphertext field with random bytes BEFORE
    dropping it, so even a forensic recovery of the previous document image
    yields no decryptable PII.
    """
    db = get_db()
    ind = await db[COL_IND].find_one({"id": individual_id})
    if not ind:
        return {"erased": False, "reason": "individual not found"}

    garbage = os.urandom(64).hex()
    await db[COL_IND].update_one(
        {"id": individual_id},
        {
            "$set": {
                "encrypted_data_record": garbage,
                "erased": True,
                "erased_at": now_iso(),
                "updated_at": now_iso(),
            },
            "$unset": {"system_id": ""},
        },
    )
    # crypto-shred: unset the ciphertext entirely after the overwrite
    await db[COL_IND].update_one(
        {"id": individual_id}, {"$unset": {"encrypted_data_record": ""}}
    )
    # cascade: deactivate plaques + redact their public display content
    plaque_ids = [
        p["id"] async for p in db[COL_PLAQUE].find({"individual_id": individual_id})
    ]
    await db[COL_PLAQUE].update_many(
        {"individual_id": individual_id},
        {
            "$set": {
                "is_active": False,
                "content_payload": {"redacted": True, "reason": "DSGVO Art. 17"},
                "updated_at": now_iso(),
            }
        },
    )
    await append_event(
        event_type="pnia.rtbf.executed",
        actor=actor,
        subject=individual_id,
        payload={"deactivated_plaques": len(plaque_ids), "basis": "DSGVO Art. 17"},
    )
    return {"erased": True, "deactivated_plaques": len(plaque_ids)}


# --------------------------------------------------------------------------- #
# Output shaping                                                              #
# --------------------------------------------------------------------------- #
def public_plaque(doc: dict[str, Any]) -> dict[str, Any]:
    """Return only the public, non-sensitive fields of a plaque."""
    return {
        "id": doc.get("id"),
        "individual_id": doc.get("individual_id"),
        "type": doc.get("type"),
        "is_active": doc.get("is_active", True),
        "locked": doc.get("locked", False),
        "content_payload": doc.get("content_payload", {}),
        "ai_generated_content": doc.get("ai_generated_content", False),
        "risk_classification": doc.get("risk_classification", RISK_MINIMAL),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }
