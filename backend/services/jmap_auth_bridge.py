"""JMAP Wallet-Auth Bridge (SD-JWT VP → JMAP session).

In this Emergent-hosted build we CANNOT run a Stalwart sidecar, so this bridge
verifies the presented SD-JWT and mints an HttpOnly session cookie stored in
Mongo. The real Stalwart config used in on-prem is shipped in
`/app/stalwart/config/config.toml` for reference.
"""
from __future__ import annotations

import base64
import secrets
from datetime import datetime, timedelta, timezone

from database import get_db
from services.sd_jwt_verifier import SDJWTVerifierV2
from services.status_list_client import StatusListClient


class JmapAuthBridge:
    def __init__(self) -> None:
        self._verifier = SDJWTVerifierV2(StatusListClient())

    async def login_with_sd_jwt(self, presentation: str) -> dict:
        result = await self._verifier.verify(presentation)
        if not result["valid"]:
            return {"ok": False, "reasons": result["reasons"]}
        claims = result["disclosed_claims"]
        email = claims.get("email") or claims.get("mail")
        if not email:
            return {"ok": False, "reasons": ["presentation must disclose `email` claim"]}
        cookie = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
        expires = datetime.now(timezone.utc) + timedelta(seconds=60)
        account_id = base64.urlsafe_b64encode(email.encode()).decode().rstrip("=")
        await get_db().sse_sessions.insert_one(
            {
                "cookie": cookie,
                "account_id": account_id,
                "email": email,
                "expires_at": expires,
                "vct": result.get("vct"),
            }
        )
        return {
            "ok": True,
            "session_cookie": cookie,
            "expires_in": 60,
            "account_email": email,
            "account_id": account_id,
        }
