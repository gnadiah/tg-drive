import asyncio
import threading
from backend.core import tg_client
from backend.api import AuthHandler, FileHandler, PasscodeHandler

class Bridge:
    def __init__(self):
        self._window = None
        # Passcode rate limiting (state kept here for shared access)
        self._failed_passcode_attempts = 0
        self._passcode_lockout_until = None
        self._session_passcode = None
        
        # Initialize Handlers
        self.auth = AuthHandler(self)
        self.files = FileHandler(self)
        self.passcode = PasscodeHandler(self)
        
        # Start a background event loop
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._start_loop, daemon=True)
        self.loop_thread.start()

    def _start_loop(self):
        print("Bridge: Starting background event loop...")
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self._startup_check())
        self.loop.run_forever()

    async def _startup_check(self):
        print("Bridge: Running startup auth check...")
        try:
            await self._ensure_client()
            is_auth = await tg_client.is_user_authorized()
            print(f"Bridge: Startup check result: is_authorized={is_auth}")
            if is_auth:
                me = await tg_client.get_me()
                print(f"Bridge: Startup user: {me.first_name if me else 'Unknown'}")
        except Exception as e:
            print(f"Bridge: Startup check failed: {e}")

    def set_window(self, window):
        self._window = window

    def _run_async(self, coro):
        """Run a coroutine on the background loop and return the result."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            res = future.result()
            return res
        except Exception as e:
            print(f"Bridge: {coro.__name__} failed: {e}")
            raise e

    async def _ensure_client(self):
        if not tg_client.client or not tg_client.client.is_connected():
            await tg_client.start()

    # --- Authentication (Delegated) ---

    def check_auth(self):
        return self._run_async(self.auth.check_auth())

    def request_code(self, phone):
        return self._run_async(self.auth.request_code(phone))

    def sign_in(self, phone, code, password=None):
        return self._run_async(self.auth.sign_in(phone, code, password))

    def logout(self):
        return self._run_async(self.auth.logout())

    def log(self, message):
        print(f"JS_LOG: {message}")

    # --- Passcode Management (Delegated) ---
    
    def has_passcode(self):
        return self._run_async(self.passcode.has_passcode())
    
    def set_passcode(self, passcode):
        return self._run_async(self.passcode.set_passcode(passcode))
    
    def verify_passcode(self, passcode):
        return self._run_async(self.passcode.verify_passcode(passcode))
    
    def change_passcode(self, old_passcode, new_passcode):
        return self._run_async(self.passcode.change_passcode(old_passcode, new_passcode))
    
    def reset_encryption(self):
        return self._run_async(self.passcode.reset_encryption())

    # --- QR Login (Delegated) ---
    
    def request_qr(self):
        return self._run_async(self.auth.request_qr())

    def check_qr_status(self, token_id):
        return self._run_async(self.auth.check_qr_status(token_id))

    # --- Files (Delegated) ---

    def list_files(self):
        return self._run_async(self.files.list_files())

    def pick_and_upload_file(self):
        # This one is synchronous wrapper around async logic inside handler
        return self.files.pick_and_upload_file()

    def download_file(self, file_id):
        return self.files.download_file(file_id)

    def rename_file(self, file_id, new_name, metadata_message_id):
        return self.files.rename_file(file_id, new_name, metadata_message_id)

    def delete_file(self, file_id, metadata_message_id):
        return self.files.delete_file(file_id, metadata_message_id)
