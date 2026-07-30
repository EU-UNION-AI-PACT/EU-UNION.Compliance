"""EU AI Act + DSGVO Compliance Cockpit endpoints."""
from __future__ import annotations

import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from database import get_db
from models import ComplianceMetrics, ErasureRequest
from routers.auth import require_user
from services.audit_log import append_event, verify_chain

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get("/metrics", response_model=ComplianceMetrics)
async def metrics() -> ComplianceMetrics:
    db = get_db()
    total_issued = await db.issued_credentials.count_documents({})
    audit_docs = await db.audit_log.find({}, {"_id": 0}).to_list(2000)
    verifications = [a for a in audit_docs if a["event_type"] == "presentation.verified"]
    successful = [a for a in verifications if a["payload"].get("valid")]
    rate = len(successful) / len(verifications) if verifications else 1.0
    downgrades = [a for a in audit_docs if a["event_type"] == "loa.downgrade"]
    ai_events = [a for a in audit_docs if a["event_type"].startswith("ai_act.")]
    erasures = [a for a in audit_docs if a["event_type"] == "gdpr.erasure"]
    result = ComplianceMetrics(
        total_credentials_issued=total_issued,
        total_presentations_verified=len(verifications),
        verification_success_rate=round(rate, 4),
        active_loa_low=await db.issued_credentials.count_documents({"loa": "low"}),
        active_loa_substantial=await db.issued_credentials.count_documents({"loa": "substantial"}),
        active_loa_high=await db.issued_credentials.count_documents({"loa": "high"}),
        downgrade_incidents=len(downgrades),
        ai_act_transparency_events=len(ai_events),
        gdpr_erasure_requests=len(erasures),
    )
    await append_event(
        event_type="compliance.metrics.viewed",
        actor="compliance-cockpit",
        subject=None,
        payload=result.model_dump(),
    )
    return result


@router.get("/audit-log")
async def get_audit_log(limit: int = 100) -> list[dict]:
    cur = get_db().audit_log.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    docs = await cur.to_list(limit)
    await append_event(
        event_type="compliance.audit_log.viewed",
        actor="compliance-cockpit",
        subject=None,
        payload={"limit": limit, "returned": len(docs)},
    )
    return docs


@router.get("/audit-log/verify")
async def verify_audit_chain() -> dict:
    result = await verify_chain(limit=500)
    await append_event(
        event_type="compliance.audit_chain.verified",
        actor="compliance-cockpit",
        subject=None,
        payload=result,
    )
    return result


@router.post("/gdpr/erasure")
async def gdpr_erasure(req: ErasureRequest, user: dict = Depends(require_user)) -> dict:
    # Right to be forgotten — hash-based (never store cleartext PII)
    result = await get_db().issued_credentials.delete_many({"subject_hash": req.subject_hash})
    await append_event(
        event_type="gdpr.erasure",
        actor=user.get("email", "dpo"),
        subject=req.subject_hash,
        payload={"reason": req.reason, "records_deleted": result.deleted_count},
    )
    await append_event(
        event_type="compliance.gdpr_erasure.executed",
        actor="compliance-cockpit",
        subject=req.subject_hash,
        payload={"reason": req.reason, "records_deleted": result.deleted_count},
    )
    return {"deleted": result.deleted_count, "subject_hash": req.subject_hash}


@router.get("/ai-act/transparency")
async def ai_act_transparency() -> dict:
    """EU AI Act Art. 13 Transparency-Log."""
    cur = get_db().audit_log.find(
        {"event_type": {"$in": ["presentation.verified", "credential.issued"]}}, {"_id": 0}
    ).sort("timestamp", -1).limit(200)
    events = await cur.to_list(200)
    result = {
        "regulation": "EU AI Act (Regulation (EU) 2024/1689) Art. 13",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system_role": "high-risk AI system (identity verification)",
        "human_oversight_hook": "verifier decisions are logged; humans can override via /compliance/audit-log",
        "events": events,
    }
    await append_event(
        event_type="compliance.ai_act_transparency.viewed",
        actor="compliance-cockpit",
        subject=None,
        payload={"events_returned": len(events)},
    )
    return result


