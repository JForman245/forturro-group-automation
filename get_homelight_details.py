#!/usr/bin/env python3
"""
Extract full HomeLight referral details from Gmail
"""

import subprocess
import json
import sys

def get_email_content(message_id):
    """Get full email content using gog"""
    try:
        # Use gog to get the email body
        cmd = f'gog gmail search "rfc822msgid:{message_id}" --max 1 --json'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('threads', [])
        else:
            print(f"Error getting email {message_id}: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception getting email {message_id}: {e}")
        return None

def main():
    # HomeLight email IDs from today
    email_ids = [
        "19d59a2b540c1d7b",  # $250,000 seller in Conway (1:55 PM)
        "19d59a71bfb0bd5b",  # Martha Allen contact info (2:00 PM) 
        "19d59da0ecef99a8",  # $250,000 seller in Pawleys Island (2:55 PM)
        "19d59e412c1ef368",  # Juliette Kelso contact info (3:06 PM)
    ]
    
    print("🏠 HOMELIGHT REFERRAL DETAILS")
    print("=" * 50)
    
    for i, email_id in enumerate(email_ids, 1):
        print(f"\n📧 EMAIL {i} (ID: {email_id})")
        print("-" * 30)
        
        # Try to get content
        content = get_email_content(email_id)
        if content:
            print(f"✅ Retrieved content for email {email_id}")
            # You'd parse the content here
        else:
            print(f"❌ Could not retrieve email {email_id}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()