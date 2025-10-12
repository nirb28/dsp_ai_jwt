# JWE (JSON Web Encryption) Support

## Overview

The DSP AI JWT service now supports **JWE (JSON Web Encryption)** for symmetric encryption of JWT tokens. This adds an additional layer of security by encrypting the entire JWT token, making it unreadable without the encryption key.

## What is JWE?

JWE is a standard (RFC 7516) for encrypting content using JSON-based data structures. Unlike JWT which only provides integrity through signatures, JWE provides **confidentiality** by encrypting the payload.

### JWT vs JWE

- **JWT (JSON Web Token)**: Signed tokens that provide integrity and authentication. The payload is Base64-encoded and readable by anyone.
- **JWE (JSON Web Encryption)**: Encrypted tokens that provide confidentiality. The payload is encrypted and unreadable without the decryption key.

## Features

### Supported Algorithms

#### Key Management
- **`dir`**: Direct use of shared symmetric key (recommended for symmetric encryption)

#### Content Encryption
- **`A128GCM`**: AES-128 GCM (requires 16-byte key)
- **`A192GCM`**: AES-192 GCM (requires 24-byte key)
- **`A256GCM`**: AES-256 GCM (requires 32-byte key) - **Recommended**
- **`A128CBC-HS256`**: AES-128 CBC with HMAC-SHA256 (requires 32-byte key)
- **`A192CBC-HS384`**: AES-192 CBC with HMAC-SHA384 (requires 48-byte key)
- **`A256CBC-HS512`**: AES-256 CBC with HMAC-SHA512 (requires 64-byte key)

#### Compression
- **`null`**: No compression (default)
- **`DEF`**: DEFLATE compression (reduces size for large payloads)

## Configuration

### 1. Control Tower Manifest Configuration

Add JWE configuration to your JWT module in the Control Tower manifest:

```json
{
  "name": "secure-auth",
  "type": "jwt_config",
  "config": {
    "secret_key": "${JWT_SECRET_KEY}",
    "algorithm": "HS256",
    "expiration_minutes": 30,
    "jwe_enabled": true,
    "jwe_encryption_key": "${JWE_ENCRYPTION_KEY}",
    "jwe_algorithm": "dir",
    "jwe_encryption": "A256GCM",
    "jwe_compression": null
  }
}
```

### 2. API Key Configuration

Configure JWE in your API key YAML file:

```yaml
id: api-key-secure-001
owner: security-team

# JWE Configuration
jwe_config:
  enabled: true
  encryption_key: "${JWE_ENCRYPTION_KEY}"  # Environment variable
  algorithm: "dir"
  encryption: "A256GCM"
  compression: null  # or "DEF" for compression

claims:
  static:
    models: ["gpt-4"]
    tier: "enterprise"
    exp_hours: 1
```

### 3. Environment Variables

Set up your encryption key in environment variables:

```bash
# Generate a new key
curl -X POST http://localhost:5000/generate-jwe-key

# Add to .env file
JWE_ENCRYPTION_KEY=your_base64_encoded_key_here
```

## Usage

### Generating Encryption Keys

#### Using the API

```bash
# Generate A256GCM key (default)
curl -X POST http://localhost:5000/generate-jwe-key \
  -H "Content-Type: application/json"

# Generate with specific algorithm and format
curl -X POST http://localhost:5000/generate-jwe-key \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "A256GCM",
    "format": "base64"
  }'
```

#### Using Python

```python
from utils.jwe_handler import JWEHandler

# Generate key
key = JWEHandler.generate_encryption_key('A256GCM', 'base64')
print(f"Encryption Key: {key}")

# Or using command line
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

### Token Generation with JWE

When an API key has JWE enabled, tokens are automatically encrypted:

```bash
# Login with JWE-enabled API key
curl -X POST http://localhost:5000/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password123",
    "api_key": "api_key_jwe_example"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGc...encrypted_jwe_token...",
  "refresh_token": "eyJhbGc...encrypted_jwe_token...",
  "token_type": "JWE",
  "encryption": "A256GCM",
  "note": "Tokens are JWE-encrypted. Use /decrypt-jwe endpoint to extract JWT."
}
```

### Manual Encryption/Decryption

#### Encrypt a JWT Token

```bash
curl -X POST http://localhost:5000/encrypt-jwe \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "encryption_key": "your_base64_key",
    "encryption": "A256GCM",
    "compression": null
  }'
