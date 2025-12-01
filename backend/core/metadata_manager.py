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
    mime_type: Optional[str] = None

class MetadataManager:
    @staticmethod
    def to_json(metadata: FileMetadata) -> str:
        return metadata.model_dump_json()

    @staticmethod
    def from_json(json_str: str) -> FileMetadata:
        return FileMetadata.model_validate_json(json_str)
