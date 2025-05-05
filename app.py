import os
from datetime import timedelta, datetime
from flask import Flask, jsonify, request, make_response, render_template, send_from_directory
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, decode_token, get_jwt
)
from dotenv import load_dotenv
import logging
import pathlib
import yaml
import uuid
import glob
from flask_swagger_ui import get_swaggerui_blueprint
from swagger_config import get_swagger_dict, get_swagger_json, get_swagger_yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import authentication methods
from auth.file_auth import authenticate_file
from auth.ldap_auth import authenticate_ldap, LDAP_AVAILABLE
from utils.api_key import get_additional_claims, BASE_API_KEY_FILE

# Ensure the templates directory exists
templates_dir = pathlib.Path(__file__).parent / 'templates'
templates_dir.mkdir(exist_ok=True)

# Initialize Flask app
app = Flask(__name__, 
            template_folder=str(templates_dir))

# Configure Swagger UI
SWAGGER_URL = '/dspai-docs'  # URL for exposing Swagger UI
API_URL = '/swagger.json'  # Where to get the swagger spec from

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "JWT Auth API Documentation",
        'deepLinking': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
    }
)

# Register the Swagger UI blueprint
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Endpoints to serve the Swagger specification
@app.route('/swagger.json')
def swagger_json():
    return get_swagger_json()

@app.route('/swagger.yaml')
def swagger_yaml():
    return get_swagger_yaml()

# Configure Flask-JWT-Extended
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)  # Default if not specified in API key
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

# Authentication method
AUTH_METHOD = os.getenv("AUTH_METHOD", "file")  # "ldap" or "file"

# Whether to always include base API key claims
ALWAYS_USE_BASE_CLAIMS = os.getenv("ALWAYS_USE_BASE_CLAIMS", "true").lower() == "true"

# Check if LDAP is requested but not available
if AUTH_METHOD == "ldap" and not LDAP_AVAILABLE:
    logger.warning("LDAP authentication method selected but python-ldap is not installed.")
    logger.warning("Falling back to file-based authentication.")
    logger.warning("To use LDAP authentication, install python-ldap: pip install python-ldap")
    AUTH_METHOD = "file"

