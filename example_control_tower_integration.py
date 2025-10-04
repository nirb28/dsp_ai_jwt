"""
Example: Integration with DSP AI Control Tower
Demonstrates how to use api_key_config payload with Control Tower manifests
"""

import requests
import json
from typing import Dict, Any

# Service URLs
CONTROL_TOWER_URL = "http://localhost:8000"
JWT_SERVICE_URL = "http://localhost:5000"
FRONT_DOOR_URL = "http://localhost:9000"


def get_manifest_from_control_tower(project_id: str) -> Dict[str, Any]:
    """
    Fetch a project manifest from Control Tower
    """
    response = requests.get(f"{CONTROL_TOWER_URL}/manifests/{project_id}")
    response.raise_for_status()
    return response.json()


def extract_jwt_config_from_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract JWT configuration from a Control Tower manifest
    """
    modules = manifest.get("modules", [])
    
    # Find the JWT module
    for module in modules:
        if module.get("type") == "jwt_config":
            return module.get("config", {})
    
    return {}


def get_jwt_token_with_manifest_config(
    username: str,
    password: str,
    project_id: str
) -> Dict[str, Any]:
    """
    Get a JWT token using configuration from Control Tower manifest
    
    Args:
        username: User's username
        password: User's password
        project_id: Control Tower project ID
        
    Returns:
        Dictionary containing access_token and refresh_token
    """
    # Step 1: Fetch manifest from Control Tower
    print(f"Fetching manifest for project: {project_id}")
    manifest = get_manifest_from_control_tower(project_id)
    
    # Step 2: Extract JWT configuration
    print("Extracting JWT configuration from manifest")
    jwt_config = extract_jwt_config_from_manifest(manifest)
    
    if not jwt_config:
        raise ValueError("No JWT configuration found in manifest")
    
    # Step 3: Use the JWT config as api_key_config payload
    print("Requesting JWT token with manifest configuration")
    response = requests.post(
        f"{JWT_SERVICE_URL}/token",
        json={
            "username": username,
            "password": password,
            "api_key_config": jwt_config
        }
    )
    
    response.raise_for_status()
    return response.json()


def example_sas2py_project():
    """
    Example: Get JWT token for SAS2PY project using Control Tower manifest
    """
    print("=" * 80)
    print("Example: SAS2PY Project with Control Tower Integration")
    print("=" * 80)
    
    try:
        # Get token using manifest configuration
        token_data = get_jwt_token_with_manifest_config(
            username="user1",
            password="password123",
            project_id="sas2py"
        )
        
        print("\n✓ Successfully obtained JWT token")
        print(f"Access Token: {token_data['access_token'][:50]}...")
        
        # Decode token to see claims
        decode_response = requests.post(
            f"{JWT_SERVICE_URL}/decode",
            json={"token": token_data["access_token"]}
        )
        
        decoded = decode_response.json()
        print("\nToken Claims:")
        print(f"  - key: {decoded.get('key')}")
        print(f"  - tier: {decoded.get('tier')}")
        print(f"  - models: {decoded.get('models')}")
        print(f"  - rate_limit: {decoded.get('rate_limit')}")
        print(f"  - project: {decoded.get('project')}")
        
        return token_data
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error: {e}")
        return None


def example_inline_config_without_control_tower():
    """
    Example: Create JWT token with inline config (no Control Tower needed)
    """
    print("\n\n" + "=" * 80)
    print("Example: Direct Inline Configuration (No Control Tower)")
    print("=" * 80)
    
    # Define configuration inline
    api_key_config = {
        "id": "direct-inline-key",
        "owner": "Direct User",
        "claims": {
            "static": {
                "key": "direct-consumer-key",
                "tier": "premium",
                "models": [
                    "gpt-4",
                    "gpt-3.5-turbo",
                    "llama-3.1-70b-versatile"
                ],
                "rate_limit": 150,
                "project": "custom-project",
                "environment": "production",
                "exp_hours": 2
            }
        },
        "metadata": {
            "description": "Direct inline configuration example",
            "created_at": "2025-10-04",
            "version": "1.0"
        }
    }
    
    try:
        response = requests.post(
            f"{JWT_SERVICE_URL}/token",
            json={
                "username": "user1",
                "password": "password123",
                "api_key_config": api_key_config
            }
        )
        
        response.raise_for_status()
        token_data = response.json()
        
        print("\n✓ Successfully obtained JWT token")
        
        # Decode token
        decode_response = requests.post(
            f"{JWT_SERVICE_URL}/decode",
            json={"token": token_data["access_token"]}
        )
        
        decoded = decode_response.json()
        print("\nToken Claims:")
        for key in ["key", "tier", "models", "rate_limit", "project", "environment"]:
            if key in decoded:
                print(f"  - {key}: {decoded[key]}")
        
        return token_data
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error: {e}")
        return None


def example_use_token_with_front_door(token: str):
    """
    Example: Use the JWT token to make a request through Front Door
    """
    print("\n\n" + "=" * 80)
    print("Example: Using JWT Token with Front Door")
    print("=" * 80)
    
    try:
        # Make a request to Front Door with the JWT token
        response = requests.post(
            f"{FRONT_DOOR_URL}/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-70b-versatile",
                "messages": [
                    {"role": "user", "content": "Hello, this is a test message"}
                ],
                "max_tokens": 50
            }
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Request successful")
            result = response.json()
            print(f"\nResponse: {result.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')}")
        else:
            print(f"✗ Request failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error: {e}")


def example_dynamic_multi_tenant():
    """
    Example: Multi-tenant application with dynamic configurations
    """
    print("\n\n" + "=" * 80)
    print("Example: Multi-Tenant Dynamic Configuration")
    print("=" * 80)
    
    # Simulate tenant configurations
    tenants = {
        "tenant-001": {
            "name": "Acme Corp",
            "tier": "enterprise",
            "rate_limit": 500,
            "models": ["gpt-4", "gpt-4-turbo"]
        },
        "tenant-002": {
            "name": "StartupXYZ",
            "tier": "standard",
            "rate_limit": 100,
            "models": ["gpt-3.5-turbo"]
        }
    }
    
    for tenant_id, tenant_info in tenants.items():
        print(f"\n--- Tenant: {tenant_info['name']} ({tenant_id}) ---")
        
        # Generate tenant-specific configuration
        api_key_config = {
            "id": f"tenant-{tenant_id}",
            "owner": tenant_info["name"],
            "claims": {
                "static": {
                    "key": f"tenant-{tenant_id}-key",
                    "tenant_id": tenant_id,
                    "tier": tenant_info["tier"],
                    "models": tenant_info["models"],
                    "rate_limit": tenant_info["rate_limit"],
                    "project": f"tenant-{tenant_id}-project"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{JWT_SERVICE_URL}/token",
                json={
                    "username": "user1",
                    "password": "password123",
                    "api_key_config": api_key_config
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                print(f"✓ Token generated for {tenant_info['name']}")
                print(f"  Tier: {tenant_info['tier']}")
                print(f"  Rate Limit: {tenant_info['rate_limit']}")
                print(f"  Models: {', '.join(tenant_info['models'])}")
            else:
                print(f"✗ Failed to generate token: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("\n")
    print("*" * 80)
    print("CONTROL TOWER INTEGRATION EXAMPLES")
    print("*" * 80)
    print("\nThese examples demonstrate how to use api_key_config payload")
    print("with Control Tower manifests and Front Door integration.")
    print("\nPrerequisites:")
    print("  - JWT Service running on http://localhost:5000")
    print("  - Control Tower running on http://localhost:8000 (for Example 1)")
    print("  - Front Door running on http://localhost:9000 (for token usage)")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    # Run examples
    
    # Example 1: With Control Tower (may fail if Control Tower not running)
    print("\nNote: Example 1 requires Control Tower to be running")
    print("Skipping if not available...\n")
    try:
        token_data = example_sas2py_project()
    except Exception as e:
        print(f"Skipped (Control Tower not available): {e}")
        token_data = None
    
    # Example 2: Direct inline config (always works)
    token_data = example_inline_config_without_control_tower()
    
    # Example 3: Multi-tenant
    example_dynamic_multi_tenant()
    
    # Example 4: Use token with Front Door (if token was generated)
    if token_data:
        print("\nNote: Example 4 requires Front Door to be running")
        print("Skipping if not available...\n")
        try:
            example_use_token_with_front_door(token_data["access_token"])
        except Exception as e:
            print(f"Skipped (Front Door not available): {e}")
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
