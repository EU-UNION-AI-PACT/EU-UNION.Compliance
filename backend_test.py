#!/usr/bin/env python3
"""
PNIA Backend API Test Suite
Tests ONLY the new PNIA endpoints (Registry, Concil, Compliance, Identity Broker)
"""
import os
import sys
import requests
import json
from typing import Dict, Any, Optional

# Base URL from frontend/.env
BASE_URL = "https://honor-registry-ai.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Bearer token from test_credentials.md
BEARER_TOKEN = "pnia-test-session-token-fixed-001"

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
    params: Optional[Dict] = None
) -> tuple[int, Any]:
    """Make HTTP request and return status code and response data"""
    url = f"{API_BASE}{endpoint}"
    headers = {}
    if auth:
        headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=json_data, timeout=30)
        else:
            return 0, {"error": f"Unsupported method {method}"}
        
        try:
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, {"text": resp.text}
    except Exception as e:
        return 0, {"error": str(e)}

# ============================================================================
# TEST GROUP 1: PNIA Registry — PUBLIC (no auth)
# ============================================================================
def test_group_1_public_registry():
    print("\n" + "="*80)
    print("TEST GROUP 1: PNIA Registry — PUBLIC endpoints (no auth)")
    print("="*80)
    
    # 1.1 GET /api/pnia/registry/ → service info
    status, data = make_request("GET", "/pnia/registry/")
    if status == 200 and "service" in data and "compliance" in data:
        log_pass("GET /pnia/registry/", f"service={data.get('service')}")
    else:
        log_fail("GET /pnia/registry/", f"status={status}, data={data}")
    
    # 1.2 GET /api/pnia/registry/plaques → count should be 17
    status, data = make_request("GET", "/pnia/registry/plaques")
    if status == 200:
        count = data.get("count", 0)
        plaques = data.get("plaques", [])
        if count == 17 and len(plaques) == 17:
            log_pass("GET /pnia/registry/plaques", f"count={count}")
            
            # Check plaque structure - should have content_payload, no raw PII
            if plaques:
                sample = plaques[0]
                has_content = "content_payload" in sample
                has_ai_flag = "ai_generated_content" in sample
                has_risk = "risk_classification" in sample
                no_encrypted = "encrypted_data_record" not in sample
                
                if has_content and has_ai_flag and has_risk and no_encrypted:
                    log_pass("Plaque structure", "content_payload present, no raw PII leak")
                else:
                    log_fail("Plaque structure", f"Missing fields or PII leak: {sample.keys()}")
        else:
            log_fail("GET /pnia/registry/plaques", f"Expected count=17, got {count}, len={len(plaques)}")
    else:
        log_fail("GET /pnia/registry/plaques", f"status={status}, data={data}")
    
    # 1.3 GET /api/pnia/registry/plaques?type=MEMORIAL_BOARD → 16
    status, data = make_request("GET", "/pnia/registry/plaques", params={"type": "MEMORIAL_BOARD"})
    if status == 200:
        count = data.get("count", 0)
        if count == 16:
            log_pass("GET /pnia/registry/plaques?type=MEMORIAL_BOARD", f"count={count}")
        else:
            log_fail("GET /pnia/registry/plaques?type=MEMORIAL_BOARD", f"Expected 16, got {count}")
    else:
        log_fail("GET /pnia/registry/plaques?type=MEMORIAL_BOARD", f"status={status}")
    
    # 1.4 GET /api/pnia/registry/plaques?type=HONORARY_PLACE → 1
    status, data = make_request("GET", "/pnia/registry/plaques", params={"type": "HONORARY_PLACE"})
    if status == 200:
        count = data.get("count", 0)
        if count == 1:
            log_pass("GET /pnia/registry/plaques?type=HONORARY_PLACE", f"count={count}")
        else:
            log_fail("GET /pnia/registry/plaques?type=HONORARY_PLACE", f"Expected 1, got {count}")
    else:
        log_fail("GET /pnia/registry/plaques?type=HONORARY_PLACE", f"status={status}")
    
    # 1.5 GET /api/pnia/registry/plaques/{id} for a known id
    # Get first plaque id from previous call
    status, data = make_request("GET", "/pnia/registry/plaques")
    if status == 200 and data.get("plaques"):
        plaque_id = data["plaques"][0].get("id")
        status2, data2 = make_request("GET", f"/pnia/registry/plaques/{plaque_id}")
        if status2 == 200 and data2.get("id") == plaque_id:
            log_pass(f"GET /pnia/registry/plaques/{plaque_id}", "plaque retrieved")
        else:
            log_fail(f"GET /pnia/registry/plaques/{plaque_id}", f"status={status2}")
    
    # 1.6 GET /api/pnia/registry/compliance
    status, data = make_request("GET", "/pnia/registry/compliance")
    if status == 200:
        plaques_data = data.get("plaques", {})
        dsgvo_data = data.get("dsgvo", {})
        ai_act_data = data.get("ai_act", {})
        
        memorial_boards = plaques_data.get("memorial_boards", 0)
        honorary_places = plaques_data.get("honorary_places", 0)
        pii_encryption = dsgvo_data.get("pii_encryption", "")
        audit_valid = ai_act_data.get("audit_chain_valid", False)
        
        checks = []
        if memorial_boards == 16:
            checks.append("memorial_boards=16")
        else:
            log_fail("Compliance memorial_boards", f"Expected 16, got {memorial_boards}")
        
        if honorary_places == 1:
            checks.append("honorary_places=1")
        else:
            log_fail("Compliance honorary_places", f"Expected 1, got {honorary_places}")
        
        if pii_encryption == "AES-256-GCM":
            checks.append("pii_encryption=AES-256-GCM")
        else:
            log_fail("Compliance pii_encryption", f"Expected AES-256-GCM, got {pii_encryption}")
        
        if audit_valid:
            checks.append("audit_chain_valid=true")
        else:
            log_fail("Compliance audit_chain_valid", f"Expected true, got {audit_valid}")
        
        if len(checks) == 4:
            log_pass("GET /pnia/registry/compliance", ", ".join(checks))
    else:
        log_fail("GET /pnia/registry/compliance", f"status={status}, data={data}")
    
    # 1.7 GET /api/pnia/registry/ai-audit
    status, data = make_request("GET", "/pnia/registry/ai-audit")
    if status == 200 and "entries" in data:
        log_pass("GET /pnia/registry/ai-audit", f"count={data.get('count', 0)}")
    else:
        log_fail("GET /pnia/registry/ai-audit", f"status={status}")
    
    # 1.8 GET /api/pnia/registry/ai-audit/verify
    status, data = make_request("GET", "/pnia/registry/ai-audit/verify")
    if status == 200 and data.get("valid") == True:
        log_pass("GET /pnia/registry/ai-audit/verify", "valid=true")
    else:
        log_fail("GET /pnia/registry/ai-audit/verify", f"status={status}, valid={data.get('valid')}")

