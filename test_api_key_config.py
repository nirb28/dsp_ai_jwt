"""
Test script for API key config payload feature
Tests the new api_key_config parameter in the /token endpoint
"""

import requests
import json
from pprint import pprint

# Base URL for the JWT service
BASE_URL = "http://localhost:5000"

USERNAME = "admin"
PASSWORD = "password"

def test_login_with_api_key_config():
    """Test login with inline API key configuration"""
    
    print("=" * 80)
    print("TEST 1: Login with inline API key configuration")
    print("=" * 80)
    
    # Prepare the request payload with inline API key config
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "api_key_config": {
            "id": "test-inline-key",
            "owner": "Test User",
            "claims": {
                "static": {
                    "key": "test-consumer-key",
                    "tier": "premium",
                    "models": ["gpt-4", "gpt-3.5-turbo", "llama-3.1-70b-versatile"],
                    "rate_limit": 200,
                    "project": "test-project",
                    "environment": "development",
                    "exp_hours": 2
                }
            },
            "metadata": {
                "description": "Test inline API key configuration",
                "created_by": "test_script"
            }
        }
    }
    
    # Make the request
    response = requests.post(f"{BASE_URL}/token", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse:")
    pprint(response.json())
    
    if response.status_code == 200:
        # Decode the token to verify claims
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        print("\n" + "=" * 80)
        print("Decoding the generated token to verify claims...")
        print("=" * 80)
        
        decode_response = requests.post(
            f"{BASE_URL}/decode",
            json={"token": access_token}
        )
        
        print(f"\nDecoded Token:")
        pprint(decode_response.json())
        
        # Verify expected claims are present
        decoded = decode_response.json()
        expected_claims = ["key", "tier", "models", "rate_limit", "project", "environment"]
        
        print("\n" + "=" * 80)
        print("Verifying expected claims...")
        print("=" * 80)
        
        for claim in expected_claims:
            if claim in decoded:
                print(f"✓ Claim '{claim}' found: {decoded[claim]}")
            else:
                print(f"✗ Claim '{claim}' NOT found")
        
        return True
    else:
        print(f"\n✗ Login failed with status code: {response.status_code}")
        return False


def test_login_with_api_key_reference():
    """Test login with API key reference (existing functionality)"""
    
    print("\n\n" + "=" * 80)
    print("TEST 2: Login with API key reference (existing functionality)")
    print("=" * 80)
    
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "api_key": "api_key_sas2py"
    }
    
    response = requests.post(f"{BASE_URL}/token", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse:")
    pprint(response.json())
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        print("\n" + "=" * 80)
        print("Decoding the generated token...")
        print("=" * 80)
        
        decode_response = requests.post(
            f"{BASE_URL}/decode",
            json={"token": access_token}
        )
        
        print(f"\nDecoded Token:")
        pprint(decode_response.json())
        
        return True
    else:
        print(f"\n✗ Login failed with status code: {response.status_code}")
        return False


def test_priority_api_key_config_over_api_key():
    """Test that api_key_config takes precedence over api_key"""
    
    print("\n\n" + "=" * 80)
    print("TEST 3: api_key_config should take precedence over api_key")
    print("=" * 80)
    
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "api_key": "api_key_sas2py",  # This should be ignored
        "api_key_config": {
            "id": "priority-test-key",
            "owner": "Priority Test",
            "claims": {
                "static": {
                    "key": "priority-key",
                    "tier": "enterprise",
                    "models": ["gpt-4-turbo"],
                    "rate_limit": 500,
                    "test_claim": "from_inline_config"
                }
            }
        }
    }
    
    response = requests.post(f"{BASE_URL}/token", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        decode_response = requests.post(
            f"{BASE_URL}/decode",
            json={"token": access_token}
        )
        
        decoded = decode_response.json()
        
        print(f"\nDecoded Token (relevant claims):")
        print(f"  key: {decoded.get('key')}")
        print(f"  tier: {decoded.get('tier')}")
        print(f"  test_claim: {decoded.get('test_claim')}")
        
        # Verify it used the inline config, not the file-based api_key
        if decoded.get('key') == 'priority-key' and decoded.get('test_claim') == 'from_inline_config':
            print("\n✓ api_key_config correctly took precedence over api_key")
            return True
        else:
            print("\n✗ api_key_config did NOT take precedence")
            return False
    else:
        print(f"\n✗ Login failed with status code: {response.status_code}")
        return False


def test_login_with_dynamic_claims_in_config():
    """Test inline API key config with dynamic claims"""
    
    print("\n\n" + "=" * 80)
    print("TEST 4: Login with inline API key config including dynamic claims")
    print("=" * 80)
    
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "api_key_config": {
            "id": "dynamic-test-key",
            "owner": "Dynamic Test User",
            "claims": {
                "static": {
                    "key": "dynamic-key",
                    "tier": "standard"
                },
                "dynamic": {
                    "usage": {
                        "type": "function",
                        "module": "claims.quota",
                        "function": "get_remaining_quota",
                        "args": {
                            "user_id": "{user_id}"
                        }
                    }
                }
            }
        }
    }
    
    response = requests.post(f"{BASE_URL}/token", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        decode_response = requests.post(
            f"{BASE_URL}/decode",
            json={"token": access_token}
        )
        
        decoded = decode_response.json()
        
        print(f"\nDecoded Token (checking for dynamic claims):")
        print(f"  key: {decoded.get('key')}")
        print(f"  tier: {decoded.get('tier')}")
        print(f"  usage (dynamic): {decoded.get('usage')}")
        
        if decoded.get('usage') is not None:
            print("\n✓ Dynamic claims were processed successfully")
            return True
        else:
            print("\n✗ Dynamic claims were NOT processed")
            return False
    else:
        print(f"\n✗ Login failed with status code: {response.status_code}")
        pprint(response.json())
        return False


if __name__ == "__main__":
    print("\n")
    print("*" * 80)
    print("API KEY CONFIG PAYLOAD FEATURE TEST SUITE")
    print("*" * 80)
    print("\nMake sure the JWT service is running on http://localhost:5000")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()
    
    results = []
    
    # Run all tests
    results.append(("Test 1: Inline API key config", test_login_with_api_key_config()))
    results.append(("Test 2: API key reference", test_login_with_api_key_reference()))
    results.append(("Test 3: Priority test", test_priority_api_key_config_over_api_key()))
    results.append(("Test 4: Dynamic claims", test_login_with_dynamic_claims_in_config()))
    
    # Print summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    print("=" * 80)
