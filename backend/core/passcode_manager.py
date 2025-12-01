"""
Passcode manager - stores encrypted passcode on Telegram.
Zero-knowledge approach: passcode encrypted by itself, no local storage.
"""
from typing import Optional


async def set_passcode_on_telegram(client, passcode: str) -> None:
    """
    Store encrypted passcode on Telegram (Saved Messages).
    Passcode is encrypted using itself as the key.
    
    Args:
        client: Telegram client
        passcode: 6-digit passcode
        
    Raises:
        ValueError: If passcode is not exactly 6 digits
    """
    from .crypto_utils import validate_passcode, encrypt_data
    
    if not validate_passcode(passcode):
        raise ValueError("Passcode must be exactly 6 digits")
    
    # Encrypt passcode using itself as key
    # This creates a verifiable hash that can only be decrypted with correct passcode
    encrypted_passcode = encrypt_data(passcode, passcode)
    
    # Send to Saved Messages (entity "me")
    await client.send_message("me", f"PASSCODE_HASH\n{encrypted_passcode}")


async def verify_passcode_from_telegram(client, passcode: str) -> bool:
    """
    Verify passcode by attempting to decrypt the stored hash.
    
    Args:
        client: Telegram client
        passcode: 6-digit passcode to verify
        
    Returns:
        True if passcode is correct, False otherwise
    """
    from .crypto_utils import validate_passcode, decrypt_data
    from cryptography.fernet import InvalidToken
    
    if not validate_passcode(passcode):
        return False
    
    # Fetch passcode hash from Telegram
    messages = await client.get_messages("me", limit=100)
    
    for msg in messages:
        if msg.text and msg.text.startswith("PASSCODE_HASH\n"):
            encrypted_passcode = msg.text.split("\n", 1)[1]
            
            try:
                # Try to decrypt with provided passcode
                decrypted = decrypt_data(encrypted_passcode, passcode)
                # If decryption succeeds and result matches input = correct passcode
                return decrypted == passcode
            except (InvalidToken, Exception):
                # Wrong passcode or corrupted data
                return False
    
    # No passcode hash found
    return False


async def has_passcode_on_telegram(client) -> bool:
    """
    Check if passcode exists on Telegram.
    
    Args:
        client: Telegram client
        
    Returns:
        True if passcode hash exists, False otherwise
    """
    messages = await client.get_messages("me", limit=100)
    
    for msg in messages:
        if msg.text and msg.text.startswith("PASSCODE_HASH\n"):
            return True
    
    return False


async def change_passcode_on_telegram(client, old_passcode: str, new_passcode: str) -> bool:
    """
    Change passcode after verifying old one.
    Deletes old hash and creates new one.
    
    Args:
        client: Telegram client
        old_passcode: Current passcode for verification
        new_passcode: New 6-digit passcode
        
    Returns:
        True if passcode changed successfully, False if old passcode wrong
        
    Raises:
        ValueError: If new passcode is not exactly 6 digits
    """
    from .crypto_utils import validate_passcode
    
    if not validate_passcode(new_passcode):
        raise ValueError("New passcode must be exactly 6 digits")
    
    # Verify old passcode first
    if not await verify_passcode_from_telegram(client, old_passcode):
        return False
    
    # Delete old passcode hash
    messages = await client.get_messages("me", limit=100)
    for msg in messages:
        if msg.text and msg.text.startswith("PASSCODE_HASH\n"):
            await client.delete_messages("me", [msg.id])
            break
    
    # Set new passcode
    await set_passcode_on_telegram(client, new_passcode)
    return True


async def delete_passcode_from_telegram(client) -> None:
    """
    Delete passcode hash from Telegram.
    WARNING: This will make all encrypted metadata unrecoverable!
    
    Args:
        client: Telegram client
    """
    messages = await client.get_messages("me", limit=100)
    
    for msg in messages:
        if msg.text and msg.text.startswith("PASSCODE_HASH\n"):
            await client.delete_messages("me", [msg.id])
            break


async def reset_all_encrypted_data(client) -> dict:
    """
    NUCLEAR OPTION: Delete all encrypted data (passcode + V2 metadata).
    This is the ONLY recovery option if passcode is forgotten.
    
    Args:
        client: Telegram client
        
    Returns:
        dict with counts: {"passcode_deleted": int, "encrypted_files_deleted": int}
    """
    messages = await client.get_messages("me", limit=None) # Fetch all messages to ensure full cleanup
    
    passcode_deleted = 0
    metadata_deleted = 0
    chunks_deleted = 0
    
    ids_to_delete = []
    
    for msg in messages:
        if msg.text:
            # Delete passcode hash
            if msg.text.startswith("PASSCODE_HASH\n"):
                ids_to_delete.append(msg.id)
                passcode_deleted += 1
            
            # Delete V2 encrypted metadata
            elif msg.text.startswith("METADATA_V2_ENCRYPTED\n"):
                ids_to_delete.append(msg.id)
                metadata_deleted += 1
                
            # Delete encrypted chunks (orphaned data)
            elif "#ENCRYPTED_CHUNK" in msg.text:
                ids_to_delete.append(msg.id)
                chunks_deleted += 1
                
    if ids_to_delete:
        # Batch delete for efficiency
        # Telethon delete_messages can handle list of IDs
        # Split into chunks of 100 just to be safe
        for i in range(0, len(ids_to_delete), 100):
            batch = ids_to_delete[i:i+100]
            await client.delete_messages("me", batch)
    
    return {
        "passcode_deleted": passcode_deleted,
        "encrypted_files_deleted": metadata_deleted,
        "chunks_deleted": chunks_deleted
    }
