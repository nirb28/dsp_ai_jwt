"""
Tests for JWE (JSON Web Encryption) functionality

This module tests symmetric encryption of JWT tokens using JWE.
"""

import pytest
import json
import base64
import secrets
from utils.jwe_handler import (
    JWEHandler,
    encrypt_jwt_token,
    decrypt_jwe_token,
    encrypt_payload_to_jwe,
    decrypt_jwe_to_payload
)


class TestJWEHandler:
    """Test JWEHandler class"""
    
    def test_generate_key(self):
        """Test key generation for different algorithms"""
        for algorithm in ['A128GCM', 'A192GCM', 'A256GCM']:
            key_base64 = JWEHandler.generate_encryption_key(algorithm, 'base64')
            key_hex = JWEHandler.generate_encryption_key(algorithm, 'hex')
            
            # Verify key is generated
            assert key_base64
            assert key_hex
            
            # Verify correct size
            key_bytes = base64.b64decode(key_base64)
            assert len(key_bytes) == JWEHandler.KEY_SIZES[algorithm]
    
    def test_encrypt_decrypt_payload(self):
        """Test encryption and decryption of a payload"""
        # Generate a key
        encryption_key = JWEHandler.generate_encryption_key('A256GCM', 'base64')
        
        # Create handler
        handler = JWEHandler(
            encryption_key=encryption_key,
            content_encryption='A256GCM'
        )
        
        # Test payload
        payload = {
            'user': 'testuser',
            'role': 'admin',
            'permissions': ['read', 'write', 'delete']
        }
        
        # Encrypt
        encrypted = handler.encrypt(payload)
        assert encrypted
        assert isinstance(encrypted, str)
        
        # Decrypt
        decrypted = handler.decrypt(encrypted)
        assert decrypted == payload
    
    def test_encrypt_decrypt_jwt_token(self):
        """Test encryption and decryption of a JWT token"""
        # Generate a key
        encryption_key = JWEHandler.generate_encryption_key('A256GCM', 'base64')
        
        # Mock JWT token
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        
        # Encrypt
        encrypted = encrypt_jwt_token(
            jwt_token,
            encryption_key,
            'A256GCM'
        )
        assert encrypted
        assert encrypted != jwt_token
        
        # Decrypt
        decrypted = decrypt_jwe_token(
            encrypted,
            encryption_key,
            'A256GCM'
        )
        assert decrypted == jwt_token
    
    def test_different_encryption_algorithms(self):
        """Test different content encryption algorithms"""
        algorithms = ['A128GCM', 'A192GCM', 'A256GCM']
        
        for algorithm in algorithms:
            # Generate appropriate key
            encryption_key = JWEHandler.generate_encryption_key(algorithm, 'base64')
            
            # Create handler
            handler = JWEHandler(
                encryption_key=encryption_key,
                content_encryption=algorithm
            )
            
            # Test payload
            payload = {'test': f'data for {algorithm}'}
            
            # Encrypt and decrypt
            encrypted = handler.encrypt(payload)
            decrypted = handler.decrypt(encrypted)
            
            assert decrypted == payload
    
    def test_compression(self):
        """Test JWE with compression enabled"""
        # Generate a key
        encryption_key = JWEHandler.generate_encryption_key('A256GCM', 'base64')
        
        # Create handler with compression
        handler = JWEHandler(
            encryption_key=encryption_key,
            content_encryption='A256GCM',
            compression='DEF'
        )
        
        # Large payload for compression
        payload = {
            'data': 'x' * 1000,  # Repetitive data compresses well
            'list': list(range(100))
        }
        
        # Encrypt with compression
        encrypted_compressed = handler.encrypt(payload)
        
        # Encrypt without compression for comparison
        handler_no_compression = JWEHandler(
            encryption_key=encryption_key,
            content_encryption='A256GCM',
            compression=None
        )
        encrypted_uncompressed = handler_no_compression.encrypt(payload)
        
        # Compressed should be smaller
        assert len(encrypted_compressed) < len(encrypted_uncompressed)
        
        # Both should decrypt correctly
        assert handler.decrypt(encrypted_compressed) == payload
        assert handler_no_compression.decrypt(encrypted_uncompressed) == payload
    
    def test_invalid_key_size(self):
        """Test that invalid key sizes raise errors"""
        # Too short key
        short_key = base64.b64encode(b'short').decode('utf-8')
        
        with pytest.raises(ValueError):
            handler = JWEHandler(
                encryption_key=short_key,
                content_encryption='A256GCM'
            )
    
    def test_key_export(self):
        """Test exporting encryption keys"""
        # Generate a key
        encryption_key = JWEHandler.generate_encryption_key('A256GCM', 'base64')
        
        # Create handler
        handler = JWEHandler(
            encryption_key=encryption_key,
            content_encryption='A256GCM'
        )
        
        # Export in different formats
        key_base64 = handler.get_key_export('base64')
        key_hex = handler.get_key_export('hex')
        key_jwk = handler.get_key_export('jwk')
        
        assert key_base64
        assert key_hex
        assert key_jwk
        assert 'kty' in key_jwk  # JWK should contain key type
    
    def test_helper_functions(self):
        """Test helper functions for encryption/decryption"""
        # Generate a key
        encryption_key = JWEHandler.generate_encryption_key('A256GCM', 'base64')
        
        # Test payload encryption
        payload = {'user': 'test', 'role': 'admin'}
        encrypted = encrypt_payload_to_jwe(
            payload,
            encryption_key,
            'A256GCM'
        )
        decrypted = decrypt_jwe_to_payload(
            encrypted,
            encryption_key,
            'A256GCM'
        )
        assert decrypted == payload
        
        # Test JWT token encryption
        jwt_token = "test.jwt.token"
        encrypted_jwt = encrypt_jwt_token(
            jwt_token,
            encryption_key,
            'A256GCM'
        )
        decrypted_jwt = decrypt_jwe_token(
            encrypted_jwt,
            encryption_key,
            'A256GCM'
        )
        assert decrypted_jwt == jwt_token
    
    def test_wrong_key_decryption(self):
        """Test that decryption with wrong key fails"""
        # Generate two different keys
        key1 = JWEHandler.generate_encryption_key('A256GCM', 'base64')
        key2 = JWEHandler.generate_encryption_key('A256GCM', 'base64')
        
        # Encrypt with key1
        handler1 = JWEHandler(encryption_key=key1, content_encryption='A256GCM')
        payload = {'secret': 'data'}
        encrypted = handler1.encrypt(payload)
        
        # Try to decrypt with key2 - should fail
        handler2 = JWEHandler(encryption_key=key2, content_encryption='A256GCM')
        with pytest.raises(Exception):
            handler2.decrypt(encrypted)


