#!/usr/bin/env python3
"""
ITERATION 10 BUG-FIX VERIFICATION — Format-Diversität (credits-aware)

BUG: Format-Diversität was returning WARN because countries lacked formats field
FIX: Added realistic per-country formats arrays to all 11 countries in test config

VERIFY ONLY:
A) POST /api/pnia-compliance/check → Format-Diversität status == PASS
B) GET /api/pnia-compliance/bsi-report → Format-Diversität status == PASS
C) GET /api/health → operational + database:true
"""

import requests
import sys
import json

BASE_URL = "https://code-audit-fix-25.preview.emergentagent.com/api"

def test_format_diversity_check():
    """A) POST /api/pnia-compliance/check - verify Format-Diversität PASS"""
    print("\n" + "="*80)
    print("TEST A: POST /api/pnia-compliance/check - Format-Diversität verification")
    print("="*80)
    
    url = f"{BASE_URL}/pnia-compliance/check"
    
    try:
        response = requests.post(url, json={}, timeout=60)
        print(f"✓ HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ FAIL: Expected HTTP 200, got {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        data = response.json()
        
        # Verify response structure
        if "checks" not in data:
            print(f"✗ FAIL: Response missing 'checks' field")
            print(f"Response keys: {data.keys()}")
            return False
        
        # Find Format-Diversität check
        format_check = None
        for check in data["checks"]:
            if "Format-Diversität" in check.get("check", ""):
                format_check = check
                break
        
        if not format_check:
            print(f"✗ FAIL: Format-Diversität check not found in response")
            print(f"Available checks: {[c.get('check') for c in data['checks']]}")
            return False
        
        print(f"✓ Found Format-Diversität check")
        print(f"  Check name: {format_check['check']}")
        print(f"  Status: {format_check['status']}")
        print(f"  Detail: {format_check['detail']}")
        
        # Assert status == PASS (not WARN)
        if format_check["status"] != "PASS":
            print(f"✗ FAIL: Format-Diversität status is '{format_check['status']}', expected 'PASS'")
            return False
        print(f"✓ Format-Diversität status is PASS (not WARN)")
        
        # Assert detail matches pattern and starts with number >= 3
        detail = format_check["detail"]
        if "verschiedene Format-Kombinationen über" not in detail:
            print(f"✗ FAIL: Detail does not contain expected text 'verschiedene Format-Kombinationen über'")
            return False
        print(f"✓ Detail contains expected text pattern")
        
        # Extract the number from the detail string
        # Expected format: "N verschiedene Format-Kombinationen über..."
        import re
        match = re.match(r'^(\d+)\s+verschiedene', detail)
        if not match:
            print(f"✗ FAIL: Could not extract number from detail string")
            return False
        
        format_count = int(match.group(1))
        print(f"✓ Format count: {format_count}")
        
        if format_count < 3:
            print(f"✗ FAIL: Format count {format_count} is less than 3")
            return False
        print(f"✓ Format count {format_count} >= 3")
        
        # Assert overall body.status is PASS
        if data.get("status") != "PASS":
            print(f"✗ FAIL: Overall compliance status is '{data.get('status')}', expected 'PASS'")
            print(f"  (Format-Diversität WARN was previously downgrading overall status)")
            return False
        print(f"✓ Overall compliance status is PASS")
        
        print(f"\n✅ TEST A PASSED: Format-Diversität check is PASS with {format_count} format combinations")
        return True
        
    except requests.exceptions.Timeout:
        print(f"✗ FAIL: Request timeout after 60 seconds")
        return False
    except Exception as e:
        print(f"✗ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bsi_report():
    """B) GET /api/pnia-compliance/bsi-report - verify Format-Diversität PASS in report"""
    print("\n" + "="*80)
    print("TEST B: GET /api/pnia-compliance/bsi-report - Format-Diversität in report")
    print("="*80)
    
    url = f"{BASE_URL}/pnia-compliance/bsi-report"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"✓ HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ FAIL: Expected HTTP 200, got {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        data = response.json()
        
        # Verify response structure
        if "checks" not in data:
            print(f"✗ FAIL: Response missing 'checks' field")
            print(f"Response keys: {data.keys()}")
            return False
        
        # Find Format-Diversität check
        format_check = None
        for check in data["checks"]:
            if "Format-Diversität" in check.get("check", ""):
                format_check = check
                break
        
        if not format_check:
            print(f"✗ FAIL: Format-Diversität check not found in BSI report")
            print(f"Available checks: {[c.get('check') for c in data['checks']]}")
            return False
        
        print(f"✓ Found Format-Diversität check in BSI report")
        print(f"  Check name: {format_check['check']}")
        print(f"  Status: {format_check['status']}")
        print(f"  Detail: {format_check['detail']}")
        
        # Assert status == PASS
        if format_check["status"] != "PASS":
            print(f"✗ FAIL: Format-Diversität status in BSI report is '{format_check['status']}', expected 'PASS'")
            return False
        print(f"✓ Format-Diversität status in BSI report is PASS")
        
        print("\n✅ TEST B PASSED: Format-Diversität check is PASS in BSI report")
        return True
        
    except Exception as e:
        print(f"✗ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_health():
    """C) GET /api/health - verify operational + database:true"""
    print("\n" + "="*80)
    print("TEST C: GET /api/health - sanity check")
    print("="*80)
    
    url = f"{BASE_URL}/health"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"✓ HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ FAIL: Expected HTTP 200, got {response.status_code}")
            return False
        
        data = response.json()
        print(f"✓ Response: {data}")
        
        if data.get("status") != "operational":
            print(f"✗ FAIL: Expected status='operational', got '{data.get('status')}'")
            return False
        print(f"✓ Status is operational")
        
        if data.get("database") != True:
            print(f"✗ FAIL: Expected database=true, got {data.get('database')}")
            return False
        print(f"✓ Database is true")
        
        print("\n✅ TEST C PASSED: Health check operational with database connection")
        return True
        
    except Exception as e:
        print(f"✗ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print("ITERATION 10 BUG-FIX VERIFICATION — Format-Diversität")
    print("="*80)
    print(f"Backend URL: {BASE_URL}")
    
    results = {
        "A_format_diversity_check": False,
        "B_bsi_report": False,
        "C_health": False
    }
    
    # Run tests in order
    results["A_format_diversity_check"] = test_format_diversity_check()
    results["B_bsi_report"] = test_bsi_report()
    results["C_health"] = test_health()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Format-Diversität bug fix verified")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
