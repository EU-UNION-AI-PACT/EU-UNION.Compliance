"""Idempotent admin role sync.

Admin identities are configured via the `ADMIN_EMAILS` env var (comma-separated).
On every successful /auth/session (Emergent Google Auth exchange), we upsert the
`role` field on the user document. If ADMIN_EMAILS is empty AND there are no
users yet (first-boot bootstrap), the very first user who signs in becomes
admin — a common pattern for reference/self-hosted deployments. This can be
disabled by setting ADMIN_EMAILS to any value.

Nothing here is ever hardcoded: no email address, no name, no role, no fallback.
"""
from __future__ import annotations

import logging
import os

from database import get_db

logger = logging.getLogger("eudi-nexus.admin_seed")


def _configured_emails() -> set[str]:
    raw = os.environ.get("ADMIN_EMAILS", "")
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


async def sync_role_on_login(email: str) -> str:
    """Return the role assigned to `email` after applying the current policy.

    Called from /api/auth/session immediately after we upsert the user row.
    """
    db = get_db()
    email_low = (email or "").strip().lower()
    admins = _configured_emails()
    if email_low in admins:
        await db.users.update_one({"email": email}, {"$set": {"role": "admin"}})
        logger.info("promoted %s to admin (ADMIN_EMAILS match)", email_low)
        return "admin"

    if not admins:
        # bootstrap: promote the first user only if there are exactly one users row
        count = await db.users.count_documents({})
        if count == 1:
            await db.users.update_one({"email": email}, {"$set": {"role": "admin"}})
            logger.info("bootstrap: promoted first-registered user %s to admin", email_low)
            return "admin"

    # anyone else: ensure a `user` role exists (never downgrade an existing admin)
    doc = await db.users.find_one({"email": email}, {"role": 1})
    if doc and doc.get("role"):
        return doc["role"]
    await db.users.update_one({"email": email}, {"$set": {"role": "user"}})
    return "user"
