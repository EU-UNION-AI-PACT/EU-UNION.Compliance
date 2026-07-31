"""BLAUPAUSE DER GESAMTARCHITEKTUR — read-only static architecture surface.

Serves the 5-layer model, the 10 building blocks (BB-01…BB-10), the
6-stage validation/screening path, the data flows and the regulatory
reference frame as defined in the reference paper (Version 1.0 · Stand:
31. Juli 2026 · Daniel Pohl / CoE e.V.).

No writes, no state. Complies with EU AI Act Art. 12 (documentation),
DMA (open API, machine-readable), DSA (statement of reasons in scope).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/blueprint", tags=["Blueprint / Architektur"])

# --------------------------------------------------------------------------- #
# Static architecture data                                                    #
# --------------------------------------------------------------------------- #
_LAYERS: list[dict[str, str]] = [
    {
        "level": "Ebene 1",
        "title": "Modulare Plattform-Architektur (GovStack-Prinzip)",
        "purpose": (
            "Zerlegung der Infrastruktur in wiederverwendbare, interoperable "
            "Bausteine (Building Blocks) statt monolithischer Systeme; "
            "dezentrale Resilienz durch modular gekoppelte Dienste und "
            "abgesicherte Datenaustausch-Layer."
        ),
    },
    {
        "level": "Ebene 2",
        "title": "Sicherheits- und Kollaborationsumgebung (CoE-Plattform)",
        "purpose": (
            "Hochgesicherter, passwortgeschützter und mehrfaktor-authentifizierter "
            "Arbeitsraum für verifizierte Akteure: Ministerien, Polizei- und "
            "Sicherheitsbehörden, Seconding- und Ausbildungsbehörden, EEAS "
            "sowie Missionspersonal."
        ),
    },
    {
        "level": "Ebene 3",
        "title": "Qualitäts- und Validierungszentrum (Excellent Hub)",
        "purpose": (
            "Zentraler, synergetischer Knotenpunkt als Qualitäts- und "
            "Validierungsinstanz für technologische Komponenten, Projektideen "
            "und Netzwerkpartner."
        ),
    },
    {
        "level": "Ebene 4",
        "title": "Inklusive Innovationsförderung und Barrierefreiheit",
        "purpose": (
            "Geschützter, barrierefreier Zugang für Innovatorinnen und "
            "Innovatoren mit gesundheitlichen, körperlichen oder sozialen "
            "Einschränkungen; ganzheitlicher Screening-Pfad ohne physische Hürden."
        ),
    },
    {
        "level": "Ebene 5",
        "title": "Institutionelle Verankerung und Compliance-Rahmen",
        "purpose": (
            "Verbindliche Selbstverpflichtungen (Pledges) und strenge legale "
            "Compliance als Fundament der gesamten Architektur; Ausrichtung an "
            "zivilen, sicherheitspolitischen, datenschutzrechtlichen und "
            "finanzaufsichtlichen Bezugsnormen."
        ),
    },
]

_BUILDING_BLOCKS: list[dict[str, str]] = [
    {"code": "BB-01", "title": "Identität und Verifikation", "purpose": "Verifizierte Teilnehmerprofile, Mehrfaktor-Authentifizierung, rollenbasierte Berechtigungen für Ministeriums- und Missionspersonal."},
    {"code": "BB-02", "title": "Sicherer Workspace", "purpose": "Passwortgeschützte Arbeitsumgebung mit projektspezifischen Sub-Plattformen."},
    {"code": "BB-03", "title": "Forschungs- und Berichts-Hub", "purpose": "Forschungsarbeiten, Evaluierungs- und Event-Berichte, strukturierte Feedback-Kanäle."},
    {"code": "BB-04", "title": "Annotation und Lesezeichen", "purpose": "Dokumenten-Annotation und kollaboratives, strukturiertes Lesezeichen-Management."},
    {"code": "BB-05", "title": "Excellent Hub (Validierung)", "purpose": "Automatisierte und manuelle Prüfpfade für Komponenten, Partner und Projektideen."},
    {"code": "BB-06", "title": "Screening und Existenzprüfung", "purpose": "Prüfung gesundheitlicher Verordnungen, Arbeitsschutzstandards und unternehmerischer Tragfähigkeit."},
    {"code": "BB-07", "title": "Inklusiver Evaluierungspfad", "purpose": "Angepasster Bewertungsweg für eingeschränkte Innovatoren; adaptive, barrierefreie Oberflächen."},
    {"code": "BB-08", "title": "API-Gateway und Onboarding (Upen)", "purpose": "Standardisierte Schnittstellen und kryptografisch abgesicherter Überführungsprozess in den operativen Infrastrukturkreislauf."},
    {"code": "BB-09", "title": "Datenschutz- und Korrektur-Ledger", "purpose": "Nachvollziehbare Berichtigung nach Art. 16 DSGVO; Wahrung informationaler Integrität."},
    {"code": "BB-10", "title": "Interoperabilitäts- und Austausch-Layer", "purpose": "Synchronisation von Datenströmen und Analysen mit verifizierten Partnern nach europäischen Interoperabilitätsstandards."},
]

_VALIDATION_PATH: list[dict[str, str]] = [
    {"stage": "Stufe 1", "title": "Eingang", "detail": "Strukturierte Einreichung über barrierefreie Oberfläche oder API-Gateway."},
    {"stage": "Stufe 2", "title": "Automatisiertes Scanning", "detail": "Maschinelle Prüfung auf regulatorische, sicherheitstechnische und formale Konformität."},
    {"stage": "Stufe 3", "title": "Gesundheits- und Arbeitsschutzprüfung", "detail": "Abgleich mit gesundheitlichen Verordnungen und Arbeitsschutzstandards (Safety First)."},
    {"stage": "Stufe 4", "title": "Unternehmerische Existenzprüfung", "detail": "Validierung organisatorischer und rechtlicher Tragfähigkeit."},
    {"stage": "Stufe 5", "title": "Manuelle Begutachtung (Excellent Hub)", "detail": "Fachliche Bewertung durch verifizierte Practitioner; Vier-Augen-Prinzip."},
    {"stage": "Stufe 6", "title": "Freigabe und Onboarding (Upen)", "detail": "Kryptografisch abgesicherte Überführung in den operativen Kreislauf."},
]

_DATA_FLOWS: list[dict[str, str]] = [
    {"flow": "Einreichung", "detail": "Barrierefreie Oberfläche oder API-Gateway an den Excellent Hub."},
    {"flow": "Prüfung", "detail": "Hub bezieht Nachweise, erzeugt Prüfvermerke und hält den Prüfstand vor."},
    {"flow": "Freigabe", "detail": "Upen-Prozess überführt die geprüfte Komponente kryptografisch abgesichert in den Betrieb."},
    {"flow": "Kollaboration", "detail": "Workspace, Forschungs- und Berichts-Hub, Annotation und Lesezeichen bleiben auf verifizierte Akteure begrenzt."},
    {"flow": "Berichtigung", "detail": "Korrektur-Ledger führt jede Änderung an personenbezogenen Angaben nachvollziehbar."},
]

_REGULATORY_REFS: list[dict[str, str]] = [
    {"ref": "EEAS", "meaning": "Europäischer Auswärtiger Dienst — institutioneller Bezugsrahmen für zivile Missionen."},
    {"ref": "CSDP", "meaning": "Gemeinsame Sicherheits- und Verteidigungspolitik — Handlungsrahmen zivilen Krisenmanagements."},
    {"ref": "CERT-EU", "meaning": "Cybersicherheitsdienst der EU-Institutionen — Referenz für Vorfallbehandlung und Härtung."},
    {"ref": "EDSA / EDSB", "meaning": "Europäischer Datenschutzausschuss und Europäischer Datenschutzbeauftragter — Auslegungsreferenz zur DSGVO."},
    {"ref": "BaFin / EBA", "meaning": "Finanzaufsicht — Referenz für Governance, Auslagerung und IT-Sicherheit bei finanzrelevanten Komponenten."},
    {"ref": "ISO / Akkreditierung", "meaning": "Internationale Normenwerke zu Informationssicherheit, Qualitäts- und Barrierefreiheitsmanagement."},
    {"ref": "EU AI Act", "meaning": "VO (EU) 2024/1689 — Anforderungen an KI-Systeme, Art. 12 Record-Keeping, Art. 50 Transparenz."},
    {"ref": "Digital Services Act", "meaning": "VO (EU) 2022/2065 — Rechtsrahmen für digitale Vermittlungsdienste."},
    {"ref": "Digital Markets Act", "meaning": "VO (EU) 2022/1925 — Marktzugangs- und Interoperabilitätspflichten."},
]

_META: dict[str, str] = {
    "title": "BLAUPAUSE DER GESAMTARCHITEKTUR",
    "subtitle": "Architektur-Paper — Blaupause einer ganzheitlichen, regulierten und inklusiven Public-Goods-Architektur",
    "version": "1.0",
    "asOf": "31. Juli 2026",
    "author": "Daniel Pohl",
    "initiative": "European Initiative — European Centre of Excellence for Civilian Crisis Management (CoE) e.V.",
    "geltungsvorbehalt": (
        "Architektonisches Konzeptwerk. Beschreibt Soll-Anforderungen und "
        "Gestaltungsprinzipien, nicht den Betriebszustand eines bestehenden "
        "Systems. Genannte Institutionen, Behörden und Normenwerke werden "
        "ausschließlich als regulatorischer Bezugsrahmen benannt. Aus der "
        "Nennung folgt keine Zertifizierung, Akkreditierung, Zulassung, "
        "Beauftragung oder Billigung durch die jeweilige Stelle."
    ),
}


# --------------------------------------------------------------------------- #
# Endpoints                                                                   #
# --------------------------------------------------------------------------- #
@router.get("/")
async def info() -> dict[str, Any]:
    return {
        "service": "PNIA · Architektur-Blaupause",
        "meta": _META,
        "counts": {
            "layers": len(_LAYERS),
            "building_blocks": len(_BUILDING_BLOCKS),
            "validation_stages": len(_VALIDATION_PATH),
            "data_flows": len(_DATA_FLOWS),
            "regulatory_refs": len(_REGULATORY_REFS),
        },
        "endpoints": [
            "/api/blueprint/layers",
            "/api/blueprint/building-blocks",
            "/api/blueprint/validation-path",
            "/api/blueprint/data-flows",
            "/api/blueprint/regulatory-refs",
            "/api/blueprint/full",
        ],
    }


@router.get("/layers")
async def layers() -> dict[str, Any]:
    return {"count": len(_LAYERS), "layers": _LAYERS}


@router.get("/building-blocks")
async def building_blocks() -> dict[str, Any]:
    return {"count": len(_BUILDING_BLOCKS), "building_blocks": _BUILDING_BLOCKS}


@router.get("/validation-path")
async def validation_path() -> dict[str, Any]:
    return {"count": len(_VALIDATION_PATH), "stages": _VALIDATION_PATH}


@router.get("/data-flows")
async def data_flows() -> dict[str, Any]:
    return {"count": len(_DATA_FLOWS), "flows": _DATA_FLOWS}


@router.get("/regulatory-refs")
async def regulatory_refs() -> dict[str, Any]:
    return {"count": len(_REGULATORY_REFS), "refs": _REGULATORY_REFS}


@router.get("/full")
async def full() -> dict[str, Any]:
    return {
        "meta": _META,
        "layers": _LAYERS,
        "building_blocks": _BUILDING_BLOCKS,
        "validation_path": _VALIDATION_PATH,
        "data_flows": _DATA_FLOWS,
        "regulatory_refs": _REGULATORY_REFS,
    }