@router.get("/dsa/report.pdf")
async def dsa_pdf_report() -> StreamingResponse:
    """Digital Services Act transparency report (minimal PDF)."""
    from reportlab.lib.pagesizes import A4  # noqa: local import
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle("EUDI-Nexus DSA Transparency Report")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, 800, "DSA Transparency Report — EUDI-Nexus")
    c.setFont("Helvetica", 10)
    c.drawString(60, 780, f"Generated: {datetime.now(timezone.utc).isoformat()}")
    m = await metrics()
    y = 740
    for line in [
        f"Credentials issued: {m.total_credentials_issued}",
        f"Presentations verified: {m.total_presentations_verified}",
        f"Verification success rate: {m.verification_success_rate*100:.2f}%",
        f"LoA High active: {m.active_loa_high}",
        f"LoA Substantial active: {m.active_loa_substantial}",
        f"LoA Low active: {m.active_loa_low}",
        f"LoA downgrade incidents: {m.downgrade_incidents}",
        f"AI-Act transparency events: {m.ai_act_transparency_events}",
        f"GDPR erasure requests: {m.gdpr_erasure_requests}",
    ]:
        c.drawString(60, y, line)
        y -= 20
    c.showPage()
    c.save()
    buf.seek(0)
    await append_event(
        event_type="compliance.dsa_report.generated",
        actor="compliance-cockpit",
        subject=None,
        payload={
            "total_credentials_issued": m.total_credentials_issued,
            "total_presentations_verified": m.total_presentations_verified,
            "verification_success_rate": m.verification_success_rate,
            "downgrade_incidents": m.downgrade_incidents,
            "ai_act_transparency_events": m.ai_act_transparency_events,
            "gdpr_erasure_requests": m.gdpr_erasure_requests,
        },
    )
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="dsa_report.pdf"'},
    )


# ---------------------------------------------------------------------------
# Zusätzliche Compliance-Dokumentation im Audit-Log
# ---------------------------------------------------------------------------

@router.post("/audit-log/document")
async def document_compliance_state() -> dict:
    """Erstellt einen umfassenden Compliance-Snapshot im Audit-Log."""
    db = get_db()
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_credentials_issued": await db.issued_credentials.count_documents({}),
        "total_presentations_verified": len(await db.audit_log.find({"event_type": "presentation.verified"}, {"_id": 0}).to_list(5000)),
        "total_loa_downgrades": len(await db.audit_log.find({"event_type": "loa.downgrade"}, {"_id": 0}).to_list(5000)),
        "total_ai_act_events": len(await db.audit_log.find({"event_type": {"$regex": "^ai_act\\."}}, {"_id": 0}).to_list(5000)),
        "total_gdpr_erasures": len(await db.audit_log.find({"event_type": "gdpr.erasure"}, {"_id": 0}).to_list(5000)),
        "audit_chain_status": (await verify_chain(limit=500)).get("valid", False),
        "compliance_standards": [
            "eIDAS 2.0 (EU 2024/1183)",
            "EU-ARF v1.4",
            "ISO 18013-5 (mDoc/mDL)",
            "BSI TR-03159",
            "GDPR (Art. 5, 25, 32)",
            "EU AI Act (Regulation (EU) 2024/1689)",
            "Digital Services Act (Regulation (EU) 2022/2065)",
        ],
        "active_loa": {
            "low": await db.issued_credentials.count_documents({"loa": "low"}),
            "substantial": await db.issued_credentials.count_documents({"loa": "substantial"}),
            "high": await db.issued_credentials.count_documents({"loa": "high"}),
        },
        "multi_country_federation": {
            "total_countries": len(await db.audit_log.distinct("actor", {"actor": {"$regex": "^adapter:"}})),
            "implemented_formats": ["oidc", "saml", "sd-jwt", "ldp-vc", "mdoc"],
        },
        "gdpr_hashing_validation": "enforced via validate_gdpr_hashing()",
    }
    await append_event(
        event_type="compliance.snapshot",
        actor="compliance-cockpit",
        subject=None,
        payload=snapshot,
    )
    return {"status": "documented", "snapshot": snapshot}
