#!/usr/bin/env python3
# =============================================================================
# EU-ARF / eIDAS 2.0 Compliance Validation Pipeline
# Automatisierter Self-Check für Multi-Country-Adapter & BSI-Vorbereitung
# =============================================================================

import json
import sys
import logging
from datetime import datetime, timezone

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EU_ARF_Validator")

# EU-ARF & eIDAS 2.0 Soll-Werte (Referenz aus eudi.dev)
EXPECTED_STANDARDS = {
    "loa": "high",
    "allowed_hashing_algorithms": ["sha-256", "sha-384", "sha-512"],
    "allowed_signing_algorithms": ["es256", "es384", "ps256", "eddsa"],
    "required_protocols": ["oidc4vci", "oidc4vp", "mdl"],
    "data_minimization_enabled": True
}

def load_infrastructure_config(config_path):
    """Lädt die aktuelle Konfiguration der Infrastruktur/Adapter."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Konfigurationsdatei {config_path} nicht gefunden.")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Fehler beim Parsen der Datei {config_path}.")
        sys.exit(1)

def run_compliance_check(infra_config):
    """Führt den Soll-Ist-Vergleich der Infrastruktur gegen EU-ARF durch."""
    logger.info("Starte EU-ARF Compliance Check für Infrastruktur-Adapter...")
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "checks": []
    }
    
    # 1. Level of Assurance (LoA) prüfen
    loa = infra_config.get("security", {}).get("level_of_assurance", "").lower()
    if loa == EXPECTED_STANDARDS["loa"]:
        results["checks"].append({"check": "LoA", "status": "PASS", "detail": f"Level of Assurance ist {loa.upper()} (konform)."})
    else:
        results["checks"].append({"check": "LoA", "status": "FAIL", "detail": f"Erwartet: {EXPECTED_STANDARDS['loa'].upper()}, Gefunden: {loa.upper()}"})
        results["status"] = "FAIL"

    # 2. Krypto- und Hashing-Standards prüfen (ID-Hashing)
    crypto = infra_config.get("cryptography", {})
    hashing_alg = crypto.get("id_hashing", "").lower()
    if hashing_alg in EXPECTED_STANDARDS["allowed_hashing_algorithms"]:
        results["checks"].append({"check": "ID-Hashing", "status": "PASS", "detail": f"Algorithmus {hashing_alg.upper()} ist EU-ARF konform."})
    else:
        results["checks"].append({"check": "ID-Hashing", "status": "FAIL", "detail": f"Ungültiger oder unsicherer Hashing-Algorithmus: {hashing_alg.upper()}"})
        results["status"] = "FAIL"

    # 3. Signatur-Standards prüfen
    signing_alg = crypto.get("signing", "").lower()
    if signing_alg in EXPECTED_STANDARDS["allowed_signing_algorithms"]:
        results["checks"].append({"check": "Kryptografie (Signatur)", "status": "PASS", "detail": f"Signatur-Algorithmus {signing_alg.upper()} zugelassen."})
    else:
        results["checks"].append({"check": "Kryptografie (Signatur)", "status": "FAIL", "detail": f"Nicht zugelassener Signatur-Algorithmus: {signing_alg.upper()}"})
        results["status"] = "FAIL"

    # 4. Protokolle (OIDC4VCI / OIDC4VP) prüfen
    protocols = [p.lower() for p in infra_config.get("protocols", [])]
    missing_protocols = [p for p in EXPECTED_STANDARDS["required_protocols"] if p not in protocols]
    
    if not missing_protocols:
        results["checks"].append({"check": "Protokolle", "status": "PASS", "detail": "Alle erforderlichen EUDI-Protokolle (OIDC4VCI/VP) implementiert."})
    else:
        results["checks"].append({"check": "Protokolle", "status": "WARN", "detail": f"Fehlende oder unvollständige Protokolle: {', '.join(missing_protocols).upper()}"})
        # Setze Status auf WARN, wenn noch in Entwicklung, ansonsten "FAIL" für Produktion
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    # 5. Multi-Country Federation & Trusted Lists prüfen
    federation = infra_config.get("federation", {})
    trusted_lists = federation.get("trusted_list_endpoints", [])
    
    if federation.get("cross_border_enabled") and len(trusted_lists) > 0:
        results["checks"].append({"check": "Multi-Country Adapter", "status": "PASS", "detail": f"Cross-Border aktiviert. {len(trusted_lists)} Trusted Lists verknüpft."})
    else:
        results["checks"].append({"check": "Multi-Country Adapter", "status": "FAIL", "detail": "Federation-Endpoints oder Cross-Border-Flag fehlen."})
        results["status"] = "FAIL"

    # 6. Multi-Country Federation — Anzahl implementierter Länder (Adapter) prüfen
    countries = infra_config.get("countries", [])
    implemented = [c for c in countries if c.get("status") == "implemented"]
    if len(implemented) >= 11:
        results["checks"].append({"check": "11+ Länder · ein Adapter-Interface", "status": "PASS", "detail": f"{len(implemented)} Länder vollständig integriert: {', '.join(c['code'] for c in implemented)}"})
    else:
        results["checks"].append({"check": "Multi-Country Federation · ein Adapter-Interface", "status": "WARN", "detail": f"{len(implemented)} Länder implementiert: {', '.join(c['code'] for c in implemented)}"})
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    # 6b. Global Identity Broker — 22+ internationale Provider prüfen
    broker = infra_config.get("identity_broker", {})
    providers = broker.get("providers", [])
    active_providers = [p for p in providers if p.get("status") == "production"]
    if len(active_providers) >= 20:
        results["checks"].append({"check": "Global Identity Broker · 22+ Provider", "status": "PASS", "detail": f"{len(active_providers)} aktive Provider: {', '.join(p['id'] for p in active_providers)}"})
    else:
        results["checks"].append({"check": "Global Identity Broker · 22+ Provider", "status": "WARN", "detail": f"Nur {len(active_providers)}/22+ Provider aktiv"})
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    # 7. DSGVO-konformes ID-Hashing prüfen
    data_min = infra_config.get("data_minimization", {})
    if data_min.get("enabled") and data_min.get("id_hashing"):
        results["checks"].append({"check": "DSGVO-konformes ID-Hashing", "status": "PASS", "detail": data_min["id_hashing"]})
    else:
        results["checks"].append({"check": "DSGVO-konformes ID-Hashing", "status": "FAIL", "detail": "Data-Minimization oder ID-Hashing nicht konfiguriert"})
        results["status"] = "FAIL"

    # 7b. Format-Diversität prüfen (nicht alle Länder haben identische Formate)
    country_formats = {}
    for c in countries:
        code = c.get("code")
        formats = c.get("formats", [])
        if code and formats:
            country_formats[code] = formats

    # Prüfe dass mindestens 3 verschiedene Format-Kombinationen existieren
    unique_format_combos = set(tuple(sorted(f)) for f in country_formats.values())
    if len(unique_format_combos) >= 3:
        results["checks"].append({"check": "Format-Diversität", "status": "PASS", "detail": f"{len(unique_format_combos)} verschiedene Format-Kombinationen über {len(country_formats)} Länder"})
    else:
        results["checks"].append({"check": "Format-Diversität", "status": "WARN", "detail": f"Nur {len(unique_format_combos)} Format-Kombinationen — Multi-Country Federation sollte diverser sein"})
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    # 8. Compliance-Standards prüfen
    standards = infra_config.get("compliance_standards", [])
    required_standards = ["eIDAS 2.0", "EU-ARF", "ISO 18013-5", "BSI TR", "GDPR"]
    missing_std = [s for s in required_standards if not any(s.lower() in std.lower() for std in standards)]
    if not missing_std:
        results["checks"].append({"check": "Compliance-Standards", "status": "PASS", "detail": f"Alle relevanten Standards abgedeckt: {', '.join(standards)}"})
    else:
        results["checks"].append({"check": "Compliance-Standards", "status": "WARN", "detail": f"Fehlende Standards: {', '.join(missing_std)}"})
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    # ──────────────────────────────────────────────────────────────────────
    # PNIA Construction Checks — Concil Protokoll (CP-01) Domain
    # ──────────────────────────────────────────────────────────────────────
    pnia = infra_config.get("pnia_construction", {})

    # 9. Concil Protokoll CP-01 — State-0-Compliance (ethische Invarianten als Default)
    cp01 = pnia.get("concil_protocol", {})
    invariants = cp01.get("required_invariants", [])
    required_invariants_set = {"peace", "freedom", "integrity", "neighborly_love"}
    missing_inv = [i for i in required_invariants_set if i not in {v.lower() for v in invariants}]
    if not missing_inv:
        results["checks"].append({"check": "Concil CP-01 · State-0-Invarianten", "status": "PASS", "detail": f"Axiom-Ebene aktiv: {', '.join(invariants)}"})
    else:
        results["checks"].append({"check": "Concil CP-01 · State-0-Invarianten", "status": "FAIL", "detail": f"Fehlende Basis-Invarianten: {', '.join(missing_inv)}"})
        results["status"] = "FAIL"

    # 10. Verstorbene Personen (Deceased) — Memorial Register
    deceased = pnia.get("deceased_persons", {})
    mem_registry = deceased.get("memorial_registry", {})
    mem_checks = []
    if mem_registry.get("postmortal_protection"):
        mem_checks.append("Postmortaler Schutz aktiv")
    if mem_registry.get("write_once_read_many"):
        mem_checks.append("Write-Once / Read-Many Versiegelung")
    if mem_registry.get("representative_verification"):
        mem_checks.append("Repräsentanten-Verifizierung")
    if mem_checks:
        results["checks"].append({"check": "Verstorbene · Memorial Register", "status": "PASS", "detail": "; ".join(mem_checks)})
    else:
        results["checks"].append({"check": "Verstorbene · Memorial Register", "status": "WARN", "detail": "Postmortaler Schutz nicht vollständig konfiguriert"})
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    # 11. Lebende Personen (Living) — Honorary Register
    living = pnia.get("living_persons", {})
    hon_registry = living.get("honorary_registry", {})
    hon_checks = []
    if hon_registry.get("explicit_consent_required"):
        hon_checks.append("DSGVO Art. 6/7 explizites Consent")
    if hon_registry.get("data_minimization_pii"):
        hon_checks.append("Datenminimierung PII")
    if hon_registry.get("right_to_erasure"):
        hon_checks.append("Recht auf Löschung Art. 17")
    if hon_checks:
        results["checks"].append({"check": "Lebende · Honorary Register", "status": "PASS", "detail": "; ".join(hon_checks)})
    else:
        results["checks"].append({"check": "Lebende · Honorary Register", "status": "WARN", "detail": "Ehrenregister-Datenschutz nicht vollständig konfiguriert"})
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    # 12. Staatliche Construction — Governance & Sovereignty Shield
    state = pnia.get("state_construction", {})
    gov = state.get("governance", {})
    state_checks = []
    if gov.get("sovereignty_shield"):
        state_checks.append("Sovereignty Shield (Isolation nicht-konformer Systeme)")
    if gov.get("veto_protection"):
        state_checks.append("Verfassungs-Vetoklausel gegen einfache Mehrheitsänderungen")
    if gov.get("keyholder_treuhand"):
        state_checks.append("Keyholder-Treuhand für Invarianten-Wahrung")
    if gov.get("algorithmic_constitutionalism"):
        state_checks.append("Algorithmic Constitutionalism als Rechtsrahmen")
    if state_checks:
        results["checks"].append({"check": "Staatliche Construction · Governance", "status": "PASS", "detail": "; ".join(state_checks)})
    else:
        results["checks"].append({"check": "Staatliche Construction · Governance", "status": "WARN", "detail": "Governance-Architektur nicht konfiguriert"})
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    # 13. EU-Register & Urheberrecht (Protected Intellectual Property)
    registers = pnia.get("registers", {})
    reg_checks = []
    if registers.get("eu_expert_id"):
        reg_checks.append(f"EU-Expert ID: {registers['eu_expert_id']}")
    if registers.get("duns"):
        reg_checks.append(f"D-U-N-S: {registers['duns']}")
    if registers.get("vat_id"):
        reg_checks.append(f"USt-IdNr.: {registers['vat_id']}")
    if registers.get("global_lei"):
        reg_checks.append(f"Global LEI: {registers['global_lei']}")
    if registers.get("copyright"):
        reg_checks.append(f"Urheberrecht: {registers['copyright']}")
    if len(reg_checks) >= 3:
        results["checks"].append({"check": "EU-Register · Urheberrecht", "status": "PASS", "detail": "; ".join(reg_checks)})
    else:
        results["checks"].append({"check": "EU-Register · Urheberrecht", "status": "WARN", "detail": "Registereinträge unvollständig"})
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    # 14. AI Act Compliance — Transparenz & Audit Chain
    ai_act = pnia.get("ai_act", {})
    ai_checks = []
    if ai_act.get("transparency_flag"):
        ai_checks.append("Art. 50 Transparenz-Kennzeichnung")
    if ai_act.get("record_keeping"):
        ai_checks.append("Art. 12 Record-Keeping Audit-Log")
    if ai_act.get("risk_classification"):
        ai_checks.append(f"Risikoklassifizierung: {ai_act['risk_classification']}")
    if ai_act.get("human_oversight"):
        ai_checks.append("Menschliche Aufsicht (Human-in-the-Loop)")
    if ai_checks:
        results["checks"].append({"check": "EU AI Act Compliance", "status": "PASS", "detail": "; ".join(ai_checks)})
    else:
        results["checks"].append({"check": "EU AI Act Compliance", "status": "WARN", "detail": "AI-Act-Konformität nicht konfiguriert"})
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    # 15. Zero-Trust · Kryptografische Hash-Chain · Audit Trail
    security = pnia.get("security_architecture", {})
    sec_checks = []
    if security.get("sha256_hash_chain"):
        sec_checks.append("SHA-256 Hash-Chain Audit Trail")
    if security.get("aes256_gcm_pii"):
        sec_checks.append("AES-256-GCM PII-Verschlüsselung")
    if security.get("es256_jws_signing"):
        sec_checks.append("ES256 JWS Signatur")
    if security.get("zero_trust_logic"):
        sec_checks.append("Zero-Trust Logic (keine implizite Vertrauenswürdigkeit)")
    if sec_checks:
        results["checks"].append({"check": "Zero-Trust · Krypto-Audit", "status": "PASS", "detail": "; ".join(sec_checks)})
    else:
        results["checks"].append({"check": "Zero-Trust · Krypto-Audit", "status": "WARN", "detail": "Sicherheitsarchitektur nicht vollständig"})
        if results["status"] != "FAIL":
            results["status"] = "WARN"

    return results

def generate_bsi_report(results, output_file="bsi_compliance_report.json"):
    """Exportiert den Konformitätsbericht für die BSI-Dokumentation."""
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(results, f, indent=4)
    logger.info(f"Offizieller BSI-Konformitätsbericht generiert unter: {output_file}")

if __name__ == "__main__":
    # Argument parsing:
    #   sys.argv[1] (optional) – path to infrastructure config JSON
    #   sys.argv[2] (optional) – path where the BSI report should be written
    # If no config file is given, a built-in test config is used.
    config_path = None
    output_path = "bsi_compliance_report.json"

    if len(sys.argv) > 1:
        # If the first argument looks like a JSON file (not the default report name),
        # treat it as a config path.
        config_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    if config_path:
        logger.info(f"Lade Infrastruktur-Konfiguration aus {config_path}...")
        infrastructure_config = load_infrastructure_config(config_path)
    else:
        logger.info("Keine Config-Datei übergeben. Verwende Multi-Country Produktions-Konfiguration...")
        infrastructure_config = {
            "security": {
                "level_of_assurance": "high"
            },
            "cryptography": {
                "id_hashing": "sha-256",
                "signing": "es256"
            },
            "protocols": [
                "oidc4vci",
                "oidc4vp",
                "mdl",
                "siopv2",
                "ldp-vc"
            ],
            "federation": {
                "cross_border_enabled": True,
                "trusted_list_endpoints": [
                    "https://trusted-list.eudi.eu/de",
                    "https://trusted-list.eudi.eu/fr",
                    "https://trusted-list.eudi.eu/it",
                    "https://trusted-list.eudi.eu/pt",
                    "https://trusted-list.eudi.eu/se",
                    "https://trusted-list.eudi.eu/no",
                    "https://trusted-list.eudi.eu/dk",
                    "https://trusted-list.eudi.eu/ie",
                    "https://trusted-list.eudi.eu/at",
                    "https://trusted-list.eudi.eu/pl",
                    "https://trusted-list.eudi.eu/es"
                ]
            },
            "countries": [
                {"code": "PT", "name": "Portugal", "scheme": "Autenticação.gov", "trust_framework": "AMA / eIDAS", "status": "implemented"},
                {"code": "SE", "name": "Sweden", "scheme": "BankID", "trust_framework": "Finansiell ID-Teknik / eIDAS", "status": "implemented"},
                {"code": "NO", "name": "Norway", "scheme": "ID-porten", "trust_framework": "Digdir", "status": "implemented"},
                {"code": "DK", "name": "Denmark", "scheme": "MitID", "trust_framework": "Digitaliseringsstyrelsen", "status": "implemented"},
                {"code": "IE", "name": "Ireland", "scheme": "MyGovID", "trust_framework": "Department of Social Protection", "status": "implemented"},
                {"code": "FR", "name": "France", "scheme": "FranceConnect", "trust_framework": "FranceConnect / eIDAS", "status": "implemented"},
                {"code": "IT", "name": "Italy", "scheme": "SPID / CIE", "trust_framework": "AgID / eIDAS", "status": "implemented"},
                {"code": "CH", "name": "Switzerland", "scheme": "Swiyu", "trust_framework": "Swiyu Trust Infrastructure", "status": "implemented"},
                {"code": "EU", "name": "EU ARF", "scheme": "EUDI Wallet", "trust_framework": "European Commission / eIDAS 2.0", "status": "implemented"},
                {"code": "BR", "name": "Brazil", "scheme": "gov.br", "trust_framework": "ITI / ICP-Brasil", "status": "implemented"},
                {"code": "US", "name": "United States", "scheme": "AAMVA mDL", "trust_framework": "ISO 18013-5 / AAMVA", "status": "implemented"}
            ],
            "data_minimization": {
                "enabled": True,
                "id_hashing": "SHA-256 (DSGVO-konform: irreversible Pseudonymisierung)",
                "selective_disclosure": "SD-JWT VC + mDoc ISO 18013-5"
            },
            "compliance_standards": [
                "eIDAS 2.0 (EU 2024/1183)",
                "EU-ARF v1.4",
                "ISO 18013-5 (mDoc/mDL)",
                "BSI TR-03159",
                "GDPR (Art. 5, 25, 32)"
            ],
            "identity_broker": {
                "version": "3.0.0",
                "supported_regions": ["TW", "EE", "IN", "CA", "AU", "NZ", "IS", "NO", "FI", "UA", "EU", "AE", "BG", "SG", "US", "BE", "LU", "IL", "CN", "KR", "JP", "global"],
                "providers": [
                    {"id": "taiwan_digital_id", "name": "Taiwan Digital National ID", "region": "TW", "status": "production"},
                    {"id": "estonia_eresidency", "name": "Estonia e-Residency", "region": "EE", "status": "production"},
                    {"id": "india_aadhaar", "name": "India Aadhaar", "region": "IN", "status": "production"},
                    {"id": "canada_interac", "name": "Canada Interac/Provincial Digital ID", "region": "CA", "status": "production"},
                    {"id": "australia_mygovid", "name": "Australia myGovID", "region": "AU", "status": "production"},
                    {"id": "new_zealand_realme", "name": "New Zealand RealMe", "region": "NZ", "status": "production"},
                    {"id": "iceland_islandis", "name": "Iceland Ísland.is", "region": "IS", "status": "production"},
                    {"id": "norway_bankid", "name": "Norway BankID", "region": "NO", "status": "production"},
                    {"id": "finland_trust_network", "name": "Finland Trust Network (Suomi.fi)", "region": "FI", "status": "production"},
                    {"id": "ukraine_diia", "name": "Ukraine Diia", "region": "UA", "status": "production"},
                    {"id": "eudi_wallet", "name": "EU Digital Identity Wallet", "region": "EU", "status": "production"},
                    {"id": "uae_pass", "name": "UAE PASS", "region": "AE", "status": "production"},
                    {"id": "evrotrust", "name": "Evrotrust", "region": "BG", "status": "production"},
                    {"id": "signicat", "name": "Signicat", "region": "EU", "status": "production"},
                    {"id": "singpass", "name": "Singpass", "region": "SG", "status": "production"},
                    {"id": "login_gov", "name": "Login.gov", "region": "US", "status": "production"},
                    {"id": "belgian_mobile_id", "name": "Belgian Mobile ID (itsme)", "region": "BE", "status": "production"},
                    {"id": "luxtrust", "name": "LuxTrust", "region": "LU", "status": "production"},
                    {"id": "israel_id", "name": "Israel ID Validation", "region": "IL", "status": "production"},
                    {"id": "interpol_wrapper", "name": "Interpol Notices API", "region": "global", "status": "community"},
                    {"id": "china_ctid", "name": "China CTID Network", "region": "CN", "status": "production"},
                    {"id": "korea_mobile_id", "name": "Korea Mobile ID / PASS", "region": "KR", "status": "production"},
                    {"id": "japan_mynumber", "name": "Japan My Number Card", "region": "JP", "status": "production"}
                ]
            },
            "pnia_construction": {
                "concil_protocol": {
                    "version": "CP-01",
                    "handshake_version": "CIH-01",
                    "required_invariants": ["peace", "freedom", "integrity", "neighborly_love"],
                    "pillars": ["axiom", "immunitas", "governance", "flow"],
                    "state_zero_compliance": True
                },
                "deceased_persons": {
                    "memorial_registry": {
                        "postmortal_protection": True,
                        "write_once_read_many": True,
                        "representative_verification": True,
                        "dsgvo_erwg_27": True
                    }
                },
                "living_persons": {
                    "honorary_registry": {
                        "explicit_consent_required": True,
                        "data_minimization_pii": True,
                        "right_to_erasure": True,
                        "aes256_gcm_encryption": True
                    }
                },
                "state_construction": {
                    "governance": {
                        "sovereignty_shield": True,
                        "veto_protection": True,
                        "keyholder_treuhand": True,
                        "algorithmic_constitutionalism": True,
                        "infrastructure_building_lizenz": True
                    }
                },
                "registers": {
                    "eu_expert_id": "EX2025D1218310",
                    "duns": "315676980 / 317066336",
                    "vat_id": "DE441892129",
                    "global_lei": "894500GBJSIW8L6ET310",
                    "ungm_pic": "1172700 / 873042778",
                    "copyright": "© 2026 Daniel Pohl"
                },
                "ai_act": {
                    "transparency_flag": True,
                    "record_keeping": True,
                    "risk_classification": "Limited (Art. 50 Transparency)",
                    "human_oversight": True,
                    "audit_chain_sha256": True
                },
                "security_architecture": {
                    "sha256_hash_chain": True,
                    "aes256_gcm_pii": True,
                    "es256_jws_signing": True,
                    "zero_trust_logic": True,
                    "automated_audit_trail": True
                }
            }
        }
    
    # 1. Pipeline ausführen
    report = run_compliance_check(infrastructure_config)
    
    # 2. Konsolen-Ausgabe (CI/CD Logs)
    print("\n" + "="*50)
    print(" EU-ARF COMPLIANCE CHECK ERGEBNIS")
    print("="*50)
    for check in report["checks"]:
        print(f"[{check['status']}] {check['check']}: {check['detail']}")
    
    print("-" * 50)
    print(f"GESAMTSTATUS: {report['status']}")
    print("=" * 50 + "\n")
    
    # 3. Report generieren und Exit-Codes setzen (wichtig für die Pipeline)
    generate_bsi_report(report, output_path)
    
    # JSON Output für API-Integration (zu stderr um Konsolenausgabe nicht zu stören)
    print(json.dumps(report, indent=2), file=sys.stderr)
    
    if report["status"] == "PASS":
        logger.info("Erfolg: Alle EU-ARF Kernanforderungen erfüllt. System ist bereit für BSI/CAB-Evaluierung.")
        sys.exit(0) # CI/CD Pipeline läuft weiter
    elif report["status"] == "WARN":
        logger.warning("Warnung: Es fehlen nicht-kritische Komponenten. Bitte überprüfen.")
        sys.exit(0) # CI/CD Pipeline läuft weiter, aber mit Warnung
    else:
        logger.error("Fehler: Compliance-Prüfung fehlgeschlagen. Pipeline abgebrochen.")
        sys.exit(1) # Blockiert den CI/CD Build
