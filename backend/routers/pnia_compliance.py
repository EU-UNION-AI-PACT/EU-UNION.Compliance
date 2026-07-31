"""PNIA Compliance Router für EU-ARF / eIDAS 2.0 Validierung"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/pnia-compliance", tags=["PNIA Compliance"])

# Pfade
BACKEND_DIR = Path(__file__).parent.parent
SCRIPT_DIR = BACKEND_DIR / "scripts"
COMPLIANCE_SCRIPT = SCRIPT_DIR / "eu_arf_compliance_check.py"
# The compliance script writes the BSI report to the backend directory (CWD-relative).
# Use the same absolute path so the router always finds it regardless of CWD.
REPORT_FILE = BACKEND_DIR / "bsi_compliance_report.json"


class ComplianceRequest(BaseModel):
    """Modell für Compliance-Check Request"""
    infrastructure_config: dict[str, Any] | None = None


class ComplianceResponse(BaseModel):
    """Modell für Compliance-Check Response"""
    timestamp: str
    status: str
    checks: list[dict[str, Any]]
    summary: str


@router.get("/")
async def get_compliance_info():
    """Informationen über PNIA Compliance Prüfung"""
    return {
        "service": "PNIA EU-ARF Compliance Validator",
        "version": "1.0.0",
        "description": "Automatisierte Validierung gegen EU-ARF / eIDAS 2.0 Standards",
        "endpoints": {
            "check": "/pnia-compliance/check",
            "check_with_config": "/pnia-compliance/check-with-config",
            "bsi_report": "/pnia-compliance/bsi-report"
        }
    }


@router.post("/check", response_model=ComplianceResponse)
async def run_compliance_check(request: ComplianceRequest):
    """
    Führt einen EU-ARF Compliance Check durch

    Validiert die Infrastruktur-Konfiguration gegen EU-ARF Standards:
    - Level of Assurance (LoA)
    - ID-Hashing Algorithmen
    - Signatur-Standards
    - Protokolle (OIDC4VCI/VP, MDL)
    - Multi-Country Federation
    """
    try:
        # Wenn Konfiguration übergeben wurde, temporäre Datei erstellen
        config_file = None
        if request.infrastructure_config:
            config_file = SCRIPT_DIR / "temp_infra_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(request.infrastructure_config, f, indent=2)

        # Skript asynchron ausführen (nicht-blockierend für den Event-Loop)
        # Pass the report output path as the second argument so the script
        # writes to a known absolute location.
        cmd = [sys.executable, str(COMPLIANCE_SCRIPT)]
        if config_file:
            cmd.append(str(config_file))
            cmd.append(str(REPORT_FILE))
        # If no config file, the script uses its built-in test config
        # and writes to the default "bsi_compliance_report.json" in CWD.
        # NOTE: this is `asyncio.create_subprocess_exec` — NOT Python's builtin
        # `exec()`. It spawns a child process with a hard-coded argv list where:
        #   argv[0] = sys.executable (trusted)
        #   argv[1] = COMPLIANCE_SCRIPT (server-controlled path, not user input)
        #   argv[2..3] = config_file / REPORT_FILE (both server-controlled paths)
        # No shell is invoked, no user string is evaluated. This is safe.
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise HTTPException(status_code=504, detail="Compliance Check Timeout")

        stdout = stdout_b.decode() if stdout_b else ""
        stderr = stderr_b.decode() if stderr_b else ""

        # Temporäre Datei aufräumen
        if config_file and config_file.exists():
            config_file.unlink()

        # Ergebnis parsen
        if proc.returncode == 0:
            # BSI Report lesen
            if REPORT_FILE.exists():
                with open(REPORT_FILE, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)

                # Zusammenfassung erstellen
                passed = len([c for c in report_data["checks"] if c["status"] == "PASS"])
                failed = len([c for c in report_data["checks"] if c["status"] == "FAIL"])
                warned = len([c for c in report_data["checks"] if c["status"] == "WARN"])

                summary = f"Compliance Check abgeschlossen: {passed} bestanden, {failed} fehlgeschlagen, {warned} Warnungen."

                return ComplianceResponse(
                    timestamp=report_data["timestamp"],
                    status=report_data["status"],
                    checks=report_data["checks"],
                    summary=summary
                )
            else:
                # Wenn keine Datei existiert, versuchen wir den JSON-Output aus stderr zu parsen
                try:
                    report_data = json.loads(stderr)
                    passed = len([c for c in report_data["checks"] if c["status"] == "PASS"])
                    failed = len([c for c in report_data["checks"] if c["status"] == "FAIL"])
                    warned = len([c for c in report_data["checks"] if c["status"] == "WARN"])

                    summary = f"Compliance Check abgeschlossen: {passed} bestanden, {failed} fehlgeschlagen, {warned} Warnungen."

                    return ComplianceResponse(
                        timestamp=report_data["timestamp"],
                        status=report_data["status"],
                        checks=report_data["checks"],
                        summary=summary
                    )
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail="BSI Report konnte nicht generiert werden")
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Compliance Check fehlgeschlagen: {stderr}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interner Fehler: {str(e)}")


@router.get("/check", response_model=ComplianceResponse)
async def run_default_compliance_check():
    """
    Führt einen Compliance Check mit Standard-Konfiguration durch
    """
    return await run_compliance_check(ComplianceRequest(infrastructure_config=None))


@router.get("/bsi-report")
async def get_bsi_report():
    """
    Lädt den generierten BSI Compliance Report
    """
    if not REPORT_FILE.exists():
        raise HTTPException(status_code=404, detail="BSI Report nicht gefunden. Führen Sie zuerst einen Check durch.")

    with open(REPORT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


@router.post("/validate-config")
async def validate_config(infra_config: dict[str, Any]):
    """
    Validiert eine gegebene Infrastruktur-Konfiguration ohne Skript-Ausführung
    """
    from scripts.eu_arf_compliance_check import EXPECTED_STANDARDS

    results = {
        "valid": True,
        "issues": []
    }

    # LoA prüfen
    loa = infra_config.get("security", {}).get("level_of_assurance", "").lower()
    if loa != EXPECTED_STANDARDS["loa"]:
        results["valid"] = False
        results["issues"].append(f"LoA muss '{EXPECTED_STANDARDS['loa']}' sein, ist '{loa}'")

    # Hashing prüfen
    hashing = infra_config.get("cryptography", {}).get("id_hashing", "").lower()
    if hashing not in EXPECTED_STANDARDS["allowed_hashing_algorithms"]:
        results["valid"] = False
        results["issues"].append(f"Hashing-Algorithmus '{hashing}' nicht zugelassen")

    # Signatur prüfen
    signing = infra_config.get("cryptography", {}).get("signing", "").lower()
    if signing not in EXPECTED_STANDARDS["allowed_signing_algorithms"]:
        results["valid"] = False
        results["issues"].append(f"Signatur-Algorithmus '{signing}' nicht zugelassen")

    return results
