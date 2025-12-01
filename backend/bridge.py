import asyncio
import os
import threading
import webview
from backend.core.client import tg_client
from backend.core.file_manager import split_file, get_file_hash, merge_files
from backend.core.metadata_manager import FileMetadata, FileChunk, MetadataManager
import uuid
import shutil
import time

class Bridge:
    def __init__(self):
        self._window = None
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
        # print(f"Bridge: Dispatching {coro.__name__} to background loop")
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            res = future.result()
            # print(f"Bridge: {coro.__name__} completed")
            return res
        except Exception as e:
            print(f"Bridge: {coro.__name__} failed: {e}")
            # Unwrap exception if possible or just raise
            raise e

    async def _ensure_client(self):
        if not tg_client.client or not tg_client.client.is_connected():
            await tg_client.start()

    # --- Authentication ---

    def check_auth(self):
        async def _check():
            print("Bridge: check_auth called")
            await self._ensure_client()
            is_auth = await tg_client.is_user_authorized()
            print(f"Bridge: is_user_authorized={is_auth}")
            
            user_data = None
            
            # Try to fetch user even if is_auth is False, just to be sure/refresh
            try:
                me = await tg_client.get_me()
                if me:
                    print(f"Bridge: get_me() success! User: {me.id}")
                    is_auth = True
                    user_data = {
                        "id": me.id,
                        "first_name": me.first_name,
                        "last_name": me.last_name,
                        "username": me.username,
                        "phone": me.phone
                    }
            except Exception as e:
                print(f"Bridge: get_me() failed (expected if not auth): {e}")

            return {"authenticated": is_auth, "user": user_data}
        
        return self._run_async(_check())

    def request_code(self, phone):
        async def _req():
            await self._ensure_client()
            await tg_client.send_code_request(phone)
            return {"success": True}
        
        try:
            return self._run_async(_req())
        except Exception as e:
            raise e

    def sign_in(self, phone, code, password=None):
        async def _sign_in():
            print(f"TGClient: sign_in called for {phone} (password={'YES' if password else 'NO'})")
            await self._ensure_client()
            try:
                await tg_client.sign_in(phone, code, password)
                return {"success": True}
            except Exception as e:
                print(f"TGClient: sign_in exception: {type(e).__name__}: {e}")
                if "SessionPasswordNeededError" in str(type(e).__name__):
                     return {"status": "needs_password"}
                return {"error": str(e)}
        
        return self._run_async(_sign_in())

    def logout(self):
        async def _logout():
            try:
                print("Bridge: logout() called")
                await self._ensure_client()
                await tg_client.log_out()
                
                # Clear QR state
                if hasattr(self, '_current_qr'): del self._current_qr
                if hasattr(self, '_qr_status'): del self._qr_status
                if hasattr(self, '_qr_created_at'): del self._qr_created_at
                if hasattr(self, '_qr_error'): del self._qr_error
                if hasattr(self, '_qr_needs_password'): del self._qr_needs_password
                
                print("Bridge: logout successful")
                return {"success": True}
            except Exception as e:
                print(f"Bridge: logout error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        try:
            return self._run_async(_logout())
        except Exception as e:
            print(f"Bridge: _run_async(logout) failed: {e}")
            raise

    def log(self, message):
        """Log message from JS."""
        print(f"JS_LOG: {message}")

    # --- QR Login ---
    
    def request_qr(self):
        async def _req_qr():
            await self._ensure_client()
            
            # Reuse existing QR if valid (created < 25s ago)
            if hasattr(self, '_current_qr') and hasattr(self, '_qr_created_at'):
                if time.time() - self._qr_created_at < 25:
                    print("Bridge: Reusing existing QR request")
                    qr = self._current_qr
                    return {
                        "qr_url": qr.url,
                        "token_id": qr.token.hex() if isinstance(qr.token, bytes) else str(qr.token),
                        "expires_in": 30
                    }

            print("Bridge: Calling qr_login_start...")
            qr = await tg_client.qr_login_start()
            print(f"Bridge: qr_login_start returned type={type(qr)}")
            
            self._current_qr = qr
            self._qr_created_at = time.time()
            self._qr_status = "waiting"
            self._qr_error = None
            self._qr_needs_password = False
            
            # Start background monitor
            asyncio.create_task(self._monitor_qr(qr))
            
            try:
                url = qr.url
                print(f"Bridge: qr.url={url}")
            except Exception as e:
                print(f"Bridge: qr.url access failed: {e}")
                raise e

            return {
                "qr_url": url,
                "token_id": qr.token.hex() if isinstance(qr.token, bytes) else str(qr.token),
                "expires_in": 30
            }
        return self._run_async(_req_qr())

    async def _monitor_qr(self, qr):
        """Background task to monitor QR status"""
        print("Bridge: Starting QR monitor task")
        try:
            # Wait for QR scan (long timeout)
            user = await qr.wait(timeout=60)
            print(f"Bridge: QR scan confirmed! User: {user}")
            self._qr_status = "confirmed"
            
        except Exception as e:
            error_name = type(e).__name__
            print(f"Bridge: QR monitor exception: {error_name}: {e}")
            
            if "SessionPasswordNeededError" in error_name:
                print("Bridge: QR Login successful (needs 2FA)")
                self._qr_status = "confirmed"
                self._qr_needs_password = True
            elif "TimeoutError" in error_name:
                self._qr_status = "expired"
            elif "already" in str(e).lower() or "authorized" in str(e).lower():
                print("Bridge: Already authorized")
                self._qr_status = "confirmed"
            else:
                self._qr_status = "error"
                self._qr_error = str(e)

    def check_qr_status(self, token_id):
        async def _check():
            if not hasattr(self, '_current_qr'):
                return {"status": "expired"}
            
            # Return cached status from monitor
            status = getattr(self, '_qr_status', 'waiting')
            
            if status == "confirmed":
                result = {"status": "confirmed"}
                if getattr(self, '_qr_needs_password', False):
                    result["needs_password"] = True
                return result
            
            elif status == "error":
                return {"status": "error", "error": getattr(self, '_qr_error', 'Unknown error')}
            
            elif status == "expired":
                return {"status": "expired"}
                
            # Fallback: Check auth state directly if still waiting
            if status == "waiting":
                try:
                    if await tg_client.is_user_authorized():
                        print("QR: User is authorized (fallback check)!")
                        self._qr_status = "confirmed"
                        return {"status": "confirmed"}
                except:
                    pass
            
            return {"status": "waiting"}
        
        return self._run_async(_check())

    # --- Files ---

    # --- Helper ---
    class TransferTracker:
        def __init__(self, total_size, file_id, window, is_upload=True):
            self.total_size = total_size
            self.file_id = file_id
            self.window = window
            self.is_upload = is_upload
            self.start_time = time.time()
            self.chunk_progress = {} # chunk_index -> bytes_transferred
            self.last_update_time = 0
            self.lock = threading.Lock()

        def update(self, chunk_index, current, total):
            with self.lock:
                self.chunk_progress[chunk_index] = current
                
                now = time.time()
                if now - self.last_update_time < 0.1: # Limit updates to 100ms
                    return

                self.last_update_time = now
                
                total_transferred = sum(self.chunk_progress.values())
                progress = int((total_transferred / self.total_size) * 100)
                
                duration = now - self.start_time
                if duration < 0.1: duration = 0.1
                speed = total_transferred / duration
                
                if speed > 1024 * 1024:
                    speed_str = f"{speed / (1024 * 1024):.1f} MB/s"
                elif speed > 1024:
                    speed_str = f"{speed / 1024:.1f} KB/s"
                else:
                    speed_str = f"{speed:.0f} B/s"
                
                method = "onUploadProgress" if self.is_upload else "onDownloadProgress"
                try:
                    self.window.evaluate_js(f"window.{method}('{self.file_id}', {progress}, '{speed_str}', 'Transferring...')")
                except:
                    pass

    # --- Files ---

    def list_files(self):
        async def _list():
            await self._ensure_client()
            messages = await tg_client.get_messages(limit=100)
            files = []
            for msg in messages:
                if msg.text and msg.text.startswith("METADATA_V1"):
                    try:
                        json_str = msg.text.split("\n", 1)[1]
                        metadata = MetadataManager.from_json(json_str)
                        file_data = metadata.model_dump()
                        file_data["metadata_message_id"] = msg.id
                        files.append(file_data)
                    except Exception:
                        continue
            return files
        return self._run_async(_list())

    def pick_and_upload_file(self):
        file_types = ('All files (*.*)',)
        result = self._window.create_file_dialog(dialog_type=webview.windows.FileDialog.OPEN, allow_multiple=False, file_types=file_types)
        
        if result:
            file_path = result[0]
            # Use run_coroutine_threadsafe directly for fire-and-forget background task
            asyncio.run_coroutine_threadsafe(self._upload_logic(file_path), self.loop)
            return {"status": "started", "file": os.path.basename(file_path)}
        return {"status": "cancelled"}

    async def _upload_logic(self, file_path):
        file_id = str(uuid.uuid4())
        try:
            await self._ensure_client()
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            try:
                self._window.evaluate_js(f"window.onUploadProgress('{file_id}', 0, '0 B/s', 'Starting...')")
            except Exception as e:
                print(f"Bridge: [Upload] Failed to init UI: {e}")

            file_hash = get_file_hash(file_path)
            
            chunk_gen = split_file(file_path)
            from backend.core.file_manager import CHUNK_SIZE
            total_chunks = (file_size // CHUNK_SIZE) + 1
            
            tracker = self.TransferTracker(file_size, file_id, self._window, is_upload=True)
            
            # Concurrency control
            active_tasks = set()
            chunks_metadata = []
            
            async def upload_worker(index, chunk_data):
                print(f"Bridge: [Upload] Starting chunk {index}/{total_chunks} ({len(chunk_data)} bytes)")
                
                # Use temp dir
                temp_dir = "temp_uploads"
                os.makedirs(temp_dir, exist_ok=True)
                chunk_temp_path = os.path.join(temp_dir, f"{file_id}_part{index}")

                with open(chunk_temp_path, "wb") as f:
                    f.write(chunk_data)
                
                chunk_hash = get_file_hash(chunk_temp_path)
                
                def progress_callback(current, total):
                    tracker.update(index, current, total)

                # Upload
                message = await tg_client.upload_file(
                    chunk_temp_path, 
                    caption=f"chunk_{index}_{file_id}",
                    progress_callback=progress_callback
                )
                print(f"Bridge: [Upload] Chunk {index} uploaded. Message ID: {message.id}")
                
                # Cleanup
                os.remove(chunk_temp_path)
                
                return FileChunk(
                    index=index,
                    message_id=message.id,
                    size=len(chunk_data),
                    hash=chunk_hash
                )

            # Producer-Consumer loop to limit memory usage
            for index, chunk_data in chunk_gen:
                if len(active_tasks) >= 5: # Limit to 5 concurrent uploads
                    done, active_tasks = await asyncio.wait(active_tasks, return_when=asyncio.FIRST_COMPLETED)
                    for t in done:
                        chunks_metadata.append(await t)
                
                task = asyncio.create_task(upload_worker(index, chunk_data))
                active_tasks.add(task)
            
            # Wait for remaining
            if active_tasks:
                done, _ = await asyncio.wait(active_tasks)
                for t in done:
                    chunks_metadata.append(await t)

            metadata = FileMetadata(
                id=file_id,
                name=filename,
                size=file_size,
                chunks=chunks_metadata,
                hash=file_hash,
                mime_type="application/octet-stream"
            )
            
            metadata_json = MetadataManager.to_json(metadata)
            await tg_client.send_message(f"METADATA_V1\n{metadata_json}")
            print(f"Bridge: [Upload] Metadata sent. Upload complete.")
            
            self._window.evaluate_js(f"window.onUploadComplete('{file_id}')")
            
        except Exception as e:
            print(f"Upload error: {e}")
            self._window.evaluate_js(f"window.onUploadError('{file_id}', '{str(e)}')")

    def download_file(self, file_id):
        # Fire and forget download logic
        asyncio.run_coroutine_threadsafe(self._download_logic(file_id), self.loop)
        return {"status": "started"}

    async def _download_logic(self, file_id):
        try:
            await self._ensure_client()
            
            messages = await tg_client.get_messages(limit=100)
            metadata = None
            for msg in messages:
                if msg.text and msg.text.startswith("METADATA_V1"):
                    try:
                        json_str = msg.text.split("\n", 1)[1]
                        m = MetadataManager.from_json(json_str)
                        if m.id == file_id:
                            metadata = m
                            break
                    except: continue
            
            if not metadata:
                self._window.evaluate_js(f"window.onDownloadError('{file_id}', 'File not found')")
                return

            save_path = self._window.create_file_dialog(dialog_type=webview.windows.FileDialog.SAVE, save_filename=metadata.name)
            
            if not save_path:
                return

            save_path = save_path if isinstance(save_path, str) else save_path[0]

            temp_dir = f"temp_download_{file_id}"
            os.makedirs(temp_dir, exist_ok=True)
            
            sorted_chunks = sorted(metadata.chunks, key=lambda c: c.index)
            total = len(sorted_chunks)
            total_size = metadata.size
            
            tracker = self.TransferTracker(total_size, file_id, self._window, is_upload=False)
            
            sem = asyncio.Semaphore(5) # Limit concurrent downloads
            
            chunk_paths = [None] * total # Pre-allocate to store in order

            async def download_worker(i, chunk):
                async with sem:
                    print(f"Bridge: [Download] Starting chunk {i}/{total}")
                    chunk_msg = await tg_client.get_message_by_id(chunk.message_id)
                    if not chunk_msg:
                        raise Exception(f"Chunk {chunk.index} missing")
                    
                    chunk_path = os.path.join(temp_dir, f"chunk_{chunk.index}")
                    
                    def progress_callback(current, total):
                        tracker.update(i, current, total)

                    await tg_client.download_media(
                        chunk_msg[0], 
                        chunk_path,
                        progress_callback=progress_callback
                    )
                    
                    if get_file_hash(chunk_path) != chunk.hash:
                        raise Exception(f"Chunk {chunk.index} hash mismatch")
                    
                    print(f"Bridge: [Download] Chunk {i} done.")
                    return i, chunk_path

            tasks = [download_worker(i, chunk) for i, chunk in enumerate(sorted_chunks)]
            results = await asyncio.gather(*tasks)
            
            # Sort results just in case, though gather preserves order
            for i, path in results:
                chunk_paths[i] = path

            print("Bridge: [Download] Merging files...")
            self._window.evaluate_js(f"window.onDownloadProgress('{file_id}', 99, '0 B/s', 'Merging...')")
            merge_files(chunk_paths, save_path)
            
            # Verify final file integrity
            print("Bridge: [Download] Verifying integrity...")
            final_hash = get_file_hash(save_path)
            if final_hash != metadata.hash:
                shutil.rmtree(temp_dir)
                if os.path.exists(save_path):
                    os.remove(save_path)
                raise Exception(f"File integrity check failed! Expected {metadata.hash[:16]}..., got {final_hash[:16]}...")
            
            print(f"Bridge: [Download] Integrity verified: {final_hash[:16]}...")
            
            shutil.rmtree(temp_dir)
            
            print("Bridge: [Download] Complete.")
            self._window.evaluate_js(f"window.onDownloadComplete('{file_id}')")

        except Exception as e:
            print(f"Download error: {e}")
            self._window.evaluate_js(f"window.onDownloadError('{file_id}', '{str(e)}')")

    def rename_file(self, file_id, new_name, metadata_message_id):
        async def _rename():
            await self._ensure_client()
            msgs = await tg_client.get_message_by_id(metadata_message_id)
            if not msgs: return {"error": "Message not found"}
            msg = msgs[0]
            
            json_str = msg.text.split("\n", 1)[1]
            metadata = MetadataManager.from_json(json_str)
            if metadata.id != file_id: return {"error": "ID mismatch"}
            
            metadata.name = new_name
            new_json = MetadataManager.to_json(metadata)
            await tg_client.edit_message(metadata_message_id, f"METADATA_V1\n{new_json}")
            return {"success": True}
        return self._run_async(_rename())

    def delete_file(self, file_id, metadata_message_id):
        async def _delete():
            await self._ensure_client()
            msgs = await tg_client.get_message_by_id(metadata_message_id)
            if not msgs: return {"error": "Message not found"}
            msg = msgs[0]
            
            json_str = msg.text.split("\n", 1)[1]
            metadata = MetadataManager.from_json(json_str)
            
            chunk_ids = [c.message_id for c in metadata.chunks]
            await tg_client.delete_messages(chunk_ids)
            await tg_client.delete_messages([metadata_message_id])
            return {"success": True}
        return self._run_async(_delete())
