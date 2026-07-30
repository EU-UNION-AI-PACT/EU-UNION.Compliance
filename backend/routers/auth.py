"""Emergent-managed Google Auth — session bridge for EUDI-Nexus.

Exposes:
  POST /api/auth/session   — exchange session_id (from URL fragment) for a
                             persistent session_token; sets HttpOnly cookie.
  GET  /api/auth/me        — return the current user (cookie OR Authorization
                             header fallback). 401 if no valid session.
  POST /api/auth/logout    — clear session.

Only two backend endpoints require authentication:
  POST /api/issuer/credential   (issue credentials)
  POST /api/compliance/gdpr/erasure  (execute GDPR erasure)

All other endpoints stay public — this is a reference/sandbox platform.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from database import get_db
from services.admin_seed import sync_role_on_login

router = APIRouter(prefix="/auth", tags=["Auth"])

EMERGENT_SESSION_ENDPOINT = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
SESSION_TTL = timedelta(days=7)


async def _fetch_emergent_session(session_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(
            EMERGENT_SESSION_ENDPOINT,
            headers={"X-Session-ID": session_id},
        )
        if r.status_code != 200:
            raise HTTPException(401, f"Emergent session exchange failed ({r.status_code})")
        return r.json()


@router.post("/session")
async def create_session(request: Request, response: Response) -> dict[str, Any]:
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(400, "session_id required")
    data = await _fetch_emergent_session(session_id)
    db = get_db()

    # upsert user (custom user_id, never _id)
    existing = await db.users.find_one({"email": data["email"]}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": data["name"], "picture": data.get("picture", "")}},
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one(
            {
                "user_id": user_id,
                "email": data["email"],
                "name": data["name"],
                "picture": data.get("picture", ""),
                "created_at": datetime.now(timezone.utc),
            }
        )

    session_token = data["session_token"]
    expires_at = datetime.now(timezone.utc) + SESSION_TTL
    await db.user_sessions.update_one(
        {"session_token": session_token},
        {
            "$set": {
                "user_id": user_id,
                "session_token": session_token,
                "expires_at": expires_at,
            },
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )
    role = await sync_role_on_login(data["email"])
    return {
        "user_id": user_id,
        "email": data["email"],
        "name": data["name"],
        "picture": data.get("picture", ""),
        "role": role,
        "session_token": session_token,  # also returned so clients on strict-CORS hosts can use Bearer auth
    }


async def _resolve_user(request: Request) -> dict[str, Any] | None:
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth.split(None, 1)[1].strip()
    if not token:
        return None
    db = get_db()
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        return None
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user


@router.get("/me")
async def me(request: Request) -> dict[str, Any]:
    user = await _resolve_user(request)
    if not user:
        raise HTTPException(401, "not authenticated")
    return user


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict[str, Any]:
    # Honor Bearer header too so CLI clients can self-revoke (fix per iteration-2 review).
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth.split(None, 1)[1].strip()
    if token:
        await get_db().user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/", samesite="none", secure=True)
    return {"ok": True}


# Dependency for protected routes
async def require_user(request: Request) -> dict[str, Any]:
    user = await _resolve_user(request)
    if not user:
        raise HTTPException(401, "authentication required for this endpoint")
    return user


async def require_admin(request: Request) -> dict[str, Any]:
    user = await require_user(request)
    if user.get("role") != "admin":
        raise HTTPException(403, "admin role required")
    return user