# ============================================================================
# TEST GROUP 2: PNIA Registry — AUTH enforcement
# ============================================================================
def test_group_2_auth_enforcement():
    print("\n" + "="*80)
    print("TEST GROUP 2: PNIA Registry — AUTH enforcement (401 without Bearer)")
    print("="*80)
    
    # 2.1 POST /api/pnia/registry/individuals WITHOUT Bearer → 401
    status, data = make_request("POST", "/pnia/registry/individuals", auth=False, json_data={
        "status": "LIVING",
        "given_name": "Test",
        "family_name": "User",
        "nationality": "DE"
    })
    if status == 401:
        log_pass("POST /pnia/registry/individuals (no auth)", "401 as expected")
    else:
        log_fail("POST /pnia/registry/individuals (no auth)", f"Expected 401, got {status}")
    
    # 2.2 POST /api/pnia/registry/plaques WITHOUT Bearer → 401
    status, data = make_request("POST", "/pnia/registry/plaques", auth=False, json_data={
        "individual_id": "test",
        "type": "HONORARY_PLACE",
        "display_name": "Test"
    })
    if status == 401:
        log_pass("POST /pnia/registry/plaques (no auth)", "401 as expected")
    else:
        log_fail("POST /pnia/registry/plaques (no auth)", f"Expected 401, got {status}")

