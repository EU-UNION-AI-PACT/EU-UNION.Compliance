"""CountryAdapter Protocol — every EU/EFTA/partner nation implements this."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class CountryConfig:
    code: str
    name: str
    flag: str
    scheme: str
    trust_framework: str
    supported_formats: list[str]
    loa_mapping: dict[str, str]
    reference_url: str
    id_hash_algorithm: str = "SHA-256"
    implemented: bool = False


class CountryAdapter(Protocol):
    config: CountryConfig

    async def verify(
        self,
        presentation: str,
        *,
        format: str,
        audience: str | None,
        nonce: str | None,
    ) -> dict[str, Any]: ...

    def hash_national_id(self, national_id: str) -> str: ...


# ---------------------------------------------------------------------------
# DSGVO-konformes ID-Hashing — zentrale Validierung
# ---------------------------------------------------------------------------

GDPR_HASH_PATTERN = re.compile(r".*_hash$")


def validate_gdpr_hashing(disclosed_claims: dict[str, Any], config: CountryConfig) -> list[str]:
    """Prüft ob DSGVO-konformes ID-Hashing angewendet wurde.

    Regeln:
    1. Klartext-ID darf nicht in disclosed_claims sein (nur *_hash Felder)
    2. Mindestens ein *_hash Feld muss vorhanden sein
    3. Hash-Wert muss 64-stelliger Hex-String sein (SHA-256)

    Returns:
        Liste von Fehlern (leer = alles OK)
    """
    errors: list[str] = []

    # 1. Prüfe dass keine Klartext-ID übermittelt wird
    # (prüfe alle Keys die NICHT auf _hash enden)
    plaintext_keys = [k for k in disclosed_claims.keys() if not GDPR_HASH_PATTERN.match(k)]

    # 2. Prüfe dass mindestens ein Hash vorhanden ist
    hash_keys = [k for k in disclosed_claims.keys() if GDPR_HASH_PATTERN.match(k)]
    if not hash_keys:
        errors.append(
            f"{config.code}: Kein ID-Hash gefunden. DSGVO-konforme Pseudonymisierung fehlt."
        )
        return errors

    # 3. Prüfe Hash-Format (SHA-256 = 64 Hex-Zeichen)
    for hk in hash_keys:
        hval = str(disclosed_claims[hk])
        if not re.fullmatch(r"[0-9a-f]{64}", hval):
            errors.append(
                f"{config.code}: Hash '{hk}' ist kein gültiger SHA-256 Hex-String: {hval[:16]}..."
            )

    # 4. Prüfe dass keine Klartext-ID zu bekannten ID-Feldern passt
    # (heuristisch: wenn disclosed_claims ein Feld hat das dem id_claim_keys Muster entspricht)
    known_id_fields = {
        "nic", "citizen_card_number",
        "personnummer", "personal_number",
        "fodselsnummer", "personal_identity_number",
        "cpr", "cpr_number",
        "ppsn", "psc_number",
        "cpf",
        "insee",
        "codice_fiscale",
        "ahv", "ahv_number",
        "emirates_id", "national_id",
        "egn",
        "national_number",
        "resident_id",
        "individual_number",
        "e_residency_id",
        "aadhaar_uid", "uid",
        "provincial_id",
        "mygovid",
        "realme_id",
        "kennitala",
        "finnish_personal_id",
        "id_number",
        "document_number", "driving_licence_number",
    }
    leaked = [k for k in plaintext_keys if k.lower() in known_id_fields]
    if leaked:
        errors.append(
            f"{config.code}: Klartext-Identifier übermittelt (DSGVO-Verstoß): {leaked}"
        )

    return errors


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