```

#### Decrypt a JWE Token

```bash
curl -X POST http://localhost:5000/decrypt-jwe \
  -H "Content-Type: application/json" \
  -d '{
    "jwe_token": "eyJhbGc...encrypted...",
    "encryption_key": "your_base64_key",
    "encryption": "A256GCM",
    "extract_jwt": true
  }'
```

#### Encrypt Payload Directly

```bash
curl -X POST http://localhost:5000/encrypt-jwe \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "user": "john.doe",
      "role": "admin",
      "permissions": ["read", "write"]
    },
    "encryption_key": "your_base64_key",
    "encryption": "A256GCM"
  }'
```

### Using in Code

#### Python Example

```python
from utils.jwe_handler import (
    JWEHandler,
    encrypt_jwt_token,
    decrypt_jwe_token
)

# Initialize handler
encryption_key = "your_base64_encoded_key"
handler = JWEHandler(
    encryption_key=encryption_key,
    content_encryption='A256GCM'
)

# Encrypt a JWT token
jwt_token = "eyJhbGci..."
encrypted_token = encrypt_jwt_token(
    jwt_token,
    encryption_key,
    'A256GCM'
)

# Decrypt JWE token
decrypted_jwt = decrypt_jwe_token(
    encrypted_token,
    encryption_key,
    'A256GCM'
)
```

## API Endpoints

### POST /generate-jwe-key

Generate a new symmetric encryption key.

**Request:**
```json
{
  "algorithm": "A256GCM",  // Optional, default: A256GCM
  "format": "base64"       // Optional: "base64" or "hex"
}
```

**Response:**
```json
{
  "encryption_key": "base64_encoded_key",
  "algorithm": "A256GCM",
  "format": "base64",
  "key_size_bytes": 32,
  "note": "Store this key securely! Add it to your environment variables."
}
```

### POST /encrypt-jwe

Encrypt a JWT token or payload.

**Request:**
```json
{
  "token": "jwt_token",           // Optional: JWT to encrypt
  "payload": {...},                // Optional: Payload to encrypt
  "encryption_key": "base64_key",  // Required
  "encryption": "A256GCM",         // Optional, default: A256GCM
  "compression": null              // Optional: null or "DEF"
}
```

**Response:**
```json
{
  "jwe_token": "encrypted_token",
  "encryption": "A256GCM",
  "compression": null
}
```

### POST /decrypt-jwe

Decrypt a JWE token.

**Request:**
```json
{
  "jwe_token": "encrypted_token",
  "encryption_key": "base64_key",
  "encryption": "A256GCM",       // Optional, default: A256GCM
  "extract_jwt": true            // Optional: extract JWT or full payload
}
```

**Response (extract_jwt=true):**
```json
{
  "jwt_token": "decrypted_jwt",
  "note": "Use /decode endpoint to decode the JWT token"
}
```

**Response (extract_jwt=false):**
```json
{
  "payload": {...}
}
```

### POST /token (Enhanced)

Automatically encrypts tokens if API key has JWE enabled.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password",
  "api_key": "api_key_with_jwe"
}
```

**Response (JWE enabled):**
```json
{
  "access_token": "encrypted_jwe_token",
  "refresh_token": "encrypted_jwe_token",
  "token_type": "JWE",
  "encryption": "A256GCM",
  "note": "Tokens are JWE-encrypted."
}
```

## Security Best Practices

### 1. Key Management

- **Generate Strong Keys**: Use cryptographically secure random keys
- **Key Storage**: Store keys in environment variables or secure key management systems
- **Key Rotation**: Implement regular key rotation policies
- **Never Hardcode**: Never hardcode encryption keys in source code

### 2. Algorithm Selection

- **Recommended**: Use `A256GCM` for maximum security
- **GCM vs CBC**: Prefer GCM modes (authenticated encryption) over CBC modes
- **Key Size**: Larger keys (256-bit) provide better security

### 3. Encryption Key Size Requirements

| Algorithm | Key Size | Security Level |
|-----------|----------|----------------|
| A128GCM | 16 bytes (128 bits) | Good |
| A192GCM | 24 bytes (192 bits) | Better |
| A256GCM | 32 bytes (256 bits) | **Best** |
| A128CBC-HS256 | 32 bytes | Good |
| A192CBC-HS384 | 48 bytes | Better |
| A256CBC-HS512 | 64 bytes | **Best** |

