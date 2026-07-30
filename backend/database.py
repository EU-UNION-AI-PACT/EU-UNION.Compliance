"""MongoDB connection + index bootstrap for EUDI-Nexus."""
from __future__ import annotations

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return _client


def get_db() -> AsyncIOMotorDatabase:
    global _db
    if _db is None:
        _db = get_client()[os.environ["DB_NAME"]]
    return _db


async def bootstrap_indexes() -> None:
    """Create TTL / text / unique indexes required by services."""
    db = get_db()
    # c_nonce (Proof-of-Possession) — TTL 300s
    await db.c_nonces.create_index("expires_at", expireAfterSeconds=0)
    await db.c_nonces.create_index("value", unique=True)
    # Issued credentials (audit) — text search for compliance cockpit
    await db.issued_credentials.create_index([("subject_hash", 1)])
    await db.issued_credentials.create_index([("issued_at", -1)])
    # Audit log — signed hash chain
    await db.audit_log.create_index([("timestamp", -1)])
    await db.audit_log.create_index([("event_type", 1)])
    # Concept paper full-text search
    await db.paper_chapters.create_index(
        [("title", "text"), ("body", "text"), ("summary", "text")],
        default_language="english",
    )
    # Country adapter events
    await db.country_events.create_index([("country_code", 1), ("timestamp", -1)])
    # SSE session cookies (JMAP bridge)
    await db.sse_sessions.create_index("expires_at", expireAfterSeconds=0)
    # Status list entries
    await db.status_list.create_index("credential_id", unique=True)
    # Credential offers (OpenID4VCI §4) — TTL 15min
    await db.credential_offers.create_index("expires_at", expireAfterSeconds=0)
    await db.credential_offers.create_index("offer_id", unique=True)
    # PNIA Registry — memorials & honorary places
    await db.pnia_individuals.create_index("id", unique=True)
    await db.pnia_plaques.create_index("id", unique=True)
    await db.pnia_plaques.create_index([("type", 1), ("is_active", 1)])
    await db.pnia_plaques.create_index("seed_key", sparse=True)
    await db.pnia_consents.create_index([("individual_id", 1), ("status", 1)])
    await db.pnia_ai_audit.create_index([("executed_at", 1)])


async def close_client() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
