import json
import pytest
from flask_jwt_extended import create_access_token

def test_decode_valid_token(client, app):
    """Test decoding a valid JWT token."""
    # Create a token with specific claims
    with app.app_context():
        claims = {
            "provider_permissions": ["openai", "groq"],
            "endpoint_permissions": ["/v1/chat/completions"],
            "models": ["gpt-4", "llama3-70b"],
            "tier": "premium"
        }
        token = create_access_token(identity="testuser", additional_claims=claims)
    
    # Test decoding the token
    response = client.post(
        '/decode',
        data=json.dumps({'token': token}),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify the decoded token contains the expected claims
    assert data['sub'] == 'testuser'
    assert data['type'] == 'access'
    assert set(data['provider_permissions']) == {"openai", "groq"}
    assert data['tier'] == 'premium'
    assert set(data['models']) == {"gpt-4", "llama3-70b"}

def test_decode_invalid_token(client):
    """Test decoding an invalid JWT token."""
    response = client.post(
        '/decode',
        data=json.dumps({'token': 'invalid-token-format'}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_decode_missing_token(client):
    """Test decoding with missing token parameter."""
    response = client.post(
        '/decode',
        data=json.dumps({}),  # Missing token
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Missing token' in data['error']
