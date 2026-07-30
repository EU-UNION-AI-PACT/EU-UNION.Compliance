"""Trust anchors, LOTL parsing, X.509 chain viewer."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models import LotlParseRequest, LotlSummary, TrustAnchor
from services.ca_generator import CAGenerator
from services.lotl_parser import parse_lotl_xml, utc_iso_or_none

router = APIRouter(prefix="/trust", tags=["Trust & LOTL"])


@router.get("/ca/chain")
async def get_ca_chain() -> list[dict]:
    return await CAGenerator.chain_summary()


@router.post("/lotl/parse", response_model=LotlSummary)
async def parse_lotl(req: LotlParseRequest) -> LotlSummary:
    try:
        parsed = parse_lotl_xml(req.xml)
    except Exception as exc:
        raise HTTPException(400, f"LOTL parse error: {exc}")
    anchors = [
        TrustAnchor(
            subject=a["tsp_name"],
            issuer=a["service_name"],
            serial_number=a["fingerprint_sha256"][:16],
            not_before=utc_iso_or_none(parsed["issue_date"]) or _epoch(),
            not_after=utc_iso_or_none(parsed["next_update"]) or _epoch(),
            key_use=["digital_signature"],
            is_root=True,
            fingerprint_sha256=a["fingerprint_sha256"],
            country_code=a["country_code"],
        )
        for a in parsed["anchors"]
    ]
    return LotlSummary(
        territory=parsed["territory"],
        scheme_operator=parsed["scheme_operator"],
        sequence_number=parsed["sequence_number"],
        issue_date=utc_iso_or_none(parsed["issue_date"]) or _epoch(),
        next_update=utc_iso_or_none(parsed["next_update"]) or _epoch(),
        anchor_count=parsed["anchor_count"],
        anchors=anchors,
    )


def _epoch():
    from datetime import datetime, timezone

    return datetime(1970, 1, 1, tzinfo=timezone.utc)
