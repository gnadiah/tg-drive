import asyncio
import os
import uuid
import shutil
import threading
import time
import webview
from backend.core import tg_client, split_file, get_file_hash, merge_files, CHUNK_SIZE, FileMetadata, FileChunk, MetadataManager
from backend.core.parallel_uploader import ParallelUploader
from backend.core.parallel_downloader import ParallelDownloader

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

class FileHandler:
    def __init__(self, bridge):
        self.bridge = bridge

    async def list_files(self):
        await self.bridge._ensure_client()
        messages = await tg_client.get_messages(limit=100)
        files = []
        passcode = getattr(self.bridge, '_session_passcode', None)
        
        for msg in messages:
            if not msg.text: continue
            
            try:
                metadata = None
                
                if msg.text.startswith("METADATA_V1"):
                    json_str = msg.text.split("\n", 1)[1]
                    metadata = MetadataManager.from_json(json_str)
                    
                elif msg.text.startswith("METADATA_V2_ENCRYPTED"):
                    if passcode:
                        try:
                            encrypted_str = msg.text.split("\n", 1)[1]
                            metadata = MetadataManager.from_json_encrypted(encrypted_str, passcode)
                        except Exception as e:
                            print(f"FileHandler: Failed to decrypt file {msg.id}: {e}")
                            continue
                    else:
                        continue
                
                if metadata:
                    file_data = metadata.model_dump()
                    file_data["metadata_message_id"] = msg.id
                    files.append(file_data)
                    
            except Exception as e:
                print(f"FileHandler: Error parsing message {msg.id}: {e}")
                continue
        return files

    def pick_and_upload_file(self):
        file_types = ('All files (*.*)',)
        window = self.bridge._window[0] if isinstance(self.bridge._window, list) else self.bridge._window
        result = window.create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=False,
            file_types=file_types
        )
        
        if result:
            file_path = result[0]
            asyncio.run_coroutine_threadsafe(self._upload_logic(file_path), self.bridge.loop)
            return {"status": "started", "file": os.path.basename(file_path)}
        return {"status": "cancelled"}

    async def _upload_logic(self, file_path):
        file_id = str(uuid.uuid4())
        try:
            await self.bridge._ensure_client()
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            try:
                self.bridge._window.evaluate_js(f"window.onUploadProgress('{file_id}', 0, '0 B/s', 'Starting...')")
            except Exception as e:
                print(f"FileHandler: [Upload] Failed to init UI: {e}")

            file_hash = get_file_hash(file_path)
            chunk_gen = split_file(file_path)
            total_chunks = (file_size // CHUNK_SIZE) + 1
            
            tracker = TransferTracker(file_size, file_id, self.bridge._window, is_upload=True)
            
            active_tasks = set()
            chunks_metadata = []
            
            async def upload_worker(index, chunk_data):
                print(f"FileHandler: [Upload] Starting chunk {index}/{total_chunks} ({len(chunk_data)} bytes)")
                temp_dir = "temp_uploads"
                os.makedirs(temp_dir, exist_ok=True)
                chunk_temp_path = os.path.join(temp_dir, f"{file_id}_part{index}")

                with open(chunk_temp_path, "wb") as f:
                    f.write(chunk_data)
                
                chunk_hash = get_file_hash(chunk_temp_path)
                
                def progress_callback(current, total):
                    tracker.update(index, current, total)

                # Upload using ParallelUploader
                passcode = getattr(self.bridge, '_session_passcode', None)
                caption = "#ENCRYPTED_CHUNK" if passcode else "#TG_DRIVE_CHUNK"
                
                uploader = ParallelUploader(tg_client.client)
                input_file = await uploader.upload_file(
                    chunk_temp_path,
                    progress_callback=progress_callback
                )
                
                # Send the uploaded file as a message
                message = await tg_client.client.send_file(
                    "me",
                    input_file,
                    caption=caption,
                    force_document=True
                )
                print(f"FileHandler: [Upload] Chunk {index} uploaded. Message ID: {message.id}")
                
                os.remove(chunk_temp_path)
                
                return FileChunk(
                    index=index,
                    message_id=message.id,
                    size=len(chunk_data),
                    hash=chunk_hash
                )

            for index, chunk_data in chunk_gen:
                if len(active_tasks) >= 5:
                    done, active_tasks = await asyncio.wait(active_tasks, return_when=asyncio.FIRST_COMPLETED)
                    for t in done:
                        chunks_metadata.append(await t)
                
                task = asyncio.create_task(upload_worker(index, chunk_data))
                active_tasks.add(task)
            
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
            
            passcode = getattr(self.bridge, '_session_passcode', None)
            
            if passcode:
                metadata_encrypted = MetadataManager.to_json_encrypted(metadata, passcode)
                await tg_client.send_message(f"METADATA_V2_ENCRYPTED\n{metadata_encrypted}")
                print(f"FileHandler: [Upload] Encrypted metadata (V2) sent.")
            else:
                metadata_json = MetadataManager.to_json(metadata)
                await tg_client.send_message(f"METADATA_V1\n{metadata_json}")
                print(f"FileHandler: [Upload] Plaintext metadata (V1) sent.")
            
            self.bridge._window.evaluate_js(f"window.onUploadComplete('{file_id}')")
            
        except Exception as e:
            print(f"Upload error: {e}")
            self.bridge._window.evaluate_js(f"window.onUploadError('{file_id}', '{str(e)}')")

    def download_file(self, file_id):
        asyncio.run_coroutine_threadsafe(self._download_logic(file_id), self.bridge.loop)
        return {"status": "started"}

    async def _download_logic(self, file_id):
        try:
            await self.bridge._ensure_client()
            messages = await tg_client.get_messages(limit=100)
            metadata = None
            passcode = getattr(self.bridge, '_session_passcode', None)
            
            for msg in messages:
                if not msg.text: continue
                try:
                    if msg.text.startswith("METADATA_V1"):
                        json_str = msg.text.split("\n", 1)[1]
                        m = MetadataManager.from_json(json_str)
                        if m.id == file_id:
                            metadata = m
                            break
                    elif msg.text.startswith("METADATA_V2_ENCRYPTED"):
                        if passcode:
                            try:
                                encrypted_str = msg.text.split("\n", 1)[1]
                                m = MetadataManager.from_json_encrypted(encrypted_str, passcode)
                                if m.id == file_id:
                                    metadata = m
                                    break
                            except: continue
                except: continue
            
            if not metadata:
                self.bridge._window.evaluate_js(f"window.onDownloadError('{file_id}', 'File not found')")
                return

            window = self.bridge._window[0] if isinstance(self.bridge._window, list) else self.bridge._window
            save_path = window.create_file_dialog(
                webview.FileDialog.SAVE,
                save_filename=metadata.name
            )
            
            if not save_path:
                return

            save_path = save_path if isinstance(save_path, str) else save_path[0]
            temp_dir = f"temp_download_{file_id}"
            os.makedirs(temp_dir, exist_ok=True)
            
            sorted_chunks = sorted(metadata.chunks, key=lambda c: c.index)
            total = len(sorted_chunks)
            total_size = metadata.size
            
            tracker = TransferTracker(total_size, file_id, self.bridge._window, is_upload=False)
            sem = asyncio.Semaphore(5)
            chunk_paths = [None] * total

            async def download_worker(i, chunk):
                async with sem:
                    print(f"FileHandler: [Download] Starting chunk {i}/{total}")
                    chunk_msg = await tg_client.get_message_by_id(chunk.message_id)
                    if not chunk_msg:
                        raise Exception(f"Chunk {chunk.index} missing")
                    
                    chunk_path = os.path.join(temp_dir, f"chunk_{chunk.index}")
                    
                    def progress_callback(current, total):
                        tracker.update(i, current, total)

                    # Use ParallelDownloader
                    downloader = ParallelDownloader(tg_client.client)
                    await downloader.download_file(
                        chunk_msg[0],
                        chunk_path,
                        progress_callback=progress_callback
                    )
                    
                    if get_file_hash(chunk_path) != chunk.hash:
                        raise Exception(f"Chunk {chunk.index} hash mismatch")
                    
                    print(f"FileHandler: [Download] Chunk {i} done.")
                    return i, chunk_path

            tasks = [download_worker(i, chunk) for i, chunk in enumerate(sorted_chunks)]
            results = await asyncio.gather(*tasks)
            
            for i, path in results:
                chunk_paths[i] = path

            print("FileHandler: [Download] Merging files...")
            self.bridge._window.evaluate_js(f"window.onDownloadProgress('{file_id}', 99, '0 B/s', 'Merging...')")
            merge_files(chunk_paths, save_path)
            
            print("FileHandler: [Download] Verifying integrity...")
            final_hash = get_file_hash(save_path)
            if final_hash != metadata.hash:
                shutil.rmtree(temp_dir)
                if os.path.exists(save_path):
                    os.remove(save_path)
                raise Exception(f"File integrity check failed!")
            
            shutil.rmtree(temp_dir)
            print("FileHandler: [Download] Complete.")
            self.bridge._window.evaluate_js(f"window.onDownloadComplete('{file_id}')")

        except Exception as e:
            print(f"Download error: {e}")
            self.bridge._window.evaluate_js(f"window.onDownloadError('{file_id}', '{str(e)}')")

    def rename_file(self, file_id, new_name, metadata_message_id):
        async def _rename():
            await self.bridge._ensure_client()
            msgs = await tg_client.get_message_by_id(metadata_message_id)
            if not msgs: return {"error": "Message not found"}
            msg = msgs[0]
            passcode = getattr(self.bridge, '_session_passcode', None)
            
            metadata = None
            is_encrypted = False
            
            if msg.text.startswith("METADATA_V1"):
                json_str = msg.text.split("\n", 1)[1]
                metadata = MetadataManager.from_json(json_str)
            elif msg.text.startswith("METADATA_V2_ENCRYPTED"):
                if not passcode: return {"error": "Passcode required"}
                try:
                    encrypted_str = msg.text.split("\n", 1)[1]
                    metadata = MetadataManager.from_json_encrypted(encrypted_str, passcode)
                    is_encrypted = True
                except: return {"error": "Decryption failed"}
            
            if not metadata: return {"error": "Invalid metadata"}
            
            metadata.name = new_name
            
            if is_encrypted:
                new_content = MetadataManager.to_json_encrypted(metadata, passcode)
                await msg.edit(f"METADATA_V2_ENCRYPTED\n{new_content}")
            else:
                new_content = MetadataManager.to_json(metadata)
                await msg.edit(f"METADATA_V1\n{new_content}")
                
            return {"success": True}
        return self.bridge._run_async(_rename())

    def delete_file(self, file_id, metadata_message_id):
        async def _delete():
            await self.bridge._ensure_client()
            msgs = await tg_client.get_message_by_id(metadata_message_id)
            if not msgs: return {"error": "Message not found"}
            msg = msgs[0]
            passcode = getattr(self.bridge, '_session_passcode', None)
            
            metadata = None
            
            if msg.text.startswith("METADATA_V1"):
                json_str = msg.text.split("\n", 1)[1]
                metadata = MetadataManager.from_json(json_str)
            elif msg.text.startswith("METADATA_V2_ENCRYPTED"):
                if not passcode: return {"error": "Passcode required"}
                try:
                    encrypted_str = msg.text.split("\n", 1)[1]
                    metadata = MetadataManager.from_json_encrypted(encrypted_str, passcode)
                except: return {"error": "Decryption failed"}
            
            if metadata:
                chunk_ids = [c.message_id for c in metadata.chunks]
                await tg_client.delete_messages(chunk_ids)
            
            await tg_client.delete_messages([metadata_message_id])
            return {"success": True}
        return self.bridge._run_async(_delete())
