#!/usr/bin/env python3
"""
Generate a user session string for Channel Guard.

This script creates a Telegram *user* session which is required to read
channel admin logs (bots cannot do that).

Usage:
1. Run: python generate_session_string.py
2. Enter your phone number (E.164, e.g. +15551234567)
3. Enter the login code from Telegram
4. If 2FA is enabled, enter your password
5. Copy the session string into config as CHANNEL_GUARD_SESSION_STRING
"""

import asyncio
from pyrogram import Client
from CONFIG.config import Config

async def generate_session_string():
    """Generate a session string for a user account."""
    
    print("=" * 60)
    print("Session String Generator for Channel Guard")
    print("=" * 60)
    print()
    print("This script will create a user session for reading admin logs.")
    print("You will need:")
    print("  - Phone number (E.164, e.g. +15551234567)")
    print("  - Login code from Telegram")
    print("  - 2FA password (if enabled)")
    print()
    
    # Check API_ID/API_HASH presence
    if not hasattr(Config, 'API_ID') or not hasattr(Config, 'API_HASH'):
        print("❌ Error: API_ID or API_HASH not found in config!")
        print("   Make sure they are set in CONFIG/config.py")
        return
    
    api_id = Config.API_ID
    api_hash = Config.API_HASH
    
    print(f"✅ Using API_ID: {api_id}")
    print(f"✅ Using API_HASH: {api_hash[:10]}...")
    print()
    
    # Create a client with a temporary session name
    session_name = "channel_guard_user_session"
    
    print("Creating client...")
    client = Client(
        name=session_name,
        api_id=api_id,
        api_hash=api_hash,
        phone_number=None,  # Will be requested interactively
    )
    
    try:
        print("Starting client...")
        await client.start()
        
        # Export session string
        session_string = await client.export_session_string()
        
        print()
        print("=" * 60)
        print("✅ Session String generated successfully!")
        print("=" * 60)
        print()
        print("Copy the following line into CONFIG/config.py:")
        print()
        print(f'    CHANNEL_GUARD_SESSION_STRING = "{session_string}"')
        print()
        print("=" * 60)
        print()
        print("⚠️  IMPORTANT:")
        print("   - Keep the session string safe!")
        print("   - Do not publish it publicly!")
        print("   - Anyone with it can access your account!")
        print()
        
        # Also save to a file for convenience
        try:
            with open("channel_guard_session_string.txt", "w", encoding="utf-8") as f:
                f.write(f"CHANNEL_GUARD_SESSION_STRING = \"{session_string}\"\n")
            print("✅ Session string also saved to: channel_guard_session_string.txt")
            print("   (delete this file after copying into config!)")
        except Exception as e:
            print(f"⚠️  Failed to save to file: {e}")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Error generating session string:")
        print("=" * 60)
        print(f"   {e}")
        print()
        print("Possible causes:")
        print("  - Incorrect phone number or login code")
        print("  - Connectivity issues to Telegram")
        print("  - Incorrect API_ID or API_HASH")
        print()
    finally:
        await client.stop()
        print("Client stopped.")

if __name__ == "__main__":
    print()
    try:
        asyncio.run(generate_session_string())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
