"""PNIA Compliance Router für EU-ARF / eIDAS 2.0 Validierung"""
from __future__ import annotations

import asyncio
import json
import subprocess
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

# Timeout (seconds) for the child compliance-check script. Kept tight so a
# stuck child cannot pin the event loop worker thread.
_SUBPROCESS_TIMEOUT_SEC = 30


def _run_compliance_script_sync(argv: list[str]) -> subprocess.CompletedProcess[bytes]:
    """
    Synchronously spawn the compliance-check helper.

    SAFETY NOTES:
      * `argv` is a fully-formed argument list controlled entirely by the
        router (sys.executable + server-controlled paths). No user string
        is ever placed on the command line and no shell is invoked.
      * `shell=False` is enforced explicitly.
      * This is `subprocess.run`, NOT Python's builtin `exec()` — there is
        no dynamic code evaluation happening here.
    """
    return subprocess.run(  # noqa: S603  (argv is trusted, see docstring)
        argv,
        shell=False,
        check=False,
        capture_output=True,
        timeout=_SUBPROCESS_TIMEOUT_SEC,
    )


async def _run_compliance_script(argv: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Async wrapper — offloads the blocking child spawn to a worker thread."""
    return await asyncio.to_thread(_run_compliance_script_sync, argv)


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

        # Skript ausführen (nicht-blockierend für den Event-Loop — spawned in
        # a worker thread by _run_compliance_script). The argv list is fully
        # server-controlled and no shell is invoked.
        cmd = [sys.executable, str(COMPLIANCE_SCRIPT)]
        if config_file:
            cmd.append(str(config_file))
            cmd.append(str(REPORT_FILE))
        # If no config file, the script uses its built-in test config
        # and writes to the default "bsi_compliance_report.json" in CWD.
        try:
            completed = await _run_compliance_script(cmd)
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="Compliance Check Timeout")

        stdout = completed.stdout.decode() if completed.stdout else ""
        stderr = completed.stderr.decode() if completed.stderr else ""
        returncode = completed.returncode

        # Temporäre Datei aufräumen
        if config_file and config_file.exists():
            config_file.unlink()

        # Ergebnis parsen
        if returncode == 0:
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
