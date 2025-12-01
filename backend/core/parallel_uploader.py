"""
Parallel File Uploader for Telegram

Based on tdlib and tdesktop approaches:
- Splits files into small parts (dynamic sizing)
- Uploads parts in parallel using asyncio
- Uses upload.saveBigFilePart for files > 10MB
- Tracks progress and handles errors

Author: Derived from tdlib FileUploader.cpp
"""

import asyncio
import hashlib
import math
import os
from typing import Callable, Optional

from telethon import TelegramClient, helpers
from telethon.tl.functions.upload import SaveBigFilePartRequest, SaveFilePartRequest
from telethon.tl.types import InputFile, InputFileBig

import logging

logger = logging.getLogger(__name__)


def get_optimal_part_size(file_size: int) -> int:
    """
    Calculate optimal part size based on file size.
    Following tdesktop's dynamic sizing:
    
    - < 1MB: 32KB
    - ≤ 10MB: 128KB
    - ≤ 50MB: 256KB  (our 20MB chunks fall here)
    - > 50MB: 512KB
    """
    if file_size < 1_000_000:  # < 1MB
        return 32 * 1024
    elif file_size <= 10_000_000:  # ≤ 10MB
        return 128 * 1024
    elif file_size <= 50_000_000:  # ≤ 50MB
        return 256 * 1024
    else:
        return 512 * 1024


class ParallelUploader:
    """
    Uploads file in parallel parts to Telegram.
    
    Matches tdlib approach but in Python:
    - Dynamic part sizing
    - Parallel upload with worker tasks
    - Progress tracking
    - Error handling with retries
    """
    
    def __init__(self, client: TelegramClient, workers: int = 4):
        """
        Initialize parallel uploader.
        
        Args:
            client: Telethon TelegramClient instance
            workers: Number of parallel upload workers (default: 4)
        """
        self.client = client
        self.workers = workers
        
    async def upload_file(
        self,
        file_path: str,
        part_size: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> InputFile:
        """
        Upload file in parallel parts.
        
        Args:
            file_path: Path to file to upload
            part_size: Size of each part (auto-calculated if None)
            progress_callback: Optional callback(uploaded_bytes, total_bytes)
            
        Returns:
            InputFile or InputFileBig for use with send_file()
        """
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        # Determine part size
        if part_size is None:
            part_size = get_optimal_part_size(file_size)
        
        # Calculate parts
        part_count = math.ceil(file_size / part_size)
        is_big = file_size > 10 * 1024 * 1024  # > 10MB
        
        # Generate unique file ID
        file_id = helpers.generate_random_long()
        
        logger.info(
            f"Starting parallel upload: {file_name} "
            f"({file_size} bytes, {part_count} parts, "
            f"part_size={part_size}, big={is_big})"
        )
        
        # Create upload queue
        queue = asyncio.Queue()
        for i in range(part_count):
            offset = i * part_size
            size = min(part_size, file_size - offset)
            await queue.put((i, offset, size))
        
        # Track progress and retries
        uploaded_bytes = 0
        progress_lock = asyncio.Lock()
        final_errors = [] # Only store errors that exceeded max retries
        retry_counts = {} # part_index -> count
        MAX_RETRIES = 5
        
        async def upload_worker(worker_id):
            """Worker task to upload parts from queue"""
            nonlocal uploaded_bytes
            
            while not queue.empty():
                try:
                    part_index, offset, size = await queue.get()
                except asyncio.QueueEmpty:
                    break
                
                try:
                    logger.info(f"[Worker {worker_id}] Starting part {part_index}/{part_count} ({size} bytes)")
                    
                    # Read part from file
                    with open(file_path, 'rb') as f:
                        f.seek(offset)
                        bytes_data = f.read(size)
                    
                    # Upload part
                    if is_big:
                        await self.client(SaveBigFilePartRequest(
                            file_id=file_id,
                            file_part=part_index,
                            file_total_parts=part_count,
                            bytes=bytes_data
                        ))
                    else:
                        await self.client(SaveFilePartRequest(
                            file_id=file_id,
                            file_part=part_index,
                            bytes=bytes_data
                        ))
                    
                    # Update progress
                    async with progress_lock:
                        uploaded_bytes += len(bytes_data)
                        if progress_callback:
                            # Call with (current, total) for compatibility with TransferTracker
                            progress_callback(uploaded_bytes, file_size)
                    
                    logger.info(f"[Worker {worker_id}] Finished part {part_index}/{part_count}")
                    
                except Exception as e:
                    current_retries = retry_counts.get(part_index, 0)
                    if current_retries < MAX_RETRIES:
                        retry_counts[part_index] = current_retries + 1
                        logger.warning(f"[Worker {worker_id}] Failed part {part_index} (Attempt {current_retries+1}/{MAX_RETRIES}): {e}. Retrying...")
                        await queue.put((part_index, offset, size))
                    else:
                        logger.error(f"[Worker {worker_id}] Failed part {part_index} after {MAX_RETRIES} attempts: {e}")
                        final_errors.append((part_index, e))
                    
                finally:
                    queue.task_done()
        
        # Create and run workers
        workers_tasks = [
            asyncio.create_task(upload_worker(i))
            for i in range(min(self.workers, part_count))
        ]
        
        # Wait for all workers
        await asyncio.gather(*workers_tasks)
        
        # Check for errors
        if final_errors:
            raise Exception(f"Upload failed for {len(final_errors)} parts. First error: {final_errors[0][1]}")
        
        logger.info(f"Upload complete: {file_name} ({file_size} bytes)")
        
        # Return appropriate InputFile
        if is_big:
            return InputFileBig(
                id=file_id,
                parts=part_count,
                name=file_name
            )
        else:
            # Calculate MD5 for small files
            with open(file_path, 'rb') as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            return InputFile(
                id=file_id,
                parts=part_count,
                name=file_name,
                md5_checksum=md5
            )
