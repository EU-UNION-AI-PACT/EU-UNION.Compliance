#!/usr/bin/env python3
"""
ITERATION 8 REGRESSION TEST — pnia-compliance refactor only
Targeted testing for subprocess.run migration (was asyncio.create_subprocess_exec)
"""
import os
import sys
import requests

# Read backend URL from frontend/.env
BACKEND_URL = None
env_path = "/app/frontend/.env"
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip()
                break

if not BACKEND_URL:
    print("❌ FATAL: Could not read REACT_APP_BACKEND_URL from /app/frontend/.env")
    sys.exit(1)

API_BASE = f"{BACKEND_URL}/api"
print(f"🔗 Testing against: {API_BASE}\n")

# Test counters
passed = 0
failed = 0
test_results = []

def test(name: str, fn):
    """Run a single test and track results"""
    global passed, failed
    try:
        fn()
        passed += 1
        test_results.append(f"✅ {name}")
        print(f"✅ {name}")
    except AssertionError as e:
        failed += 1
        test_results.append(f"❌ {name}: {e}")
        print(f"❌ {name}: {e}")
    except Exception as e:
        failed += 1
        test_results.append(f"❌ {name}: EXCEPTION {type(e).__name__}: {e}")
        print(f"❌ {name}: EXCEPTION {type(e).__name__}: {e}")

# ============================================================================
# A) GET /api/pnia-compliance/ → service info
# ============================================================================
def test_a_service_info():
    r = requests.get(f"{API_BASE}/pnia-compliance/", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    body = r.json()
    assert body.get("service") == "PNIA EU-ARF Compliance Validator", \
        f"Expected service='PNIA EU-ARF Compliance Validator', got {body.get('service')}"
    endpoints = body.get("endpoints", {})
    assert endpoints.get("bsi_report") == "/pnia-compliance/bsi-report", \
        f"Expected bsi_report='/pnia-compliance/bsi-report', got {endpoints.get('bsi_report')}"

test("A) GET /api/pnia-compliance/ returns service info", test_a_service_info)

# ============================================================================
# B) GET /api/pnia-compliance/bsi-report → BSI report with checks
# ============================================================================
def test_b_bsi_report():
    r = requests.get(f"{API_BASE}/pnia-compliance/bsi-report", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    body = r.json()
    
    # Check status is one of the expected values
    status = body.get("status")
    assert status in ["PASS", "WARN", "FAIL"], \
        f"Expected status in ['PASS', 'WARN', 'FAIL'], got {status}"
    
    # Check checks is a non-empty list
    checks = body.get("checks")
    assert isinstance(checks, list), f"Expected checks to be a list, got {type(checks)}"
    assert len(checks) > 0, f"Expected non-empty checks list, got {len(checks)} items"
    
    # Check each check has required keys
    for i, check in enumerate(checks):
        assert "check" in check, f"Check {i} missing 'check' key"
        assert "status" in check, f"Check {i} missing 'status' key"
        assert "detail" in check, f"Check {i} missing 'detail' key"
    
    # Check at least one check has status "PASS"
    pass_count = sum(1 for c in checks if c.get("status") == "PASS")
    assert pass_count > 0, f"Expected at least one check with status='PASS', got {pass_count}"

test("B) GET /api/pnia-compliance/bsi-report returns valid report", test_b_bsi_report)

# ============================================================================
# C) POST /api/pnia-compliance/check with body {} → compliance response
# ============================================================================
def test_c_post_check():
    r = requests.post(f"{API_BASE}/pnia-compliance/check", json={}, timeout=35)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    body = r.json()
    
    # Check required keys
    assert "timestamp" in body, "Missing 'timestamp' key"
    assert "status" in body, "Missing 'status' key"
    assert "checks" in body, "Missing 'checks' key"
    assert "summary" in body, "Missing 'summary' key"
    
    # Check status is valid
    status = body.get("status")
    assert status in ["PASS", "WARN", "FAIL"], \
        f"Expected status in ['PASS', 'WARN', 'FAIL'], got {status}"
    
    # Check checks is a list with at least 4 items
    checks = body.get("checks")
    assert isinstance(checks, list), f"Expected checks to be a list, got {type(checks)}"
    assert len(checks) >= 4, f"Expected at least 4 checks, got {len(checks)}"
    
    # Check summary is a non-empty string in German
    summary = body.get("summary")
    assert isinstance(summary, str), f"Expected summary to be a string, got {type(summary)}"
    assert len(summary) > 0, f"Expected non-empty summary, got empty string"
    # Check for German words (basic check)
    german_indicators = ["abgeschlossen", "bestanden", "fehlgeschlagen", "Warnungen"]
    has_german = any(word in summary for word in german_indicators)
    assert has_german, f"Expected German summary, got: {summary}"
    
    # Check timestamp is valid ISO-8601
    timestamp = body.get("timestamp")
    assert isinstance(timestamp, str), f"Expected timestamp to be a string, got {type(timestamp)}"
    assert "T" in timestamp, f"Expected ISO-8601 timestamp with 'T', got {timestamp}"

test("C) POST /api/pnia-compliance/check returns compliance response", test_c_post_check)

# ============================================================================
# D) GET /api/identity-broker/providers and /health → sanity checks
# ============================================================================
def test_d1_identity_providers():
    r = requests.get(f"{API_BASE}/identity-broker/providers", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    body = r.json()
    
    # Check we have at least 20 providers
    providers = body if isinstance(body, list) else body.get("providers", [])
    assert len(providers) >= 20, f"Expected at least 20 providers, got {len(providers)}"

test("D1) GET /api/identity-broker/providers returns >= 20 providers", test_d1_identity_providers)

def test_d2_identity_health():
    r = requests.get(f"{API_BASE}/identity-broker/health", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    body = r.json()
    
    # Check status is "healthy"
    status = body.get("status")
    assert status == "healthy", f"Expected status='healthy', got {status}"

test("D2) GET /api/identity-broker/health returns status=healthy", test_d2_identity_health)

# ============================================================================
# Additional sanity: GET /api/health → operational with database
# ============================================================================
def test_additional_health():
    r = requests.get(f"{API_BASE}/health", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    body = r.json()
    
    # Check status is "operational"
    status = body.get("status")
    assert status == "operational", f"Expected status='operational', got {status}"
    
    # Check database is true
    database = body.get("database")
    assert database is True, f"Expected database=true, got {database}"

test("Additional) GET /api/health returns operational with database=true", test_additional_health)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print(f"ITERATION 8 REGRESSION TEST RESULTS")
print("="*80)
print(f"✅ PASSED: {passed}")
print(f"❌ FAILED: {failed}")
print(f"📊 TOTAL:  {passed + failed}")
print("="*80)

if failed > 0:
    print("\n❌ FAILED TESTS:")
    for result in test_results:
        if result.startswith("❌"):
            print(f"  {result}")
    sys.exit(1)
else:
    print("\n✅ ALL TESTS PASSED - pnia-compliance refactor is regression-safe")
    sys.exit(0)
