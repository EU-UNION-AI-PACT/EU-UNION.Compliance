"""Sprint 9 — Postman collection export + GitHub live-sync for OSS repos."""
from __future__ import annotations

import asyncio
import os
import re
import time
from typing import Any

import httpx
from fastapi import APIRouter, Request

router = APIRouter(prefix="/hub", tags=["Developer Hub"])


# --------- GitHub live-sync cache ---------
_GITHUB_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_GH_TTL = 60 * 60  # 1h

_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


async def _fetch_github_meta(slug: str) -> dict[str, Any]:
    now = time.time()
    cached = _GITHUB_CACHE.get(slug)
    if cached and now - cached[0] < _GH_TTL:
        return cached[1]
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "eudi-nexus/1.0"}
    if _GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {_GITHUB_TOKEN}"
    async with httpx.AsyncClient(timeout=8, follow_redirects=True, headers=headers) as c:
        try:
            r = await c.get(f"https://api.github.com/repos/{slug}")
            if r.status_code == 200:
                d = r.json()
                meta = {
                    "stars": d.get("stargazers_count", 0),
                    "forks": d.get("forks_count", 0),
                    "last_commit": d.get("pushed_at"),
                    "open_issues": d.get("open_issues_count", 0),
                    "watchers": d.get("subscribers_count", 0),
                    "license": (d.get("license") or {}).get("spdx_id"),
                    "reachable": True,
                }
            else:
                meta = {"stars": None, "reachable": False, "error": f"http {r.status_code}"}
        except Exception as exc:
            meta = {"stars": None, "reachable": False, "error": str(exc)}
    _GITHUB_CACHE[slug] = (now, meta)
    return meta


@router.get("/repos/live")
async def repos_live() -> list[dict[str, Any]]:
    """Same list as /hub/repos but with GitHub stars/last-commit merged in.

    GitHub public API is rate-limited to 60 req/h unauth — we cache each repo
    for 1 hour. Failing lookups return {reachable: false} so the frontend can
    still render.
    """
    from routers.hub import REGISTRY  # avoid circular

    slugs = [r.slug for r in REGISTRY if "/" in r.slug]
    metas = await asyncio.gather(*(_fetch_github_meta(s) for s in slugs))
    out = []
    for repo, meta in zip(REGISTRY, metas):
        out.append({**repo.model_dump(), "github": meta})
    return out


# --------- Postman collection export ---------


def _openapi_to_postman(spec: dict[str, Any], base_url: str) -> dict[str, Any]:
    coll: dict[str, Any] = {
        "info": {
            "name": spec.get("info", {}).get("title", "EUDI-Nexus"),
            "description": spec.get("info", {}).get("description", ""),
            "version": spec.get("info", {}).get("version", "1.0.0"),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [],
        "variable": [{"key": "baseUrl", "value": base_url}],
    }
    groups: dict[str, list[dict[str, Any]]] = {}
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                continue
            tag = (op.get("tags") or ["default"])[0]
            item = {
                "name": op.get("summary") or f"{method.upper()} {path}",
                "request": {
                    "method": method.upper(),
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "url": {
                        "raw": "{{baseUrl}}" + path,
                        "host": ["{{baseUrl}}"],
                        "path": [p for p in path.strip("/").split("/") if p],
                    },
                    "description": op.get("description", ""),
                },
                "response": [],
            }
            # naive body sample from schema
            req_body = op.get("requestBody", {}).get("content", {}).get("application/json", {})
            schema = req_body.get("schema") or {}
            if schema:
                sample = _sample_from_schema(schema, spec)
                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": _format_json(sample),
                    "options": {"raw": {"language": "json"}},
                }
            groups.setdefault(tag, []).append(item)
    for tag, items in groups.items():
        coll["item"].append({"name": tag, "item": items})
    return coll


def _sample_from_schema(schema: dict[str, Any], spec: dict[str, Any]) -> Any:
    """Rough JSON sample generator from an OpenAPI schema."""
    if "$ref" in schema:
        ref = schema["$ref"]
        m = re.match(r"^#/components/schemas/(\w+)$", ref)
        if m:
            resolved = spec.get("components", {}).get("schemas", {}).get(m.group(1), {})
            return _sample_from_schema(resolved, spec)
    t = schema.get("type")
    if t == "object" or "properties" in schema:
        return {k: _sample_from_schema(v, spec) for k, v in (schema.get("properties") or {}).items()}
    if t == "array":
        return [_sample_from_schema(schema.get("items") or {}, spec)]
    if t == "string":
        return schema.get("example", schema.get("default", "string"))
    if t == "integer":
        return schema.get("example", 0)
    if t == "number":
        return schema.get("example", 0.0)
    if t == "boolean":
        return schema.get("example", False)
    return None


def _format_json(v: Any) -> str:
    import json

    return json.dumps(v, indent=2)


@router.get("/postman-collection")
async def postman_collection(request: Request, download: int = 0):
    """Generate a Postman v2.1 collection from the live OpenAPI schema.

    Pass `?download=1` for a `Content-Disposition: attachment` response so
    browsers save the file directly instead of previewing JSON.
    """
    spec = request.app.openapi()
    base = str(request.base_url).rstrip("/")
    coll = _openapi_to_postman(spec, base)
    if download:
        import json

        from fastapi.responses import Response

        return Response(
            content=json.dumps(coll, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": 'attachment; filename="eudi-nexus.postman_collection.json"'
            },
        )
    return coll
