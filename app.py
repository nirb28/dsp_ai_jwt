import os
from datetime import timedelta
from flask import Flask, jsonify, request, make_response, render_template
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, decode_token, get_jwt
)
from dotenv import load_dotenv
import logging
import pathlib
from datetime import datetime

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
from utils.api_key import get_additional_claims

# Ensure the templates directory exists
templates_dir = pathlib.Path(__file__).parent / 'templates'
templates_dir.mkdir(exist_ok=True)

# Initialize Flask app
app = Flask(__name__, 
            template_folder=str(templates_dir))

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
