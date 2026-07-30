"""JMAP Wallet-Auth Bridge (mock adapter — real Stalwart config in /stalwart/)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models import JmapAuthRequest, JmapAuthResponse
from services.jmap_auth_bridge import JmapAuthBridge

router = APIRouter(prefix="/jmap", tags=["JMAP (Wallet Auth Bridge)"])


@router.post("/auth", response_model=JmapAuthResponse)
async def auth(req: JmapAuthRequest) -> JmapAuthResponse:
    result = await JmapAuthBridge().login_with_sd_jwt(req.sd_jwt_presentation)
    if not result["ok"]:
        raise HTTPException(401, {"error": "invalid_vp", "reasons": result["reasons"]})
    return JmapAuthResponse(
        session_cookie=result["session_cookie"],
        expires_in=result["expires_in"],
        account_email=result["account_email"],
        account_id=result["account_id"],
    )


@router.get("/config")
async def jmap_config() -> dict:
    """Return the reference Stalwart configuration path — for on-prem deployment."""
    return {
        "reference_config_path": "/app/stalwart/config/config.toml",
        "runtime_mode": "MOCK_BRIDGE (Emergent K8s does not run Stalwart)",
        "session_ttl_seconds": 60,
        "supported_vct": ["eu.europa.ec.eudi.email.1"],
        "docs": "See docs/kapitel_03_jmap_wallet_auth.mdx",
    }
