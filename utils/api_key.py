import os
import yaml
import json
import logging
import importlib
import requests
from typing import Dict, Any, Optional, Callable, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the name of the base API key file
BASE_API_KEY_FILE = "base_api_key.yaml"

def get_additional_claims(api_key: str = None, user_context: Dict[str, Any] = None) -> Dict:
    """
    Get additional claims based on the provided API key
    
    Args:
        api_key: The API key to look up, if None or empty, will use the base API key
        user_context: Optional context about the user (e.g., user_id, team_id)
        
    Returns:
        Dict with additional claims to include in the JWT token
    """
    try:
        if user_context is None:
            user_context = {}
            
        # Get API keys directory path from environment variable or use default
        api_keys_dir = os.getenv("API_KEYS_DIR", "config/api_keys")
        
        # Check if directory exists
        if not os.path.exists(api_keys_dir):
            logger.error(f"API keys directory not found: {api_keys_dir}")
            return {}
        
        # Determine which API key file to use
        api_key_file = None
        
        # If API key is provided, try to find its config file
        if api_key:
            specific_key_file = os.path.join(api_keys_dir, f"{api_key}.yaml")
            if os.path.exists(specific_key_file):
                api_key_file = specific_key_file
            else:
                logger.warning(f"Config file for API key not found: {api_key}")
                logger.info("Falling back to base API key")
        
        # If no API key provided or specific key not found, use the base API key
        if not api_key_file:
            base_key_file = os.path.join(api_keys_dir, BASE_API_KEY_FILE)
            if os.path.exists(base_key_file):
                api_key_file = base_key_file
                logger.info("Using base API key")
            else:
                logger.warning(f"Base API key file not found: {BASE_API_KEY_FILE}")
                return {}
        
        # Load API key config from file
        with open(api_key_file, 'r') as f:
            key_data = yaml.safe_load(f)
        
        # Extract static claims
        static_claims = key_data.get('claims', {}).get('static', {})
        
        # Process dynamic claims
        dynamic_claims = process_dynamic_claims(
            key_data.get('claims', {}).get('dynamic', {}),
            user_context,
            api_key or "base_api_key",  # Use base_api_key as the key name if no specific key
            key_data.get('id', '')
        )
        
        # Use only the static and dynamic claims, no metadata
        additional_claims = {**static_claims, **dynamic_claims}
        
        return additional_claims
        
    except Exception as e:
        logger.error(f"Unexpected error getting additional claims: {str(e)}")
        return {}

def process_dynamic_claims(
    dynamic_claims_config: Dict[str, Any],
    user_context: Dict[str, Any],
    api_key: str,
    api_key_id: str
) -> Dict[str, Any]:
    """
    Process dynamic claims configuration and execute the specified functions or API calls
    
    Args:
        dynamic_claims_config: Configuration for dynamic claims
        user_context: Context about the user (e.g., user_id, team_id)
        api_key: The original API key string
        api_key_id: The ID associated with the API key
        
    Returns:
        Dict with resolved dynamic claims
    """
    if not dynamic_claims_config:
        return {}
    
    result = {}
    
    for claim_name, claim_config in dynamic_claims_config.items():
        try:
            claim_type = claim_config.get('type', '')
            
            if claim_type == 'function':
                # Execute a Python function to get the claim value
                claim_value = execute_function_claim(claim_config, user_context, api_key, api_key_id)
                if claim_value:
                    result[claim_name] = claim_value
                    
            elif claim_type == 'api':
                # Call an external API to get the claim value
                claim_value = execute_api_claim(claim_config, user_context, api_key, api_key_id)
                if claim_value:
                    result[claim_name] = claim_value
                    
            else:
                logger.warning(f"Unknown claim type: {claim_type} for claim: {claim_name}")
                
        except Exception as e:
            logger.error(f"Error processing dynamic claim '{claim_name}': {str(e)}")
    
    return result

def execute_function_claim(
    claim_config: Dict[str, Any],
    user_context: Dict[str, Any],
    api_key: str,
    api_key_id: str
) -> Optional[Any]:
    """
    Execute a function-based dynamic claim
    
    Args:
        claim_config: Configuration for the function claim
        user_context: Context about the user
        api_key: The original API key string
        api_key_id: The ID associated with the API key
        
    Returns:
        The claim value returned by the function, or None if execution failed
    """
    try:
        module_name = claim_config.get('module')
        function_name = claim_config.get('function')
        
        if not module_name or not function_name:
            logger.error("Missing module or function name in function claim configuration")
            return None
        
        # Import the module
        module = importlib.import_module(module_name)
        
        # Get the function
        func = getattr(module, function_name)
        
        # Prepare arguments
        args = claim_config.get('args', {})
        processed_args = {}
        
        # Replace placeholders in arguments with values from context
        for arg_name, arg_value in args.items():
            if isinstance(arg_value, str) and arg_value.startswith('{') and arg_value.endswith('}'):
                # Extract the placeholder name
                placeholder = arg_value[1:-1]
                
                if placeholder == 'api_key':
                    processed_args[arg_name] = api_key
                elif placeholder == 'api_key_id':
                    processed_args[arg_name] = api_key_id
                else:
                    # Look for the value in user_context
                    processed_args[arg_name] = user_context.get(placeholder, '')
            else:
                processed_args[arg_name] = arg_value
        
        # Call the function with the processed arguments
        return func(**processed_args)
        
    except Exception as e:
        logger.error(f"Error executing function claim: {str(e)}")
        return None

def execute_api_claim(
    claim_config: Dict[str, Any],
    user_context: Dict[str, Any],
    api_key: str,
    api_key_id: str
) -> Optional[Any]:
    """
    Execute an API-based dynamic claim
    
    Args:
        claim_config: Configuration for the API claim
        user_context: Context about the user
        api_key: The original API key string
        api_key_id: The ID associated with the API key
        
    Returns:
        The claim value returned by the API, or None if execution failed
    """
    try:
        url = claim_config.get('url')
        method = claim_config.get('method', 'GET')
        headers = claim_config.get('headers', {})
        response_field = claim_config.get('response_field')
        
        if not url:
            logger.error("Missing URL in API claim configuration")
            return None
        
        # Replace placeholders in URL
        processed_url = url
        for placeholder, value in {
            '{api_key}': api_key,
            '{api_key_id}': api_key_id,
            **{f'{{{k}}}': v for k, v in user_context.items()}
        }.items():
            processed_url = processed_url.replace(placeholder, str(value))
        
        # Replace placeholders in headers
        processed_headers = {}
        for header_name, header_value in headers.items():
            if isinstance(header_value, str) and '{' in header_value and '}' in header_value:
                for placeholder, value in {
                    '{api_key}': api_key,
                    '{api_key_id}': api_key_id,
                    '{internal_token}': os.getenv('INTERNAL_API_TOKEN', ''),
                    **{f'{{{k}}}': v for k, v in user_context.items()}
                }.items():
                    header_value = header_value.replace(placeholder, str(value))
            processed_headers[header_name] = header_value
        
        # Make the API request
        response = requests.request(
            method=method,
            url=processed_url,
            headers=processed_headers,
            timeout=5  # 5 second timeout
        )
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
        
        # Parse the response
        response_data = response.json()
        
        # Extract the specified field if provided
        if response_field:
            # Support for nested fields using dot notation (e.g., "data.user.quota")
            parts = response_field.split('.')
            value = response_data
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    logger.error(f"Response field '{response_field}' not found in API response")
                    return None
            return value
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error executing API claim: {str(e)}")
        return None