class TestJWEEndpoints:
    """Test JWE API endpoints"""
    
    @pytest.fixture
    def encryption_key(self):
        """Generate an encryption key for tests"""
        return JWEHandler.generate_encryption_key('A256GCM', 'base64')
    
    @pytest.fixture
    def jwt_token(self):
        """Mock JWT token for tests"""
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.test"
    
    def test_generate_key_endpoint(self, client):
        """Test /generate-jwe-key endpoint"""
        # Test with default parameters
        response = client.post('/generate-jwe-key')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'encryption_key' in data
        assert data['algorithm'] == 'A256GCM'
        assert data['format'] == 'base64'
        
        # Test with custom parameters
        response = client.post(
            '/generate-jwe-key',
            json={'algorithm': 'A128GCM', 'format': 'hex'}
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['algorithm'] == 'A128GCM'
        assert data['format'] == 'hex'
    
    def test_encrypt_decrypt_endpoints(self, client, encryption_key, jwt_token):
        """Test /encrypt-jwe and /decrypt-jwe endpoints"""
        # Encrypt JWT token
        response = client.post(
            '/encrypt-jwe',
            json={
                'token': jwt_token,
                'encryption_key': encryption_key,
                'encryption': 'A256GCM'
            }
        )
        assert response.status_code == 200
        
        encrypt_data = json.loads(response.data)
        assert 'jwe_token' in encrypt_data
        jwe_token = encrypt_data['jwe_token']
        
        # Decrypt JWE token
        response = client.post(
            '/decrypt-jwe',
            json={
                'jwe_token': jwe_token,
                'encryption_key': encryption_key,
                'encryption': 'A256GCM'
            }
        )
        assert response.status_code == 200
        
        decrypt_data = json.loads(response.data)
        assert decrypt_data['jwt_token'] == jwt_token
    
    def test_encrypt_payload_endpoint(self, client, encryption_key):
        """Test encrypting a payload directly"""
        payload = {
            'user': 'testuser',
            'permissions': ['read', 'write']
        }
        
        # Encrypt payload
        response = client.post(
            '/encrypt-jwe',
            json={
                'payload': payload,
                'encryption_key': encryption_key,
                'encryption': 'A256GCM'
            }
        )
        assert response.status_code == 200
        
        encrypt_data = json.loads(response.data)
        jwe_token = encrypt_data['jwe_token']
        
        # Decrypt payload
        response = client.post(
            '/decrypt-jwe',
            json={
                'jwe_token': jwe_token,
                'encryption_key': encryption_key,
                'encryption': 'A256GCM',
                'extract_jwt': False
            }
        )
        assert response.status_code == 200
        
        decrypt_data = json.loads(response.data)
        assert decrypt_data['payload'] == payload
    
    def test_encrypt_with_compression(self, client, encryption_key, jwt_token):
        """Test encryption with compression"""
        response = client.post(
            '/encrypt-jwe',
            json={
                'token': jwt_token,
                'encryption_key': encryption_key,
                'encryption': 'A256GCM',
                'compression': 'DEF'
            }
        )
        assert response.status_code == 200
        
        encrypt_data = json.loads(response.data)
        assert encrypt_data['compression'] == 'DEF'
    
    def test_encrypt_missing_key(self, client, jwt_token):
        """Test encryption without encryption key"""
        response = client.post(
            '/encrypt-jwe',
            json={'token': jwt_token}
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_decrypt_wrong_key(self, client, jwt_token):
        """Test decryption with wrong key"""
        # Generate two keys
        key1 = JWEHandler.generate_encryption_key('A256GCM', 'base64')
        key2 = JWEHandler.generate_encryption_key('A256GCM', 'base64')
        
        # Encrypt with key1
        response = client.post(
            '/encrypt-jwe',
            json={
                'token': jwt_token,
                'encryption_key': key1,
                'encryption': 'A256GCM'
            }
        )
        jwe_token = json.loads(response.data)['jwe_token']
        
        # Try to decrypt with key2
        response = client.post(
            '/decrypt-jwe',
            json={
                'jwe_token': jwe_token,
                'encryption_key': key2,
                'encryption': 'A256GCM'
            }
        )
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
