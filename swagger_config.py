"""
Swagger API documentation configuration module for the JWT Auth application.
Provides a centralized location for API specifications and documentation.
"""

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask, jsonify
import yaml

# Create an APISpec
spec = APISpec(
    title="JWT Auth API",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[MarshmallowPlugin()],
    info={
        "description": "API for JWT authentication and API key management",
        "contact": {"email": "support@dspai.com"}
    },
    servers=[
        {"url": "http://localhost:5000", "description": "Development server"}
    ],
    tags=[
        {"name": "auth", "description": "Authentication endpoints"},
        {"name": "token", "description": "Token management endpoints"},
        {"name": "api-keys", "description": "API key management endpoints"},
    ],
)

# Define security schemes
spec.components.security_scheme(
    "bearerAuth", 
    {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
)

# Access Token Response Schema
spec.components.schema(
    "TokenResponse", 
    {
        "type": "object",
        "properties": {
            "access_token": {"type": "string"},
            "refresh_token": {"type": "string"}
        }
    }
)

# API Key Schema
spec.components.schema(
    "ApiKey", 
    {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "owner": {"type": "string"},
            "provider_permissions": {
                "type": "array",
                "items": {"type": "string"}
            },
            "endpoint_permissions": {
                "type": "array",
                "items": {"type": "string"}
            },
            "claims": {
                "type": "object",
                "properties": {
                    "static": {"type": "object"},
                    "dynamic": {"type": "object"}
                }
            }
        }
    }
)

# API Key Creation Schema
spec.components.schema(
    "ApiKeyCreation", 
    {
        "type": "object",
        "required": ["owner"],
        "properties": {
            "owner": {"type": "string"},
            "provider_permissions": {
                "type": "array",
                "items": {"type": "string"}
            },
            "endpoint_permissions": {
                "type": "array",
                "items": {"type": "string"}
            },
            "static_claims": {"type": "object"}
        }
    }
)

# Define the token login endpoint
login_endpoint = {
    "post": {
        "tags": ["auth"],
        "summary": "Generate JWT tokens based on user login",
        "description": "Authenticate a user with username and password, optionally using an API key or inline API key configuration, and return JWT tokens",
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["username", "password"],
                        "properties": {
                            "username": {"type": "string", "description": "Username for authentication"},
                            "password": {"type": "string", "description": "Password for authentication"},
                            "api_key": {"type": "string", "description": "API key string to look up configuration from file"},
                            "api_key_config": {
                                "type": "object",
                                "description": "Inline API key configuration (takes precedence over api_key)",
                                "properties": {
                                    "id": {"type": "string"},
                                    "owner": {"type": "string"},
                                    "claims": {
                                        "type": "object",
                                        "properties": {
                                            "static": {
                                                "type": "object",
                                                "description": "Static claims to include in JWT",
                                                "additionalProperties": True
                                            },
                                            "dynamic": {
                                                "type": "object",
                                                "description": "Dynamic claims configuration",
                                                "additionalProperties": True
                                            }
                                        }
                                    },
                                    "metadata": {
                                        "type": "object",
                                        "description": "Metadata not included in JWT but used for function calls",
                                        "additionalProperties": True
                                    }
                                }
                            },
                            "secret": {"type": "string", "description": "Custom secret for token generation"}
                        }
                    },
                    "examples": {
                        "with_api_key": {
                            "summary": "Login with API key reference",
                            "value": {
                                "username": "user1",
                                "password": "password123",
                                "api_key": "api_key_sas2py"
                            }
                        },
                        "with_inline_config": {
                            "summary": "Login with inline API key config",
                            "value": {
                                "username": "user1",
                                "password": "password123",
                                "api_key_config": {
                                    "id": "custom-inline-key",
                                    "owner": "Custom User",
                                    "claims": {
                                        "static": {
                                            "key": "custom-key",
                                            "tier": "premium",
                                            "models": ["gpt-4", "gpt-3.5-turbo"],
                                            "rate_limit": 100,
                                            "exp_hours": 2
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "Successful authentication",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TokenResponse"}
                    }
                }
            },
            "400": {"description": "Invalid request"},
            "401": {"description": "Authentication failed"}
        }
    }
}

# Define the refresh token endpoint
refresh_endpoint = {
    "post": {
        "tags": ["token"],
        "summary": "Refresh access token",
        "description": "Get a new access token using a refresh token",
        "security": [{"bearerAuth": []}],
        "responses": {
            "200": {
                "description": "New access token",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "access_token": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "401": {"description": "Invalid refresh token"}
        }
    }
}

# Define the decode token endpoint
decode_endpoint = {
    "post": {
        "tags": ["token"],
        "summary": "Decode JWT token",
        "description": "Decode a JWT token and return its contents",
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["token"],
                        "properties": {
                            "token": {"type": "string"}
                        }
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "Token successfully decoded",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object"
                        }
                    }
                }
            },
            "400": {"description": "Invalid token"}
        }
    }
}

# Define the validate token endpoint
validate_endpoint = {
    "post": {
        "tags": ["token"],
        "summary": "Validate JWT token signature",
        "description": "Validate a JWT token's signature and check if it has expired",
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["token"],
                        "properties": {
                            "token": {"type": "string"}
                        }
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "Token validation results",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "valid": {"type": "boolean"},
                                "signature_verified": {"type": "boolean"},
                                "expired": {"type": "boolean"},
                                "expiry_time": {"type": "string"},
                                "issued_at": {"type": "string"},
                                "issuer": {"type": "string"},
                                "subject": {"type": "string"},
                                "error": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "400": {"description": "Missing token"}
        }
    }
}

