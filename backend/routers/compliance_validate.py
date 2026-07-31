"""Stateless Compliance Validation REST + SSE router.

Endpoints
---------
GET  /api/validate/                 module descriptor
GET  /api/validate/frameworks       list of the 251 real frameworks (sortable)
GET  /api/validate/frameworks/{code} single framework details
GET  /api/validate/rules/{code}     framework rule book (specialised or generic)
POST /api/validate                  validate a payload against ONE framework
POST /api/validate/batch            validate against SEVERAL frameworks at once
GET  /api/validate/stream           Server-Sent Events live-ticker of validations

Statelessness contract
----------------------
- NO MongoDB writes anywhere in this module.
- NO in-memory cross-request storage of payload values.
- The SSE stream keeps a rolling in-process ring buffer with **no payload values**
  (only rule-hits, framework code and timestamps). The buffer is bounded to
  200 entries and lives inside the FastAPI process — it does NOT persist across
  restarts, and disappears the moment the process stops.
- All responses are pure JSON and free from any Personally Identifiable data.
"""
from __future__ import annotations

import asyncio
import json
from collections import deque
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from routers.auth import require_admin
from services import compliance_custom_rules as custom_rules_svc
from services import compliance_engine as engine
from services import compliance_ledger as ledger_svc
from services import compliance_pdf as pdf_svc
from services import ops_webhook as ops_svc

router = APIRouter(prefix="/validate", tags=["Compliance Validator"])

# --------------------------------------------------------------------------- #
# In-process event bus (bounded, no persistence)                              #
# --------------------------------------------------------------------------- #
_TICKER: deque[dict[str, Any]] = deque(maxlen=200)
_SUBSCRIBERS: set[asyncio.Queue] = set()


def _publish(event: dict[str, Any]) -> None:
    _TICKER.append(event)
    for q in list(_SUBSCRIBERS):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass
    # Fire-and-forget realtime ops alert (Slack/Teams-compatible)
    ops_svc.dispatch_bg(event)


# --------------------------------------------------------------------------- #
# Pydantic models                                                             #
# --------------------------------------------------------------------------- #
class ValidateRequest(BaseModel):
    framework: str = Field(..., description="Framework code, e.g. 'GDPR' or 'DORA'")
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="anonymous", max_length=64)


class BatchValidateRequest(BaseModel):
    frameworks: list[str] = Field(..., min_length=1, max_length=20)
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="anonymous", max_length=64)


class CustomRuleIn(BaseModel):
    field: str = Field(..., min_length=1, max_length=120)
    hint: str = Field(..., min_length=1, max_length=500)
    severity: str = Field(default="REQUIRED", pattern="^(REQUIRED|RECOMMENDED)$")


class PdfReportRequest(BaseModel):
    report: dict[str, Any]


class PdfBundleRequest(BaseModel):
    reports: list[dict[str, Any]] = Field(..., min_length=1, max_length=20)


class WebhookSettingsIn(BaseModel):
    webhook_url: str | None = None
    on_fail_only: bool = True
    min_score: int | None = None


class WebhookTestIn(BaseModel):
    webhook_url: str


# --------------------------------------------------------------------------- #
# Descriptor + read endpoints                                                 #
# --------------------------------------------------------------------------- #
@router.get("/")
async def info() -> dict[str, Any]:
    st = engine.stats()
    return {
        "service": "PNIA · Stateless Compliance Validator",
        "version": "1.0.0",
        "stateless": True,
        "database": None,
        "engine": st["engine"],
        "frameworks_total": st["total"],
        "specialised_validators": st["specialised_validators"],
        "compliance": st["compliance"],
        "endpoints": [
            "GET  /api/validate/frameworks",
            "GET  /api/validate/frameworks/{code}",
            "GET  /api/validate/rules/{code}",
            "POST /api/validate",
            "POST /api/validate/batch",
            "GET  /api/validate/stream (SSE)",
        ],
    }


@router.get("/frameworks")
async def list_frameworks(
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(500, ge=1, le=500),
) -> dict[str, Any]:
    frameworks = engine.list_frameworks(category=category, jurisdiction=jurisdiction, q=q)
    return {"count": len(frameworks), "frameworks": frameworks[:limit]}


@router.get("/frameworks/{code}")
async def get_framework(code: str) -> dict[str, Any]:
    fw = engine.get_framework(code)
    if fw is None:
        raise HTTPException(404, f"framework '{code}' not found")
    return fw


@router.get("/rules/{code}")
async def get_rules(code: str) -> dict[str, Any]:
    rb = engine.rule_book(code)
    if rb is None:
        raise HTTPException(404, f"framework '{code}' not found")
    return rb


@router.get("/stats")
async def get_stats() -> dict[str, Any]:
    return engine.stats()


