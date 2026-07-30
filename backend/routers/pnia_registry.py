"""PNIA Memorial & Honorary Registry — REST API.

DSGVO + EU AI Act + DMA compliant. Public read endpoints implement the DMA
"open API / no vendor lock-in" mandate; write, AI and consent endpoints are
protected via the platform's Emergent-managed auth.
"""
from __future__ import annotations

import io
from typing import Any, Literal, Optional
from urllib.parse import quote

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from database import get_db
from routers.auth import require_user
from routers.governance import find_by_country
from services import pnia_ai
from services import pnia_registry as reg
from services.audit_log import append_event

router = APIRouter(prefix="/pnia/registry", tags=["PNIA Registry"])


# --------------------------------------------------------------------------- #
# Request models                                                              #
# --------------------------------------------------------------------------- #
class IndividualCreate(BaseModel):
    status: Literal["LIVING", "DECEASED"]
    given_name: str
    family_name: str
    birth_place: str = ""
    birth_date: str = ""
    death_date: str = ""
    nationality: str = ""


class ConsentCreate(BaseModel):
    individual_id: str
    consent_document_hash: str = ""
    origin_trace: str = ""
    representative: str = ""
    basis: str = "DSGVO Art. 6(1)(a) — explicit consent"


class PlaqueCreate(BaseModel):
    individual_id: str
    type: Literal["MEMORIAL_BOARD", "HONORARY_PLACE"]
    display_name: str
    role: str = ""
    institution: str = ""
    resting_place: str = ""
    tribute_text: str = ""
    epitaph: str = ""


class TributeRequest(BaseModel):
    language: str = "Deutsch"
    tone: str = "würdevoll und sachlich"
    extra_context: str = ""


class TranslateRequest(BaseModel):
    target_language: str = Field(..., min_length=2)


# --------------------------------------------------------------------------- #
# Module descriptor (DMA open-API surface)                                    #
# --------------------------------------------------------------------------- #
@router.get("/")
async def info() -> dict[str, Any]:
    return {
        "service": "PNIA Memorial & Honorary Registry",
        "version": "1.0.0",
        "description": (
            "Register für Gedenktafeln (Verstorbene) und Ehrenplätze (Lebende). "
            "DSGVO-, EU-AI-Act- und DMA-konform."
        ),
        "compliance": {
            "dsgvo": ["Art. 5 Data Minimization", "Art. 6/7 Consent", "Art. 17 Erasure", "Erwägungsgrund 27"],
            "eu_ai_act": ["Art. 12 Record-Keeping", "Art. 50 Transparency"],
            "dma": ["Open API", "Interoperabilität", "kein Vendor Lock-in"],
        },
        "security": ["AES-256-GCM PII-Tokenisierung", "SHA-256 Hash-Chain", "ES256 JWS"],
        "endpoints": {
            "plaques": "/api/pnia/registry/plaques",
            "compliance": "/api/pnia/registry/compliance",
            "ai_audit": "/api/pnia/registry/ai-audit",
        },
    }


# --------------------------------------------------------------------------- #
# Public read surface                                                         #
# --------------------------------------------------------------------------- #
@router.get("/plaques")
async def list_plaques(
    type: Optional[Literal["MEMORIAL_BOARD", "HONORARY_PLACE"]] = None,
    include_inactive: bool = False,
) -> dict[str, Any]:
    db = get_db()
    query: dict[str, Any] = {}
    if not include_inactive:
        query["is_active"] = True
    if type:
        query["type"] = type
    docs = await db[reg.COL_PLAQUE].find(query, {"_id": 0}).sort("created_at", 1).to_list(500)
    return {"count": len(docs), "plaques": [reg.public_plaque(d) for d in docs]}


