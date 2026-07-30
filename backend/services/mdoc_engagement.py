"""ISO 18013-5 device engagement — ephemeral eDeviceKey + SessionTranscript scaffold."""
from __future__ import annotations

import base64
import uuid
from datetime import datetime, timedelta, timezone

import cbor2
from cbor2 import CBORTag
from cryptography.hazmat.primitives.asymmetric import ec

from database import get_db


def _ec_public_to_cose(pk: ec.EllipticCurvePublicKey) -> dict[int, object]:
    numbers = pk.public_numbers()
    x = numbers.x.to_bytes(32, "big")
    y = numbers.y.to_bytes(32, "big")
    return {1: 2, -1: 1, -2: x, -3: y}


async def create_engagement() -> dict[str, object]:
    e_key = ec.generate_private_key(ec.SECP256R1())
    e_pub = e_key.public_key()
    device_engagement = {
        0: "1.0",
        1: [
            {1: 1, 2: 1, -1: _ec_public_to_cose(e_pub)}  # eDeviceKey
        ],
        2: [],  # deviceRetrievalMethods (empty — mock)
    }
    engagement_cbor = cbor2.dumps(CBORTag(24, cbor2.dumps(device_engagement)))
    engagement_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    numbers = e_pub.public_numbers()
    session_key_public_jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": base64.urlsafe_b64encode(numbers.x.to_bytes(32, "big")).decode().rstrip("="),
        "y": base64.urlsafe_b64encode(numbers.y.to_bytes(32, "big")).decode().rstrip("="),
    }
    await get_db().engagements.insert_one(
        {
            "engagement_id": engagement_id,
            "device_engagement_hex": engagement_cbor.hex(),
            "session_key_public_jwk": session_key_public_jwk,
            "created_at": now,
            "expires_at": now + timedelta(minutes=5),
        }
    )
    return {
        "engagement_id": engagement_id,
        "device_engagement_hex": engagement_cbor.hex(),
        "session_key_public_jwk": session_key_public_jwk,
        "expires_at": now + timedelta(minutes=5),
    }