# --------------------------------------------------------------------------- #
# Validation endpoints (pure passthrough — NO STORAGE)                        #
# --------------------------------------------------------------------------- #
def _event_from_report(source: str, report: dict[str, Any]) -> dict[str, Any]:
    """Build a ticker event that carries NO payload values — only outcomes."""
    return {
        "type": "validation",
        "source": source,
        "at": report.get("evaluated_at"),
        "framework": report.get("framework", {}).get("code")
        if isinstance(report.get("framework"), dict)
        else report.get("framework"),
        "status": report.get("status"),
        "score": report.get("score"),
        "missing_required": report.get("counts", {}).get("missing_required", 0),
        "recommended_warnings": report.get("counts", {}).get("recommended_warnings", 0),
    }


@router.post("")
async def do_validate(body: ValidateRequest) -> dict[str, Any]:
    extra = await custom_rules_svc.list_rules(body.framework)
    report = engine.validate(body.payload, body.framework, extra_rules=extra)
    _publish(_event_from_report(body.source, report))
    return report


@router.post("/")
async def do_validate_slash(body: ValidateRequest) -> dict[str, Any]:
    return await do_validate(body)


@router.post("/batch")
async def do_batch_validate(body: BatchValidateRequest) -> dict[str, Any]:
    # merge custom rules per framework
    reports = []
    for code in body.frameworks:
        extra = await custom_rules_svc.list_rules(code)
        reports.append(engine.validate(body.payload, code, extra_rules=extra))
    overall = "PASS"
    for r in reports:
        if r.get("status") == "FAIL":
            overall = "FAIL"
            break
        if r.get("status") == "PASS_WITH_WARNINGS" and overall == "PASS":
            overall = "PASS_WITH_WARNINGS"
    result = {
        "overall_status": overall,
        "count": len(reports),
        "reports": reports,
        "evaluated_at": reports[0]["evaluated_at"] if reports else None,
    }
    for report in reports:
        _publish(_event_from_report(body.source, report))
    return result


# --------------------------------------------------------------------------- #
# Signed PDF export                                                            #
# --------------------------------------------------------------------------- #
@router.post("/report.pdf")
async def report_pdf(body: PdfReportRequest, request: Request) -> Response:
    """Render a validation report to a signed A4 PDF (ES256 JWS)."""
    if not isinstance(body.report, dict):
        raise HTTPException(422, "report must be an object")
    signature = await pdf_svc.sign_report(body.report)
    pdf_bytes = pdf_svc.render_report_pdf(body.report, signature)
    # Append to chain-of-custody ledger (public, safe metadata only)
    fw = body.report.get("framework", {}) or {}
    if isinstance(fw, str):
        fw_code = fw
    else:
        fw_code = str(fw.get("code", "—"))
    await ledger_svc.append(
        digest_sha256=signature["digest_sha256"],
        kid=signature["kid"],
        algorithm=signature["algorithm"],
        framework_code=fw_code,
        status=str(body.report.get("status", "—")),
        score=body.report.get("score") if isinstance(body.report.get("score"), int) else None,
        kind="pdf",
        requester=str(request.headers.get("X-Requester", "anonymous"))[:60],
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="pnia-compliance-report.pdf"',
            "X-PNIA-Signature-Alg": signature["algorithm"],
            "X-PNIA-Signature-KID": signature["kid"],
            "X-PNIA-Digest-SHA256": signature["digest_sha256"],
        },
    )


@router.post("/report.sign")
async def report_sign(body: PdfReportRequest, request: Request) -> dict[str, Any]:
    """Return the JWS envelope for a report without rendering a PDF."""
    signature = await pdf_svc.sign_report(body.report)
    fw = body.report.get("framework", {}) or {}
    fw_code = fw if isinstance(fw, str) else str(fw.get("code", "—"))
    await ledger_svc.append(
        digest_sha256=signature["digest_sha256"],
        kid=signature["kid"],
        algorithm=signature["algorithm"],
        framework_code=fw_code,
        status=str(body.report.get("status", "—")),
        score=body.report.get("score") if isinstance(body.report.get("score"), int) else None,
        kind="sign",
        requester=str(request.headers.get("X-Requester", "anonymous"))[:60],
    )
    return signature


@router.post("/report-bundle.pdf")
async def report_bundle_pdf(body: PdfBundleRequest, request: Request) -> Response:
    """Combine several signed reports into a single PDF booklet with TOC."""
    # Compute a bundle-level signature over the concatenated JSON of all reports.
    bundle_report = {
        "kind": "bundle",
        "count": len(body.reports),
        "reports": body.reports,
    }
    signature = await pdf_svc.sign_report(bundle_report)
    pdf_bytes = pdf_svc.render_bundle_pdf(body.reports, signature)
    # Append one bundle entry to the ledger with per-report digests as extras
    per_report_codes = []
    for r in body.reports:
        fw = r.get("framework", {}) or {}
        per_report_codes.append(fw if isinstance(fw, str) else str(fw.get("code", "—")))
    await ledger_svc.append(
        digest_sha256=signature["digest_sha256"],
        kid=signature["kid"],
        algorithm=signature["algorithm"],
        framework_code="BUNDLE",
        status="BUNDLE",
        score=None,
        kind="bundle",
        requester=str(request.headers.get("X-Requester", "anonymous"))[:60],
        extras={"count": len(body.reports), "frameworks": per_report_codes},
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="pnia-compliance-bundle.pdf"',
            "X-PNIA-Signature-Alg": signature["algorithm"],
            "X-PNIA-Signature-KID": signature["kid"],
            "X-PNIA-Digest-SHA256": signature["digest_sha256"],
            "X-PNIA-Bundle-Count": str(len(body.reports)),
        },
    )