jwt = JWTManager(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/token', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    api_key = request.json.get('api_key', None)

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    # Authenticate based on the configured method
    if AUTH_METHOD == "ldap":
        authenticated, user_data = authenticate_ldap(username, password)
    else:  # file-based authentication
        authenticated, user_data = authenticate_file(username, password)

    if not authenticated:
        error_message = "Invalid username or password"
        if "error" in user_data:
            error_message = user_data["error"]
        return jsonify({"error": error_message}), 401

    # Create user context for dynamic claims processing
    user_context = {
        "user_id": username,
        "email": user_data.get("email", ""),
        "groups": user_data.get("groups", []),
        "roles": user_data.get("roles", []),
        "team_id": get_team_id_from_user(username, user_data)
    }

    # Get additional claims based on API key if provided, otherwise use base API key
    # The get_additional_claims function now handles using the base API key when api_key is None
    additional_claims = get_additional_claims(api_key, user_context)
    
    # Log which API key is being used
    if api_key:
        logger.info(f"Using provided API key: {api_key}")
    else:
        logger.info("No API key provided, using base API key")

    # Merge user data with additional claims
    claims = {**user_data, **additional_claims}
    
    # Get expiration time from API key configuration if available
    expires_delta = app.config["JWT_ACCESS_TOKEN_EXPIRES"]  # Default
    if 'exp_hours' in claims:
        expires_delta = timedelta(hours=claims['exp_hours'])
        logger.info(f"Using custom expiration time from API key: {claims['exp_hours']} hours")
        # Remove exp_hours from claims to avoid conflicts
        claims.pop('exp_hours')
    
    # Create tokens with custom expiration if specified
    access_token = create_access_token(
        identity=username, 
        additional_claims=claims,
        expires_delta=expires_delta,
        fresh=True  # Mark the token as fresh since it's from direct login
    )
    refresh_token = create_refresh_token(identity=username, additional_claims=claims)

    return jsonify(access_token=access_token, refresh_token=refresh_token), 200

def get_team_id_from_user(username, user_data):
    """
    Determine the team ID from the user's data
    This is a simple implementation - in a real app, you would look this up from a database
    
    Args:
        username: The username of the user
        user_data: The user data retrieved during authentication
        
    Returns:
        A team ID string
    """
    # Simple mapping based on groups
    groups = user_data.get("groups", [])
    
    if "administrators" in groups or "admins" in groups:
        return "admin-team"
    elif "ai-team" in groups:
        return "ai-team"
    elif "ml-team" in groups:
        return "ml-team"
    
    # Default team
    return "general-users"

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    # Get all claims from the current refresh token
    jwt_claims = get_jwt()
    
    # Remove JWT reserved claims that shouldn't be transferred
    reserved_claims = ['exp', 'iat', 'nbf', 'jti', 'type', 'fresh']
    additional_claims = {key: value for key, value in jwt_claims.items() 
                         if key not in reserved_claims}
    
    # Create new access token with the same additional claims
    access_token = create_access_token(
        identity=current_user,
        additional_claims=additional_claims
    )
    
    # Log the claims being carried over
    logger.info(f"Refreshing token for user {current_user} with claims: {additional_claims}")
    
    return jsonify(access_token=access_token), 200

@app.route('/decode', methods=['POST'])
def decode():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    token = request.json.get('token', None)
    if not token:
        return jsonify({"error": "Missing token"}), 400

    try:
        decoded = decode_token(token)
        return jsonify(decoded), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/sensitive-action', methods=['POST'])
@jwt_required(fresh=True)
def sensitive_action():
    """This endpoint requires a fresh token (from direct login, not from refresh)"""
    current_user = get_jwt_identity()
    jwt_claims = get_jwt()
    
    # Demo of a sensitive action like password change, payment, etc.
    return jsonify({
        "message": "Sensitive action performed successfully",
        "user": current_user,
        "token_status": "Fresh token confirmed",
        "token_freshness": jwt_claims.get('fresh', False),
        "action_time": str(datetime.now())
    }), 200

# API Key Management Endpoints
@app.route('/api-keys', methods=['GET'])
@jwt_required(fresh=True)
def get_api_keys():
    """Get a list of all API keys"""
    # Only allow administrators to access this endpoint
    claims = get_jwt()
    groups = claims.get('groups', [])
    
    if 'administrators' not in groups and 'admins' not in groups:
        return jsonify({"error": "Administrator access required"}), 403
    
    # Get API keys directory path
    api_keys_dir = os.getenv("API_KEYS_DIR", "config/api_keys")
    
    if not os.path.exists(api_keys_dir):
        return jsonify({"error": "API keys directory not found"}), 500
    
    # Get all API key files (excluding base key)
    api_key_files = glob.glob(os.path.join(api_keys_dir, "*.yaml"))
    api_keys = []
    
    for key_file in api_key_files:
        filename = os.path.basename(key_file)
        if filename != BASE_API_KEY_FILE:
            try:
                with open(key_file, 'r') as f:
                    key_data = yaml.safe_load(f)
                    
                api_keys.append({
                    'filename': filename,
                    'id': key_data.get('id', ''),
                    'owner': key_data.get('owner', ''),
                    'provider_permissions': key_data.get('provider_permissions', []),
                    'endpoint_permissions': key_data.get('endpoint_permissions', []),
                    'static_claims': key_data.get('claims', {}).get('static', {})
                })
            except Exception as e:
                logger.error(f"Error reading API key file {filename}: {str(e)}")
    
    return jsonify(api_keys), 200

@app.route('/api-keys/<api_key_id>', methods=['GET'])
@jwt_required(fresh=True)
def get_api_key(api_key_id):
    """Get details for a specific API key"""
    # Only allow administrators to access this endpoint
    claims = get_jwt()
    groups = claims.get('groups', [])
    
    if 'administrators' not in groups and 'admins' not in groups:
        return jsonify({"error": "Administrator access required"}), 403
    
    # Get API keys directory path
    api_keys_dir = os.getenv("API_KEYS_DIR", "config/api_keys")
    
    # Look for the API key file
    api_key_files = glob.glob(os.path.join(api_keys_dir, "*.yaml"))
    
    for key_file in api_key_files:
        try:
            with open(key_file, 'r') as f:
                key_data = yaml.safe_load(f)
                
                if key_data.get('id') == api_key_id:
                    return jsonify(key_data), 200
        except Exception as e:
            logger.error(f"Error reading API key file {key_file}: {str(e)}")
    
    return jsonify({"error": "API key not found"}), 404

@app.route('/api-keys', methods=['POST'])
@jwt_required(fresh=True)
def create_api_key():
    """Create a new API key"""
    # Only allow administrators to access this endpoint
    claims = get_jwt()
    groups = claims.get('groups', [])
    
    if 'administrators' not in groups and 'admins' not in groups:
        return jsonify({"error": "Administrator access required"}), 403
    
    # Check request data
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    
    # Validate required fields
    required_fields = ['owner']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
    
    # Generate API key string and ID
    api_key_string = str(uuid.uuid4()).replace('-', '')
    api_key_id = f"api-key-{str(uuid.uuid4())[:8]}"
    
    # Create API key data
    api_key_data = {
        'id': api_key_id,
        'owner': data['owner'],
        'provider_permissions': data.get('provider_permissions', ['openai']),
        'endpoint_permissions': data.get('endpoint_permissions', 
                                        ['/v1/chat/completions', '/v1/embeddings']),
        'claims': {
            'static': data.get('static_claims', {
                'models': ['gpt-3.5-turbo'],
                'rate_limit': 20,
                'tier': 'standard',
                'exp_hours': 1
            }),
            'dynamic': data.get('dynamic_claims', {})
        }
    }
    
    # Get API keys directory path
    api_keys_dir = os.getenv("API_KEYS_DIR", "config/api_keys")
    
    # Ensure API keys directory exists
    if not os.path.exists(api_keys_dir):
        os.makedirs(api_keys_dir)
    
    # Save API key to file
    api_key_file = os.path.join(api_keys_dir, f"{api_key_string}.yaml")
    
    try:
        with open(api_key_file, 'w') as f:
            yaml.dump(api_key_data, f, default_flow_style=False)
    except Exception as e:
        logger.error(f"Error creating API key file: {str(e)}")
        return jsonify({"error": f"Failed to create API key: {str(e)}"}), 500
    
    # Return API key data with the key string
    return jsonify({
        **api_key_data,
        'api_key': api_key_string
    }), 201

@app.route('/api-keys/<api_key_string>', methods=['PUT'])
@jwt_required(fresh=True)
def update_api_key(api_key_string):
    """Update an existing API key"""
    # Only allow administrators to access this endpoint
    claims = get_jwt()
    groups = claims.get('groups', [])
    
    if 'administrators' not in groups and 'admins' not in groups:
        return jsonify({"error": "Administrator access required"}), 403
    
    # Check request data
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    
    # Get API keys directory path
    api_keys_dir = os.getenv("API_KEYS_DIR", "config/api_keys")
    
    # Check if API key file exists
    api_key_file = os.path.join(api_keys_dir, f"{api_key_string}.yaml")
    
    if not os.path.exists(api_key_file):
        return jsonify({"error": "API key not found"}), 404
    
    try:
        # Read existing API key data
        with open(api_key_file, 'r') as f:
            existing_data = yaml.safe_load(f)
        
        # Update API key data with new values while preserving the ID
        api_key_id = existing_data['id']
        
        # Update fields from request data
        updated_data = {
            'id': api_key_id,  # Preserve original ID
            'owner': data.get('owner', existing_data.get('owner')),
            'provider_permissions': data.get('provider_permissions', 
                                          existing_data.get('provider_permissions', [])),
            'endpoint_permissions': data.get('endpoint_permissions', 
                                          existing_data.get('endpoint_permissions', [])),
            'claims': {
                'static': data.get('static_claims', existing_data.get('claims', {}).get('static', {})),
                'dynamic': data.get('dynamic_claims', existing_data.get('claims', {}).get('dynamic', {}))
            }
        }
        
        # Save updated API key to file
        with open(api_key_file, 'w') as f:
            yaml.dump(updated_data, f, default_flow_style=False)
        
        return jsonify(updated_data), 200
    except Exception as e:
        logger.error(f"Error updating API key: {str(e)}")
        return jsonify({"error": f"Failed to update API key: {str(e)}"}), 500

@app.route('/api-keys/<api_key_string>', methods=['DELETE'])
@jwt_required(fresh=True)
def delete_api_key(api_key_string):
    """Delete an API key"""
    # Only allow administrators to access this endpoint
    claims = get_jwt()
    groups = claims.get('groups', [])
    
    if 'administrators' not in groups and 'admins' not in groups:
        return jsonify({"error": "Administrator access required"}), 403
    
    # Get API keys directory path
    api_keys_dir = os.getenv("API_KEYS_DIR", "config/api_keys")
    
    # Check if API key file exists
    api_key_file = os.path.join(api_keys_dir, f"{api_key_string}.yaml")
    
    if not os.path.exists(api_key_file):
        return jsonify({"error": "API key not found"}), 404
    
    try:
        # Delete API key file
        os.remove(api_key_file)
        return jsonify({"message": "API key deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting API key: {str(e)}")
        return jsonify({"error": f"Failed to delete API key: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
