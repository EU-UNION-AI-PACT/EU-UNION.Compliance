"""PNIA Core — Concil Protokoll (CP-01) reference implementation.

Derived 1:1 from the PNIA Komplettpaket concept document:

  PNIA = *Production Network ID Architecture* — the operational layer of the
  Concil Protokoll (CP-01), where regulatory & ethical requirements are embedded
  as systemic *invariants* directly into the data stream (State-0-Compliance)
  rather than checked retrospectively.

This module exposes:
  * the concept (four CP-01 pillars + technical pillars + governance roles)
  * a live CIH-01 handshake (Discovery → Invariant-Validation → Activation)
    that enforces the hard-coded governance invariants (Axiom layer) and
    isolates non-compliant systems via the *Sovereignty Shield* (HTTP 403).
  * the protected Urheberrecht / Register statement (© 2026 Daniel Pohl).

All handshakes are written to the platform's SHA-256 hash-chained audit log.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from services.audit_log import append_event
from services.issuer_signer import sign_jws

# Axiom layer — hard-coded governance invariants (State-0 base states)
REQUIRED_INVARIANTS = ["peace", "freedom", "integrity", "neighborly_love"]

PROTOCOL_VERSION = "CP-01"
HANDSHAKE_VERSION = "CIH-01"
AI_MODEL_TAG = "PNIA-Core-v1.2"

CP01_PILLARS = [
    {
        "key": "axiom",
        "name": "Axiom-Ebene",
        "en": "Axiom Layer",
        "desc": "Grundprinzipien Frieden, Freiheit, Integrität und Nächstenliebe als binäre Basiszustände des Systems.",
    },
    {
        "key": "immunitas",
        "name": "Immunitas-Modus",
        "en": "Immunity Mode",
        "desc": "Verschlüsselter, autonomer Sicherheitsmodus für „Established Access“ und Systemintegrität.",
    },
    {
        "key": "governance",
        "name": "Governance-Veredelung",
        "en": "Governance Refinement",
        "desc": "Technische Übersetzung externer Regularien (DORA, MiCA, EU AI Act, DSGVO, Menschenrechte) in Concil-Code.",
    },
    {
        "key": "flow",
        "name": "Multi-Ewigkeits-Flow",
        "en": "Multi-Eternity Flow",
        "desc": "Ressourcensteuerung nach Beitrag zu gesellschaftlicher Harmonie und Stabilität statt nach Profit.",
    },
]

TECHNICAL_PILLARS = [
    {"name": "Automated Audit Trail", "desc": "Kryptografische Signatur je Datenpunkt — Echtzeit-Validierungslog."},
    {"name": "Operational Resilience (DORA)", "desc": "Infrastrukturelle Redundanz, erfüllt DORA-Resilienzanforderungen."},
    {"name": "Interoperability-Layer (EBSI)", "desc": "Standardisierte Anbindung an EBSI, DID-Systeme und Identity-Frameworks."},
    {"name": "Governance Invariants", "desc": "Hart kodierte Constraints als ethisch-regulatorischer Mindeststandard."},
]

GOVERNANCE_ROLES = [
    {"role": "Key-Holder / Schatzmeister", "desc": "Treuhänderische Wahrung der Invarianten; koordiniert & validiert Concil-Updates; unabhängig von Staaten/Konzernen."},
    {"role": "System-Operator", "desc": "Technischer Betrieb CP-01-konformer Netze; Pflege der Governance-Invarianten."},
    {"role": "Aufsichtsbehörde", "desc": "Validiert Architektur; technische Compliance-Prüfung („Architecture Guarantors“)."},
    {"role": "Nutzer / Teilnehmer", "desc": "Hält Zugangsvoraussetzungen ein und respektiert die Axiome."},
    {"role": "Standardisierungsgremium", "desc": "Prüft, referenziert und standardisiert Protokollkomponenten."},
    {"role": "Initiator / Autor", "desc": "Daniel Pohl — Urheber & konzeptioneller Initiator."},
]

# Protected ownership / register statement (from the PNIA Komplettpaket).
OWNERSHIP = {
    "copyright": "© 2026 Daniel Pohl",
    "holder": "Daniel Pohl",
    "location": "Detmold, NRW-OWL-LIPPE, Deutschland",
    "statement": (
        "Dieses Dokument und die beschriebene Architektur (PNIA / Concil Protokoll CP-01, "
        "Gedenk- & Ehrenregister) unterliegen dem Urheberrecht des Autors. Nutzung, "
        "Vervielfältigung oder Verarbeitung bedürfen der ausdrücklichen Genehmigung, "
        "sofern nicht schriftlich anders vereinbart. Alle Register- und Urheberrechte "
        "verbleiben beim Initiator."
    ),
    "trademarks": ["Hnoss® (eingetragene Marke)", "HNOSS™ IDENTITY© (No Rights Waived)"],
    "registers": [
        {"label": "EU-Expert ID", "value": "EX2025D1218310"},
        {"label": "D-U-N-S", "value": "315676980 / 317066336"},
        {"label": "USt-IdNr. (VAT)", "value": "DE441892129"},
        {"label": "Global LEI", "value": "894500GBJSIW8L6ET310"},
        {"label": "UNGM / PIC", "value": "1172700 / 873042778"},
    ],
    "governance": {
        "VetoShield": "Verfassungsklausel — verhindert Änderungen an Säulen/Invarianten durch einfache Mehrheit oder Admin-Zugriff.",
        "Konzill-Update": "Dokumentierte Evolution: schriftliche Begründung, Axiom-Kompatibilität, Impact-Analyse, transparente Doku, freiwillige Adoption.",
        "Infrastruktur Building Lizenz": "Governance-Vereinbarung (keine kommerzielle Lizenz) zum Betrieb PNIA-standardkonformer Systeme.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def concept() -> dict[str, Any]:
    return {
        "acronym": "PNIA — Production Network ID Architecture",
        "definition": (
            "Technisches Referenzdesign, das regulatorische und ethische Anforderungen als "
            "systemische Invarianten direkt in den Datenstrom einbettet (State-0-Compliance) — "
            "die operative Ebene des Concil Protokoll (CP-01)."
        ),
        "protocol_version": PROTOCOL_VERSION,
        "handshake_version": HANDSHAKE_VERSION,
        "cp01_pillars": CP01_PILLARS,
        "technical_pillars": TECHNICAL_PILLARS,
        "governance_roles": GOVERNANCE_ROLES,
        "principles": [
            "State-0-Compliance (Compliance als Default-Zustand)",
            "Zero-Trust Logic",
            "Algorithmic Constitutionalism",
            "Sovereignty Shield (Isolation nicht-konformer Systeme)",
        ],
        "required_invariants": REQUIRED_INVARIANTS,
    }


async def discovery() -> dict[str, Any]:
    """CIH-01 Discovery payload — signed keyholder attestation of live invariants."""
    payload = {
        "concil_status": "active",
        "invariants": REQUIRED_INVARIANTS,
        "protocol_version": PROTOCOL_VERSION,
        "last_updated": _now(),
    }
    body = f"{payload['protocol_version']}:{','.join(payload['invariants'])}:{payload['last_updated']}"
    payload["keyholder_signature"] = "sha256-" + hashlib.sha256(body.encode()).hexdigest()
    payload["jws"] = await sign_jws({"discovery": payload["keyholder_signature"]}, typ="concil+jwt")
    return payload


async def handshake(
    *,
    system_id: str | None,
    accepted_invariants: list[str],
    commitment: str | None,
    mode: str = "State-0-Invariante",
    actor: str = "anonymous",
) -> dict[str, Any]:
    """CIH-01 Invariant-Validation + Activation.

    Returns HTTP-style ``status`` 200 (Established Access) or 403
    (Governance-Mismatch → Sovereignty Shield isolates the caller).
    """
    system_id = system_id or f"sys-{uuid.uuid4()}"
    accepted = {str(i).strip().lower().replace(" ", "_") for i in (accepted_invariants or [])}
    missing = [inv for inv in REQUIRED_INVARIANTS if inv not in accepted]
    has_commitment = bool(commitment)

    if not missing and has_commitment:
        session_token = f"concil-{uuid.uuid4().hex}"
        await append_event(
            event_type="concil.handshake.established",
            actor=actor,
            subject=system_id,
            payload={"mode": mode, "invariants": sorted(accepted)},
        )
        return {
            "status": 200,
            "decision": "ESTABLISHED_ACCESS",
            "system_id": system_id,
            "session_token": session_token,
            "sovereignty_shield": "passive",
            "lsm_config": {
                "protocol": "Concil-Standard-V2",
                "mode": mode,
                "invariants": REQUIRED_INVARIANTS,
            },
            "concil_signature_header": "sha256-"
            + hashlib.sha256(f"{system_id}:{session_token}".encode()).hexdigest(),
            "timestamp": _now(),
            "message": "Established Access gewährt — alle Governance-Invarianten erfüllt.",
        }

    reason = (
        f"Fehlende Invarianten: {', '.join(missing)}" if missing else "Fehlendes konstitutionelles Commitment"
    )
    await append_event(
        event_type="concil.handshake.rejected",
        actor=actor,
        subject=system_id,
        payload={"missing": missing, "commitment": has_commitment},
    )
    return {
        "status": 403,
        "decision": "GOVERNANCE_MISMATCH",
        "system_id": system_id,
        "sovereignty_shield": "isolated",
        "missing_invariants": missing,
        "commitment_present": has_commitment,
        "timestamp": _now(),
        "message": f"Invariante-Verletzung — {reason}. System durch Sovereignty Shield isoliert.",
    }
