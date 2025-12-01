"""
Cryptographic utilities for encrypting/decrypting metadata.
Uses AES-256 encryption with PBKDF2HMAC key derivation from 6-digit passcode.
"""
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet


def validate_passcode(passcode: str) -> bool:
    """
    Validate that passcode is exactly 6 digits.
    
    Args:
        passcode: String to validate
        
    Returns:
        True if valid 6-digit passcode, False otherwise
    """
    return passcode.isdigit() and len(passcode) == 6


def derive_key(passcode: str, salt: bytes) -> bytes:
    """
    Derive encryption key from 6-digit passcode using PBKDF2HMAC.
    
    Args:
        passcode: 6-digit numeric passcode
        salt: Random salt bytes (16 bytes recommended)
        
    Returns:
        32-byte key suitable for Fernet
        
    Raises:
        ValueError: If passcode is not exactly 6 digits
    """
    if not validate_passcode(passcode):
        raise ValueError("Passcode must be exactly 6 digits")
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,  # High iteration count for security
    )
    key = kdf.derive(passcode.encode())
    return base64.urlsafe_b64encode(key)


def encrypt_data(data: str, passcode: str) -> str:
    """
    Encrypt data using AES-256 with passcode.
    
    Args:
        data: Plaintext string to encrypt
        passcode: 6-digit numeric passcode
        
    Returns:
        Base64-encoded string containing salt + encrypted data
        
    Raises:
        ValueError: If passcode is invalid
    """
    if not validate_passcode(passcode):
        raise ValueError("Passcode must be exactly 6 digits")
    
    # Generate random salt
    salt = os.urandom(16)
    
    # Derive key from passcode
    key = derive_key(passcode, salt)
    
    # Encrypt data
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    
    # Combine salt + encrypted data and encode
    combined = salt + encrypted
    return base64.b64encode(combined).decode()


def decrypt_data(encrypted_data: str, passcode: str) -> str:
    """
    Decrypt data encrypted with encrypt_data.
    
    Args:
        encrypted_data: Base64-encoded encrypted data (salt + ciphertext)
        passcode: 6-digit numeric passcode
        
    Returns:
        Decrypted plaintext string
        
    Raises:
        ValueError: If passcode is invalid
        cryptography.fernet.InvalidToken: If passcode is wrong or data corrupted
    """
    if not validate_passcode(passcode):
        raise ValueError("Passcode must be exactly 6 digits")
    
    # Decode base64
    combined = base64.b64decode(encrypted_data)
    
    # Extract salt and encrypted data
    salt = combined[:16]
    encrypted = combined[16:]
    
    # Derive key from passcode
    key = derive_key(passcode, salt)
    
    # Decrypt data
    f = Fernet(key)
    decrypted = f.decrypt(encrypted)
    
    return decrypted.decode()
