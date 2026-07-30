"""Persistent 3-level Certificate Authority (Root → Intermediate → Signer).

Private keys are AES-256-GCM wrapped by KeyStorageManager and stored in Mongo.
The public certificates are also stored (PEM) so downstream services and the
frontend can inspect the chain.

We use P-256 for all levels (fastest) and X.509 v3 with basicConstraints CA=true
for root/intermediate, and EKU codeSigning + `1.0.18013.5.1.2` (mdocSigner) on
the leaf.
"""
from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from database import get_db
from services.key_storage import KeyStorageManager

MDOC_SIGNER_OID = x509.ObjectIdentifier("1.0.18013.5.1.2")


class CAGenerator:
    _lock = asyncio.Lock()
    _bootstrapped = False

    @classmethod
    async def bootstrap(cls) -> None:
        async with cls._lock:
            if cls._bootstrapped:
                return
            db = get_db()
            existing = await db.ca_material.count_documents({})
            if existing == 0:
                await cls._generate_chain()
            cls._bootstrapped = True

    @classmethod
    async def _generate_chain(cls) -> None:
        db = get_db()
        ks = KeyStorageManager()
        now = dt.datetime.now(dt.timezone.utc)

        # Root
        root_key = ec.generate_private_key(ec.SECP256R1())
        root_name = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "EU"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EUDI-Nexus"),
                x509.NameAttribute(NameOID.COMMON_NAME, "EUDI-Nexus Root CA"),
            ]
        )
        root_cert = (
            x509.CertificateBuilder()
            .subject_name(root_name)
            .issuer_name(root_name)
            .public_key(root_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(days=1))
            .not_valid_after(now + dt.timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=1), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(root_key, hashes.SHA256())
        )

        # Intermediate
        inter_key = ec.generate_private_key(ec.SECP256R1())
        inter_name = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "EU"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EUDI-Nexus"),
                x509.NameAttribute(NameOID.COMMON_NAME, "EUDI-Nexus Intermediate CA"),
            ]
        )
        inter_cert = (
            x509.CertificateBuilder()
            .subject_name(inter_name)
            .issuer_name(root_name)
            .public_key(inter_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(days=1))
            .not_valid_after(now + dt.timedelta(days=1825))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(root_key, hashes.SHA256())
        )

        # Signer (leaf) — mDoc signer
        signer_key = ec.generate_private_key(ec.SECP256R1())
        signer_name = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "EU"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EUDI-Nexus"),
                x509.NameAttribute(NameOID.COMMON_NAME, "EUDI-Nexus mDoc Signer"),
            ]
        )
        signer_cert = (
            x509.CertificateBuilder()
            .subject_name(signer_name)
            .issuer_name(inter_name)
            .public_key(signer_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(days=1))
            .not_valid_after(now + dt.timedelta(days=730))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([MDOC_SIGNER_OID]),
                critical=False,
            )
            .sign(inter_key, hashes.SHA256())
        )

        def _wrap_key(k: ec.EllipticCurvePrivateKey) -> str:
            pem = k.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            return ks.wrap(pem)

        def _pem_cert(c: x509.Certificate) -> str:
            return c.public_bytes(serialization.Encoding.PEM).decode()

        await db.ca_material.insert_many(
            [
                {"role": "root", "cert_pem": _pem_cert(root_cert), "wrapped_key": _wrap_key(root_key)},
                {"role": "intermediate", "cert_pem": _pem_cert(inter_cert), "wrapped_key": _wrap_key(inter_key)},
                {"role": "signer", "cert_pem": _pem_cert(signer_cert), "wrapped_key": _wrap_key(signer_key)},
            ]
        )

    @classmethod
    async def get_material(cls) -> dict[str, Any]:
        await cls.bootstrap()
        db = get_db()
        docs = {
            d["role"]: d async for d in db.ca_material.find({}, {"_id": 0})
        }
        ks = KeyStorageManager()
        material: dict[str, Any] = {}
        for role, doc in docs.items():
            cert = x509.load_pem_x509_certificate(doc["cert_pem"].encode())
            pem = ks.unwrap(doc["wrapped_key"])
            key = serialization.load_pem_private_key(pem, password=None)
            material[role] = {"cert": cert, "key": key, "pem": doc["cert_pem"]}
        return material

    @classmethod
    async def chain_summary(cls) -> list[dict[str, Any]]:
        mat = await cls.get_material()
        out = []
        for role in ("root", "intermediate", "signer"):
            cert: x509.Certificate = mat[role]["cert"]
            fp = cert.fingerprint(hashes.SHA256()).hex()
            out.append(
                {
                    "role": role,
                    "subject": cert.subject.rfc4514_string(),
                    "issuer": cert.issuer.rfc4514_string(),
                    "serial": hex(cert.serial_number),
                    "not_before": cert.not_valid_before_utc.isoformat(),
                    "not_after": cert.not_valid_after_utc.isoformat(),
                    "fingerprint_sha256": fp,
                    "pem": mat[role]["pem"],
                }
            )
        return out
