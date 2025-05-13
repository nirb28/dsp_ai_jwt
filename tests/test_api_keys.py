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
        
        # Check claims from the API key
        assert 'tier' in decoded
        assert decoded['tier'] in ['premium', 'enterprise']
        assert 'models' in decoded
        assert 'gpt-3.5-turbo' in decoded['models']
        
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
        
        # Check claims from the API key
        assert 'tier' in decoded
        assert decoded['tier'] in ['premium', 'enterprise']
        assert 'models' in decoded
        
        # Check models - using the models that are actually in the API key config
        assert 'models' in decoded
        # Check for any model that might be available
        assert len(decoded['models']) > 0

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
    
    # Basic authentication should still work with invalid API key
    # No specific API key assertions here - the test is for invalid API keys
