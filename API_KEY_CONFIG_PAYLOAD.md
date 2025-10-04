# API Key Config Payload Feature

## Overview

The JWT authentication service now supports passing API key configuration as an inline payload in the `/token` endpoint, in addition to the existing file-based API key reference method.

## Feature Description

### Previous Behavior (Still Supported)
Previously, you could only reference an API key by its string identifier, which would look up the configuration from a YAML file:

```json
{
  "username": "user1",
  "password": "password123",
  "api_key": "api_key_sas2py"
}
```

This would load the configuration from `config/api_keys/api_key_sas2py.yaml`.

### New Behavior
You can now provide the entire API key configuration inline as a JSON payload:

```json
{
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
    },
    "metadata": {
      "description": "Custom inline configuration",
      "created_by": "api_client"
    }
  }
}
```

## Priority

When both `api_key` and `api_key_config` are provided, **`api_key_config` takes precedence**.

## Use Cases

### 1. Dynamic Configuration
Generate API key configurations on-the-fly without creating files:
```python
import requests

config = {
    "id": f"session-{session_id}",
    "owner": user_email,
    "claims": {
        "static": {
            "key": f"user-{user_id}",
            "tier": user_tier,
            "models": get_user_allowed_models(user_id),
            "rate_limit": calculate_rate_limit(user_tier)
        }
    }
}

response = requests.post("http://localhost:5000/token", json={
    "username": username,
    "password": password,
    "api_key_config": config
})
```

### 2. Testing and Development
Quickly test different configurations without creating files:
```bash
curl -X POST http://localhost:5000/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass",
    "api_key_config": {
      "id": "test-key",
      "claims": {
        "static": {
          "tier": "test",
          "models": ["gpt-3.5-turbo"],
          "rate_limit": 10
        }
      }
    }
  }'
```

### 3. Multi-Tenant Applications
Generate tenant-specific configurations dynamically:
```python
def get_tenant_jwt_token(username, password, tenant_id):
    tenant_config = load_tenant_config(tenant_id)
    
    api_key_config = {
        "id": f"tenant-{tenant_id}",
        "owner": tenant_config["name"],
        "claims": {
            "static": {
                "key": f"tenant-{tenant_id}-key",
                "tenant_id": tenant_id,
                "tier": tenant_config["tier"],
                "models": tenant_config["allowed_models"],
                "rate_limit": tenant_config["rate_limit"],
                "project": tenant_config["project_name"]
            }
        }
    }
    
    return requests.post(JWT_URL, json={
        "username": username,
        "password": password,
        "api_key_config": api_key_config
    })
```

### 4. Integration with Control Tower
Pass Control Tower manifest configurations directly:
```python
# Load manifest from Control Tower
manifest = get_manifest_from_control_tower(project_id)
jwt_module = manifest["modules"]["jwt_config"]

# Use the JWT module config directly
response = requests.post("http://localhost:5000/token", json={
    "username": username,
    "password": password,
    "api_key_config": jwt_module["config"]
})
```

## API Key Config Structure

### Required Fields
None - all fields are optional, but providing claims is recommended.

### Optional Fields

#### `id` (string)
Identifier for the API key configuration.

#### `owner` (string)
Owner of the API key.

#### `claims` (object)
Claims to include in the JWT token.

##### `claims.static` (object)
Static claims that are directly included in the token:
- `key`: Consumer key for APISIX or other gateways
- `tier`: Service tier (e.g., "standard", "premium", "enterprise")
- `models`: Array of allowed model names
- `rate_limit`: Rate limit value
- `exp_hours`: Token expiration in hours
- Any other custom claims

##### `claims.dynamic` (object)
Dynamic claims that are computed at token generation time:
- `type`: "function" or "api"
- `module`: Python module path (for function type)
- `function`: Function name to call (for function type)
- `args`: Arguments to pass to the function
- `url`: API endpoint (for api type)
- `method`: HTTP method (for api type)

#### `metadata` (object)
Metadata that is NOT included in the JWT token but can be used by dynamic claim functions.

## Examples

### Example 1: Simple Static Claims
```json
{
  "username": "user1",
  "password": "password123",
  "api_key_config": {
    "claims": {
      "static": {
        "tier": "standard",
        "rate_limit": 50
      }
    }
  }
}
```

### Example 2: With Dynamic Claims
```json
{
  "username": "user1",
  "password": "password123",
  "api_key_config": {
    "id": "dynamic-key",
    "claims": {
      "static": {
        "tier": "premium"
      },
      "dynamic": {
        "quota": {
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
```

### Example 3: APISIX Integration
```json
{
  "username": "user1",
  "password": "password123",
  "api_key_config": {
    "id": "apisix-consumer-key",
    "owner": "SAS2PY Team",
    "claims": {
      "static": {
        "key": "sas2py-consumer",
        "tier": "standard",
        "models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant"],
        "rate_limit": 100,
        "project": "sas2py",
        "environment": "production"
      }
    }
  }
}
```

## Testing

Run the test suite to verify the feature:

```bash
cd d:\ds\work\workspace\git\dsp_ai_jwt
python test_api_key_config.py
```

The test suite includes:
1. Login with inline API key configuration
2. Login with API key reference (existing functionality)
3. Priority test (api_key_config over api_key)
4. Dynamic claims processing

## Implementation Details

### Modified Files

1. **`utils/api_key.py`**
   - Updated `get_additional_claims()` to accept `api_key_config` parameter
   - Added logic to use inline config when provided
   - Inline config takes precedence over file-based lookup

2. **`app.py`**
   - Updated `/token` endpoint to accept `api_key_config` in request body
   - Pass `api_key_config` to `get_additional_claims()`
   - Enhanced logging to indicate when inline config is used

3. **`swagger_config.py`**
   - Updated OpenAPI specification for `/token` endpoint
   - Added `api_key_config` parameter documentation
   - Added examples showing both usage patterns

### Backward Compatibility

This feature is fully backward compatible:
- Existing code using `api_key` parameter continues to work
- No changes required to existing API key YAML files
- No changes to token structure or validation

## Security Considerations

1. **Authentication Required**: Users must still provide valid username/password
2. **No Bypass**: Inline config doesn't bypass authentication
3. **Same Processing**: Dynamic claims and metadata are processed identically
4. **Logging**: All inline configs are logged for audit purposes

## Swagger Documentation

The feature is fully documented in the Swagger UI at `http://localhost:5000/dspai-docs`.

The `/token` endpoint now shows:
- Both `api_key` and `api_key_config` parameters
- Example requests for each usage pattern
- Complete schema for `api_key_config` structure
