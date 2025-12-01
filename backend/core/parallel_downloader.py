"""
Parallel File Downloader for Telegram

Strategy: Download parts to SEPARATE files, then merge!
- No file lock contention (each worker writes to own file)
- Cross-platform (no pwrite needed)
- Simple and fast
- Same approach as aria2, IDM, wget

Author: Inspired by user's brilliant suggestion!
"""

import asyncio
import math
import os
import shutil
from typing import Callable, Optional
from pathlib import Path

from telethon import TelegramClient

import logging

logger = logging.getLogger(__name__)


def get_optimal_download_part_size(file_size: int) -> int:
    """
    Calculate optimal part size for download.
    Larger parts = fewer concurrent requests but better throughput.
    
    - < 10MB: 512KB (small files don't benefit from too many parts)
    - ≤ 50MB: 1MB
    - > 50MB: 2MB
    """
    if file_size < 10_000_000:
        return 512 * 1024  # 512KB
    elif file_size <= 50_000_000:
        return 1024 * 1024  # 1MB
    else:
        return 2048 * 1024  # 2MB


class ParallelDownloader:
    """
    Downloads file in parallel parts to separate temp files, then merges.
    
    Advantages:
    - No file locking needed (each part = separate file)
    - Cross-platform (works on Windows without pwrite)
    - Simple implementation
    - Clean separation of concerns
    """
    
    def __init__(self, client: TelegramClient, workers: int = 1):
        """
        Initialize parallel downloader.
        
        Args:
            client: Telethon TelegramClient instance
            workers: Number of parallel download workers (default: 1)
                    Note: Using > 1 workers may trigger Telegram FloodWait rate limits
        """
        self.client = client
        self.workers = workers
        
    async def download_file(
        self,
        message,
        file_path: str,
        part_size: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        Download file in parallel parts, then merge.
        
        Args:
            message: Telegram message object containing the file
            file_path: Path where file should be saved
            part_size: Size of each part (auto-calculated if None)
            progress_callback: Optional callback(downloaded_bytes, total_bytes)
            
        Returns:
            Path to downloaded file
        """
        # Get file info
        if not message.file:
            raise ValueError("Message does not contain a file")
        
        file_size = message.file.size
        file_name = message.file.name or os.path.basename(file_path)
        
        # Determine part size
        if part_size is None:
            part_size = get_optimal_download_part_size(file_size)
        
        # Calculate parts
        part_count = math.ceil(file_size / part_size)
        
        logger.info(
            f"Starting parallel download: {file_name} "
            f"({file_size} bytes, {part_count} parts, "
            f"part_size={part_size})"
        )
        
        # Create temp directory for parts
        temp_dir = f"{file_path}.parts"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Create download queue
            queue = asyncio.Queue()
            for i in range(part_count):
                offset = i * part_size
                limit = min(part_size, file_size - offset)
                part_file = os.path.join(temp_dir, f"part_{i:04d}")
                await queue.put((i, offset, limit, part_file))
            
            # Track progress
            downloaded_bytes = 0
            progress_lock = asyncio.Lock()
            errors = []
            
            async def download_worker():
                """Worker task to download parts from queue"""
                nonlocal downloaded_bytes
                
                while not queue.empty():
                    try:
                        part_index, offset, limit, part_file = await queue.get()
                    except asyncio.QueueEmpty:
                        break
                    
                    try:
                        # Download this part to separate file - NO LOCKS NEEDED!
                        # IMPORTANT: iter_download's 'limit' is requestSize per chunk,
                        # NOT total bytes! We need to stop after 'limit' total bytes.
                        part_data = b''
                        bytes_downloaded = 0
                        
                        async for chunk in self.client.iter_download(
                            message.media,
                            offset=offset,
                            request_size=min(limit, 1024 * 1024)  # Max 1MB per request
                        ):
                            # Only take what we need
                            bytes_needed = limit - bytes_downloaded
                            if bytes_needed <= 0:
                                break
                            
                            if len(chunk) > bytes_needed:
                                part_data += chunk[:bytes_needed]
                                bytes_downloaded += bytes_needed
                                break
                            else:
                                part_data += chunk
                                bytes_downloaded += len(chunk)
                        
                        # Write to separate file (simple!)
                        with open(part_file, 'wb') as f:
                            f.write(part_data)
                        
                        # Update progress
                        async with progress_lock:
                            downloaded_bytes += len(part_data)
                            if progress_callback:
                                progress_callback(downloaded_bytes, file_size)
                        
                        logger.debug(f"Part {part_index}/{part_count} downloaded ({len(part_data)} bytes)")
                        
                    except Exception as e:
                        logger.error(f"Failed to download part {part_index}: {e}")
                        errors.append((part_index, e))
                        
                    finally:
                        queue.task_done()
            
            # Create and run workers
            workers_tasks = [
                asyncio.create_task(download_worker())
                for _ in range(min(self.workers, part_count))
            ]
            
            # Wait for all workers
            await asyncio.gather(*workers_tasks)
            
            # Check for errors
            if errors:
                raise Exception(f"Download failed for {len(errors)} parts: {errors[0][1]}")
            
            # Merge all parts into final file
            logger.info(f"Merging {part_count} parts...")
            
            with open(file_path, 'wb') as output_file:
                for i in range(part_count):
                    part_file = os.path.join(temp_dir, f"part_{i:04d}")
                    with open(part_file, 'rb') as part:
                        shutil.copyfileobj(part, output_file)
            
            logger.info(f"Download complete: {file_name} ({file_size} bytes)")
            
        finally:
            # Clean up temp directory and parts
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temp directory: {temp_dir}")
        
        return file_path
