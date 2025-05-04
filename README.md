# DSP AI JWT Token Service

A Flask-based JWT token service designed for integration with APISIX gateway. This service provides JWT token generation with flexible authentication methods and support for dynamic claims based on API keys.

## Features

- **Multiple Authentication Methods**: Support for LDAP (Active Directory) and file-based authentication
- **Configurable JWT Tokens**: JWT tokens are signed with a configurable key that can be shared with the APISIX gateway
- **Individual API Key Configuration**: Each API key has its own configuration file
- **Dynamic Claims**: Support for generating claims dynamically via:
  - Function calls (Python functions)
  - API calls (External HTTP services)
- **Token Decoding**: Simple mechanism to decode and verify JWT tokens

## Setup

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-org/dsp_ai_jwt.git
   cd dsp_ai_jwt
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Copy the example environment file and update it:
   ```
   copy .env.example .env
   ```
   
5. Update the `.env` file with your configuration settings.

## Configuration

### Authentication Methods

#### File-based Authentication

User credentials are stored in `config/users.yaml`. Example format:

```yaml
username:
  password: hashed_password  # SHA-256 hash
  name: User Full Name
  email: user@example.com
  groups:
    - group1
    - group2
  roles:
    - role1
    - role2
```

#### LDAP Authentication

LDAP authentication requires the following settings in your `.env` file:

```
LDAP_SERVER=ldap://your-ldap-server:389
LDAP_BASE_DN=dc=example,dc=com
LDAP_USER_DN=cn=users,dc=example,dc=com
LDAP_ADMIN_DN=cn=admin,dc=example,dc=com
LDAP_ADMIN_PASSWORD=admin_password
```

### API Key Configuration

Each API key has its own configuration file in the `config/api_keys/` directory. The filename should match the API key value (e.g., `api_key_openai_1234567890.yaml`).

Example API key configuration:

```yaml
id: service-id
owner: Team Name
provider_permissions:
  - provider1
  - provider2
endpoint_permissions:
  - /v1/endpoint1
  - /v1/endpoint2
claims:
  static:
    # Static claims that will always be included
    tier: premium
    models:
      - model1
      - model2
    rate_limit: 100
  dynamic:
    # Dynamic claims that will be resolved at runtime
    quota:
      type: function
      module: claims.quota
      function: get_remaining_quota
      args:
        user_id: "{user_id}"  # Placeholder that will be replaced
    usage_stats:
      type: api
      url: "http://usage-service/api/stats/{api_key_id}"
      headers:
        Authorization: "Bearer {internal_token}"
      method: GET
      response_field: data
```

#### Dynamic Claims

Dynamic claims can be generated in two ways:

1. **Function-based**:
   ```yaml
   claim_name:
     type: function
     module: package.module
     function: function_name
     args:
       arg1: value1
       arg2: "{placeholder}"  # Will be replaced with context values
   ```

2. **API-based**:
   ```yaml
   claim_name:
     type: api
     url: "http://api-endpoint/{placeholder}"
     method: GET|POST|PUT|DELETE
     headers:
       Header-Name: "value"
     response_field: path.to.field  # Optional dot notation to extract specific data
   ```

Available placeholders:
- `{user_id}`: The authenticated user's ID
- `{api_key}`: The original API key
- `{api_key_id}`: The ID of the API key
- `{team_id}`: The team ID of the user
- `{internal_token}`: Token for internal service communication

## API Endpoints

### Generate JWT Token

```
POST /token
Content-Type: application/json

{
  "username": "user",
  "password": "password",
  "api_key": "api_key_value"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi..."
}
```

### Refresh JWT Token

```
POST /refresh
Authorization: Bearer {refresh_token}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAi..."
}
```

### Decode JWT Token

```
POST /decode
Content-Type: application/json

{
  "token": "eyJ0eXAi..."
}
```

**Response**:
```json
{
  "sub": "username",
  "tier": "premium",
  "provider_permissions": ["openai", "groq"],
  ...
}
```

## Running Tests

```
pytest
```

## Integration with APISIX

Configure APISIX to use the JWT token for authentication by setting up the JWT plugin with the same secret key.

Example APISIX configuration:

```json
{
  "plugins": {
    "jwt-auth": {
      "key": "user-key",
      "secret": "your-jwt-secret-key"
    }
  }
}
```

## Development

### Creating New Dynamic Claim Providers

1. Add a new module in the `claims/` directory
2. Implement functions that accept parameters and return dictionaries of claim values
3. Reference the new function in API key configurations


### HELP - DELETE and Clean these
Testing the Application
To run the tests, you can use pytest with your virtual environment:


# Make sure your virtual environment is activated
.\venv\Scripts\activate

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=.

# Run a specific test file
pytest tests/test_authentication.py

# Run tests in verbose mode
pytest -v
The tests will use a test configuration defined in tests/conftest.py, which creates temporary test files for users and API keys.

Manually Testing the API
You can also test the API endpoints manually using tools like curl or Postman:

Generate a token:
curl -X POST http://localhost:5000/token -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"password\",\"api_key\":\"api_key_openai_1234567890\"}"

Decode a token:
curl -X POST http://localhost:5000/decode -H "Content-Type: application/json" -d "{\"token\":\"your-jwt-token-here\"}"

Access a protected endpoint:
curl -X GET http://localhost:5000/protected -H "Authorization: Bearer your-jwt-token-here"