# ============================================================================
# TEST GROUP 3: PNIA Registry — FULL COMPLIANCE FLOW (with Bearer)
# ============================================================================
def test_group_3_compliance_flow():
    print("\n" + "="*80)
    print("TEST GROUP 3: PNIA Registry — FULL COMPLIANCE FLOW (with Bearer)")
    print("="*80)
    
    # 3.1 Create LIVING individual
    status, data = make_request("POST", "/pnia/registry/individuals", auth=True, json_data={
        "status": "LIVING",
        "given_name": "Maria",
        "family_name": "Schmidt",
        "birth_place": "Berlin",
        "nationality": "DE"
    })
    if status == 200 and "id" in data and "system_id" in data:
        individual_id = data["id"]
        system_id = data["system_id"]
        log_pass("POST /pnia/registry/individuals (LIVING)", f"id={individual_id}")
    else:
        log_fail("POST /pnia/registry/individuals (LIVING)", f"status={status}, data={data}")
        return  # Can't continue without individual_id
    
    # 3.2 Try to create plaque WITHOUT consent → should 403
    status, data = make_request("POST", "/pnia/registry/plaques", auth=True, json_data={
        "individual_id": individual_id,
        "type": "HONORARY_PLACE",
        "display_name": "Maria Schmidt",
        "role": "Test Role",
        "institution": "Test Institution"
    })
    if status == 403:
        log_pass("POST /pnia/registry/plaques (no consent)", "403 as expected (DSGVO Art.6/7)")
    else:
        log_fail("POST /pnia/registry/plaques (no consent)", f"Expected 403, got {status}")
    
    # 3.3 Create consent
    status, data = make_request("POST", "/pnia/registry/consents", auth=True, json_data={
        "individual_id": individual_id
    })
    if status == 200 and data.get("status") == "GRANTED":
        consent_id = data.get("id")
        log_pass("POST /pnia/registry/consents", f"status=GRANTED, id={consent_id}")
    else:
        log_fail("POST /pnia/registry/consents", f"status={status}, data={data}")
        return
    
    # 3.4 Create plaque WITH consent → should 200
    status, data = make_request("POST", "/pnia/registry/plaques", auth=True, json_data={
        "individual_id": individual_id,
        "type": "HONORARY_PLACE",
        "display_name": "Maria Schmidt",
        "role": "Community Leader",
        "institution": "Berlin Community Center"
    })
    if status == 200:
        plaque_id = data.get("id")
        is_active = data.get("is_active")
        ai_generated = data.get("ai_generated_content")
        risk = data.get("risk_classification")
        
        if is_active and ai_generated == False and risk == "MINIMAL_RISK":
            log_pass("POST /pnia/registry/plaques (with consent)", 
                    f"id={plaque_id}, is_active=true, ai_generated=false, risk=MINIMAL_RISK")
        else:
            log_fail("POST /pnia/registry/plaques (with consent)", 
                    f"Unexpected values: is_active={is_active}, ai_generated={ai_generated}, risk={risk}")
    else:
        log_fail("POST /pnia/registry/plaques (with consent)", f"status={status}, data={data}")
        return
    
    # 3.5 GET individual (with Bearer) → should return decrypted PII
    status, data = make_request("GET", f"/pnia/registry/individuals/{individual_id}", auth=True)
    if status == 200:
        pii = data.get("pii")
        erased = data.get("erased")
        if pii and pii.get("given_name") == "Maria" and not erased:
            log_pass(f"GET /pnia/registry/individuals/{individual_id}", 
                    f"PII decrypted: given_name={pii.get('given_name')}, erased=false")
        else:
            log_fail(f"GET /pnia/registry/individuals/{individual_id}", 
                    f"PII not decrypted or erased: pii={pii}, erased={erased}")
    else:
        log_fail(f"GET /pnia/registry/individuals/{individual_id}", f"status={status}")
    
    # 3.6 Revoke consent (DSGVO Art.17) → crypto-shred
    status, data = make_request("POST", f"/pnia/registry/consents/{individual_id}/revoke", auth=True)
    if status == 200:
        revoked = data.get("revoked")
        erased = data.get("erased")
        deactivated = data.get("deactivated_plaques", 0)
        
        if revoked and erased and deactivated >= 1:
            log_pass(f"POST /pnia/registry/consents/{individual_id}/revoke", 
                    f"revoked=true, erased=true, deactivated_plaques={deactivated}")
        else:
            log_fail(f"POST /pnia/registry/consents/{individual_id}/revoke", 
                    f"Unexpected: revoked={revoked}, erased={erased}, deactivated={deactivated}")
    else:
        log_fail(f"POST /pnia/registry/consents/{individual_id}/revoke", f"status={status}")
    
    # 3.7 GET individual again → should show erased=true, pii=null
    status, data = make_request("GET", f"/pnia/registry/individuals/{individual_id}", auth=True)
    if status == 200:
        erased = data.get("erased")
        pii = data.get("pii")
        if erased and pii is None:
            log_pass(f"GET /pnia/registry/individuals/{individual_id} (after revoke)", 
                    "erased=true, pii=null (crypto-shred verified)")
        else:
            log_fail(f"GET /pnia/registry/individuals/{individual_id} (after revoke)", 
                    f"Expected erased=true, pii=null, got erased={erased}, pii={pii}")
    else:
        log_fail(f"GET /pnia/registry/individuals/{individual_id} (after revoke)", f"status={status}")
    
    # 3.8 Type/status mismatch check: LIVING + MEMORIAL_BOARD → 422
    status, data = make_request("POST", "/pnia/registry/individuals", auth=True, json_data={
        "status": "LIVING",
        "given_name": "Hans",
        "family_name": "Mueller",
        "nationality": "DE"
    })
    if status == 200:
        living_id = data["id"]
        # Create consent first
        make_request("POST", "/pnia/registry/consents", auth=True, json_data={
            "individual_id": living_id
        })
        # Try to create MEMORIAL_BOARD for LIVING → should 422
        status2, data2 = make_request("POST", "/pnia/registry/plaques", auth=True, json_data={
            "individual_id": living_id,
            "type": "MEMORIAL_BOARD",
            "display_name": "Hans Mueller"
        })
        if status2 == 422:
            log_pass("Type/status mismatch (LIVING + MEMORIAL_BOARD)", "422 as expected")
        else:
            log_fail("Type/status mismatch (LIVING + MEMORIAL_BOARD)", f"Expected 422, got {status2}")

