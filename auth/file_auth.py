import os
import yaml
import logging
import hashlib
from typing import Dict, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def authenticate_file(username: str, password: str) -> Tuple[bool, Dict]:
    """
    Authenticate a user using a users file
    
    Args:
        username: The username to authenticate
        password: The password for authentication
        
    Returns:
        Tuple containing:
            - Boolean indicating if authentication was successful
            - Dict with user data if successful, empty dict otherwise
    """
    try:
        # Get user file path from environment variable or use default
        users_file = os.getenv("USERS_FILE", "config/users.yaml")
        
        # Check if file exists
        if not os.path.exists(users_file):
            logger.error(f"Users file not found: {users_file}")
            return False, {}
        
        # Load users from file
        with open(users_file, 'r') as f:
            users = yaml.safe_load(f)
        
        # Check if user exists
        if username not in users:
            logger.warning(f"User {username} not found in users file")
            return False, {}
        
        user_data = users[username]
        
        # Verify password
        # Note: In production, you'd want to use a secure password hashing library like bcrypt
        stored_password = user_data.get('password', '')
        
        # Simple SHA-256 hashing for demonstration purposes
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        if stored_password != hashed_password:
            logger.warning(f"Invalid password for user {username}")
            return False, {}
        
        # Authentication successful
        # Prepare claims for JWT
        claims = {
            "sub": username,
            "name": user_data.get('name', username),
            "email": user_data.get('email', ''),
            "groups": user_data.get('groups', []),
            "roles": user_data.get('roles', [])
        }
        
        return True, claims
        
    except Exception as e:
        logger.error(f"Unexpected error during file authentication: {str(e)}")
        return False, {}
