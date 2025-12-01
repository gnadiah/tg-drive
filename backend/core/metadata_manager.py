from pydantic import BaseModel
from typing import List, Optional
import json


class FileChunk(BaseModel):
    index: int
    message_id: int
    size: int
    hash: str


class FileMetadata(BaseModel):
    id: str
    name: str
    size: int
    chunks: List[FileChunk]
    hash: str
    mime_type: str


class MetadataManager:
    """Manager for file metadata serialization with optional encryption."""
    
    @staticmethod
    def to_json(metadata: FileMetadata) -> str:
        """
        Convert metadata to JSON string (V1 plaintext format).
        
        Args:
            metadata: FileMetadata object
            
        Returns:
            JSON string
        """
        return metadata.model_dump_json()
    
    @staticmethod
    def to_json_encrypted(metadata: FileMetadata, passcode: str) -> str:
        """
        Convert metadata to encrypted JSON string (V2 format).
        
        Args:
            metadata: FileMetadata object
            passcode: 6-digit encryption passcode
            
        Returns:
            Encrypted base64 string
            
        Raises:
            ValueError: If passcode is invalid
        """
        from .crypto_utils import encrypt_data
        
        json_str = metadata.model_dump_json()
        return encrypt_data(json_str, passcode)
    
    @staticmethod
    def from_json(json_str: str) -> FileMetadata:
        """
        Parse metadata from JSON string (V1 plaintext format).
        
        Args:
            json_str: JSON string
            
        Returns:
            FileMetadata object
        """
        # The original implementation used model_validate_json.
        # The provided change introduced a version using json.loads and FileMetadata(**data)
        # and then duplicated the original model_validate_json version.
        # To resolve the conflict and maintain Pydantic's preferred parsing,
        # we will keep the model_validate_json approach and add the docstring.
        return FileMetadata.model_validate_json(json_str)
    
    @staticmethod
    def from_json_encrypted(encrypted_str: str, passcode: str) -> FileMetadata:
        """
        Parse metadata from encrypted string (V2 format).
        
        Args:
            encrypted_str: Encrypted base64 string
            passcode: 6-digit decryption passcode
            
        Returns:
            FileMetadata object
            
        Raises:
            ValueError: If passcode is invalid
            cryptography.fernet.InvalidToken: If passcode is wrong
        """
        from .crypto_utils import decrypt_data
        
        json_str = decrypt_data(encrypted_str, passcode)
        return MetadataManager.from_json(json_str)
