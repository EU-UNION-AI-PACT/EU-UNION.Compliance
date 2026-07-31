#!/usr/bin/env python3
"""
PNIA Backend API Test Suite - ITERATION 6 ONLY
Tests ONLY the NEW Iteration-6 backend features (Signed PDF + Custom Rules)
DO NOT rerun Iteration 5 tests (44 tests already passing)
"""
import os
import sys
import requests
import json
from typing import Dict, Any, Optional

# Base URL from frontend/.env
BASE_URL = "https://code-audit-fix-25.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_pass(test_name: str, details: str = ""):
    """Log a passing test"""
    msg = f"✅ {test_name}"
    if details:
        msg += f" - {details}"
    print(msg)
    test_results["passed"].append(test_name)

def log_fail(test_name: str, details: str):
    """Log a failing test"""
    msg = f"❌ {test_name} - {details}"
    print(msg)
    test_results["failed"].append(f"{test_name}: {details}")

def log_warning(test_name: str, details: str):
    """Log a warning"""
    msg = f"⚠️  {test_name} - {details}"
    print(msg)
    test_results["warnings"].append(f"{test_name}: {details}")

def make_request(
    method: str,
    endpoint: str,
    auth: bool = False,
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    bearer_token: Optional[str] = None
) -> tuple[int, Any, Any]:
    """Make HTTP request and return status code, response data, and headers object"""
    url = f"{API_BASE}{endpoint}"
    headers = {}
    if auth and bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=json_data, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            return 0, {"error": f"Unsupported method {method}"}, {}
        
        # Try to parse JSON, but also handle binary responses
        try:
            return resp.status_code, resp.json(), resp.headers
        except Exception:
            # For binary responses (like PDF)
            return resp.status_code, resp.content, resp.headers
    except Exception as e:
        return 0, {"error": str(e)}, {}

# Sample report for testing (from review request)
SAMPLE_REPORT = {
    "status": "FAIL",
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
        "rules_total": 9,
        "required_total": 7,
        "covered_required": 2,
        "missing_required": 5,
        "recommended_warnings": 2
    },
    "missing": [
        {
            "field": "legal_basis",
            "severity": "REQUIRED",
            "hint": "Art. 6"
        }
    ],
    "covered": [
        {
            "field": "controller",
            "severity": "REQUIRED"
        }
    ],
    "warnings": [],
    "evaluated_at": "2026-07-31T16:00Z",
    "engine": "PNIA"
}

