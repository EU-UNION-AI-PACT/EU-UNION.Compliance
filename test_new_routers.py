#!/usr/bin/env python3
"""
Test suite for NEW routers ONLY:
- Compliance Validator (/api/validate)
- Blueprint (/api/blueprint)

DO NOT run PNIA tests (credits-aware policy).
"""
import sys
import requests
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
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None
) -> tuple[int, Any]:
    """Make HTTP request and return status code and response data"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            resp = requests.post(url, json=json_data, timeout=30)
        else:
            return 0, {"error": f"Unsupported method {method}"}
        
        try:
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, {"text": resp.text}
    except Exception as e:
        return 0, {"error": str(e)}

# ============================================================================
# TEST GROUP A: STATELESS COMPLIANCE VALIDATOR
# ============================================================================
def test_compliance_validator():
    print("\n" + "="*80)
    print("TEST GROUP A: STATELESS COMPLIANCE VALIDATOR (/api/validate)")
    print("="*80)
    
    # (A) GET /api/validate/ → service info
    print("\n(A) Testing GET /api/validate/ - service info")
    status, data = make_request("GET", "/validate/")
    if status == 200:
        frameworks_total = data.get("frameworks_total", 0)
        specialised = data.get("specialised_validators", [])
        
        expected_specialised = ["GDPR", "DORA", "EU AI ACT", "DMA", "DSA", "NIS2", "EIDAS 2", "CRA"]
        
        if frameworks_total == 251:
            log_pass("(A) frameworks_total", f"251 frameworks")
        else:
            log_fail("(A) frameworks_total", f"Expected 251, got {frameworks_total}")
        
        missing = [s for s in expected_specialised if s not in specialised]
        if not missing:
            log_pass("(A) specialised_validators", f"All 8 expected validators present: {expected_specialised}")
        else:
            log_fail("(A) specialised_validators", f"Missing: {missing}, got: {specialised}")
    else:
        log_fail("(A) GET /api/validate/", f"status={status}, data={data}")
    
    # (B) GET /api/validate/frameworks?category=Privacy&q=gdpr
    print("\n(B) Testing GET /api/validate/frameworks?category=Privacy&q=gdpr")
    status, data = make_request("GET", "/validate/frameworks", params={"category": "Privacy", "q": "gdpr"})
    if status == 200:
        count = data.get("count", 0)
        frameworks = data.get("frameworks", [])
        
        if count >= 1:
            log_pass("(B) frameworks count", f"count={count}")
        else:
            log_fail("(B) frameworks count", f"Expected count >= 1, got {count}")
        
        gdpr_found = any(fw.get("code") == "GDPR" for fw in frameworks)
        if gdpr_found:
            log_pass("(B) GDPR in results", "GDPR framework found")
        else:
            log_fail("(B) GDPR in results", f"GDPR not found in frameworks: {[fw.get('code') for fw in frameworks]}")
    else:
        log_fail("(B) GET /api/validate/frameworks", f"status={status}")
    
    # (C) GET /api/validate/frameworks/GDPR
    print("\n(C) Testing GET /api/validate/frameworks/GDPR")
    status, data = make_request("GET", "/validate/frameworks/GDPR")
    if status == 200:
        code = data.get("code")
        category = data.get("category")
        
        if code == "GDPR":
            log_pass("(C) framework code", "code=GDPR")
        else:
            log_fail("(C) framework code", f"Expected GDPR, got {code}")
        
        if category == "Privacy":
            log_pass("(C) framework category", "category=Privacy")
        else:
            log_fail("(C) framework category", f"Expected Privacy, got {category}")
    else:
        log_fail("(C) GET /api/validate/frameworks/GDPR", f"status={status}, data={data}")
    
    # (D) GET /api/validate/rules/GDPR
    print("\n(D) Testing GET /api/validate/rules/GDPR")
    status, data = make_request("GET", "/validate/rules/GDPR")
    if status == 200:
        mode = data.get("mode")
        rules = data.get("rules", [])
        
        if mode == "SPECIALISED":
            log_pass("(D) rules mode", "mode=SPECIALISED")
        else:
            log_fail("(D) rules mode", f"Expected SPECIALISED, got {mode}")
        
        if len(rules) >= 7:
            log_pass("(D) rules count", f"count={len(rules)}")
            
            # Check rule structure
            if rules:
                sample = rules[0]
                has_field = "field" in sample
                has_severity = "severity" in sample
                has_hint = "hint" in sample
                
                if has_field and has_severity and has_hint:
                    log_pass("(D) rule structure", "field, severity, hint present")
                else:
                    log_fail("(D) rule structure", f"Missing fields in rule: {sample.keys()}")
        else:
            log_fail("(D) rules count", f"Expected >= 7, got {len(rules)}")
    else:
        log_fail("(D) GET /api/validate/rules/GDPR", f"status={status}")
    
    # (E) GET /api/validate/rules/PCI%20DSS
    print("\n(E) Testing GET /api/validate/rules/PCI DSS")
    status, data = make_request("GET", "/validate/rules/PCI DSS")
    if status == 200:
        mode = data.get("mode")
        rules = data.get("rules", [])
        
        if mode == "GENERIC_GOVERNANCE_SKELETON":
            log_pass("(E) rules mode", "mode=GENERIC_GOVERNANCE_SKELETON")
        else:
            log_fail("(E) rules mode", f"Expected GENERIC_GOVERNANCE_SKELETON, got {mode}")
        
        if len(rules) > 0:
            log_pass("(E) rules non-empty", f"count={len(rules)}")
        else:
            log_fail("(E) rules non-empty", "Expected non-empty rules")
    else:
        log_fail("(E) GET /api/validate/rules/PCI DSS", f"status={status}")
    
    # (F) POST /api/validate with GDPR partial payload
    print("\n(F) Testing POST /api/validate - GDPR partial payload (should FAIL)")
    status, data = make_request("POST", "/validate", json_data={
        "framework": "GDPR",
        "payload": {
            "controller": "acme",
            "processing_purpose": "auth"
        },
        "source": "pytest"
    })
    if status == 200:
        report_status = data.get("status")
        score = data.get("score", 100)
        counts = data.get("counts", {})
        missing_required = counts.get("missing_required", 0)
        
        if report_status == "FAIL":
            log_pass("(F) validation status", "status=FAIL")
        else:
            log_fail("(F) validation status", f"Expected FAIL, got {report_status}")
        
        if score < 100:
            log_pass("(F) validation score", f"score={score} < 100")
        else:
            log_fail("(F) validation score", f"Expected score < 100, got {score}")
        
        if missing_required >= 1:
            log_pass("(F) missing_required", f"missing_required={missing_required}")
        else:
            log_fail("(F) missing_required", f"Expected >= 1, got {missing_required}")
    else:
        log_fail("(F) POST /api/validate GDPR", f"status={status}, data={data}")
    
    # (G) POST /api/validate with DORA full payload
    print("\n(G) Testing POST /api/validate - DORA full payload (should PASS)")
    status, data = make_request("POST", "/validate", json_data={
        "framework": "DORA",
        "payload": {
            "ict_governance": "board",
            "ict_risk_register": "exists",
            "incident_classification": "tier1",
            "incident_reporting_timeline": "4h/1M",
            "digital_operational_resilience_testing": "annual",
            "third_party_ict_register": "yes",
            "critical_third_party_designation": "assessed",
            "business_continuity_plan": "RTO=4h"
        },
        "source": "pytest"
    })
    if status == 200:
        report_status = data.get("status")
        counts = data.get("counts", {})
        missing_required = counts.get("missing_required", 0)
        
        if report_status in ["PASS", "PASS_WITH_WARNINGS"]:
            log_pass("(G) validation status", f"status={report_status}")
        else:
            log_fail("(G) validation status", f"Expected PASS or PASS_WITH_WARNINGS, got {report_status}")
        
        if missing_required == 0:
            log_pass("(G) missing_required", "missing_required=0")
        else:
            log_fail("(G) missing_required", f"Expected 0, got {missing_required}")
    else:
        log_fail("(G) POST /api/validate DORA", f"status={status}, data={data}")
    
    # (H) POST /api/validate with unknown framework
    print("\n(H) Testing POST /api/validate - unknown framework")
    status, data = make_request("POST", "/validate", json_data={
        "framework": "DOES_NOT_EXIST",
        "payload": {},
        "source": "pytest"
    })
    if status == 200:
        report_status = data.get("status")
        if report_status == "UNKNOWN_FRAMEWORK":
            log_pass("(H) unknown framework", "status=UNKNOWN_FRAMEWORK")
        else:
            log_fail("(H) unknown framework", f"Expected UNKNOWN_FRAMEWORK, got {report_status}")
    else:
        log_fail("(H) POST /api/validate unknown", f"status={status}")
    
    # (I) POST /api/validate/batch
    print("\n(I) Testing POST /api/validate/batch - GDPR + DORA")
    status, data = make_request("POST", "/validate/batch", json_data={
        "frameworks": ["GDPR", "DORA"],
        "payload": {},
        "source": "pytest"
    })
    if status == 200:
        reports = data.get("reports", [])
        overall_status = data.get("overall_status")
        
        if len(reports) == 2:
            log_pass("(I) batch reports count", "reports.length=2")
        else:
            log_fail("(I) batch reports count", f"Expected 2, got {len(reports)}")
        
        if overall_status in ["FAIL", "PASS_WITH_WARNINGS", "PASS"]:
            log_pass("(I) batch overall_status", f"overall_status={overall_status}")
        else:
            log_fail("(I) batch overall_status", f"Unexpected status: {overall_status}")
    else:
        log_fail("(I) POST /api/validate/batch", f"status={status}")
    
    # (J) GET /api/validate/history
    print("\n(J) Testing GET /api/validate/history - verify no payload values leaked")
    status, data = make_request("GET", "/validate/history")
    if status == 200:
        events = data.get("events", [])
        count = data.get("count", 0)
        
        if count >= 2:
            log_pass("(J) history count", f"count={count} (>= 2 events from F, G, I)")
        else:
            log_fail("(J) history count", f"Expected >= 2, got {count}")
        
        # Check for payload value leaks
        leaked_values = []
        for event in events:
            event_str = str(event)
            # Check if sensitive values like "acme" appear in history
            if "acme" in event_str.lower():
                leaked_values.append("'acme' found in event")
        
        if not leaked_values:
            log_pass("(J) no payload leaks", "No payload values (like 'acme') found in history events")
        else:
            log_fail("(J) no payload leaks", f"Payload values leaked: {leaked_values}")
        
        # Verify events have expected summary fields
        if events:
            sample = events[0]
            expected_fields = ["framework", "status", "at", "source"]
            missing_fields = [f for f in expected_fields if f not in sample]
            
            if not missing_fields:
                log_pass("(J) event structure", f"Events have expected fields: {expected_fields}")
            else:
                log_fail("(J) event structure", f"Missing fields: {missing_fields}")
    else:
        log_fail("(J) GET /api/validate/history", f"status={status}")

# ============================================================================
# TEST GROUP K: BLAUPAUSE (BLUEPRINT)
# ============================================================================
def test_blueprint():
    print("\n" + "="*80)
    print("TEST GROUP K: BLAUPAUSE DER GESAMTARCHITEKTUR (/api/blueprint)")
    print("="*80)
    
    # (K1) GET /api/blueprint/ → counts
    print("\n(K1) Testing GET /api/blueprint/ - service info and counts")
    status, data = make_request("GET", "/blueprint/")
    if status == 200:
        counts = data.get("counts", {})
        meta = data.get("meta", {})
        
        expected_counts = {
            "layers": 5,
            "building_blocks": 10,
            "validation_stages": 6,
            "data_flows": 5,
            "regulatory_refs": 9
        }
        
        all_correct = True
        for key, expected_val in expected_counts.items():
            actual_val = counts.get(key, 0)
            if actual_val == expected_val:
                log_pass(f"(K1) counts.{key}", f"{key}={actual_val}")
            else:
                log_fail(f"(K1) counts.{key}", f"Expected {expected_val}, got {actual_val}")
                all_correct = False
        
        version = meta.get("version")
        as_of = meta.get("asOf", "")
        
        if version == "1.0":
            log_pass("(K1) meta.version", "version=1.0")
        else:
            log_fail("(K1) meta.version", f"Expected 1.0, got {version}")
        
        if "2026" in as_of:
            log_pass("(K1) meta.asOf", f"asOf contains 2026: {as_of}")
        else:
            log_fail("(K1) meta.asOf", f"Expected 2026 in asOf, got {as_of}")
    else:
        log_fail("(K1) GET /api/blueprint/", f"status={status}")
    
    # (K2) GET /api/blueprint/layers
    print("\n(K2) Testing GET /api/blueprint/layers")
    status, data = make_request("GET", "/blueprint/layers")
    if status == 200:
        count = data.get("count", 0)
        layers = data.get("layers", [])
        
        if count == 5:
            log_pass("(K2) layers count", "count=5")
        else:
            log_fail("(K2) layers count", f"Expected 5, got {count}")
        
        if layers and layers[0].get("level") == "Ebene 1":
            log_pass("(K2) first layer level", "level='Ebene 1'")
        else:
            log_fail("(K2) first layer level", f"Expected 'Ebene 1', got {layers[0].get('level') if layers else 'no layers'}")
    else:
        log_fail("(K2) GET /api/blueprint/layers", f"status={status}")
    
    # (K3) GET /api/blueprint/building-blocks
    print("\n(K3) Testing GET /api/blueprint/building-blocks")
    status, data = make_request("GET", "/blueprint/building-blocks")
    if status == 200:
        count = data.get("count", 0)
        blocks = data.get("building_blocks", [])
        
        if count == 10:
            log_pass("(K3) building_blocks count", "count=10")
        else:
            log_fail("(K3) building_blocks count", f"Expected 10, got {count}")
        
        if blocks and blocks[0].get("code") == "BB-01":
            log_pass("(K3) first block code", "code='BB-01'")
        else:
            log_fail("(K3) first block code", f"Expected 'BB-01', got {blocks[0].get('code') if blocks else 'no blocks'}")
    else:
        log_fail("(K3) GET /api/blueprint/building-blocks", f"status={status}")
    
    # (K4) GET /api/blueprint/validation-path
    print("\n(K4) Testing GET /api/blueprint/validation-path")
    status, data = make_request("GET", "/blueprint/validation-path")
    if status == 200:
        count = data.get("count", 0)
        stages = data.get("stages", [])
        
        if count == 6:
            log_pass("(K4) validation_path count", "count=6")
        else:
            log_fail("(K4) validation_path count", f"Expected 6, got {count}")
        
        if stages:
            all_start_with_stufe = all(s.get("stage", "").startswith("Stufe") for s in stages)
            if all_start_with_stufe:
                log_pass("(K4) stage names", "All stages start with 'Stufe'")
            else:
                log_fail("(K4) stage names", f"Not all stages start with 'Stufe': {[s.get('stage') for s in stages]}")
    else:
        log_fail("(K4) GET /api/blueprint/validation-path", f"status={status}")
    
    # (K5) GET /api/blueprint/data-flows
    print("\n(K5) Testing GET /api/blueprint/data-flows")
    status, data = make_request("GET", "/blueprint/data-flows")
    if status == 200:
        count = data.get("count", 0)
        
        if count == 5:
            log_pass("(K5) data_flows count", "count=5")
        else:
            log_fail("(K5) data_flows count", f"Expected 5, got {count}")
    else:
        log_fail("(K5) GET /api/blueprint/data-flows", f"status={status}")
    
    # (K6) GET /api/blueprint/regulatory-refs
    print("\n(K6) Testing GET /api/blueprint/regulatory-refs")
    status, data = make_request("GET", "/blueprint/regulatory-refs")
    if status == 200:
        count = data.get("count", 0)
        refs = data.get("refs", [])
        
        if count == 9:
            log_pass("(K6) regulatory_refs count", "count=9")
        else:
            log_fail("(K6) regulatory_refs count", f"Expected 9, got {count}")
        
        eeas_found = any(r.get("ref") == "EEAS" for r in refs)
        if eeas_found:
            log_pass("(K6) EEAS reference", "EEAS found in regulatory refs")
        else:
            log_fail("(K6) EEAS reference", f"EEAS not found in refs: {[r.get('ref') for r in refs]}")
    else:
        log_fail("(K6) GET /api/blueprint/regulatory-refs", f"status={status}")
    
    # (K7) GET /api/blueprint/full
    print("\n(K7) Testing GET /api/blueprint/full")
    status, data = make_request("GET", "/blueprint/full")
    if status == 200:
        expected_keys = ["meta", "layers", "building_blocks", "validation_path", "data_flows", "regulatory_refs"]
        
        all_present = True
        for key in expected_keys:
            if key in data and data[key]:
                log_pass(f"(K7) full.{key}", f"{key} present and non-empty")
            else:
                log_fail(f"(K7) full.{key}", f"{key} missing or empty")
                all_present = False
    else:
        log_fail("(K7) GET /api/blueprint/full", f"status={status}")

# ============================================================================
# MAIN
# ============================================================================
def main():
    print("\n" + "="*80)
    print("NEW ROUTERS TEST SUITE")
    print("Testing ONLY: Compliance Validator + Blueprint")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print("="*80)
    
    # Run test groups
    test_compliance_validator()
    test_blueprint()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
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
