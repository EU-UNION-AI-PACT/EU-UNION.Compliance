"""OpenID4VP Verifier — with LoA downgrade tracking (AI Act Art. 14)."""
from __future__ import annotations

from fastapi import APIRouter

from models import VerifyRequest, VerifyResponse
from services.audit_log import append_event
from services.oversight import track_and_detect
from services.sd_jwt_verifier import SDJWTVerifierV2
from services.status_list_client import StatusListClient

router = APIRouter(prefix="/verifier", tags=["Verifier (OpenID4VP)"])


def _loa_for_vct(vct: str | None) -> str | None:
    if not vct:
        return None
    if "pid" in vct or "mdl" in vct:
        return "high"
    if "email" in vct:
        return "substantial"
    return "low"


@router.post("/verify", response_model=VerifyResponse)
async def verify(req: VerifyRequest) -> VerifyResponse:
    verifier = SDJWTVerifierV2(StatusListClient())
    result = await verifier.verify(req.presentation, audience=req.audience, nonce=req.nonce)
    vct = result.get("vct") or ""
    loa = _loa_for_vct(vct)
    result["loa"] = loa
    result["trust_chain"] = [result.get("issuer") or "unknown"]

    # LoA downgrade detection (only for successful, valid verifications)
    if result["valid"]:
        await track_and_detect(
            result.get("disclosed_claims", {}),
            loa,
            context={"vct": vct, "endpoint": "/api/verifier/verify"},
        )

    await append_event(
        event_type="presentation.verified",
        actor="verifier",
        subject=result.get("disclosed_claims", {}).get("family_name"),
        payload={"valid": result["valid"], "reasons": result["reasons"], "vct": vct, "loa": loa},
    )
    return VerifyResponse(**result)
