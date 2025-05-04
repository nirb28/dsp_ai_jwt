import os
import logging
from typing import Dict, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import ldap, but make it optional
LDAP_AVAILABLE = False
try:
    import ldap
    LDAP_AVAILABLE = True
except ImportError:
    logger.warning("python-ldap module not installed. LDAP authentication will not be available.")
    logger.warning("To enable LDAP authentication, install python-ldap: pip install python-ldap")

def authenticate_ldap(username: str, password: str) -> Tuple[bool, Dict]:
    """
    Authenticate a user using LDAP/Active Directory
    
    Args:
        username: The username to authenticate
        password: The password for authentication
        
    Returns:
        Tuple containing:
            - Boolean indicating if authentication was successful
            - Dict with user data if successful, empty dict otherwise
    """
    if not LDAP_AVAILABLE:
        logger.error("LDAP authentication requested but python-ldap module is not installed")
        return False, {"error": "LDAP authentication is not available. Install python-ldap package."}
    
    try:
        # Get LDAP configuration from environment variables
        ldap_server = os.getenv("LDAP_SERVER", "ldap://localhost:389")
        ldap_base_dn = os.getenv("LDAP_BASE_DN", "dc=example,dc=com")
        ldap_user_dn = os.getenv("LDAP_USER_DN", "cn=users,dc=example,dc=com")
        ldap_admin_dn = os.getenv("LDAP_ADMIN_DN", "")
        ldap_admin_password = os.getenv("LDAP_ADMIN_PASSWORD", "")
        
        # Initialize LDAP connection
        conn = ldap.initialize(ldap_server)
        conn.protocol_version = 3
        conn.set_option(ldap.OPT_REFERRALS, 0)
        
        # Bind with admin credentials if provided (for user search)
        if ldap_admin_dn and ldap_admin_password:
            conn.simple_bind_s(ldap_admin_dn, ldap_admin_password)
            
            # Search for the user
            search_filter = f"(sAMAccountName={username})"
            result = conn.search_s(
                ldap_user_dn, 
                ldap.SCOPE_SUBTREE, 
                search_filter, 
                ['cn', 'mail', 'memberOf']
            )
            
            if not result:
                logger.warning(f"User {username} not found in LDAP")
                return False, {}
                
            user_dn = result[0][0]
            user_data = result[0][1]
        else:
            # Construct the user DN directly if admin search is not available
            user_dn = f"cn={username},{ldap_user_dn}"
            user_data = {}
        
        # Now try to bind with the user's credentials
        conn.simple_bind_s(user_dn, password)
        
        # Authentication successful
        # Extract relevant user info for JWT claims
        claims = {
            "sub": username,
            "name": user_data.get('cn', [b''])[0].decode('utf-8') if 'cn' in user_data else username,
            "email": user_data.get('mail', [b''])[0].decode('utf-8') if 'mail' in user_data else "",
            "groups": [group.decode('utf-8') for group in user_data.get('memberOf', [])] if 'memberOf' in user_data else []
        }
        
        conn.unbind_s()
        return True, claims
        
    except ldap.INVALID_CREDENTIALS:
        logger.warning(f"Invalid credentials for user {username}")
        return False, {}
    except ldap.LDAPError as e:
        logger.error(f"LDAP error: {str(e)}")
        return False, {}
    except Exception as e:
        logger.error(f"Unexpected error during LDAP authentication: {str(e)}")
        return False, {}
