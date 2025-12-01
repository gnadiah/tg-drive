import asyncio
import logging
from typing import List
from telethon import TelegramClient
from telethon.sessions import StringSession

logger = logging.getLogger(__name__)

class ClientPool:
    def __init__(self, main_client: TelegramClient, session_path: str, pool_size: int = 4):
        self.main_client = main_client
        self.pool_size = pool_size
        self.workers: List[TelegramClient] = []
        self._ready = False

    async def start(self):
        """Initialize and start worker clients. Returns True if successful, False otherwise."""
        try:
            if not self.main_client.is_connected:
                await self.main_client.connect()

            # Ensure main client is authorized
            if not await self.main_client.is_user_authorized():
                logger.warning("Main client not authorized, cannot start pool.")
                return False

            api_id = self.main_client.api_id
            api_hash = self.main_client.api_hash

            # Export session to string to share auth key without file locks
            # We manually construct a StringSession from the current SQLite session
            session_data = StringSession()
            session_data.set_dc(
                self.main_client.session.dc_id,
                self.main_client.session.server_address,
                self.main_client.session.port
            )
            session_data.auth_key = self.main_client.session.auth_key
            session_string = session_data.save()

            # Create worker clients
            successful_workers = 0
            for i in range(self.pool_size):
                try:
                    # Use StringSession for workers
                    # Note: StringSession does not persist updates (like new salts) to disk automatically
                    # But for a worker pool that just uploads/downloads, this is fine.
                    # The main client handles the persistent session.
                    client = TelegramClient(StringSession(session_string), api_id, api_hash)
                    
                    # Add timeout for connection
                    await asyncio.wait_for(client.connect(), timeout=10.0)
                    
                    # We assume authorization is valid since we copied the key
                    # Skipping is_user_authorized() to avoid GetUsersRequest spam/race conditions
                    
                    self.workers.append(client)
                    successful_workers += 1
                    logger.info(f"Worker {i} started successfully.")
                    
                    # Add delay to avoid race conditions/message ID collisions during startup
                    await asyncio.sleep(2)
                    
                except asyncio.TimeoutError:
                    logger.error(f"Worker {i} connection timeout after 10s")
                except Exception as e:
                    logger.error(f"Failed to start worker {i}: {e}")
            
            if successful_workers > 0:
                self._ready = True
                logger.info(f"Client pool started with {successful_workers}/{self.pool_size} workers")
                return True
            else:
                logger.warning("No workers started successfully")
                return False
                
        except Exception as e:
            logger.error(f"Client pool start failed: {e}")
            return False

    async def close(self):
        """Disconnect all workers."""
        for client in self.workers:
            if client.is_connected:
                await client.disconnect()
        self.workers.clear()
        self._ready = False

    def is_ready(self) -> bool:
        """Check if the pool is ready with active workers."""
        return self._ready and len(self.workers) > 0

    def get_workers(self) -> List[TelegramClient]:
        return self.workers
