"""Multi-country adapter router."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from adapters.base import validate_gdpr_hashing
from adapters.registry import REGISTRY
from models import CountryInfo, CountryVerifyRequest, VerifyResponse
from services.audit_log import append_event

router = APIRouter(prefix="/country", tags=["Multi-Country Adapters"])


@router.get("/list", response_model=list[CountryInfo])
async def list_countries() -> list[CountryInfo]:
    out = []
    for code, adapter in REGISTRY.items():
        cfg = adapter.config
        out.append(
            CountryInfo(
                code=cfg.code,
                name=cfg.name,
                flag=cfg.flag,
                scheme=cfg.scheme,
                trust_framework=cfg.trust_framework,
                supported_formats=cfg.supported_formats,
                loa_mapping=cfg.loa_mapping,
                reference_url=cfg.reference_url,
                id_hash_algorithm=cfg.id_hash_algorithm,
                implemented=cfg.implemented,
            )
        )
    # sort: implemented first, then alphabetical
    return sorted(out, key=lambda c: (not c.implemented, c.name))


@router.get("/{code}", response_model=CountryInfo)
async def get_country(code: str) -> CountryInfo:
    adapter = REGISTRY.get(code.upper())
    if not adapter:
        raise HTTPException(404, f"country {code} not registered")
    cfg = adapter.config
    return CountryInfo(
        code=cfg.code,
        name=cfg.name,
        flag=cfg.flag,
        scheme=cfg.scheme,
        trust_framework=cfg.trust_framework,
        supported_formats=cfg.supported_formats,
        loa_mapping=cfg.loa_mapping,
        reference_url=cfg.reference_url,
        id_hash_algorithm=cfg.id_hash_algorithm,
        implemented=cfg.implemented,
    )


@router.post("/verify", response_model=VerifyResponse)
async def country_verify(req: CountryVerifyRequest) -> VerifyResponse:
    adapter = REGISTRY.get(req.country_code.upper())
    if not adapter:
        raise HTTPException(404, f"country {req.country_code} not registered")
    result = await adapter.verify(
        req.presentation,
        format=req.format,
        audience=req.audience,
        nonce=req.nonce,
    )
    result.setdefault("disclosed_claims", {})
    result.setdefault("issuer", None)
    result.setdefault("vct", None)
    result.setdefault("trust_chain", [])
    result.setdefault("status", "unknown")
    result.setdefault("loa", None)

    # DSGVO-konformes ID-Hashing validieren
    gdpr_errors = validate_gdpr_hashing(result["disclosed_claims"], adapter.config)
    if gdpr_errors:
        result["valid"] = False
        result.setdefault("reasons", [])
        result["reasons"].extend(gdpr_errors)

    await append_event(
        event_type="country.verified",
        actor=f"adapter:{req.country_code}",
        payload={"valid": result["valid"], "format": req.format, "gdpr_errors": gdpr_errors},
    )
    return VerifyResponse(**result)
