"""Encryption utilities for securing user API keys."""

import base64
import secrets
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.config import settings


class APIKeyEncryption:
    """Handles encryption and decryption of user API keys."""
    
    def __init__(self):
        """Initialize encryption with app's encryption key."""
        self.encryption_key = self._get_or_generate_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_or_generate_key(self) -> bytes:
        """Get encryption key from settings or generate a new one."""
        if settings.ENCRYPTION_KEY:
            # Use configured key
            key_bytes = settings.ENCRYPTION_KEY.encode()
        else:
            # Generate a new key (for development only)
            key_bytes = secrets.token_bytes(32)
        
        # Derive a Fernet key from the raw key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"eduagi-salt-2026",  # Static salt for consistency
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext API key."""
        if not plaintext:
            return ""
        
        encrypted_bytes = self.fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt(self, encrypted_text: str) -> Optional[str]:
        """Decrypt an encrypted API key."""
        if not encrypted_text:
            return None
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception:
            return None


# Global instance
api_key_encryption = APIKeyEncryption()