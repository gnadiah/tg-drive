import asyncio
import time
from backend.core import tg_client

class AuthHandler:
    def __init__(self, bridge):
        self.bridge = bridge

    async def check_auth(self):
        print("AuthHandler: check_auth called")
        await self.bridge._ensure_client()
        is_auth = await tg_client.is_user_authorized()
        print(f"AuthHandler: is_user_authorized={is_auth}")
        
        user_data = None
        
        try:
            me = await tg_client.get_me()
            if me:
                print(f"AuthHandler: get_me() success! User: {me.id}")
                is_auth = True
                user_data = {
                    "id": me.id,
                    "first_name": me.first_name,
                    "last_name": me.last_name,
                    "username": me.username,
                    "phone": me.phone
                }
        except Exception as e:
            print(f"AuthHandler: get_me() failed: {e}")

        return {"authenticated": is_auth, "user": user_data}

    async def request_code(self, phone):
        await self.bridge._ensure_client()
        await tg_client.send_code_request(phone)
        return {"success": True}

    async def sign_in(self, phone, code, password=None):
        print(f"AuthHandler: sign_in called for {phone}")
        await self.bridge._ensure_client()
        try:
            await tg_client.sign_in(phone, code, password)
            return {"success": True}
        except Exception as e:
            print(f"AuthHandler: sign_in exception: {type(e).__name__}: {e}")
            if "SessionPasswordNeededError" in str(type(e).__name__):
                    return {"status": "needs_password"}
            return {"error": str(e)}

    async def logout(self):
        try:
            print("AuthHandler: logout() called")
            await self.bridge._ensure_client()
            await tg_client.log_out()
            
            # Clear QR state on bridge
            if hasattr(self.bridge, '_current_qr'): del self.bridge._current_qr
            if hasattr(self.bridge, '_qr_status'): del self.bridge._qr_status
            if hasattr(self.bridge, '_qr_created_at'): del self.bridge._qr_created_at
            if hasattr(self.bridge, '_qr_error'): del self.bridge._qr_error
            if hasattr(self.bridge, '_qr_needs_password'): del self.bridge._qr_needs_password
            
            # Clear Passcode state on bridge
            if hasattr(self.bridge, '_session_passcode'): self.bridge._session_passcode = None
            self.bridge._failed_passcode_attempts = 0
            self.bridge._passcode_lockout_until = None
            
            print("AuthHandler: logout successful")
            return {"success": True}
        except Exception as e:
            print(f"AuthHandler: logout error: {e}")
            raise

    async def request_qr(self):
        await self.bridge._ensure_client()
        
        # Reuse existing QR if valid
        if hasattr(self.bridge, '_current_qr') and hasattr(self.bridge, '_qr_created_at'):
            if time.time() - self.bridge._qr_created_at < 25:
                print("AuthHandler: Reusing existing QR request")
                qr = self.bridge._current_qr
                return {
                    "qr_url": qr.url,
                    "token_id": qr.token.hex() if isinstance(qr.token, bytes) else str(qr.token),
                    "expires_in": 30
                }

        print("AuthHandler: Calling qr_login_start...")
        qr = await tg_client.qr_login_start()
        
        self.bridge._current_qr = qr
        self.bridge._qr_created_at = time.time()
        self.bridge._qr_status = "waiting"
        self.bridge._qr_error = None
        self.bridge._qr_needs_password = False
        
        # Start background monitor
        asyncio.create_task(self._monitor_qr(qr))
        
        return {
            "qr_url": qr.url,
            "token_id": qr.token.hex() if isinstance(qr.token, bytes) else str(qr.token),
            "expires_in": 30
        }

    async def _monitor_qr(self, qr):
        print("AuthHandler: Starting QR monitor task")
        try:
            user = await qr.wait(timeout=60)
            print(f"AuthHandler: QR scan confirmed! User: {user}")
            self.bridge._qr_status = "confirmed"
        except Exception as e:
            error_name = type(e).__name__
            print(f"AuthHandler: QR monitor exception: {error_name}: {e}")
            if "SessionPasswordNeededError" in error_name:
                self.bridge._qr_status = "confirmed"
                self.bridge._qr_needs_password = True
            elif "TimeoutError" in error_name:
                self.bridge._qr_status = "expired"
            elif "already" in str(e).lower() or "authorized" in str(e).lower():
                self.bridge._qr_status = "confirmed"
            else:
                self.bridge._qr_status = "error"
                self.bridge._qr_error = str(e)

    async def check_qr_status(self, token_id):
        if not hasattr(self.bridge, '_current_qr'):
            return {"status": "expired"}
        
        status = getattr(self.bridge, '_qr_status', 'waiting')
        
        if status == "confirmed":
            result = {"status": "confirmed"}
            if getattr(self.bridge, '_qr_needs_password', False):
                result["needs_password"] = True
            return result
        elif status == "error":
            return {"status": "error", "error": getattr(self.bridge, '_qr_error', 'Unknown error')}
        elif status == "expired":
            return {"status": "expired"}
            
        # Fallback check
        if status == "waiting":
            try:
                if await tg_client.is_user_authorized():
                    self.bridge._qr_status = "confirmed"
                    return {"status": "confirmed"}
            except:
                pass
        
        return {"status": "waiting"}
