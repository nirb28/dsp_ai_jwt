"""
JWE (JSON Web Encryption) Handler for symmetric encryption of JWT tokens

This module provides utilities for encrypting and decrypting JWT tokens using
JSON Web Encryption (JWE) with symmetric encryption algorithms.

Supported algorithms:
- Key Management: dir (Direct use of shared symmetric key)
- Content Encryption: A128GCM, A192GCM, A256GCM, A128CBC-HS256, A192CBC-HS384, A256CBC-HS512
- Compression: DEF (Deflate)
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple
from jwcrypto import jwk, jwe
from jwcrypto.common import json_encode, json_decode
import base64
import secrets

logger = logging.getLogger(__name__)


class JWEHandler:
    """Handler for JWE encryption and decryption operations"""
    
    # Supported algorithms
    SUPPORTED_KEY_ALGORITHMS = ['dir']  # Direct use of shared symmetric key
    SUPPORTED_CONTENT_ENCRYPTION = [
        'A128GCM', 'A192GCM', 'A256GCM',
        'A128CBC-HS256', 'A192CBC-HS384', 'A256CBC-HS512'
    ]
    SUPPORTED_COMPRESSION = [None, 'DEF']  # DEF = Deflate compression
    
    # Key size requirements (in bytes)
    KEY_SIZES = {
        'A128GCM': 16,         # 128 bits
        'A192GCM': 24,         # 192 bits
        'A256GCM': 32,         # 256 bits
        'A128CBC-HS256': 32,   # 256 bits (128-bit key + 128-bit MAC key)
        'A192CBC-HS384': 48,   # 384 bits (192-bit key + 192-bit MAC key)
        'A256CBC-HS512': 64    # 512 bits (256-bit key + 256-bit MAC key)
    }
    
    def __init__(
        self,
        encryption_key: Optional[str] = None,
        key_algorithm: str = 'dir',
        content_encryption: str = 'A256GCM',
        compression: Optional[str] = None
    ):
        """
        Initialize JWE handler
        
        Args:
            encryption_key: Base64-encoded symmetric encryption key or hex string
            key_algorithm: Key management algorithm (default: 'dir' for direct symmetric)
            content_encryption: Content encryption algorithm (default: 'A256GCM')
            compression: Compression algorithm (default: None, use 'DEF' for deflate)
        """
        self.key_algorithm = key_algorithm
        self.content_encryption = content_encryption
        self.compression = compression
        
        # Validate algorithms
        if key_algorithm not in self.SUPPORTED_KEY_ALGORITHMS:
            raise ValueError(f"Unsupported key algorithm: {key_algorithm}")
        if content_encryption not in self.SUPPORTED_CONTENT_ENCRYPTION:
            raise ValueError(f"Unsupported content encryption: {content_encryption}")
        if compression not in self.SUPPORTED_COMPRESSION:
            raise ValueError(f"Unsupported compression: {compression}")
        
        # Load or generate encryption key
        if encryption_key:
            self.jwk_key = self._load_key(encryption_key)
        else:
            # Generate a new key if none provided
            self.jwk_key = self._generate_key()
            logger.warning("No encryption key provided, generated a new one")
    
    def _load_key(self, key_data: str) -> jwk.JWK:
        """
        Load encryption key from string
        
        Args:
            key_data: Base64-encoded or hex-encoded key string
            
        Returns:
            JWK key object
        """
        try:
            # Determine required key size
            required_size = self.KEY_SIZES[self.content_encryption]
            
            # Try to decode as base64
            try:
                key_bytes = base64.b64decode(key_data)
            except Exception:
                # Try as hex string
                try:
                    key_bytes = bytes.fromhex(key_data)
                except Exception:
                    # Use as raw string bytes
                    key_bytes = key_data.encode('utf-8')
            
            # Validate key size
            if len(key_bytes) != required_size:
                raise ValueError(
                    f"Invalid key size: expected {required_size} bytes for {self.content_encryption}, "
                    f"got {len(key_bytes)} bytes"
                )
            
            # Create JWK key object
            key = jwk.JWK(kty='oct', k=base64.urlsafe_b64encode(key_bytes).decode('utf-8'))
            return key
            
        except Exception as e:
            logger.error(f"Error loading JWE key: {str(e)}")
            raise
    
    def _generate_key(self) -> jwk.JWK:
        """
        Generate a new symmetric key
        
        Returns:
            JWK key object
        """
        required_size = self.KEY_SIZES[self.content_encryption]
        key_bytes = secrets.token_bytes(required_size)
        key = jwk.JWK(kty='oct', k=base64.urlsafe_b64encode(key_bytes).decode('utf-8'))
        return key
    
    def encrypt(self, payload: Dict[str, Any]) -> str:
        """
        Encrypt a payload using JWE
        
        Args:
            payload: Dictionary containing the data to encrypt
            
        Returns:
            JWE compact serialization string
        """
        try:
            # Create JWE token
            protected_header = {
                'alg': self.key_algorithm,
                'enc': self.content_encryption
            }
            
            # Add compression if enabled
            if self.compression:
                protected_header['zip'] = self.compression
            
            # Convert payload to JSON string
            plaintext = json_encode(payload)
            
            # Create and encrypt JWE token
            jwe_token = jwe.JWE(
                plaintext=plaintext.encode('utf-8'),
                protected=protected_header
            )
            jwe_token.add_recipient(self.jwk_key)
            
            # Return compact serialization
            encrypted = jwe_token.serialize(compact=True)
            
            logger.info(f"Successfully encrypted payload with {self.content_encryption}")
            return encrypted
            
        except Exception as e:
            logger.error(f"Error encrypting payload: {str(e)}")
            raise
    
    def decrypt(self, jwe_token: str) -> Dict[str, Any]:
        """
        Decrypt a JWE token
        
        Args:
            jwe_token: JWE compact serialization string
            
        Returns:
            Decrypted payload as dictionary
        """
        try:
            # Create JWE object from token
            jwe_obj = jwe.JWE()
            jwe_obj.deserialize(jwe_token)
            
            # Decrypt with the key
            jwe_obj.decrypt(self.jwk_key)
            
            # Get the plaintext payload
            plaintext = jwe_obj.payload.decode('utf-8')
            
            # Parse JSON
            payload = json_decode(plaintext)
            
            logger.info(f"Successfully decrypted JWE token")
            return payload
            
        except Exception as e:
            logger.error(f"Error decrypting JWE token: {str(e)}")
            raise
    
    def get_key_export(self, format: str = 'base64') -> str:
        """
        Export the encryption key
        
        Args:
            format: Export format ('base64', 'hex', or 'jwk')
            
        Returns:
            Exported key string
        """
        try:
            if format == 'jwk':
                return self.jwk_key.export()
            
            # Get the raw key bytes
            key_data = self.jwk_key.export_to_pem(private_key=True, password=None)
            key_dict = json_decode(self.jwk_key.export())
            k_value = key_dict['k']
            
            # Decode the base64url-encoded key
            key_bytes = base64.urlsafe_b64decode(k_value + '==')  # Add padding
            
            if format == 'base64':
                return base64.b64encode(key_bytes).decode('utf-8')
            elif format == 'hex':
                return key_bytes.hex()
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting key: {str(e)}")
            raise
    
    @staticmethod
    def generate_encryption_key(algorithm: str = 'A256GCM', format: str = 'base64') -> str:
        """
        Generate a new encryption key for the specified algorithm
        
        Args:
            algorithm: Content encryption algorithm
            format: Output format ('base64' or 'hex')
            
        Returns:
            Generated key as a string
        """
        if algorithm not in JWEHandler.KEY_SIZES:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        required_size = JWEHandler.KEY_SIZES[algorithm]
        key_bytes = secrets.token_bytes(required_size)
        
        if format == 'base64':
            return base64.b64encode(key_bytes).decode('utf-8')
        elif format == 'hex':
            return key_bytes.hex()
        else:
            raise ValueError(f"Unsupported format: {format}")


def encrypt_jwt_token(
    jwt_token: str,
    encryption_key: str,
    content_encryption: str = 'A256GCM',
    compression: Optional[str] = None
) -> str:
    """
    Encrypt a JWT token into a JWE token
    
    Args:
        jwt_token: The JWT token string to encrypt
        encryption_key: Base64-encoded or hex-encoded encryption key
        content_encryption: Content encryption algorithm (default: A256GCM)
        compression: Compression algorithm (default: None)
        
    Returns:
        JWE compact serialization string
    """
    handler = JWEHandler(
        encryption_key=encryption_key,
        content_encryption=content_encryption,
        compression=compression
    )
    
    # Wrap the JWT token in a payload
    payload = {'jwt': jwt_token}
    return handler.encrypt(payload)


def decrypt_jwe_token(
    jwe_token: str,
    encryption_key: str,
    content_encryption: str = 'A256GCM'
) -> str:
    """
    Decrypt a JWE token to retrieve the JWT token
    
    Args:
        jwe_token: JWE compact serialization string
        encryption_key: Base64-encoded or hex-encoded encryption key
        content_encryption: Content encryption algorithm (default: A256GCM)
        
    Returns:
        Decrypted JWT token string
    """
    handler = JWEHandler(
        encryption_key=encryption_key,
        content_encryption=content_encryption
    )
    
    payload = handler.decrypt(jwe_token)
    return payload.get('jwt', '')


def encrypt_payload_to_jwe(
    payload: Dict[str, Any],
    encryption_key: str,
    content_encryption: str = 'A256GCM',
    compression: Optional[str] = None
) -> str:
    """
    Encrypt a payload dictionary directly into a JWE token
    
    Args:
        payload: Dictionary containing the data to encrypt
        encryption_key: Base64-encoded or hex-encoded encryption key
        content_encryption: Content encryption algorithm (default: A256GCM)
        compression: Compression algorithm (default: None)
        
    Returns:
        JWE compact serialization string
    """
    handler = JWEHandler(
        encryption_key=encryption_key,
        content_encryption=content_encryption,
        compression=compression
    )
    
    return handler.encrypt(payload)


def decrypt_jwe_to_payload(
    jwe_token: str,
    encryption_key: str,
    content_encryption: str = 'A256GCM'
) -> Dict[str, Any]:
    """
    Decrypt a JWE token to retrieve the payload
    
    Args:
        jwe_token: JWE compact serialization string
        encryption_key: Base64-encoded or hex-encoded encryption key
        content_encryption: Content encryption algorithm (default: A256GCM)
        
    Returns:
        Decrypted payload as dictionary
    """
    handler = JWEHandler(
        encryption_key=encryption_key,
        content_encryption=content_encryption
    )
    
    return handler.decrypt(jwe_token)