# ============================================================================
# TEST GROUP A: POST /api/validate/report.sign
# ============================================================================
def test_group_a_report_sign():
    print("\n" + "="*80)
    print("TEST GROUP A: POST /api/validate/report.sign (ES256 JWS)")
    print("="*80)
    
    status, data, headers = make_request("POST", "/validate/report.sign", json_data={
        "report": SAMPLE_REPORT
    })
    
    if status != 200:
        log_fail("POST /api/validate/report.sign", f"Expected HTTP 200, got {status}")
        return
    
    # Check if response is JSON
    if isinstance(data, bytes):
        log_fail("POST /api/validate/report.sign", "Expected JSON response, got bytes")
        return
    
    # A.1: Check required keys
    required_keys = ["algorithm", "kid", "jws", "digest_sha256", "signed_at"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        log_fail("POST /api/validate/report.sign - required keys", f"Missing keys: {missing_keys}")
        return
    else:
        log_pass("POST /api/validate/report.sign - required keys", "All keys present")
    
    # A.2: algorithm == "ES256"
    if data.get("algorithm") == "ES256":
        log_pass("POST /api/validate/report.sign - algorithm", "algorithm=ES256")
    else:
        log_fail("POST /api/validate/report.sign - algorithm", f"Expected ES256, got {data.get('algorithm')}")
    
    # A.3: digest_sha256 is 64-char lowercase hex
    digest = data.get("digest_sha256", "")
    if len(digest) == 64 and all(c in "0123456789abcdef" for c in digest):
        log_pass("POST /api/validate/report.sign - digest_sha256", f"64-char hex: {digest[:16]}...")
    else:
        log_fail("POST /api/validate/report.sign - digest_sha256", f"Expected 64-char hex, got {len(digest)} chars: {digest}")
    
    # A.4: jws is a string with exactly 3 segments separated by dots
    jws = data.get("jws", "")
    if isinstance(jws, str):
        parts = jws.split(".")
        if len(parts) == 3:
            log_pass("POST /api/validate/report.sign - jws", f"3 segments: {len(parts[0])}.{len(parts[1])}.{len(parts[2])}")
        else:
            log_fail("POST /api/validate/report.sign - jws", f"Expected 3 segments, got {len(parts)}")
    else:
        log_fail("POST /api/validate/report.sign - jws", f"Expected string, got {type(jws)}")
    
    # A.5: kid is non-empty
    kid = data.get("kid", "")
    if kid:
        log_pass("POST /api/validate/report.sign - kid", f"kid={kid[:16]}...")
    else:
        log_fail("POST /api/validate/report.sign - kid", "kid is empty")
    
    # A.6: signed_at ends with "Z"
    signed_at = data.get("signed_at", "")
    if signed_at.endswith("Z"):
        log_pass("POST /api/validate/report.sign - signed_at", f"signed_at={signed_at}")
    else:
        log_fail("POST /api/validate/report.sign - signed_at", f"Expected to end with 'Z', got {signed_at}")

# ============================================================================
# TEST GROUP B: POST /api/validate/report.pdf
# ============================================================================
def test_group_b_report_pdf():
    print("\n" + "="*80)
    print("TEST GROUP B: POST /api/validate/report.pdf (Signed PDF)")
    print("="*80)
    
    status, data, headers = make_request("POST", "/validate/report.pdf", json_data={
        "report": SAMPLE_REPORT
    })
    
    # B.1: HTTP 200
    if status != 200:
        log_fail("POST /api/validate/report.pdf - status", f"Expected HTTP 200, got {status}")
        return
    else:
        log_pass("POST /api/validate/report.pdf - status", "HTTP 200")
    
    # B.2: content-type contains "application/pdf"
    content_type = headers.get("content-type", "").lower()
    if "application/pdf" in content_type:
        log_pass("POST /api/validate/report.pdf - content-type", f"content-type={content_type}")
    else:
        log_fail("POST /api/validate/report.pdf - content-type", f"Expected application/pdf, got {content_type}")
    
    # B.3: response body is bytes
    if not isinstance(data, bytes):
        log_fail("POST /api/validate/report.pdf - body type", f"Expected bytes, got {type(data)}")
        return
    
    # B.4: response body length > 2000
    if len(data) > 2000:
        log_pass("POST /api/validate/report.pdf - body length", f"length={len(data)} bytes")
    else:
        log_fail("POST /api/validate/report.pdf - body length", f"Expected > 2000 bytes, got {len(data)}")
    
    # B.5: response body starts with b"%PDF-1.4"
    if data.startswith(b"%PDF-1.4"):
        log_pass("POST /api/validate/report.pdf - PDF header", "starts with %PDF-1.4")
    else:
        log_fail("POST /api/validate/report.pdf - PDF header", f"Expected %PDF-1.4, got {data[:20]}")
    
    # B.6: response header "X-PNIA-Signature-Alg" == "ES256"
    sig_alg = headers.get("x-pnia-signature-alg", "")
    if sig_alg == "ES256":
        log_pass("POST /api/validate/report.pdf - X-PNIA-Signature-Alg", "ES256")
    else:
        log_fail("POST /api/validate/report.pdf - X-PNIA-Signature-Alg", f"Expected ES256, got {sig_alg}")
    
    # B.7: response header "X-PNIA-Signature-KID" is non-empty
    sig_kid = headers.get("x-pnia-signature-kid", "")
    if sig_kid:
        log_pass("POST /api/validate/report.pdf - X-PNIA-Signature-KID", f"kid={sig_kid[:16]}...")
    else:
        log_fail("POST /api/validate/report.pdf - X-PNIA-Signature-KID", "kid is empty")
    
    # B.8: response header "X-PNIA-Digest-SHA256" is 64-hex
    sig_digest = headers.get("x-pnia-digest-sha256", "")
    if len(sig_digest) == 64 and all(c in "0123456789abcdef" for c in sig_digest.lower()):
        log_pass("POST /api/validate/report.pdf - X-PNIA-Digest-SHA256", f"64-hex: {sig_digest[:16]}...")
    else:
        log_fail("POST /api/validate/report.pdf - X-PNIA-Digest-SHA256", f"Expected 64-hex, got {sig_digest}")

# ============================================================================
# TEST GROUP C: Custom rules auth guards (no Bearer sent)
# ============================================================================
def test_group_c_custom_rules_auth():
    print("\n" + "="*80)
    print("TEST GROUP C: Custom rules auth guards (no Bearer)")
    print("="*80)
    
    # C.1: POST /api/validate/custom-rules/GDPR (no Bearer) → 401 or 403
    status, data, headers = make_request("POST", "/validate/custom-rules/GDPR", json_data={
        "field": "dpia_reference",
        "hint": "Art. 35 DPIA",
        "severity": "REQUIRED"
    })
    if status in [401, 403]:
        log_pass("POST /api/validate/custom-rules/GDPR (no auth)", f"HTTP {status} (unauthenticated)")
    else:
        log_fail("POST /api/validate/custom-rules/GDPR (no auth)", f"Expected 401 or 403, got {status}")
    
    # C.2: DELETE /api/validate/custom-rules/nonexistent-id (no Bearer) → 401 or 403
    status, data, headers = make_request("DELETE", "/validate/custom-rules/nonexistent-id")
    if status in [401, 403]:
        log_pass("DELETE /api/validate/custom-rules/nonexistent-id (no auth)", f"HTTP {status} (unauthenticated)")
    else:
        log_fail("DELETE /api/validate/custom-rules/nonexistent-id (no auth)", f"Expected 401 or 403, got {status}")
    
    # C.3: GET /api/validate/custom-rules (no Bearer) → 401 or 403 (admin-scoped list)
    status, data, headers = make_request("GET", "/validate/custom-rules")
    if status in [401, 403]:
        log_pass("GET /api/validate/custom-rules (no auth)", f"HTTP {status} (admin-scoped)")
    else:
        log_fail("GET /api/validate/custom-rules (no auth)", f"Expected 401 or 403, got {status}")
    
    # C.4: GET /api/validate/custom-rules/GDPR (no Bearer) → 200 (public read)
    status, data, headers = make_request("GET", "/validate/custom-rules/GDPR")
    if status == 200:
        if isinstance(data, dict):
            required_keys = ["framework", "count", "rules"]
            missing_keys = [k for k in required_keys if k not in data]
            if missing_keys:
                log_fail("GET /api/validate/custom-rules/GDPR (public read) - keys", f"Missing keys: {missing_keys}")
            else:
                if isinstance(data.get("rules"), list):
                    log_pass("GET /api/validate/custom-rules/GDPR (public read)", 
                            f"HTTP 200, framework={data.get('framework')}, count={data.get('count')}, rules is list")
                else:
                    log_fail("GET /api/validate/custom-rules/GDPR (public read) - rules", 
                            f"Expected rules to be list, got {type(data.get('rules'))}")
        else:
            log_fail("GET /api/validate/custom-rules/GDPR (public read)", f"Expected JSON dict, got {type(data)}")
    else:
        log_fail("GET /api/validate/custom-rules/GDPR (public read)", f"Expected HTTP 200, got {status}")

# ============================================================================
# TEST GROUP D: Regression on POST /api/validate
# ============================================================================
def test_group_d_regression():
    print("\n" + "="*80)
    print("TEST GROUP D: Regression on POST /api/validate (custom-rules merge)")
    print("="*80)
    
    status, data, headers = make_request("POST", "/validate", json_data={
        "framework": "GDPR",
        "payload": {},
        "source": "pytest-iter6"
    })
    
    # D.1: HTTP 200
    if status != 200:
        log_fail("POST /api/validate (GDPR empty payload) - status", f"Expected HTTP 200, got {status}")
        return
    else:
        log_pass("POST /api/validate (GDPR empty payload) - status", "HTTP 200")
    
    # D.2: status == "FAIL"
    if data.get("status") == "FAIL":
        log_pass("POST /api/validate (GDPR empty payload) - status", "status=FAIL")
    else:
        log_fail("POST /api/validate (GDPR empty payload) - status", f"Expected FAIL, got {data.get('status')}")
    
    # D.3: counts.missing_required >= 5
    missing_required = data.get("counts", {}).get("missing_required", 0)
    if missing_required >= 5:
        log_pass("POST /api/validate (GDPR empty payload) - missing_required", f"missing_required={missing_required}")
    else:
        log_fail("POST /api/validate (GDPR empty payload) - missing_required", f"Expected >= 5, got {missing_required}")
    
    # D.4: No leaked payload values in the response
    # Check that covered/missing carry only field names, not values
    covered = data.get("covered", [])
    missing = data.get("missing", [])
    
    # Since payload is empty, we shouldn't see any actual values leaked
    # Just verify the structure is correct (field names only)
    leaked = False
    for item in covered + missing:
        if isinstance(item, dict):
            # Should only have field, severity, hint - no actual payload values
            if "value" in item or "data" in item:
                leaked = True
                break
    
    if not leaked:
        log_pass("POST /api/validate (GDPR empty payload) - no payload leak", "No payload values in response")
    else:
        log_fail("POST /api/validate (GDPR empty payload) - no payload leak", "Payload values leaked in response")

# ============================================================================
# MAIN
# ============================================================================
def main():
    print("\n" + "="*80)
    print("PNIA BACKEND API TEST SUITE - ITERATION 6 ONLY")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print("Testing: Signed PDF Report + Custom Rule Editor")
    print("="*80)
    
    # Run all test groups
    test_group_a_report_sign()
    test_group_b_report_pdf()
    test_group_c_custom_rules_auth()
    test_group_d_regression()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY - ITERATION 6")
    print("="*80)
    print(f"✅ PASSED: {len(test_results['passed'])}")
    print(f"❌ FAILED: {len(test_results['failed'])}")
    print(f"⚠️  WARNINGS: {len(test_results['warnings'])}")
    
    if test_results['failed']:
        print("\nFAILED TESTS:")
        for fail in test_results['failed']:
            print(f"  ❌ {fail}")
    
    if test_results['warnings']:
        print("\nWARNINGS:")
        for warn in test_results['warnings']:
            print(f"  ⚠️  {warn}")
    
    print("\n" + "="*80)
    
    # Exit with appropriate code
    sys.exit(0 if len(test_results['failed']) == 0 else 1)

if __name__ == "__main__":
    main()
