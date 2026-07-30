"""HNOSS Bridge Gateway — REST API (Default-Deny gateway demo)."""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import hnoss_bridge as bridge

router = APIRouter(prefix="/hnoss-bridge", tags=["HNOSS Bridge"])


class TransferRequest(BaseModel):
    source_domain: str = "mcci-internal"
    target_domain: str = "eu-commission"
    data_classification: str = "RESTRICTED"
    batch_size: int = 1
    jurisdiction: str = "EU"
    identity_whitelisted: bool = False


class ModeRequest(BaseModel):
    mode: Literal["Normal", "Quarantäne", "Read-Only", "Fail-Closed"]


@router.get("/")
async def info() -> dict[str, Any]:
    return {
        "service": "HNOSS Bridge — Default-Deny Gateway",
        "version": "1.0",
        "principle": "Default-Deny + Whitelisting (jede Transaktion bedarf expliziter, protokollierter Freigabe)",
        "components": bridge.COMPONENTS,
        "modes": bridge.MODES,
        "current_mode": await bridge.get_mode(),
    }


@router.get("/policies")
async def policies() -> dict[str, Any]:
    return {"policies": bridge.POLICIES}


@router.get("/mode")
async def mode() -> dict[str, Any]:
    return {"mode": await bridge.get_mode(), "available": bridge.MODES}


@router.post("/mode")
async def change_mode(body: ModeRequest) -> dict[str, Any]:
    try:
        m = await bridge.set_mode(body.mode)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"mode": m}


@router.post("/transfer")
async def transfer(body: TransferRequest) -> dict[str, Any]:
    return await bridge.evaluate_transfer(
        source_domain=body.source_domain,
        target_domain=body.target_domain,
        data_classification=body.data_classification,
        batch_size=body.batch_size,
        jurisdiction=body.jurisdiction,
        identity_whitelisted=body.identity_whitelisted,
    )


@router.get("/transfers")
async def transfers() -> dict[str, Any]:
    docs = await bridge.recent_transfers()
    return {"count": len(docs), "transfers": docs}
