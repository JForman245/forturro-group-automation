#!/usr/bin/env python3
"""
SMS Integration with Twilio for Birdy
Direct messaging between Jeff and Birdy via SMS/iMessage
"""

import os
import requests
from datetime import datetime

class BirdySMS:
    def __init__(self):
        # Load credentials from environment
        from dotenv import load_dotenv
        load_dotenv('/Users/claw1/.openclaw/workspace/.env.twilio')
        
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.to_number = '+18439024325'  # Jeff's number
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Missing Twilio credentials in .env.twilio")
            
    def send_sms(self, message):
        """Send SMS to Jeff"""
        url = f'https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json'
        
        data = {
            'From': self.from_number,
            'To': self.to_number,
            'Body': message
        }
        
        try:
            response = requests.post(url, auth=(self.account_sid, self.auth_token), data=data, timeout=10)
            
            if response.status_code == 201:
                msg_data = response.json()
                print(f"✅ SMS sent successfully!")
                print(f"   From: {self.from_number}")
                print(f"   To: {self.to_number}")
                print(f"   SID: {msg_data['sid']}")
                return True
            else:
                print(f"❌ SMS failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ SMS error: {e}")
            return False
    
    def test_integration(self):
        """Test SMS integration"""
        print("📱 TESTING BIRDY SMS INTEGRATION")
        print("=" * 40)
        print(f"From number: {self.from_number}")
        print(f"To number: {self.to_number}")
        print()
        
        test_message = "🐦 Hey Jeff! This is Birdy on my new dedicated number. Save me as a contact - no more WhatsApp self-messaging! SMS and voice ready! 🚀"
        
        success = self.send_sms(test_message)
        
        if success:
            print()
            print("✅ BIRDY SMS IS LIVE!")
            print("📱 Check your iPhone Messages app")
            print("💾 Save (843) 286-4613 as 'Birdy 🐦'")
            print("📞 Voice calling integration ready!")
        else:
            print()
            print("❌ SMS setup needs debugging")
            
        return success

def main():
    try:
        sms = BirdySMS()
        sms.test_integration()
    except Exception as e:
        print(f"❌ Setup error: {e}")

if __name__ == "__main__":
    main()