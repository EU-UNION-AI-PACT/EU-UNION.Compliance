"""OpenID4VCI Issuer — /nonce + /credential."""
from __future__ import annotations

import json
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from models import (
    CredentialOfferRequest,
    CredentialResponse,
    NonceResponse,
)
from routers.auth import require_user
from services.audit_log import append_event
from services.proof_jwt_validator import ProofJWTValidator
from services.sd_jwt_builder import SDJWTBuilder
from services.status_list_client import StatusListClient

router = APIRouter(prefix="/issuer", tags=["Issuer (OpenID4VCI)"])


def _issuer_url() -> str:
    return os.environ.get("ISSUER_URL", "http://localhost:8001")


def _status_uri() -> str:
    return f"{_issuer_url()}/api/issuer/status-list/primary"


def _loa_for_vct(vct: str) -> str:
    """Compute eIDAS LoA at issuance time so Compliance Cockpit counters work."""
    if "pid" in vct or "mdl" in vct:
        return "high"
    if "email" in vct:
        return "substantial"
    return "low"


@router.post("/nonce", response_model=NonceResponse)
async def issue_nonce() -> NonceResponse:
    validator = ProofJWTValidator(expected_audience=_issuer_url())
    nonce, ttl = await validator.issue_nonce()
    return NonceResponse(c_nonce=nonce, c_nonce_expires_in=ttl)


@router.post("/credential", response_model=CredentialResponse)
async def issue_credential(
    req: CredentialOfferRequest,
    user: dict = Depends(require_user),
) -> CredentialResponse:
    # Proof of Possession — the wallet's holder-binding JWT
    if req.proof_jwt:
        validator = ProofJWTValidator(expected_audience=_issuer_url())
        proof = await validator.validate(req.proof_jwt, req.holder_jwk)
        if not proof["valid"]:
            raise HTTPException(400, {"error": "invalid_proof", "reasons": proof["reasons"]})

    db = get_db()
    counter = await db.status_counter.find_one_and_update(
        {"_id": "primary"},
        {"$inc": {"next": 1}},
        upsert=True,
        return_document=True,
    )
    status_idx = counter["next"] if counter else 0

    builder = SDJWTBuilder(issuer=_issuer_url(), vct=req.vct)
    compact, count = await builder.issue(
        claims=req.subject_claims,
        holder_jwk=req.holder_jwk,
        status_index=status_idx,
        status_list_uri=_status_uri(),
    )

    await db.issued_credentials.insert_one(
        {
            "vct": req.vct,
            "status_index": status_idx,
            "country_code": req.country_code,
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "compact_head": compact[:120],
            "loa": _loa_for_vct(req.vct),
        }
    )
    await StatusListClient().set_status(_status_uri(), status_idx, "active")

    await append_event(
        event_type="credential.issued",
        actor=user.get("email", "issuer"),
        subject=req.subject_claims.get("family_name"),
        payload={"vct": req.vct, "country": req.country_code, "status_idx": status_idx},
    )
    return CredentialResponse(credential=compact, disclosures_count=count, vct=req.vct)


@router.get("/status-list/{list_id}")
async def get_status_list(list_id: str) -> dict:
    """Return the status list bit vector (compressed b64)."""
    uri = f"{_issuer_url()}/api/issuer/status-list/{list_id}"
    doc = await get_db().status_list_docs.find_one({"uri": uri}, {"_id": 0})
    if not doc:
        return {"uri": uri, "bits_b64": "", "size": 0}
    return doc


@router.post("/status-list/{list_id}/revoke/{idx}")
async def revoke(list_id: str, idx: int) -> dict:
    uri = f"{_issuer_url()}/api/issuer/status-list/{list_id}"
    await StatusListClient().set_status(uri, idx, "revoked")
    await append_event(
        event_type="credential.revoked",
        actor="issuer",
        payload={"status_idx": idx, "list": list_id},
    )
    return {"revoked": True, "idx": idx}


# --------- Credential Offer (OpenID4VCI §4) ---------

@router.post("/credential-offer")
async def create_credential_offer(
    body: dict, user: dict = Depends(require_user)
) -> dict:
    """Create a pre-authorized credential offer.

    Body: `{"vct": "...", "grants": {...} (optional)}`. Returns:
      - offer_id
      - offer_uri (openid-credential-offer://…) — for QR code display
      - by_reference_uri (https://…/credential-offer/{id}) — for wallets that
        prefer fetching the offer JSON separately
      - offer (the inline JSON object) — for wallets that inline
    """
    vct = body.get("vct", "eu.europa.ec.eudi.pid.1")
    pre_auth = secrets.token_urlsafe(24)
    offer_id = uuid.uuid4().hex[:16]
    offer = {
        "credential_issuer": _issuer_url(),
        "credential_configuration_ids": [vct],
        "grants": {
            "urn:ietf:params:oauth:grant-type:pre-authorized_code": {
                "pre-authorized_code": pre_auth,
                "tx_code": {"input_mode": "numeric", "length": 6},
            }
        },
    }
    await get_db().credential_offers.insert_one(
        {
            "offer_id": offer_id,
            "offer": offer,
            "actor": user.get("email"),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
        }
    )
    by_ref = f"{_issuer_url()}/api/issuer/credential-offer/{offer_id}"
    inline = "openid-credential-offer://?" + urlencode(
        {"credential_offer": json.dumps(offer, separators=(",", ":"))}
    )
    by_ref_uri = "openid-credential-offer://?" + urlencode({"credential_offer_uri": by_ref})
    await append_event(
        event_type="credential.offer_created",
        actor=user.get("email", "issuer"),
        payload={"vct": vct, "offer_id": offer_id},
    )
    return {
        "offer_id": offer_id,
        "offer_uri": inline,
        "by_reference_uri": by_ref_uri,
        "offer": offer,
        "expires_in": 900,
    }


@router.get("/credential-offer/{offer_id}")
async def get_credential_offer(offer_id: str) -> dict:
    doc = await get_db().credential_offers.find_one({"offer_id": offer_id}, {"_id": 0, "offer": 1})
    if not doc:
        raise HTTPException(404, "credential offer not found")
    return doc["offer"]