# --------------------------------------------------------------------------- #
# Chain-of-custody ledger (public read, tamper-evident)                        #
# --------------------------------------------------------------------------- #
@router.get("/ledger")
async def ledger_recent(limit: int = Query(50, ge=1, le=500)) -> dict[str, Any]:
    entries = await ledger_svc.recent(limit=limit)
    st = await ledger_svc.stats()
    return {"total": st["total"], "count": len(entries), "entries": entries}


@router.get("/ledger/verify")
async def ledger_verify(limit: int = Query(500, ge=1, le=2000)) -> dict[str, Any]:
    return await ledger_svc.verify_chain(limit=limit)


# --------------------------------------------------------------------------- #
# Ops webhook (admin)                                                          #
# --------------------------------------------------------------------------- #
@router.get("/ops-webhook")
async def get_ops_webhook(user: dict = Depends(require_admin)) -> dict[str, Any]:
    cfg = await ops_svc.get_settings()
    return {"settings": cfg, "history": ops_svc.history(limit=20)}


@router.post("/ops-webhook")
async def set_ops_webhook(
    body: WebhookSettingsIn, user: dict = Depends(require_admin)
) -> dict[str, Any]:
    return await ops_svc.set_settings(
        webhook_url=body.webhook_url,
        on_fail_only=body.on_fail_only,
        min_score=body.min_score,
        actor=user.get("email", "admin"),
    )


@router.post("/ops-webhook/test")
async def test_ops_webhook(
    body: WebhookTestIn, user: dict = Depends(require_admin)
) -> dict[str, Any]:
    return await ops_svc.send_test(body.webhook_url)


# --------------------------------------------------------------------------- #
# Custom Rule Editor (admin only)                                              #
# --------------------------------------------------------------------------- #
@router.get("/custom-rules")
async def list_all_custom_rules(user: dict = Depends(require_admin)) -> dict[str, Any]:
    rules = await custom_rules_svc.all_rules()
    counts = await custom_rules_svc.count_by_framework()
    return {"count": len(rules), "by_framework": counts, "rules": rules}


@router.get("/custom-rules/{framework}")
async def get_custom_rules(framework: str) -> dict[str, Any]:
    """Publicly readable — showing the effective ruleset builds trust."""
    rules = await custom_rules_svc.list_rules(framework)
    return {"framework": framework.upper(), "count": len(rules), "rules": rules}


@router.post("/custom-rules/{framework}")
async def add_custom_rule(
    framework: str,
    body: CustomRuleIn,
    user: dict = Depends(require_admin),
) -> dict[str, Any]:
    if engine.get_framework(framework) is None:
        raise HTTPException(404, f"framework '{framework}' not found")
    try:
        doc = await custom_rules_svc.add_rule(
            framework_code=framework,
            field=body.field,
            hint=body.hint,
            severity=body.severity,
            actor=user.get("email", "admin"),
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    return doc


@router.delete("/custom-rules/{rule_id}")
async def delete_custom_rule(
    rule_id: str, user: dict = Depends(require_admin)
) -> dict[str, Any]:
    ok = await custom_rules_svc.delete_rule(rule_id)
    if not ok:
        raise HTTPException(404, "rule not found")
    return {"id": rule_id, "deleted": True}


# --------------------------------------------------------------------------- #
# SSE Live-Ticker                                                             #
# --------------------------------------------------------------------------- #
@router.get("/history")
async def get_recent() -> dict[str, Any]:
    """Snapshot of the volatile in-process ticker (no DB, purged on restart)."""
    return {"count": len(_TICKER), "events": list(_TICKER)}


async def _sse_generator(queue: asyncio.Queue, seed: list[dict[str, Any]]):
    # Immediately push a hello + optional replay of last events for context.
    hello = {
        "type": "hello",
        "message": "PNIA Live Compliance Ticker · stateless · closes with tab",
        "buffered": len(seed),
    }
    yield f"event: hello\ndata: {json.dumps(hello)}\n\n"
    for evt in seed:
        yield f"event: replay\ndata: {json.dumps(evt)}\n\n"
    try:
        while True:
            try:
                evt = await asyncio.wait_for(queue.get(), timeout=20.0)
                yield f"event: validation\ndata: {json.dumps(evt)}\n\n"
            except asyncio.TimeoutError:
                # keep the connection warm through k8s / proxies
                yield ": keep-alive\n\n"
    finally:
        pass


@router.get("/stream")
async def sse_stream():
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _SUBSCRIBERS.add(queue)

    async def wrapper():
        try:
            async for chunk in _sse_generator(queue, list(_TICKER)[-20:]):
                yield chunk
        finally:
            _SUBSCRIBERS.discard(queue)

    return StreamingResponse(
        wrapper(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
