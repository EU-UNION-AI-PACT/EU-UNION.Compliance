"""OpenID discovery — /.well-known/openid-credential-issuer."""
from __future__ import annotations

import os

from fastapi import APIRouter

from services.signer_singleton import SignerSingleton

router = APIRouter(tags=["OpenID Discovery"])


@router.get("/openid-credential-issuer")
async def credential_issuer_metadata() -> dict:
    base = os.environ.get("ISSUER_URL", "http://localhost:8001")
    signer = await SignerSingleton.instance()
    return {
        "credential_issuer": base,
        "credential_endpoint": f"{base}/api/issuer/credential",
        "nonce_endpoint": f"{base}/api/issuer/nonce",
        "authorization_servers": [base],
        "credential_configurations_supported": {
            "eu.europa.ec.eudi.pid.1": {
                "format": "vc+sd-jwt",
                "vct": "eu.europa.ec.eudi.pid.1",
                "cryptographic_binding_methods_supported": ["jwk"],
                "credential_signing_alg_values_supported": ["ES256"],
                "proof_types_supported": {"jwt": {"proof_signing_alg_values_supported": ["ES256"]}},
                "display": [{"name": "EUDI PID", "locale": "en"}],
            },
            "eu.europa.ec.eudi.mdl.1": {
                "format": "vc+sd-jwt",
                "vct": "eu.europa.ec.eudi.mdl.1",
                "cryptographic_binding_methods_supported": ["jwk"],
                "credential_signing_alg_values_supported": ["ES256"],
                "proof_types_supported": {"jwt": {"proof_signing_alg_values_supported": ["ES256"]}},
            },
            "eu.europa.ec.eudi.email.1": {
                "format": "vc+sd-jwt",
                "vct": "eu.europa.ec.eudi.email.1",
                "cryptographic_binding_methods_supported": ["jwk"],
                "credential_signing_alg_values_supported": ["ES256"],
                "proof_types_supported": {"jwt": {"proof_signing_alg_values_supported": ["ES256"]}},
            },
        },
        "jwks": {"keys": [signer.public_jwk()]},
    }


@router.get("/jwks.json")
async def jwks() -> dict:
    signer = await SignerSingleton.instance()
    return {"keys": [signer.public_jwk()]}
