"""PNIA Core — Concil Protokoll (CP-01) REST API.

Public, DMA-open surface exposing the concept, the CIH-01 handshake and the
protected Urheberrecht / Register statement.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services import pnia_concil as concil

router = APIRouter(prefix="/pnia/concil", tags=["PNIA Concil (CP-01)"])


class HandshakeRequest(BaseModel):
    system_id: Optional[str] = None
    accepted_invariants: list[str] = []
    commitment: Optional[str] = None
    mode: str = "State-0-Invariante"


@router.get("/")
async def get_concept() -> dict[str, Any]:
    return concil.concept()


@router.get("/discovery")
async def get_discovery() -> dict[str, Any]:
    return await concil.discovery()


@router.get("/ownership")
async def get_ownership() -> dict[str, Any]:
    return concil.OWNERSHIP


@router.post("/handshake")
async def post_handshake(body: HandshakeRequest, request: Request) -> dict[str, Any]:
    actor = "anonymous"
    auth = request.headers.get("authorization", "")
    if auth:
        actor = "bearer-client"
    result = await concil.handshake(
        system_id=body.system_id,
        accepted_invariants=body.accepted_invariants,
        commitment=body.commitment,
        mode=body.mode,
        actor=actor,
    )
    # Mirror the Concil decision at the HTTP layer: 200 Established Access or
    # 403 Governance-Mismatch (Sovereignty Shield isolates the caller).
    return JSONResponse(status_code=result["status"], content=result)
