import os
import pytest
import tempfile
import yaml
from flask_jwt_extended import create_access_token
from app import app as flask_app

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Set testing configuration
    flask_app.config.update({
        "TESTING": True,
        "JWT_SECRET_KEY": "test-secret-key",
        "AUTH_METHOD": "file"  # Use file-based auth for testing by default
    })
    
    # Create a temporary users file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        users = {
            "testuser": {
                "password": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # SHA-256 for 'password'
                "name": "Test User",
                "email": "test@example.com",
                "groups": ["testers"],
                "roles": ["user"]
            },
            "adminuser": {
                "password": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # SHA-256 for 'password'
                "name": "Admin User",
                "email": "admin@example.com",
                "groups": ["admins"],
                "roles": ["admin", "user"]
            }
        }
        yaml.dump(users, f)
        flask_app.config['USERS_FILE'] = f.name
    
    # Create a temporary API keys file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        api_keys = {
            "test_api_key_openai": {
                "id": "test-openai",
                "owner": "Test Team",
                "provider_permissions": ["openai"],
                "endpoint_permissions": ["/v1/chat/completions"],
                "claims": {
                    "models": ["gpt-3.5-turbo"],
                    "rate_limit": 10,
                    "tier": "test"
                }
            },
            "test_api_key_groq": {
                "id": "test-groq",
                "owner": "Test Team",
                "provider_permissions": ["groq"],
                "endpoint_permissions": ["/v1/chat/completions"],
                "claims": {
                    "models": ["llama3-70b"],
                    "rate_limit": 5,
                    "tier": "test"
                }
            }
        }
        yaml.dump(api_keys, f)
        flask_app.config['API_KEYS_FILE'] = f.name
    
    yield flask_app
    
    # Clean up temporary files
    os.unlink(flask_app.config['USERS_FILE'])
    os.unlink(flask_app.config['API_KEYS_FILE'])

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def auth_token(app):
    """Create a valid JWT token for testing protected routes."""
    with app.app_context():
        token = create_access_token(identity="testuser")
        return token
