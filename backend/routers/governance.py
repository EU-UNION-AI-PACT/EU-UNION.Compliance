"""Governance & Rechtsgrundlagen — durchsuchbare Staatenliste (205 Staaten).

Reference data parsed 1:1 from the archive
"Governance_und_Rechtsgrundlagen_Staatenliste" (Teil 1–3). Served read-only
(DMA open API). Used to give each PNIA memorial a legal-basis context by
nationality.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/governance", tags=["Governance Staatenliste"])

_DATA_PATH = Path(__file__).parent.parent / "data" / "governance_states.json"
_STATES: list[dict[str, Any]] = []


def _load() -> list[dict[str, Any]]:
    global _STATES
    if not _STATES and _DATA_PATH.exists():
        _STATES = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return _STATES


def find_by_country(name: str) -> Optional[dict[str, Any]]:
    """Best-effort match of a (German) country name to a governance entry."""
    if not name:
        return None
    states = _load()
    key = name.strip().lower().split("/")[0].split(",")[0].strip()
    if not key:
        return None
    for s in states:
        if s["state"].lower() == key:
            return s
    for s in states:
        sl = s["state"].lower()
        if key in sl or sl in key:
            return s
    return None


@router.get("/")
async def info() -> dict[str, Any]:
    states = _load()
    return {
        "service": "Governance & Rechtsgrundlagen der Staatenliste",
        "count": len(states),
        "source": "Archiv: Governance_und_Rechtsgrundlagen_Staatenliste (Teil 1–3)",
        "fields": [
            "state", "iso3", "capital", "legal_form", "independence",
            "first_constitution", "key_figures", "legal_basis_today", "notes",
        ],
    }


@router.get("/states")
async def list_states(
    q: Optional[str] = None, limit: int = Query(300, le=500)
) -> dict[str, Any]:
    states = _load()
    if q:
        ql = q.strip().lower()
        states = [
            s
            for s in states
            if ql in s["state"].lower()
            or ql in s.get("iso3", "").lower()
            or ql in s.get("capital", "").lower()
            or ql in s.get("key_figures", "").lower()
            or ql in s.get("legal_form", "").lower()
        ]
    return {"count": len(states), "states": states[:limit]}


@router.get("/states/{name}")
async def get_state(name: str) -> dict[str, Any]:
    s = find_by_country(name)
    if not s:
        raise HTTPException(404, "state not found")
    return s
