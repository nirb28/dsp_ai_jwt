# Quick Start: API Key Config Payload

## TL;DR

You can now pass API key configuration directly in the `/token` request instead of referencing a file.

## Before (File-based)

```bash
curl -X POST http://localhost:5000/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user1",
    "password": "password123",
    "api_key": "api_key_sas2py"
  }'
```

## After (Inline Config)

```bash
curl -X POST http://localhost:5000/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user1",
    "password": "password123",
    "api_key_config": {
      "id": "my-custom-key",
      "claims": {
        "static": {
          "key": "consumer-key",
          "tier": "premium",
          "models": ["gpt-4"],
          "rate_limit": 100
        }
      }
    }
  }'
```

## Python Example

```python
import requests

response = requests.post("http://localhost:5000/token", json={
    "username": "user1",
    "password": "password123",
    "api_key_config": {
        "id": "dynamic-key",
        "owner": "My Team",
        "claims": {
            "static": {
                "key": "my-consumer-key",
                "tier": "enterprise",
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "rate_limit": 200,
                "project": "my-project",
                "exp_hours": 2
            }
        }
    }
})

token = response.json()["access_token"]
print(f"Token: {token}")
```

## Control Tower Integration

```python
import requests

# Get manifest from Control Tower
manifest = requests.get(
    "http://localhost:8000/manifests/sas2py"
).json()

# Extract JWT config from manifest
jwt_module = next(
    m for m in manifest["modules"] 
    if m["type"] == "jwt_config"
)

# Use it directly
response = requests.post("http://localhost:5000/token", json={
    "username": "user1",
    "password": "password123",
    "api_key_config": jwt_module["config"]
})
```

## Test It

```bash
cd d:\ds\work\workspace\git\dsp_ai_jwt
python test_api_key_config.py
```

## Full Documentation

- **Complete Guide**: [API_KEY_CONFIG_PAYLOAD.md](API_KEY_CONFIG_PAYLOAD.md)
- **Examples**: [example_control_tower_integration.py](example_control_tower_integration.py)
- **Swagger UI**: http://localhost:5000/dspai-docs
