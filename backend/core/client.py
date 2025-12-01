from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import os
import logging
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_NAME = "telegram_drive_session"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TGClient:
    def __init__(self):
        self.client = None

    def _init_client(self):
        logger.info(f"TGClient: Initializing TelegramClient with API_ID={API_ID}...")
        if API_ID and API_HASH:
            self.client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)
            logger.info("TGClient: TelegramClient initialized")

    async def start(self):
        logger.info("TGClient: start() called")
        if not self.client:
            self._init_client()
        
        if not self.client:
            raise Exception("API_ID and API_HASH not set")
            
        if not self.client.is_connected():
            logger.info("TGClient: Connecting...")
            await self.client.connect()
            logger.info("TGClient: Connected")

    async def stop(self):
        if self.client:
            await self.client.disconnect()

    async def is_user_authorized(self):
        if not self.client:
            return False
        return await self.client.is_user_authorized()

    async def send_code_request(self, phone):
        if not self.client:
             await self.start()
        if not self.client.is_connected():
             await self.start()
        await self.client.send_code_request(phone)

    async def sign_in(self, phone, code, password=None):
        logger.info(f"TGClient: sign_in called for {phone} (password={'YES' if password else 'NO'})")
        if not self.client:
             await self.start()
        
        try:
            await self.client.sign_in(phone, code)
            logger.info("TGClient: sign_in(phone, code) successful")
        except SessionPasswordNeededError:
            logger.info("TGClient: SessionPasswordNeededError caught")
            if password:
                 logger.info("TGClient: Attempting sign_in with password")
                 await self.client.sign_in(password=password)
                 logger.info("TGClient: sign_in(password) successful")
            else:
                raise
        except Exception as e:
            logger.error(f"TGClient: sign_in exception: {type(e).__name__}: {e}")
            if "password" in str(e).lower() and password:
                 logger.info("TGClient: 'password' in error, attempting sign_in with password")
                 await self.client.sign_in(password=password)
                 logger.info("TGClient: sign_in(password) successful")
            else:
                raise e

    async def get_me(self):
        if not self.client:
             await self.start()
        return await self.client.get_me()
    
    async def log_out(self):
        """Logout from Telegram and disconnect"""
        if not self.client:
            return
        
        logger.info("TGClient: Logging out...")
        try:
            await self.client.log_out()
            logger.info("TGClient: Logged out successfully")
        except Exception as e:
            logger.error(f"TGClient: Logout error: {e}")
        finally:
            if self.client:
                if self.client.is_connected():
                    await self.client.disconnect()
                logger.info("TGClient: Disconnected")
                self.client = None # Force re-initialization on next start()

    async def upload_file(self, file_path, caption=None, progress_callback=None):
        if not self.client:
             await self.start()
        
        from .parallel_uploader import ParallelUploader
        
        logger.info(f"Uploading file using ParallelUploader: {file_path}")
        
        # Use new parallel uploader for better performance
        uploader = ParallelUploader(self.client, workers=4)
        input_file = await uploader.upload_file(file_path, progress_callback=progress_callback)
        
        # Send file to "me" (Saved Messages)
        return await self.client.send_file("me", input_file, caption=caption, force_document=True)

    async def send_message(self, message):
        if not self.client:
             await self.start()
        return await self.client.send_message("me", message)
    
    async def get_messages(self, limit=100):
        if not self.client:
             await self.start()
        return await self.client.get_messages("me", limit=limit)

    async def get_message_by_id(self, message_id):
        if not self.client:
             await self.start()
        result = await self.client.get_messages("me", ids=message_id)
        # Ensure we always return a list for consistency
        if result and not isinstance(result, list):
            return [result]
        return result

    async def download_media(self, message, file_path, progress_callback=None):
        if not self.client:
             await self.start()
        
        logger.info(f"Downloading: {file_path}")
        
        # Using Telethon's built-in download (stable and reliable)
        return await self.client.download_media(
            message, 
            file_path, 
            progress_callback=progress_callback
        )

    async def delete_messages(self, message_ids):
        if not self.client:
             await self.start()
        await self.client.delete_messages("me", message_ids)

    async def edit_message(self, message_id, text):
        if not self.client:
             await self.start()
        await self.client.edit_message("me", message_id, text)

    async def qr_login_start(self):
        """Start QR code login and return QR login object"""
        if not self.client:
            await self.start()
        if not self.client.is_connected():
            await self.start()
        
        qr_login = await self.client.qr_login()
        return qr_login
    
    async def qr_login_wait(self, qr_login, timeout=30):
        """Wait for QR code to be scanned and confirmed"""
        try:
            await qr_login.wait(timeout=timeout)
            return True
        except Exception as e:
            print(f"QR login wait error: {e}")
            return False

tg_client = TGClient()