# ============================================================================
# TEST GROUP 4: PNIA Registry — AI generation (with Bearer) — RUN ONLY ONCE
# ============================================================================
def test_group_4_ai_generation():
    print("\n" + "="*80)
    print("TEST GROUP 4: PNIA Registry — AI generation (RUN ONLY ONCE - uses real LLM credits)")
    print("="*80)
    
    # Create a fresh LIVING individual + consent + HONORARY_PLACE plaque (unlocked)
    status, data = make_request("POST", "/pnia/registry/individuals", auth=True, json_data={
        "status": "LIVING",
        "given_name": "Friedrich",
        "family_name": "Weber",
        "birth_place": "München",
        "nationality": "DE"
    })
    if status != 200:
        log_fail("AI test setup: create individual", f"status={status}")
        return
    
    individual_id = data["id"]
    
    # Create consent
    status, data = make_request("POST", "/pnia/registry/consents", auth=True, json_data={
        "individual_id": individual_id
    })
    if status != 200:
        log_fail("AI test setup: create consent", f"status={status}")
        return
    
    # Create HONORARY_PLACE plaque (unlocked by default)
    status, data = make_request("POST", "/pnia/registry/plaques", auth=True, json_data={
        "individual_id": individual_id,
        "type": "HONORARY_PLACE",
        "display_name": "Friedrich Weber",
        "role": "Stadtrat",
        "institution": "Stadt München"
    })
    if status != 200:
        log_fail("AI test setup: create plaque", f"status={status}")
        return
    
    plaque_id = data["id"]
    log_pass("AI test setup", f"Created unlocked plaque {plaque_id}")
    
    # 4.1 POST /api/pnia/registry/plaques/{id}/generate-tribute
    status, data = make_request("POST", f"/pnia/registry/plaques/{plaque_id}/generate-tribute", 
                               auth=True, json_data={
        "language": "Deutsch",
        "tone": "würdevoll und sachlich"
    })
    if status == 200:
        tribute_text = data.get("tribute_text", "")
        ai_generated = data.get("ai_generated_content")
        risk = data.get("risk_classification")
        audit = data.get("audit", {})
        audit_hash = audit.get("hash", "")
        
        if tribute_text and ai_generated and risk == "LIMITED_RISK_TRANSPARENCY" and audit_hash:
            log_pass(f"POST /pnia/registry/plaques/{plaque_id}/generate-tribute", 
                    f"tribute_text={len(tribute_text)} chars, ai_generated=true, risk=LIMITED_RISK_TRANSPARENCY, audit_hash={audit_hash[:16]}...")
        else:
            log_fail(f"POST /pnia/registry/plaques/{plaque_id}/generate-tribute", 
                    f"Missing fields: tribute_text={bool(tribute_text)}, ai_generated={ai_generated}, risk={risk}, audit_hash={bool(audit_hash)}")
    else:
        log_fail(f"POST /pnia/registry/plaques/{plaque_id}/generate-tribute", f"status={status}, data={data}")
        return
    
    # 4.2 Verify audit chain still valid
    status, data = make_request("GET", "/pnia/registry/ai-audit/verify")
    if status == 200 and data.get("valid") == True:
        log_pass("GET /pnia/registry/ai-audit/verify (after AI generation)", "valid=true")
    else:
        log_fail("GET /pnia/registry/ai-audit/verify (after AI generation)", f"valid={data.get('valid')}")
    
    # 4.3 Lock the plaque
    status, data = make_request("POST", f"/pnia/registry/plaques/{plaque_id}/lock", auth=True)
    if status == 200 and data.get("locked"):
        log_pass(f"POST /pnia/registry/plaques/{plaque_id}/lock", "locked=true")
    else:
        log_fail(f"POST /pnia/registry/plaques/{plaque_id}/lock", f"status={status}")
    
    # 4.4 Try generate-tribute on LOCKED plaque → should 409
    status, data = make_request("POST", f"/pnia/registry/plaques/{plaque_id}/generate-tribute", 
                               auth=True, json_data={
        "language": "English"
    })
    if status == 409:
        log_pass(f"POST /pnia/registry/plaques/{plaque_id}/generate-tribute (locked)", "409 as expected")
    else:
        log_fail(f"POST /pnia/registry/plaques/{plaque_id}/generate-tribute (locked)", f"Expected 409, got {status}")

