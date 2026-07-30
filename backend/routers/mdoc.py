"""ISO 18013-5 mDoc router — issue, verify, engagement."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from database import get_db
from models import (
    EngagementResponse,
    MDocIssueRequest,
    MDocIssueResponse,
    MDocVerifyRequest,
    MDocVerifyResponse,
)
from services.audit_log import append_event
from services.mdoc_engagement import create_engagement
from services.mdoc_issuer import MDocIssuerSingleton
from services.mdoc_verifier import MDocVerifier

router = APIRouter(prefix="/mdoc", tags=["mDoc (ISO 18013-5)"])


@router.post("/issue", response_model=MDocIssueResponse)
async def issue_mdoc(req: MDocIssueRequest) -> MDocIssueResponse:
    issuer = await MDocIssuerSingleton.instance()
    mdoc_bytes, count = issuer.issue(
        doctype=req.doctype,
        namespaces=req.namespaces,
        device_public_jwk=req.device_public_key,
    )
    await append_event(
        event_type="mdoc.issued",
        actor="mdoc-issuer",
        payload={"doctype": req.doctype, "digest_count": count, "country": req.country_code},
    )
    return MDocIssueResponse(
        doctype=req.doctype,
        mdoc_hex=mdoc_bytes.hex(),
        digest_count=count,
    )


@router.post("/verify", response_model=MDocVerifyResponse)
async def verify_mdoc(req: MDocVerifyRequest) -> MDocVerifyResponse:
    try:
        raw = bytes.fromhex(req.mdoc_hex)
    except ValueError as exc:
        raise HTTPException(400, f"mdoc_hex not a hex string: {exc}")
    result = await MDocVerifier().verify(raw)
    await append_event(
        event_type="mdoc.verified",
        actor="mdoc-verifier",
        payload={"valid": result["valid"], "doctype": result.get("doctype")},
    )
    return MDocVerifyResponse(**result)


@router.get("/engagement/{engagement_id}", response_model=EngagementResponse)
async def get_engagement(engagement_id: str) -> EngagementResponse:
    doc = await get_db().engagements.find_one({"engagement_id": engagement_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "engagement not found")
    return EngagementResponse(**doc)


@router.post("/engagement", response_model=EngagementResponse)
async def new_engagement() -> EngagementResponse:
    result = await create_engagement()
    return EngagementResponse(**result)
