import asyncio
import os
import sys
from telethon import TelegramClient
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

load_dotenv('backend/.env')

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_NAME = "backend/telegram_drive_session"

async def check_session():
    """Check existing session and try to reactivate it"""
    print("=== Checking Existing Session ===\n")
    
    # Check if session file exists
    session_file = f"{SESSION_NAME}.session"
    if not os.path.exists(session_file):
        print(f"✗ No session file found: {session_file}")
        return False
    
    print(f"✓ Session file exists: {session_file}")
    print(f"  Size: {os.path.getsize(session_file)} bytes\n")
    
    # Create client with existing session
    client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)
    
    try:
        print("Connecting to Telegram...")
        await client.connect()
        print("✓ Connected to Telegram\n")
        
        # Check if authorized
        is_authorized = await client.is_user_authorized()
        print(f"Authorization status: {is_authorized}")
        
        if is_authorized:
            print("✓ Session is AUTHENTICATED!\n")
            
            # Get user info
            me = await client.get_me()
            print("=== User Info ===")
            print(f"ID: {me.id}")
            print(f"First Name: {me.first_name}")
            print(f"Last Name: {me.last_name}")
            print(f"Username: @{me.username}" if me.username else "Username: None")
            print(f"Phone: {me.phone}")
            print(f"Bot: {me.bot}")
            print(f"Verified: {me.verified}")
            
            print("\n✅ You can use this session! Just access the app and it should work.")
            print("   The backend will use this session automatically.")
            
            return True
        else:
            print("✗ Session exists but is NOT authenticated")
            print("\nℹ  This means:")
            print("  - The session file has data but login was never completed")
            print("  - OR the session was logged out")
            print("  - OR the session expired")
            
            print("\n💡 Solution:")
            print("  1. Delete the session file:")
            print("     rm backend/telegram_drive_session.session*")
            print("  2. Wait 1-2 hours for rate limit to reset")
            print("  3. Try logging in again through the frontend")
            
            return False
            
    except Exception as e:
        print(f"\n✗ Error checking session: {e}")
        print(f"   Type: {type(e).__name__}")
        return False
    finally:
        await client.disconnect()
        print("\nDisconnected from Telegram")

async def main():
    try:
        result = await check_session()
        
        if result:
            print("\n" + "="*60)
            print("🎉 GOOD NEWS: Your session is active and authenticated!")
            print("   Just refresh your browser and you should be logged in.")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("⚠️  Session exists but is not usable")
            print("   You need to delete it and re-login after rate limit resets")
            print("="*60)
            
    except Exception as e:
        print(f"\nFatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
