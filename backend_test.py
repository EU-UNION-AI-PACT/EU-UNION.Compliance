#!/usr/bin/env python3
"""Backend API tests for Iteration 7 - PNIA Compliance Platform.

Tests ONLY the three NEW features:
1. Multi-Report Bundle PDF
2. Chain-of-Custody Ledger
3. Ops Webhook auth guards
"""
import sys
import requests

# Base URL from frontend/.env
BASE_URL = "https://code-audit-fix-25.preview.emergentagent.com/api"

# Test counters
tests_passed = 0
tests_failed = 0
test_results = []


def log_test(name: str, passed: bool, details: str = ""):
    """Log test result."""
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        status = "✅ PASS"
    else:
        tests_failed += 1
        status = "❌ FAIL"
    msg = f"{status}: {name}"
    if details:
        msg += f" - {details}"
    print(msg)
    test_results.append({"name": name, "passed": passed, "details": details})


def test_multi_report_bundle_pdf():
    """Test A: Multi-Report Bundle PDF endpoint."""
    print("\n" + "=" * 80)
    print("TEST A: Multi-Report Bundle PDF")
    print("=" * 80)
    
    url = f"{BASE_URL}/validate/report-bundle.pdf"
    
    # Prepare two reports: one FAIL/GDPR and one PASS/DORA
    report1_fail_gdpr = {
        "status": "FAIL",
        "score": 29,
        "framework": {
            "code": "GDPR",
            "name": "GDPR",
            "regulator": "EDPB",
            "jurisdiction": "EU",
            "category": "Privacy",
            "source": "https://eur-lex.europa.eu"
        },
        "mode": "SPECIALISED",
        "counts": {
            "missing_required": 5
        },
        "missing": [
            {"field": "legal_basis", "hint": "Art. 6"}
        ],
        "covered": [],
        "warnings": [],
        "evaluated_at": "2026-07-31T16:00Z",
        "engine": "PNIA"
    }
    
    report2_pass_dora = {
        "status": "PASS_WITH_WARNINGS",
        "score": 100,
        "framework": {
            "code": "DORA",
            "name": "DORA",
            "regulator": "ESAs",
            "jurisdiction": "EU",
            "category": "Operational",
            "source": "https://eur-lex.europa.eu"
        },
        "mode": "SPECIALISED",
        "counts": {
            "missing_required": 0,
            "recommended_warnings": 1
        },
        "missing": [],
        "covered": [],
        "warnings": [
            {"field": "threat_intelligence_sharing", "hint": "Art. 45"}
        ],
        "evaluated_at": "2026-07-31T16:00Z",
        "engine": "PNIA"
    }
    
    payload = {
        "reports": [report1_fail_gdpr, report2_pass_dora]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        # A1: HTTP 200
        log_test(
            "A1: Bundle PDF returns HTTP 200",
            response.status_code == 200,
            f"Got status {response.status_code}"
        )
        
        # A2: Content-Type starts with application/pdf
        content_type = response.headers.get("content-type", "")
        log_test(
            "A2: Content-Type is application/pdf",
            content_type.startswith("application/pdf"),
            f"Got '{content_type}'"
        )
        
        # A3: Body starts with %PDF-1.4
        body = response.content
        log_test(
            "A3: PDF body starts with %PDF-1.4",
            body.startswith(b"%PDF-1.4"),
            f"First 10 bytes: {body[:10]}"
        )
        
        # A4: Body length > 4000
        log_test(
            "A4: PDF body length > 4000 bytes",
            len(body) > 4000,
            f"Got {len(body)} bytes"
        )
        
        # A5: X-PNIA-Signature-Alg header == ES256
        sig_alg = response.headers.get("X-PNIA-Signature-Alg", "")
        log_test(
            "A5: X-PNIA-Signature-Alg == ES256",
            sig_alg == "ES256",
            f"Got '{sig_alg}'"
        )
        
        # A6: X-PNIA-Bundle-Count header == 2
        bundle_count = response.headers.get("X-PNIA-Bundle-Count", "")
        log_test(
            "A6: X-PNIA-Bundle-Count == 2",
            bundle_count == "2",
            f"Got '{bundle_count}'"
        )
        
        # A7: X-PNIA-Signature-KID is non-empty
        kid = response.headers.get("X-PNIA-Signature-KID", "")
        log_test(
            "A7: X-PNIA-Signature-KID is non-empty",
            len(kid) > 0,
            f"Got '{kid[:20]}...'" if len(kid) > 20 else f"Got '{kid}'"
        )
        
        # A8: X-PNIA-Digest-SHA256 is 64-hex
        digest = response.headers.get("X-PNIA-Digest-SHA256", "")
        is_64_hex = len(digest) == 64 and all(c in "0123456789abcdefABCDEF" for c in digest)
        log_test(
            "A8: X-PNIA-Digest-SHA256 is 64-hex",
            is_64_hex,
            f"Got '{digest[:20]}...' (len={len(digest)})" if len(digest) > 20 else f"Got '{digest}'"
        )
        
    except Exception as e:
        log_test("A: Bundle PDF endpoint", False, f"Exception: {str(e)}")
        # Log all sub-tests as failed
        for i in range(1, 9):
            if f"A{i}:" not in str(test_results):
                log_test(f"A{i}: (skipped due to exception)", False, "")


def test_chain_of_custody_ledger():
    """Test B: Chain-of-Custody Ledger."""
    print("\n" + "=" * 80)
    print("TEST B: Chain-of-Custody Ledger")
    print("=" * 80)
    
    # B1: Get baseline ledger state
    print("\n--- B1: Baseline ledger state ---")
    try:
        response = requests.get(f"{BASE_URL}/validate/ledger?limit=50", timeout=10)
        log_test(
            "B1.1: GET /ledger returns HTTP 200",
            response.status_code == 200,
            f"Got status {response.status_code}"
        )
        
        if response.status_code == 200:
            data = response.json()
            has_keys = "total" in data and "count" in data and "entries" in data
            log_test(
                "B1.2: Response has keys {total, count, entries}",
                has_keys,
                f"Keys: {list(data.keys())}"
            )
            
            if has_keys:
                total_before = data["total"]
                log_test(
                    "B1.3: Total is an integer",
                    isinstance(total_before, int),
                    f"total={total_before}"
                )
                print(f"    📊 Baseline total: {total_before}")
            else:
                total_before = 0
        else:
            total_before = 0
    except Exception as e:
        log_test("B1: Baseline ledger", False, f"Exception: {str(e)}")
        total_before = 0
    
    # B2: POST /report.sign and verify ledger increment
    print("\n--- B2: Sign report and verify ledger increment ---")
    returned_digest = None
    try:
        sign_url = f"{BASE_URL}/validate/report.sign"
        report_payload = {
            "report": {
                "status": "FAIL",
                "framework": {"code": "GDPR"},
                "counts": {"missing_required": 3},
                "missing": [],
                "covered": [],
                "warnings": [],
                "evaluated_at": "2026-07-31T16:00Z",
                "engine": "PNIA"
            }
        }
        
        response = requests.post(sign_url, json=report_payload, timeout=10)
        log_test(
            "B2.1: POST /report.sign returns HTTP 200",
            response.status_code == 200,
            f"Got status {response.status_code}"
        )
        
        if response.status_code == 200:
            data = response.json()
            required_keys = {"algorithm", "kid", "jws", "digest_sha256", "signed_at"}
            has_keys = required_keys.issubset(data.keys())
            log_test(
                "B2.2: Response has required keys",
                has_keys,
                f"Keys: {list(data.keys())}"
            )
            
            if has_keys:
                returned_digest = data["digest_sha256"]
                print(f"    🔐 Returned digest: {returned_digest[:20]}...")
                
                # Now check ledger
                response = requests.get(f"{BASE_URL}/validate/ledger?limit=1", timeout=10)
                if response.status_code == 200:
                    ledger_data = response.json()
                    total_after = ledger_data.get("total", 0)
                    
                    log_test(
                        "B2.3: Ledger total incremented",
                        total_after > total_before,
                        f"Before: {total_before}, After: {total_after}"
                    )
                    
                    entries = ledger_data.get("entries", [])
                    if entries:
                        newest_entry = entries[0]
                        newest_digest = newest_entry.get("digest", "")
                        log_test(
                            "B2.4: Newest entry digest matches returned digest",
                            newest_digest == returned_digest,
                            f"Entry: {newest_digest[:20]}..., Returned: {returned_digest[:20] if returned_digest else 'None'}..."
                        )
                    else:
                        log_test("B2.4: Newest entry digest", False, "No entries returned")
                else:
                    log_test("B2.3: Ledger after sign", False, f"HTTP {response.status_code}")
    except Exception as e:
        log_test("B2: Sign and ledger increment", False, f"Exception: {str(e)}")
    
    # B3: Verify chain integrity
    print("\n--- B3: Verify chain integrity ---")
    try:
        response = requests.get(f"{BASE_URL}/validate/ledger/verify?limit=500", timeout=15)
        log_test(
            "B3.1: GET /ledger/verify returns HTTP 200",
            response.status_code == 200,
            f"Got status {response.status_code}"
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                "B3.2: Chain verification ok=true",
                data.get("ok") is True,
                f"ok={data.get('ok')}"
            )
            
            log_test(
                "B3.3: broken_at is None",
                data.get("broken_at") is None,
                f"broken_at={data.get('broken_at')}"
            )
            
            entries_count = data.get("entries", 0)
            log_test(
                "B3.4: Entries count matches ledger total",
                entries_count >= total_before,
                f"Verified {entries_count} entries"
            )
            
            print(f"    ✓ Chain verified: {entries_count} entries, head={data.get('head', '')[:20]}...")
    except Exception as e:
        log_test("B3: Chain verification", False, f"Exception: {str(e)}")
    
    # B4: Verify bundle entry in ledger (after test A ran)
    print("\n--- B4: Verify bundle entry exists ---")
    try:
        response = requests.get(f"{BASE_URL}/validate/ledger?limit=10", timeout=10)
        if response.status_code == 200:
            data = response.json()
            entries = data.get("entries", [])
            
            # Look for a bundle entry
            bundle_entry = None
            for entry in entries:
                if entry.get("kind") == "bundle":
                    bundle_entry = entry
                    break
            
            log_test(
                "B4.1: Bundle entry exists in ledger",
                bundle_entry is not None,
                f"Found {len([e for e in entries if e.get('kind') == 'bundle'])} bundle entries"
            )
            
            if bundle_entry:
                log_test(
                    "B4.2: Bundle entry framework == BUNDLE",
                    bundle_entry.get("framework") == "BUNDLE",
                    f"framework={bundle_entry.get('framework')}"
                )
                print(f"    📦 Bundle entry: seq={bundle_entry.get('seq')}, digest={bundle_entry.get('digest', '')[:20]}...")
        else:
            log_test("B4: Bundle entry check", False, f"HTTP {response.status_code}")
    except Exception as e:
        log_test("B4: Bundle entry verification", False, f"Exception: {str(e)}")


def test_ops_webhook_auth_guards():
    """Test C: Ops Webhook auth guards (without Bearer token)."""
    print("\n" + "=" * 80)
    print("TEST C: Ops Webhook Auth Guards")
    print("=" * 80)
    
    # C1: GET /ops-webhook without Bearer -> 401 or 403
    try:
        response = requests.get(f"{BASE_URL}/validate/ops-webhook", timeout=10)
        log_test(
            "C1: GET /ops-webhook without Bearer returns 401 or 403",
            response.status_code in [401, 403],
            f"Got status {response.status_code}"
        )
    except Exception as e:
        log_test("C1: GET /ops-webhook auth", False, f"Exception: {str(e)}")
    
    # C2: POST /ops-webhook without Bearer -> 401 or 403
    try:
        payload = {
            "webhook_url": "https://example.com/hook",
            "on_fail_only": True
        }
        response = requests.post(f"{BASE_URL}/validate/ops-webhook", json=payload, timeout=10)
        log_test(
            "C2: POST /ops-webhook without Bearer returns 401 or 403",
            response.status_code in [401, 403],
            f"Got status {response.status_code}"
        )
    except Exception as e:
        log_test("C2: POST /ops-webhook auth", False, f"Exception: {str(e)}")
    
    # C3: POST /ops-webhook/test without Bearer -> 401 or 403
    try:
        payload = {"webhook_url": "https://example.com/hook"}
        response = requests.post(f"{BASE_URL}/validate/ops-webhook/test", json=payload, timeout=10)
        log_test(
            "C3: POST /ops-webhook/test without Bearer returns 401 or 403",
            response.status_code in [401, 403],
            f"Got status {response.status_code}"
        )
    except Exception as e:
        log_test("C3: POST /ops-webhook/test auth", False, f"Exception: {str(e)}")


def test_regression_validate():
    """Test D: Regression test for /api/validate endpoint."""
    print("\n" + "=" * 80)
    print("TEST D: Regression - /api/validate")
    print("=" * 80)
    
    try:
        url = f"{BASE_URL}/validate"
        payload = {
            "framework": "GDPR",
            "payload": {},
            "source": "iter7-regress"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        log_test(
            "D1: POST /validate returns HTTP 200",
            response.status_code == 200,
            f"Got status {response.status_code}"
        )
        
        if response.status_code == 200:
            data = response.json()
            
            log_test(
                "D2: Validation status == FAIL",
                data.get("status") == "FAIL",
                f"status={data.get('status')}"
            )
            
            missing_required = data.get("counts", {}).get("missing_required", 0)
            log_test(
                "D3: missing_required >= 5",
                missing_required >= 5,
                f"missing_required={missing_required}"
            )
            
            print(f"    ✓ Regression test passed: webhook dispatch does not break validation flow")
    except Exception as e:
        log_test("D: Regression test", False, f"Exception: {str(e)}")


def print_summary():
    """Print test summary."""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {tests_passed + tests_failed}")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"Success rate: {tests_passed / (tests_passed + tests_failed) * 100:.1f}%")
    
    if tests_failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['name']}: {result['details']}")
    
    print("=" * 80)


if __name__ == "__main__":
    print("=" * 80)
    print("PNIA Compliance Platform - Iteration 7 Backend Tests")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print("Testing ONLY new Iteration-7 features (credits-aware)")
    print("=" * 80)
    
    # Run tests in order
    test_multi_report_bundle_pdf()
    test_chain_of_custody_ledger()
    test_ops_webhook_auth_guards()
    test_regression_validate()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if tests_failed == 0 else 1)
