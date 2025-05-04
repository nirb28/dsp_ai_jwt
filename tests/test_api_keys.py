import json
import pytest
from unittest.mock import patch, MagicMock
from flask_jwt_extended import decode_token

def test_api_key_openai_only(client, app):
    """Test that OpenAI-only API key adds correct provider permissions."""
    # Mock the dynamic claims functions and API calls
    with patch('utils.api_key.execute_api_claim', return_value={"usage": 0}), \
         patch('claims.quota.get_remaining_quota', return_value={"remaining_tokens": 10000}):
        
        response = client.post(
            '/token',
            data=json.dumps({
                'username': 'testuser', 
                'password': 'password',
                'api_key': 'api_key_openai_1234567890'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        token = data['access_token']
        
        # Use the Flask app context when decoding tokens
        with app.app_context():
            decoded = decode_token(token)
        
        # Check provider permissions
        assert 'provider_permissions' in decoded
        assert 'openai' in decoded['provider_permissions']
        assert 'groq' not in decoded['provider_permissions']
        
        # Check additional claims
        assert 'models' in decoded
        assert 'gpt-3.5-turbo' in decoded['models']
        assert 'tier' in decoded
        assert decoded['tier'] == 'premium'

def test_api_key_groq_only(client, app):
    """Test that Groq-only API key adds correct provider permissions."""
    # Mock the dynamic claims functions and API calls
    with patch('utils.api_key.execute_api_claim', return_value={"usage": 0}), \
         patch('claims.quota.get_remaining_quota', return_value={"remaining_tokens": 5000}), \
         patch('claims.access.check_model_access', return_value={"available_models": ["llama3-70b"]}):
        
        response = client.post(
            '/token',
            data=json.dumps({
                'username': 'testuser', 
                'password': 'password',
                'api_key': 'api_key_groq_0987654321'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        token = data['access_token']
        
        # Use the Flask app context when decoding tokens
        with app.app_context():
            decoded = decode_token(token)
        
        # Check provider permissions
        assert 'provider_permissions' in decoded
        assert 'groq' in decoded['provider_permissions']
        assert 'openai' not in decoded['provider_permissions']
        
        # Check additional claims
        assert 'models' in decoded
        assert 'llama3-70b' in decoded['models'] or 'llama3-70b' in decoded.get('available_models', [])

def test_invalid_api_key(client, app):
    """Test that invalid API key doesn't add any claims but still authenticates."""
    response = client.post(
        '/token',
        data=json.dumps({
            'username': 'testuser', 
            'password': 'password',
            'api_key': 'invalid_api_key'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    token = data['access_token']
    
    # Use the Flask app context when decoding tokens
    with app.app_context():
        decoded = decode_token(token)
    
    # Basic claims should still be present
    assert decoded['sub'] == 'testuser'
    
    # But no API key specific claims
    assert 'tier' not in decoded or decoded.get('tier') != 'premium'
    assert 'provider_permissions' not in decoded or not decoded.get('provider_permissions', [])
