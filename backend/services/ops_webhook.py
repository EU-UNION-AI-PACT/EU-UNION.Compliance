"""Realtime Ops Alert — fire a webhook when a FAIL validation happens.

The webhook URL is stored in Mongo under `compliance_ops_settings.singleton`
(configurable at runtime via the admin endpoint). The dispatcher is fire-and-forget
and captures the last 100 deliveries in an in-process ring buffer so the admin
can inspect success/failure without touching a DB.
"""
from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Any

import httpx

from database import get_db

COL = "compliance_ops_settings"
SINGLE = "singleton"

# In-process ring buffer (no DB writes for deliveries)
_HISTORY: deque[dict[str, Any]] = deque(maxlen=100)


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


async def get_settings() -> dict[str, Any]:
    db = get_db()
    doc = await db[COL].find_one({"_id": SINGLE}, {"_id": 0})
    if not doc:
        return {"webhook_url": None, "on_fail_only": True, "min_score": None}
    return doc


async def set_settings(
    webhook_url: str | None,
    on_fail_only: bool = True,
    min_score: int | None = None,
    actor: str = "admin",
) -> dict[str, Any]:
    db = get_db()
    doc = {
        "webhook_url": webhook_url,
        "on_fail_only": bool(on_fail_only),
        "min_score": min_score,
        "updated_by": actor,
        "updated_at": _now(),
    }
    await db[COL].update_one({"_id": SINGLE}, {"$set": doc}, upsert=True)
    return doc


def _slack_teams_payload(event: dict[str, Any]) -> dict[str, Any]:
    fw = event.get("framework") or "framework"
    status = event.get("status") or "?"
    score = event.get("score")
    return {
        "text": (
            f":rotating_light: *PNIA Compliance {status}* on `{fw}` "
            f"(score {score}, missing {event.get('missing_required')})"
        ),
        "attachments": [
            {
                "color": "#dc2626" if status == "FAIL" else "#d97706",
                "fields": [
                    {"title": "Framework", "value": fw, "short": True},
                    {"title": "Status", "value": status, "short": True},
                    {"title": "Score", "value": str(score), "short": True},
                    {"title": "Source", "value": event.get("source", "-"), "short": True},
                    {"title": "At", "value": event.get("at", "-"), "short": False},
                ],
            }
        ],
    }


async def _do_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.post(url, json=payload)
        return {"http": r.status_code, "ok": 200 <= r.status_code < 300}


async def dispatch(event: dict[str, Any]) -> None:
    """Fire the webhook if configured and event matches the filter.

    Never raises — a failing webhook must not break the validate() call.
    """
    try:
        cfg = await get_settings()
    except Exception:
        return
    url = cfg.get("webhook_url")
    if not url:
        return

    status = event.get("status")
    if cfg.get("on_fail_only", True) and status != "FAIL":
        return

    min_score = cfg.get("min_score")
    if min_score is not None and event.get("score") is not None:
        try:
            if int(event["score"]) >= int(min_score):
                return
        except Exception:
            pass

    payload = _slack_teams_payload(event)
    result = {
        "url": url,
        "at": _now(),
        "event": {
            "framework": event.get("framework"),
            "status": status,
            "score": event.get("score"),
            "source": event.get("source"),
        },
    }
    try:
        r = await _do_post(url, payload)
        result.update(r)
    except Exception as e:
        result.update({"http": None, "ok": False, "error": str(e)[:200]})
    _HISTORY.append(result)


def dispatch_bg(event: dict[str, Any]) -> None:
    """Non-blocking wrapper — schedule delivery on the current loop."""
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(dispatch(event))
    except Exception:
        pass


async def send_test(url: str) -> dict[str, Any]:
    """Send a synchronous test message; used by the admin UI."""
    payload = _slack_teams_payload(
        {
            "framework": "TEST",
            "status": "FAIL",
            "score": 0,
            "missing_required": 3,
            "recommended_warnings": 1,
            "source": "test-button",
            "at": _now(),
        }
    )
    r = await _do_post(url, payload)
    r["at"] = _now()
    _HISTORY.append({**r, "url": url, "event": {"framework": "TEST"}})
    return r


def history(limit: int = 20) -> list[dict[str, Any]]:
    return list(_HISTORY)[-limit:][::-1]