# Define the protected endpoint
protected_endpoint = {
    "get": {
        "tags": ["auth"],
        "summary": "Protected endpoint",
        "description": "Test endpoint that requires a valid JWT token",
        "security": [{"bearerAuth": []}],
        "responses": {
            "200": {
                "description": "Successfully authenticated",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "logged_in_as": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "401": {"description": "Authentication failed"}
        }
    }
}

# Define the sensitive action endpoint
sensitive_action_endpoint = {
    "post": {
        "tags": ["auth"],
        "summary": "Sensitive action endpoint",
        "description": "Test endpoint that requires a fresh JWT token (from direct login)",
        "security": [{"bearerAuth": []}],
        "responses": {
            "200": {
                "description": "Sensitive action performed",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"},
                                "user": {"type": "string"},
                                "token_status": {"type": "string"},
                                "token_freshness": {"type": "boolean"},
                                "action_time": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "401": {"description": "Authentication failed or token not fresh"}
        }
    }
}

# Define the get API keys endpoint
get_api_keys_endpoint = {
    "get": {
        "tags": ["api-keys"],
        "summary": "Get all API keys",
        "description": "Get a list of all API keys (admin only)",
        "security": [{"bearerAuth": []}],
        "responses": {
            "200": {
                "description": "List of API keys",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ApiKey"}
                        }
                    }
                }
            },
            "401": {"description": "Authentication failed"},
            "403": {"description": "Not authorized (admin only)"}
        }
    }
}

# Define the get specific API key endpoint
get_api_key_endpoint = {
    "get": {
        "tags": ["api-keys"],
        "summary": "Get API key details",
        "description": "Get details for a specific API key (admin only)",
        "security": [{"bearerAuth": []}],
        "parameters": [
            {
                "name": "api_key_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key ID"
            }
        ],
        "responses": {
            "200": {
                "description": "API key details",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ApiKey"}
                    }
                }
            },
            "401": {"description": "Authentication failed"},
            "403": {"description": "Not authorized (admin only)"},
            "404": {"description": "API key not found"}
        }
    }
}

# Define the create API key endpoint
create_api_key_endpoint = {
    "post": {
        "tags": ["api-keys"],
        "summary": "Create a new API key",
        "description": "Create a new API key with specified permissions (admin only)",
        "security": [{"bearerAuth": []}],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ApiKeyCreation"}
                }
            }
        },
        "responses": {
            "201": {
                "description": "API key created",
                "content": {
                    "application/json": {
                        "schema": {
                            "allOf": [
                                {"$ref": "#/components/schemas/ApiKey"},
                                {
                                    "type": "object",
                                    "properties": {
                                        "api_key": {"type": "string"}
                                    }
                                }
                            ]
                        }
                    }
                }
            },
            "400": {"description": "Invalid request"},
            "401": {"description": "Authentication failed"},
            "403": {"description": "Not authorized (admin only)"}
        }
    }
}

# Define the update API key endpoint
update_api_key_endpoint = {
    "put": {
        "tags": ["api-keys"],
        "summary": "Update an API key",
        "description": "Update an existing API key (admin only)",
        "security": [{"bearerAuth": []}],
        "parameters": [
            {
                "name": "api_key_string",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key string"
            }
        ],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ApiKeyCreation"}
                }
            }
        },
        "responses": {
            "200": {
                "description": "API key updated",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ApiKey"}
                    }
                }
            },
            "400": {"description": "Invalid request"},
            "401": {"description": "Authentication failed"},
            "403": {"description": "Not authorized (admin only)"},
            "404": {"description": "API key not found"}
        }
    }
}

# Define the delete API key endpoint
delete_api_key_endpoint = {
    "delete": {
        "tags": ["api-keys"],
        "summary": "Delete an API key",
        "description": "Delete an existing API key (admin only)",
        "security": [{"bearerAuth": []}],
        "parameters": [
            {
                "name": "api_key_string",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "API key string"
            }
        ],
        "responses": {
            "200": {
                "description": "API key deleted",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "401": {"description": "Authentication failed"},
            "403": {"description": "Not authorized (admin only)"},
            "404": {"description": "API key not found"}
        }
    }
}

# Add paths to spec
spec.path(path="/token", operations=login_endpoint)
spec.path(path="/refresh", operations=refresh_endpoint)
spec.path(path="/decode", operations=decode_endpoint)
spec.path(path="/validate", operations=validate_endpoint)
spec.path(path="/protected", operations=protected_endpoint)
spec.path(path="/sensitive-action", operations=sensitive_action_endpoint)
spec.path(path="/api-keys", operations={**get_api_keys_endpoint, **create_api_key_endpoint})
spec.path(path="/api-keys/{api_key_id}", operations=get_api_key_endpoint)
spec.path(path="/api-keys/{api_key_string}", operations={**update_api_key_endpoint, **delete_api_key_endpoint})

def get_swagger_dict():
    """Return the Swagger specification as a dictionary."""
    return spec.to_dict()

def get_swagger_json():
    """Return the Swagger specification as JSON."""
    return jsonify(get_swagger_dict())

def get_swagger_yaml():
    """Return the Swagger specification as YAML."""
    return yaml.dump(get_swagger_dict())
