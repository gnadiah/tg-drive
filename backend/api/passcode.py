import time
from backend.core import tg_client

class PasscodeHandler:
    def __init__(self, bridge):
        self.bridge = bridge

    async def has_passcode(self):
        await self.bridge._ensure_client()
        from backend.core import has_passcode_on_telegram
        return {"has_passcode": await has_passcode_on_telegram(tg_client.client)}

    async def set_passcode(self, passcode):
        await self.bridge._ensure_client()
        from backend.core import set_passcode_on_telegram, validate_passcode
        
        if not validate_passcode(passcode):
            return {"success": False, "error": "Passcode must be exactly 6 digits"}
        
        try:
            await set_passcode_on_telegram(tg_client.client, passcode)
            self.bridge._session_passcode = passcode
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def verify_passcode(self, passcode):
        # Check if locked out
        if self.bridge._passcode_lockout_until and time.time() < self.bridge._passcode_lockout_until:
            retry_after = int(self.bridge._passcode_lockout_until - time.time())
            return {
                "valid": False,
                "error": "locked_out",
                "message": f"Too many failed attempts. Try again in {retry_after}s",
                "retry_after": retry_after
            }
        
        await self.bridge._ensure_client()
        from backend.core import verify_passcode_from_telegram
        
        valid = await verify_passcode_from_telegram(tg_client.client, passcode)
        
        if valid:
            self.bridge._failed_passcode_attempts = 0
            self.bridge._passcode_lockout_until = None
            self.bridge._session_passcode = passcode
            return {"valid": True}
        else:
            self.bridge._failed_passcode_attempts += 1
            attempts_remaining = 5 - self.bridge._failed_passcode_attempts
            
            if self.bridge._failed_passcode_attempts >= 5:
                self.bridge._passcode_lockout_until = time.time() + 30
                return {
                    "valid": False,
                    "error": "too_many_attempts",
                    "message": "Too many failed attempts. Locked for 30 seconds",
                    "locked_for": 30,
                    "attempts_remaining": 0
                }
            else:
                return {
                    "valid": False,
                    "error": "incorrect",
                    "message": f"Incorrect passcode. {attempts_remaining} attempts remaining",
                    "attempts_remaining": attempts_remaining
                }

    async def change_passcode(self, old_passcode, new_passcode):
        await self.bridge._ensure_client()
        from backend.core import change_passcode_on_telegram, validate_passcode
        
        if not validate_passcode(new_passcode):
            return {"error": "New passcode must be exactly 6 digits"}
        
        try:
            success = await change_passcode_on_telegram(tg_client.client, old_passcode, new_passcode)
            if success:
                self.bridge._session_passcode = new_passcode
                
                # Re-encrypt all V2 metadata messages
                try:
                    from backend.core import MetadataManager
                    print("PasscodeHandler: Starting metadata re-encryption...")
                    count = 0
                    async for msg in tg_client.client.iter_messages("me"):
                        if msg.text and msg.text.startswith("METADATA_V2_ENCRYPTED"):
                            try:
                                encrypted_str = msg.text.split("\n", 1)[1]
                                metadata = MetadataManager.from_json_encrypted(encrypted_str, old_passcode)
                                new_content = MetadataManager.to_json_encrypted(metadata, new_passcode)
                                await msg.edit(f"METADATA_V2_ENCRYPTED\n{new_content}")
                                count += 1
                            except Exception as e:
                                print(f"PasscodeHandler: Failed to re-encrypt message {msg.id}: {e}")
                    print(f"PasscodeHandler: Re-encryption complete. Processed {count} files.")
                except Exception as e:
                    print(f"PasscodeHandler: Critical error during re-encryption: {e}")
                
                return {"success": True}
            else:
                return {"error": "Incorrect old passcode"}
        except ValueError as e:
            return {"error": str(e)}

    async def reset_encryption(self):
        await self.bridge._ensure_client()
        from backend.core import reset_all_encrypted_data
        result = await reset_all_encrypted_data(tg_client.client)
        
        if hasattr(self.bridge, '_session_passcode'):
            self.bridge._session_passcode = None
        self.bridge._failed_passcode_attempts = 0
        self.bridge._passcode_lockout_until = None
        
        return {
            "success": True,
            "passcode_deleted": result["passcode_deleted"],
            "encrypted_files_deleted": result["encrypted_files_deleted"],
            "chunks_deleted": result.get("chunks_deleted", 0)
        }
