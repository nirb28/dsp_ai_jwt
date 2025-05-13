import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_team_permissions(team_id: str, api_key_id: str, **kwargs) -> Dict[str, Any]:
    """
    Get permissions for a team
    
    Args:
        team_id: The ID of the team
        api_key_id: The ID of the API key
        **kwargs: Additional parameters that might be needed
        
    Returns:
        Dict containing the team permissions
    """
    logger.info(f"Getting permissions for team: {team_id} with API key: {api_key_id}")
    metadata = kwargs.get('metadata', {}) if 'metadata' in kwargs else {}
    
    # Prefer team_permissions from metadata if present
    team_permissions = metadata.get('team_permissions')
    if team_permissions is None:
        # Fallback to hardcoded mock
        team_permissions = {
        "admin-team": {
            "can_manage_users": True,
            "can_create_api_keys": True,
            "can_view_billing": True,
            "max_models_per_request": 5
        },
        "ai-team": {
            "can_manage_users": False,
            "can_create_api_keys": False,
            "can_view_billing": False,
            "max_models_per_request": 3
        },
        "ml-team": {
            "can_manage_users": False,
            "can_create_api_keys": False,
            "can_view_billing": False,
            "max_models_per_request": 2
        }
    }
    
    # Return permissions for the team, or a default set if not found
    return team_permissions.get(team_id, {
        "can_manage_users": False,
        "can_create_api_keys": False,
        "can_view_billing": False,
        "max_models_per_request": 1
    })
