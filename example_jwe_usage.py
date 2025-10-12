"""
Example script demonstrating JWE (JSON Web Encryption) usage

This script shows how to:
1. Generate encryption keys
2. Encrypt JWT tokens
3. Decrypt JWE tokens
4. Use JWE with API keys
"""

import requests
import json
import os
from utils.jwe_handler import JWEHandler, encrypt_jwt_token, decrypt_jwe_token

# Base URL for the JWT service
BASE_URL = os.getenv("JWT_SERVICE_URL", "http://localhost:5000")


def example_1_generate_key():
    """Example 1: Generate a new JWE encryption key"""
    print("\n" + "="*60)
    print("Example 1: Generate JWE Encryption Key")
    print("="*60)
    
    # Generate key using API
    response = requests.post(f"{BASE_URL}/generate-jwe-key", json={
        "algorithm": "A256GCM",
        "format": "base64"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Generated encryption key successfully")
        print(f"  Algorithm: {data['algorithm']}")
        print(f"  Format: {data['format']}")
        print(f"  Key Size: {data['key_size_bytes']} bytes")
        print(f"  Key: {data['encryption_key'][:20]}...")
        print(f"\n  💡 Save this to your .env file:")
        print(f"     JWE_ENCRYPTION_KEY={data['encryption_key']}")
        return data['encryption_key']
    else:
        print(f"✗ Failed to generate key: {response.text}")
        return None


def example_2_encrypt_decrypt_token(encryption_key):
    """Example 2: Encrypt and decrypt a JWT token"""
    print("\n" + "="*60)
    print("Example 2: Encrypt and Decrypt JWT Token")
    print("="*60)
    
    # Mock JWT token
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcwMDAwMDAwMH0.test_signature"
    
    print(f"Original JWT: {jwt_token[:50]}...")
    
    # Encrypt
    response = requests.post(f"{BASE_URL}/encrypt-jwe", json={
        "token": jwt_token,
        "encryption_key": encryption_key,
        "encryption": "A256GCM"
    })
    
    if response.status_code == 200:
        encrypted_data = response.json()
        jwe_token = encrypted_data['jwe_token']
        print(f"\n✓ Encrypted to JWE token")
        print(f"  Encryption: {encrypted_data['encryption']}")
        print(f"  JWE Token: {jwe_token[:50]}...")
        
        # Decrypt
        response = requests.post(f"{BASE_URL}/decrypt-jwe", json={
            "jwe_token": jwe_token,
            "encryption_key": encryption_key,
            "encryption": "A256GCM",
            "extract_jwt": True
        })
        
        if response.status_code == 200:
            decrypted_data = response.json()
            decrypted_jwt = decrypted_data['jwt_token']
            print(f"\n✓ Decrypted JWE token")
            print(f"  JWT Token: {decrypted_jwt[:50]}...")
            print(f"  Match: {decrypted_jwt == jwt_token}")
        else:
            print(f"✗ Failed to decrypt: {response.text}")
    else:
        print(f"✗ Failed to encrypt: {response.text}")


def example_3_encrypt_payload(encryption_key):
    """Example 3: Encrypt a custom payload"""
    print("\n" + "="*60)
    print("Example 3: Encrypt Custom Payload")
    print("="*60)
    
    # Custom payload
    payload = {
        "user": "john.doe",
        "role": "admin",
        "permissions": ["read", "write", "delete"],
        "metadata": {
            "department": "engineering",
            "level": 5
        }
    }
    
    print(f"Original Payload:")
    print(json.dumps(payload, indent=2))
    
    # Encrypt
    response = requests.post(f"{BASE_URL}/encrypt-jwe", json={
        "payload": payload,
        "encryption_key": encryption_key,
        "encryption": "A256GCM"
    })
    
    if response.status_code == 200:
        encrypted_data = response.json()
        jwe_token = encrypted_data['jwe_token']
        print(f"\n✓ Encrypted payload")
        print(f"  JWE Token: {jwe_token[:50]}...")
        
        # Decrypt
        response = requests.post(f"{BASE_URL}/decrypt-jwe", json={
            "jwe_token": jwe_token,
            "encryption_key": encryption_key,
            "encryption": "A256GCM",
            "extract_jwt": False
        })
        
        if response.status_code == 200:
            decrypted_data = response.json()
            print(f"\n✓ Decrypted payload:")
            print(json.dumps(decrypted_data['payload'], indent=2))
        else:
            print(f"✗ Failed to decrypt: {response.text}")
    else:
        print(f"✗ Failed to encrypt: {response.text}")


def example_4_login_with_jwe():
    """Example 4: Login with JWE-enabled API key"""
    print("\n" + "="*60)
    print("Example 4: Login with JWE-Enabled API Key")
    print("="*60)
    
    # Check if JWE example API key exists
    print("Note: This requires api_key_jwe_example.yaml to be configured")
    print("      and JWE_ENCRYPTION_KEY environment variable to be set")
    
    # Login
    response = requests.post(f"{BASE_URL}/token", json={
        "username": "admin",
        "password": "admin123",
        "api_key": "api_key_jwe_example"
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('token_type') == 'JWE':
            print(f"\n✓ Received JWE-encrypted tokens")
            print(f"  Token Type: {data['token_type']}")
            print(f"  Encryption: {data['encryption']}")
            print(f"  Access Token: {data['access_token'][:50]}...")
            print(f"  Note: {data.get('note', '')}")
            return data['access_token']
        else:
            print(f"\n✓ Received standard JWT tokens (JWE not enabled)")
            print(f"  Access Token: {data['access_token'][:50]}...")
    else:
        print(f"✗ Login failed: {response.text}")
    
    return None


def example_5_python_direct_usage():
    """Example 5: Use JWE handler directly in Python"""
    print("\n" + "="*60)
    print("Example 5: Direct Python Usage")
    print("="*60)
    
    # Generate key
    encryption_key = JWEHandler.generate_encryption_key('A256GCM', 'base64')
    print(f"Generated Key: {encryption_key[:20]}...")
    
    # Create handler
    handler = JWEHandler(
        encryption_key=encryption_key,
        content_encryption='A256GCM'
    )
    
    # Encrypt payload
    payload = {
        "user_id": "12345",
        "action": "transfer",
        "amount": 1000.00
    }
    
    print(f"\nOriginal Payload:")
    print(json.dumps(payload, indent=2))
    
    encrypted = handler.encrypt(payload)
    print(f"\n✓ Encrypted: {encrypted[:50]}...")
    
    # Decrypt
    decrypted = handler.decrypt(encrypted)
    print(f"\n✓ Decrypted:")
    print(json.dumps(decrypted, indent=2))
    
    # Verify match
    print(f"\nPayload Match: {payload == decrypted}")


def example_6_compression():
    """Example 6: JWE with compression"""
    print("\n" + "="*60)
    print("Example 6: JWE with Compression")
    print("="*60)
    
    # Generate key
    encryption_key = JWEHandler.generate_encryption_key('A256GCM', 'base64')
    
    # Large payload (repetitive data compresses well)
    large_payload = {
        "data": "x" * 1000,
        "logs": [f"Log entry {i}" for i in range(100)],
        "metadata": {f"key_{i}": f"value_{i}" for i in range(50)}
    }
    
    # Encrypt without compression
    handler_no_comp = JWEHandler(
        encryption_key=encryption_key,
        content_encryption='A256GCM',
        compression=None
    )
    encrypted_no_comp = handler_no_comp.encrypt(large_payload)
    
    # Encrypt with compression
    handler_with_comp = JWEHandler(
        encryption_key=encryption_key,
        content_encryption='A256GCM',
        compression='DEF'
    )
    encrypted_with_comp = handler_with_comp.encrypt(large_payload)
    
    print(f"Original Payload Size: ~{len(json.dumps(large_payload))} bytes")
    print(f"Without Compression: {len(encrypted_no_comp)} bytes")
    print(f"With Compression: {len(encrypted_with_comp)} bytes")
    print(f"Compression Ratio: {len(encrypted_with_comp) / len(encrypted_no_comp):.2%}")
    print(f"Space Saved: {len(encrypted_no_comp) - len(encrypted_with_comp)} bytes")
    
    # Verify both decrypt correctly
    decrypted_no_comp = handler_no_comp.decrypt(encrypted_no_comp)
    decrypted_with_comp = handler_with_comp.decrypt(encrypted_with_comp)
    
    print(f"\n✓ Both decrypt correctly: {decrypted_no_comp == decrypted_with_comp == large_payload}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("JWE (JSON Web Encryption) Examples")
    print("="*60)
    
    try:
        # Example 1: Generate key
        encryption_key = example_1_generate_key()
        
        if encryption_key:
            # Example 2: Encrypt/decrypt JWT
            example_2_encrypt_decrypt_token(encryption_key)
            
            # Example 3: Encrypt custom payload
            example_3_encrypt_payload(encryption_key)
        
        # Example 4: Login with JWE
        example_4_login_with_jwe()
        
        # Example 5: Direct Python usage
        example_5_python_direct_usage()
        
        # Example 6: Compression
        example_6_compression()
        
        print("\n" + "="*60)
        print("✓ All examples completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
