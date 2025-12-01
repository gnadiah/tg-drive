import os
import hashlib

CHUNK_SIZE = 1024 * 1024 * 1024  # 1GB default

def get_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def split_file(file_path: str, chunk_size: int = CHUNK_SIZE):
    """
    Generator that yields chunks of the file.
    Yields: (chunk_index, chunk_data_bytes)
    """
    with open(file_path, "rb") as f:
        index = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield index, chunk
            index += 1

def merge_files(chunk_paths: list[str], output_path: str):
    """Merge multiple chunk files into one."""
    with open(output_path, "wb") as outfile:
        for chunk_path in chunk_paths:
            with open(chunk_path, "rb") as infile:
                outfile.write(infile.read())

def verify_file(file_path: str, expected_hash: str) -> bool:
    """Verify file integrity."""
    return get_file_hash(file_path) == expected_hash