# ============================================================================
# TEST GROUP 5: PNIA Concil (CP-01)
# ============================================================================
def test_group_5_concil():
    print("\n" + "="*80)
    print("TEST GROUP 5: PNIA Concil (CP-01)")
    print("="*80)
    
    # 5.1 GET /api/pnia/concil/
    status, data = make_request("GET", "/pnia/concil/")
    if status == 200:
        acronym = data.get("acronym", "")
        pillars = data.get("cp01_pillars", [])
        roles = data.get("governance_roles", [])
        invariants = data.get("required_invariants", [])
        
        checks = []
        if "PNIA" in acronym:
            checks.append("acronym contains PNIA")
        else:
            log_fail("Concil concept acronym", f"Expected PNIA in acronym, got {acronym}")
        
        if len(pillars) == 4:
            checks.append("cp01_pillars=4")
        else:
            log_fail("Concil concept pillars", f"Expected 4 pillars, got {len(pillars)}")
        
        if len(roles) == 6:
            checks.append("governance_roles=6")
        else:
            log_fail("Concil concept roles", f"Expected 6 roles, got {len(roles)}")
        
        expected_invariants = ["peace", "freedom", "integrity", "neighborly_love"]
        if set(invariants) == set(expected_invariants):
            checks.append("required_invariants correct")
        else:
            log_fail("Concil concept invariants", f"Expected {expected_invariants}, got {invariants}")
        
        if len(checks) == 4:
            log_pass("GET /pnia/concil/", ", ".join(checks))
    else:
        log_fail("GET /pnia/concil/", f"status={status}")
    
    # 5.2 GET /api/pnia/concil/discovery
    status, data = make_request("GET", "/pnia/concil/discovery")
    if status == 200:
        concil_status = data.get("concil_status")
        keyholder_sig = data.get("keyholder_signature")
        jws = data.get("jws")
        
        if concil_status == "active" and keyholder_sig and jws:
            log_pass("GET /pnia/concil/discovery", 
                    f"concil_status=active, keyholder_signature present, jws present")
        else:
            log_fail("GET /pnia/concil/discovery", 
                    f"Missing fields: status={concil_status}, sig={bool(keyholder_sig)}, jws={bool(jws)}")
    else:
        log_fail("GET /pnia/concil/discovery", f"status={status}")
    
    # 5.3 GET /api/pnia/concil/ownership
    status, data = make_request("GET", "/pnia/concil/ownership")
    if status == 200:
        copyright = data.get("copyright", "")
        registers = data.get("registers", [])
        trademarks = data.get("trademarks", [])
        
        checks = []
        if "© 2026 Daniel Pohl" in copyright:
            checks.append("copyright correct")
        else:
            log_fail("Concil ownership copyright", f"Expected '© 2026 Daniel Pohl', got {copyright}")
        
        if len(registers) == 5:
            checks.append("registers=5")
        else:
            log_fail("Concil ownership registers", f"Expected 5 registers, got {len(registers)}")
        
        if len(trademarks) == 2:
            checks.append("trademarks=2")
        else:
            log_fail("Concil ownership trademarks", f"Expected 2 trademarks, got {len(trademarks)}")
        
        if len(checks) == 3:
            log_pass("GET /pnia/concil/ownership", ", ".join(checks))
    else:
        log_fail("GET /pnia/concil/ownership", f"status={status}")
    
    # 5.4 POST /api/pnia/concil/handshake (all 4 invariants + commitment) → 200
    status, data = make_request("POST", "/pnia/concil/handshake", json_data={
        "accepted_invariants": ["peace", "freedom", "integrity", "neighborly_love"],
        "commitment": "sha256-test-commitment-hash"
    })
    if status == 200:
        decision = data.get("decision")
        sovereignty_shield = data.get("sovereignty_shield")
        session_token = data.get("session_token")
        
        if decision == "ESTABLISHED_ACCESS" and sovereignty_shield == "passive" and session_token:
            log_pass("POST /pnia/concil/handshake (all invariants)", 
                    f"decision=ESTABLISHED_ACCESS, sovereignty_shield=passive, session_token present")
        else:
            log_fail("POST /pnia/concil/handshake (all invariants)", 
                    f"Unexpected: decision={decision}, shield={sovereignty_shield}, token={bool(session_token)}")
    else:
        log_fail("POST /pnia/concil/handshake (all invariants)", f"status={status}, data={data}")
    
    # 5.5 POST /api/pnia/concil/handshake (missing invariants) → 403
    status, data = make_request("POST", "/pnia/concil/handshake", json_data={
        "accepted_invariants": ["peace"],
        "commitment": "sha256-test"
    })
    if status == 403:
        decision = data.get("decision")
        sovereignty_shield = data.get("sovereignty_shield")
        missing = data.get("missing_invariants", [])
        
        expected_missing = ["freedom", "integrity", "neighborly_love"]
        if (decision == "GOVERNANCE_MISMATCH" and 
            sovereignty_shield == "isolated" and 
            set(missing) == set(expected_missing)):
            log_pass("POST /pnia/concil/handshake (missing invariants)", 
                    f"403, decision=GOVERNANCE_MISMATCH, sovereignty_shield=isolated, missing={missing}")
        else:
            log_fail("POST /pnia/concil/handshake (missing invariants)", 
                    f"Unexpected: decision={decision}, shield={sovereignty_shield}, missing={missing}")
    else:
        log_fail("POST /pnia/concil/handshake (missing invariants)", f"Expected 403, got {status}")
    
    # 5.6 POST /api/pnia/concil/handshake (missing commitment) → 403
    status, data = make_request("POST", "/pnia/concil/handshake", json_data={
        "accepted_invariants": ["peace", "freedom", "integrity", "neighborly_love"],
        "commitment": None
    })
    if status == 403:
        log_pass("POST /pnia/concil/handshake (missing commitment)", "403 as expected")
    else:
        log_fail("POST /pnia/concil/handshake (missing commitment)", f"Expected 403, got {status}")