### 4. Compression Considerations

- Use `DEF` compression only for large payloads
- Compression can reveal information about payload structure
- For sensitive data, prefer no compression

### 5. Environment-Specific Keys

Use different encryption keys for different environments:

```bash
# Development
DEV_JWE_KEY=dev_base64_key

# Production
PROD_JWE_KEY=prod_base64_key
```

## Use Cases

### 1. High-Security Applications

JWE is ideal for applications handling sensitive data:
- Healthcare systems (HIPAA compliance)
- Financial services (PCI DSS compliance)
- Government applications
- Legal/confidential document systems

### 2. Token Transit Security

Encrypt tokens when transmitting through:
- Untrusted networks
- Third-party APIs
- Public channels
- Multi-hop architectures

### 3. Compliance Requirements

JWE helps meet regulatory requirements for:
- Data encryption in transit
- Confidentiality guarantees
- Privacy protection

## Performance Considerations

- **Overhead**: JWE adds encryption/decryption overhead (~1-5ms per operation)
- **Token Size**: JWE tokens are larger than JWT tokens
- **Compression**: Use compression for large payloads to reduce size
- **Caching**: Consider caching decrypted tokens when appropriate

## Troubleshooting

### Invalid Key Size Error

```
ValueError: Invalid key size: expected 32 bytes for A256GCM, got X bytes
```

**Solution**: Ensure your encryption key is the correct size for the algorithm.

```python
# Generate correct size key
key = JWEHandler.generate_encryption_key('A256GCM', 'base64')
```

### Decryption Failed

```
Error: Decryption failed
```

**Possible Causes**:
1. Wrong encryption key
2. Mismatched algorithm
3. Corrupted token
4. Token tampered with

**Solution**: Verify you're using the same key and algorithm used for encryption.

### Environment Variable Not Set

```
JWE encryption key environment variable not set: JWE_ENCRYPTION_KEY
```

**Solution**: Set the environment variable:

```bash
export JWE_ENCRYPTION_KEY=your_base64_key
```

## Testing

Run JWE tests:

```bash
# Run all JWE tests
pytest tests/test_jwe.py -v

# Run specific test
pytest tests/test_jwe.py::TestJWEHandler::test_encrypt_decrypt_payload -v
```

## Example Workflow

### Complete End-to-End Example

```bash
# 1. Generate encryption key
curl -X POST http://localhost:5000/generate-jwe-key

# Save the key to environment
export JWE_ENCRYPTION_KEY="generated_key_here"

# 2. Create API key with JWE enabled (api_key_jwe_example.yaml already configured)

# 3. Login and get JWE-encrypted tokens
curl -X POST http://localhost:5000/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "api_key": "api_key_jwe_example"
  }'

# 4. Decrypt the token to get JWT
curl -X POST http://localhost:5000/decrypt-jwe \
  -H "Content-Type: application/json" \
  -d '{
    "jwe_token": "encrypted_token_from_step3",
    "encryption_key": "'$JWE_ENCRYPTION_KEY'",
    "encryption": "A256GCM"
  }'

# 5. Decode the JWT
curl -X POST http://localhost:5000/decode \
  -H "Content-Type: application/json" \
  -d '{
    "token": "jwt_from_step4"
  }'
```

## Migration Guide

### Enabling JWE for Existing API Keys

1. Add JWE configuration to existing API key:

```yaml
# config/api_keys/existing_key.yaml
jwe_config:
  enabled: true
  encryption_key: "${JWE_ENCRYPTION_KEY}"
  algorithm: "dir"
  encryption: "A256GCM"
```

2. Set environment variable:

```bash
export JWE_ENCRYPTION_KEY=$(curl -X POST http://localhost:5000/generate-jwe-key | jq -r '.encryption_key')
```

3. Test token generation:

```bash
curl -X POST http://localhost:5000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test", "api_key": "existing_key"}'
```

## Additional Resources

- [RFC 7516 - JSON Web Encryption](https://tools.ietf.org/html/rfc7516)
- [jwcrypto Documentation](https://jwcrypto.readthedocs.io/)
- [JOSE (JSON Object Signing and Encryption)](https://datatracker.ietf.org/wg/jose/documents/)

## Support

For issues or questions about JWE implementation:
1. Check the troubleshooting section
2. Review test cases in `tests/test_jwe.py`
3. Consult the DSP AI JWT documentation
