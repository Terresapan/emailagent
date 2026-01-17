#!/usr/bin/env python
"""One-time OAuth authorization for Arcade.dev tools (Reddit & Twitter).

Run this script once to authorize your Arcade user_id for Reddit and Twitter.
After authorization, the discovery workflow can run without manual intervention.

Usage:
    uv run python scripts/authorize_arcade.py
"""
import sys
sys.path.insert(0, '.')

from arcadepy import Arcade
from config import settings

def main():
    print("=" * 60)
    print("Arcade.dev OAuth Authorization Setup")
    print("=" * 60)
    print()
    
    api_key = settings.ARCADE_API_KEY
    user_id = getattr(settings, "ARCADE_USER_ID", None)
    
    if not api_key:
        print("❌ ARCADE_API_KEY not set in .env")
        return
    
    if not user_id:
        print("❌ ARCADE_USER_ID not set in .env")
        print("   Add: ARCADE_USER_ID=your-email@example.com")
        return
    
    print(f"User ID: {user_id}")
    print()
    
    client = Arcade(api_key=api_key)
    
    # Tools that require OAuth
    tools = [
        ("Reddit.GetPostsInSubreddit", "Reddit"),
        ("X.SearchRecentTweetsByKeywords", "Twitter/X"),
    ]
    
    for tool_name, display_name in tools:
        print(f"🔐 Checking {display_name}...")
        
        try:
            auth_response = client.tools.authorize(
                tool_name=tool_name,
                user_id=user_id,
            )
            
            if auth_response.status == "completed":
                print(f"   ✅ {display_name} already authorized!")
            else:
                print(f"   🔗 Authorization required for {display_name}")
                print(f"   Click this link to authorize:")
                print()
                print(f"   {auth_response.url}")
                print()
                print("   Waiting for you to complete authorization...")
                client.auth.wait_for_completion(auth_response.id)
                print(f"   ✅ {display_name} authorized!")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("=" * 60)
    print("✅ Authorization complete!")
    print("   You can now run: uv run python main.py --type discovery")
    print("=" * 60)


if __name__ == "__main__":
    main()