# ============================================================================
# TEST GROUP 6: Säule B merge
# ============================================================================
def test_group_6_saeule_b():
    print("\n" + "="*80)
    print("TEST GROUP 6: Säule B merge — pnia-compliance + identity-broker")
    print("="*80)
    
    # 6.1 GET /api/pnia-compliance/bsi-report
    status, data = make_request("GET", "/pnia-compliance/bsi-report")
    if status == 200:
        report_status = data.get("status")
        checks = data.get("checks", [])
        
        if report_status == "PASS" and len(checks) == 5:
            log_pass("GET /pnia-compliance/bsi-report", f"status=PASS, checks=5")
        else:
            log_fail("GET /pnia-compliance/bsi-report", 
                    f"Expected status=PASS, checks=5, got status={report_status}, checks={len(checks)}")
    else:
        log_fail("GET /pnia-compliance/bsi-report", f"status={status}, data={data}")
    
    # 6.2 GET /api/pnia-compliance/
    status, data = make_request("GET", "/pnia-compliance/")
    if status == 200 and "service" in data:
        log_pass("GET /pnia-compliance/", f"service={data.get('service')}")
    else:
        log_fail("GET /pnia-compliance/", f"status={status}")
    
    # 6.3 GET /api/identity-broker/providers
    status, data = make_request("GET", "/identity-broker/providers")
    if status == 200:
        providers = data.get("providers", [])
        if len(providers) == 23:
            log_pass("GET /api/identity-broker/providers", f"providers count=23")
        else:
            log_fail("GET /api/identity-broker/providers", f"Expected 23 providers, got {len(providers)}")
    else:
        log_fail("GET /api/identity-broker/providers", f"status={status}")
    
    # 6.4 GET /api/identity-broker/health
    status, data = make_request("GET", "/identity-broker/health")
    if status == 200 and "status" in data:
        log_pass("GET /api/identity-broker/health", f"status={data.get('status')}")
    else:
        log_fail("GET /api/identity-broker/health", f"status={status}")

# ============================================================================
# MAIN
# ============================================================================
def main():
    print("\n" + "="*80)
    print("PNIA BACKEND API TEST SUITE")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Bearer Token: {BEARER_TOKEN[:20]}...")
    print("="*80)
    
    # Run all test groups
    test_group_1_public_registry()
    test_group_2_auth_enforcement()
    test_group_3_compliance_flow()
    test_group_4_ai_generation()
    test_group_5_concil()
    test_group_6_saeule_b()
    
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
