"""AI Act Art. 14 oversight router."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from services.oversight import list_downgrades, override

router = APIRouter(prefix="/compliance/oversight", tags=["Compliance"])


class OverrideRequest(BaseModel):
    subject_fp: str
    decision: Literal["accept", "reject", "escalate"]
    reviewer: str
    note: str = ""


@router.get("/downgrades")
async def get_downgrades(limit: int = 50) -> list[dict]:
    return await list_downgrades(limit=limit)


@router.post("/override")
async def post_override(body: OverrideRequest) -> dict:
    return await override(
        subject_fp=body.subject_fp,
        decision=body.decision,
        reviewer=body.reviewer,
        note=body.note,
    )
