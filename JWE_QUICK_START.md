# JWE Quick Start Guide

## What is JWE?

JWE (JSON Web Encryption) adds **encryption** to your JWT tokens, making them unreadable without the decryption key. This provides confidentiality in addition to the integrity that JWT signatures provide.

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
cd dsp_ai_jwt
pip install -r requirements.txt
```

### 2. Generate Encryption Key

```bash
# Start the JWT service
python app.py

# In another terminal, generate a key
curl -X POST http://localhost:5000/generate-jwe-key
```

### 3. Add Key to Environment

```bash
# Copy the encryption_key from the response
echo "JWE_ENCRYPTION_KEY=your_generated_key_here" >> .env
```

### 4. Configure API Key

Create or edit `config/api_keys/my_secure_key.yaml`:

```yaml
id: my-secure-api-key
owner: your-team

# Enable JWE encryption
jwe_config:
  enabled: true
  encryption_key: "${JWE_ENCRYPTION_KEY}"
  algorithm: "dir"
  encryption: "A256GCM"

claims:
  static:
    models: ["gpt-4"]
    tier: "premium"
    exp_hours: 1
```

### 5. Test It!

```bash
# Login with your JWE-enabled API key
curl -X POST http://localhost:5000/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "api_key": "my_secure_key"
  }'
```

You'll get encrypted tokens:
```json
{
  "access_token": "eyJhbGc...encrypted...",
  "refresh_token": "eyJhbGc...encrypted...",
  "token_type": "JWE",
  "encryption": "A256GCM"
}
```

## Common Use Cases

### Encrypt Existing JWT Token

```bash
curl -X POST http://localhost:5000/encrypt-jwe \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your.jwt.token",
    "encryption_key": "your_encryption_key",
    "encryption": "A256GCM"
  }'
```

### Decrypt JWE Token

```bash
curl -X POST http://localhost:5000/decrypt-jwe \
  -H "Content-Type: application/json" \
  -d '{
    "jwe_token": "encrypted_token",
    "encryption_key": "your_encryption_key",
    "encryption": "A256GCM"
  }'
```

### Encrypt Custom Data

```bash
curl -X POST http://localhost:5000/encrypt-jwe \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "user": "john",
      "role": "admin"
    },
    "encryption_key": "your_encryption_key",
    "encryption": "A256GCM"
  }'
```

## Python Usage

```python
from utils.jwe_handler import JWEHandler

# Generate key
key = JWEHandler.generate_encryption_key('A256GCM', 'base64')

# Create handler
handler = JWEHandler(
    encryption_key=key,
    content_encryption='A256GCM'
)

# Encrypt
payload = {"user": "john", "role": "admin"}
encrypted = handler.encrypt(payload)

# Decrypt
decrypted = handler.decrypt(encrypted)
```

## Available Algorithms

| Algorithm | Key Size | Recommended For |
|-----------|----------|-----------------|
| A128GCM | 16 bytes | Good security |
| A192GCM | 24 bytes | Better security |
| **A256GCM** | **32 bytes** | **Best security (recommended)** |
| A128CBC-HS256 | 32 bytes | Legacy support |
| A192CBC-HS384 | 48 bytes | Legacy support |
| A256CBC-HS512 | 64 bytes | Legacy support |

**Recommendation**: Use `A256GCM` for new implementations.

## Security Tips

1. **Store Keys Securely**: Use environment variables or key management systems
2. **Use Strong Keys**: Always generate keys with cryptographic random functions
3. **Rotate Keys**: Implement regular key rotation policies
4. **Different Environments**: Use separate keys for dev, staging, and production
5. **Never Hardcode**: Never put encryption keys in source code

## Compression

For large payloads, enable compression:

```yaml
jwe_config:
  enabled: true
  encryption_key: "${JWE_ENCRYPTION_KEY}"
  encryption: "A256GCM"
  compression: "DEF"  # Enable DEFLATE compression
```

## Control Tower Integration

In your Control Tower manifest:

```json
{
  "name": "secure-auth",
  "type": "jwt_config",
  "config": {
    "secret_key": "${JWT_SECRET_KEY}",
    "jwe_enabled": true,
    "jwe_encryption_key": "${JWE_ENCRYPTION_KEY}",
    "jwe_encryption": "A256GCM"
  }
}
```

## Testing

Run the test suite:

```bash
pytest tests/test_jwe.py -v
```

Run example script:

```bash
python example_jwe_usage.py
```

## Troubleshooting

### "Invalid key size" error
**Problem**: Your encryption key is the wrong size.  
**Solution**: Generate a new key with the correct size for your algorithm.

### "Decryption failed" error
**Problem**: Wrong key, algorithm, or corrupted token.  
**Solution**: Verify you're using the same key and algorithm used for encryption.

### Environment variable not set
**Problem**: `JWE_ENCRYPTION_KEY` not in environment.  
**Solution**: Add it to your `.env` file or export it in your shell.

## Next Steps

- 📖 Read the full [JWE Documentation](JWE_DOCUMENTATION.md)
- 🧪 Run the [example script](example_jwe_usage.py)
- 🔬 Review [test cases](tests/test_jwe.py)
- 🛠️ Configure [Control Tower](../dsp-ai-control-tower/)

## Support

For detailed information, see:
- [JWE_DOCUMENTATION.md](JWE_DOCUMENTATION.md) - Complete documentation
- [tests/test_jwe.py](tests/test_jwe.py) - Test examples
- [example_jwe_usage.py](example_jwe_usage.py) - Usage examples