@router.get("/plaques/{plaque_id}")
async def get_plaque(plaque_id: str) -> dict[str, Any]:
    db = get_db()
    doc = await db[reg.COL_PLAQUE].find_one({"id": plaque_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "plaque not found")
    return reg.public_plaque(doc)


def _maps_url(place: str) -> str:
    if not place:
        return ""
    return f"https://www.google.com/maps/search/?api=1&query={quote(place)}"


@router.get("/plaques/{plaque_id}/context")
async def plaque_context(plaque_id: str) -> dict[str, Any]:
    """Public detail context: maps link to resting place + governance legal-basis.

    Governance/nationality context is only exposed for DECEASED memorials
    (historical public figures — DSGVO Erwägungsgrund 27); for LIVING honorary
    places no nationality is disclosed (data minimization).
    """
    db = get_db()
    doc = await db[reg.COL_PLAQUE].find_one({"id": plaque_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "plaque not found")
    cp = doc.get("content_payload", {})
    resting = cp.get("resting_place", "")
    result: dict[str, Any] = {
        "id": plaque_id,
        "type": doc.get("type"),
        "maps_url": _maps_url(resting),
        "qr_url": f"/api/pnia/registry/plaques/{plaque_id}/qr.png",
        "governance": None,
    }
    ind = await db[reg.COL_IND].find_one({"id": doc.get("individual_id")}, {"_id": 0})
    if (
        ind
        and ind.get("status") == "DECEASED"
        and not ind.get("erased")
        and ind.get("encrypted_data_record")
    ):
        try:
            pii = reg.decrypt_pii(ind["encrypted_data_record"], ind["system_id"])
            nationality = pii.get("nationality", "")
            gov = find_by_country(nationality)
            if gov:
                result["governance"] = gov
                result["nationality"] = nationality
        except Exception:
            pass
    return result


@router.get("/plaques/{plaque_id}/qr.png")
async def plaque_qr(plaque_id: str) -> Response:
    db = get_db()
    doc = await db[reg.COL_PLAQUE].find_one({"id": plaque_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "plaque not found")
    cp = doc.get("content_payload", {})
    target = _maps_url(cp.get("resting_place", "")) or (cp.get("display_name", "PNIA"))
    img = qrcode.make(target)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/ai-audit")
async def list_ai_audit(limit: int = Query(200, le=500)) -> dict[str, Any]:
    db = get_db()
    docs = (
        await db[reg.COL_AUDIT]
        .find({}, {"_id": 0})
        .sort("executed_at", -1)
        .to_list(limit)
    )
    return {"count": len(docs), "entries": docs}


@router.get("/ai-audit/verify")
async def verify_ai_audit() -> dict[str, Any]:
    return await reg.verify_ai_chain()


@router.get("/compliance")
async def compliance_summary() -> dict[str, Any]:
    db = get_db()
    total = await db[reg.COL_PLAQUE].count_documents({})
    memorials = await db[reg.COL_PLAQUE].count_documents({"type": "MEMORIAL_BOARD"})
    honorary = await db[reg.COL_PLAQUE].count_documents({"type": "HONORARY_PLACE"})
    active = await db[reg.COL_PLAQUE].count_documents({"is_active": True})
    ai_content = await db[reg.COL_PLAQUE].count_documents({"ai_generated_content": True})
    locked = await db[reg.COL_PLAQUE].count_documents({"locked": True})
    consents_granted = await db[reg.COL_CONSENT].count_documents({"status": "GRANTED"})
    consents_revoked = await db[reg.COL_CONSENT].count_documents({"status": "REVOKED"})
    individuals = await db[reg.COL_IND].count_documents({})
    erased = await db[reg.COL_IND].count_documents({"erased": True})
    chain = await reg.verify_ai_chain()
    return {
        "plaques": {
            "total": total,
            "memorial_boards": memorials,
            "honorary_places": honorary,
            "active": active,
            "locked_write_once": locked,
        },
        "ai_act": {
            "ai_generated_plaques": ai_content,
            "transparency_flag_enforced": True,
            "audit_chain_valid": chain["valid"],
            "audit_entries": chain["checked"],
        },
        "dsgvo": {
            "individuals": individuals,
            "consents_granted": consents_granted,
            "consents_revoked": consents_revoked,
            "erased_right_to_be_forgotten": erased,
            "pii_encryption": "AES-256-GCM",
        },
        "dma": {"open_api": True, "vendor_lock_in": False},
    }


# --------------------------------------------------------------------------- #
# Protected: individuals + consent                                            #
# --------------------------------------------------------------------------- #
@router.post("/individuals")
async def create_individual(
    body: IndividualCreate, user: dict = Depends(require_user)
) -> dict[str, Any]:
    db = get_db()
    system_id = reg.make_system_id()
    individual_id = reg.uid()
    now = reg.now_iso()
    pii = {
        "given_name": body.given_name,
        "family_name": body.family_name,
        "birth_place": body.birth_place,
        "birth_date": body.birth_date,
        "death_date": body.death_date,
        "nationality": body.nationality,
    }
    encrypted = reg.encrypt_pii(pii, system_id)
    await db[reg.COL_IND].insert_one(
        {
            "id": individual_id,
            "system_id": system_id,
            "status": body.status,
            "encrypted_data_record": encrypted,
            "erased": False,
            "created_at": now,
            "updated_at": now,
        }
    )
    await append_event(
        event_type="pnia.individual.created",
        actor=user["email"],
        subject=system_id,
        payload={"status": body.status},
    )
    return {"id": individual_id, "system_id": system_id, "status": body.status}


@router.get("/individuals/{individual_id}")
async def get_individual(
    individual_id: str, user: dict = Depends(require_user)
) -> dict[str, Any]:
    db = get_db()
    doc = await db[reg.COL_IND].find_one({"id": individual_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "individual not found")
    if doc.get("erased") or not doc.get("encrypted_data_record"):
        return {
            "id": individual_id,
            "status": doc.get("status"),
            "erased": True,
            "pii": None,
        }
    pii = reg.decrypt_pii(doc["encrypted_data_record"], doc["system_id"])
    return {
        "id": individual_id,
        "system_id": doc["system_id"],
        "status": doc["status"],
        "erased": False,
        "pii": pii,
    }


@router.post("/consents")
async def create_consent(
    body: ConsentCreate, user: dict = Depends(require_user)
) -> dict[str, Any]:
    db = get_db()
    ind = await db[reg.COL_IND].find_one({"id": body.individual_id})
    if not ind:
        raise HTTPException(404, "individual not found")
    now = reg.now_iso()
    doc = {
        "id": reg.uid(),
        "individual_id": body.individual_id,
        "status": "GRANTED",
        "basis": body.basis,
        "consent_document_hash": body.consent_document_hash
        or reg.sha256_hex(f"{body.individual_id}:{now}"),
        "origin_trace": body.origin_trace,
        "representative": body.representative,
        "signed_at": now,
        "revoked_at": None,
        "created_at": now,
    }
    await db[reg.COL_CONSENT].insert_one(dict(doc))
    doc.pop("_id", None)
    await append_event(
        event_type="pnia.consent.granted",
        actor=user["email"],
        subject=ind.get("system_id"),
        payload={"basis": body.basis},
    )
    return doc


@router.post("/consents/{individual_id}/revoke")
async def revoke_consent(
    individual_id: str, user: dict = Depends(require_user)
) -> dict[str, Any]:
    """DSGVO Art. 17 — revoke consent, crypto-shred PII, cascade deactivate."""
    db = get_db()
    ind = await db[reg.COL_IND].find_one({"id": individual_id})
    if not ind:
        raise HTTPException(404, "individual not found")
    now = reg.now_iso()
    await db[reg.COL_CONSENT].update_many(
        {"individual_id": individual_id, "status": "GRANTED"},
        {"$set": {"status": "REVOKED", "revoked_at": now}},
    )
    result = await reg.crypto_shred_and_cascade(individual_id, actor=user["email"])
    return {"individual_id": individual_id, "revoked": True, **result}


# --------------------------------------------------------------------------- #
# Protected: plaques                                                          #
# --------------------------------------------------------------------------- #
@router.post("/plaques")
async def create_plaque(
    body: PlaqueCreate, user: dict = Depends(require_user)
) -> dict[str, Any]:
    db = get_db()
    ind = await db[reg.COL_IND].find_one({"id": body.individual_id})
    if not ind:
        raise HTTPException(404, "individual not found")

    # Consistency: plaque type must match individual status
    expected = "MEMORIAL_BOARD" if ind["status"] == "DECEASED" else "HONORARY_PLACE"
    if body.type != expected:
        raise HTTPException(
            422,
            f"individual is {ind['status']} — plaque type must be {expected}",
        )

    # DSGVO: publishing a LIVING person requires GRANTED consent
    if ind["status"] == "LIVING" and not await reg.has_granted_consent(body.individual_id):
        raise HTTPException(
            403,
            "DSGVO Art. 6/7: a GRANTED consent is required before publishing an "
            "honorary place for a living person.",
        )
    # Postmortal: DECEASED requires a representative verification record
    if ind["status"] == "DECEASED" and not await reg.has_granted_consent(body.individual_id):
        raise HTTPException(
            403,
            "Postmortal protection: a representative verification record is "
            "required before publishing a memorial board.",
        )

    now = reg.now_iso()
    doc = {
        "id": reg.uid(),
        "individual_id": body.individual_id,
        "type": body.type,
        "is_active": True,
        "locked": False,
        "content_payload": {
            "display_name": body.display_name,
            "role": body.role,
            "institution": body.institution,
            "resting_place": body.resting_place,
            "tribute_text": body.tribute_text,
            "epitaph": body.epitaph,
        },
        "ai_generated_content": False,
        "risk_classification": reg.RISK_MINIMAL,
        "created_at": now,
        "updated_at": now,
    }
    await db[reg.COL_PLAQUE].insert_one(dict(doc))
    await append_event(
        event_type="pnia.plaque.created",
        actor=user["email"],
        subject=ind.get("system_id"),
        payload={"type": body.type},
    )
    return reg.public_plaque(doc)


@router.post("/plaques/{plaque_id}/lock")
async def lock_plaque(
    plaque_id: str, user: dict = Depends(require_user)
) -> dict[str, Any]:
    """Seal a plaque Write-Once / Read-Many (postmortal protection)."""
    db = get_db()
    doc = await db[reg.COL_PLAQUE].find_one({"id": plaque_id})
    if not doc:
        raise HTTPException(404, "plaque not found")
    await db[reg.COL_PLAQUE].update_one(
        {"id": plaque_id}, {"$set": {"locked": True, "updated_at": reg.now_iso()}}
    )
    await append_event(
        event_type="pnia.plaque.locked",
        actor=user["email"],
        subject=plaque_id,
        payload={},
    )
    return {"id": plaque_id, "locked": True}


@router.post("/plaques/{plaque_id}/generate-tribute")
async def generate_tribute(
    plaque_id: str, body: TributeRequest, user: dict = Depends(require_user)
) -> dict[str, Any]:
    db = get_db()
    doc = await db[reg.COL_PLAQUE].find_one({"id": plaque_id})
    if not doc:
        raise HTTPException(404, "plaque not found")
    if doc.get("locked"):
        raise HTTPException(409, "plaque is sealed (Write-Once) — cannot modify")

    cp = doc.get("content_payload", {})
    try:
        text, prompt, model_version = await pnia_ai.generate_tribute(
            display_name=cp.get("display_name", ""),
            role=cp.get("role", ""),
            institution=cp.get("institution", ""),
            resting_place=cp.get("resting_place", ""),
            plaque_type=doc["type"],
            language=body.language,
            tone=body.tone,
            extra_context=body.extra_context,
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(502, f"AI generation failed: {exc}") from exc

    cp["tribute_text"] = text
    await db[reg.COL_PLAQUE].update_one(
        {"id": plaque_id},
        {
            "$set": {
                "content_payload": cp,
                "ai_generated_content": True,
                "risk_classification": reg.RISK_LIMITED_TRANSPARENCY,
                "updated_at": reg.now_iso(),
            }
        },
    )
    audit = await reg.append_ai_audit(
        plaque_id=plaque_id,
        action_type="TEXT_GENERATION",
        ai_model_version=model_version,
        prompt=prompt,
        output=text,
    )
    await append_event(
        event_type="pnia.ai.tribute_generated",
        actor=user["email"],
        subject=plaque_id,
        payload={"model": model_version, "audit_hash": audit["hash"]},
    )
    return {
        "id": plaque_id,
        "tribute_text": text,
        "ai_generated_content": True,
        "risk_classification": reg.RISK_LIMITED_TRANSPARENCY,
        "audit": audit,
    }


@router.post("/plaques/{plaque_id}/translate")
async def translate_tribute(
    plaque_id: str, body: TranslateRequest, user: dict = Depends(require_user)
) -> dict[str, Any]:
    db = get_db()
    doc = await db[reg.COL_PLAQUE].find_one({"id": plaque_id})
    if not doc:
        raise HTTPException(404, "plaque not found")
    cp = doc.get("content_payload", {})
    source = cp.get("tribute_text", "")
    if not source:
        raise HTTPException(422, "no tribute text to translate")
    try:
        translated, prompt, model_version = await pnia_ai.translate_tribute(
            text=source, target_language=body.target_language
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(502, f"AI translation failed: {exc}") from exc

    translations = cp.get("translations", {})
    translations[body.target_language] = translated
    cp["translations"] = translations
    await db[reg.COL_PLAQUE].update_one(
        {"id": plaque_id},
        {
            "$set": {
                "content_payload": cp,
                "ai_generated_content": True,
                "risk_classification": reg.RISK_LIMITED_TRANSPARENCY,
                "updated_at": reg.now_iso(),
            }
        },
    )
    audit = await reg.append_ai_audit(
        plaque_id=plaque_id,
        action_type="TRANSLATION",
        ai_model_version=model_version,
        prompt=prompt,
        output=translated,
    )
    return {
        "id": plaque_id,
        "target_language": body.target_language,
        "translated": translated,
        "audit": audit,
    }
