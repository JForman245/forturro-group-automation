#!/usr/bin/env python3
"""
Voice Call Automation for Real Estate Lead Outreach
Automated calling system for MLS leads with phone numbers
"""

import os
import csv
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

class VoiceCallAutomation:
    def __init__(self):
        # Load Twilio credentials
        load_dotenv('/Users/claw1/.openclaw/workspace/.env.twilio')
        
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Missing Twilio credentials")
    
    def create_twiml_script(self, lead_type, address, city):
        """Generate TwiML script for different lead types"""
        
        scripts = {
            'expired': f"""
                <Response>
                    <Pause length="1"/>
                    <Say voice="Polly.Matthew">
                        Hello! This is Jeff from The Forturro Group. I'm calling about your property at {address} in {city}. 
                        I noticed your listing recently expired and I'd love to discuss how we can help you sell your home quickly and for top dollar. 
                        I have buyers actively looking in your area. Please give me a call back at 8-4-3, 9-0-2, 4-3-2-5. 
                        That's Jeff at The Forturro Group, 8-4-3, 9-0-2, 4-3-2-5. Thank you and have a great day.
                    </Say>
                </Response>
            """,
            'withdrawn': f"""
                <Response>
                    <Pause length="1"/>
                    <Say voice="Polly.Matthew">
                        Hi! This is Jeff Forman with The Forturro Group. I'm calling about your property at {address} in {city}. 
                        I saw you recently took it off the market and I wanted to reach out. 
                        I specialize in helping homeowners sell quickly, even in challenging situations. 
                        I'd love to discuss your options with no obligation. Please call me back at 8-4-3, 9-0-2, 4-3-2-5. 
                        Again, that's Jeff at The Forturro Group, 8-4-3, 9-0-2, 4-3-2-5. Thanks!
                    </Say>
                </Response>
            """,
            'price_reduction': f"""
                <Response>
                    <Pause length="1"/>
                    <Say voice="Polly.Matthew">
                        Hello! Jeff Forman here from The Forturro Group. I'm calling about your listing at {address} in {city}. 
                        I noticed you recently adjusted the price and I wanted to reach out. 
                        I have several qualified buyers looking in your area and price range. 
                        Let's connect to see if we can get your home sold quickly. Please call me at 8-4-3, 9-0-2, 4-3-2-5. 
                        That's Jeff with The Forturro Group, 8-4-3, 9-0-2, 4-3-2-5. Looking forward to hearing from you!
                    </Say>
                </Response>
            """
        }
        
        return scripts.get(lead_type, scripts['expired']).strip()
    
    def upload_twiml_to_server(self, twiml_content):
        """Upload TwiML to a temporary server (simplified version)"""
        # For now, we'll use Twilio's demo server and enhance later
        # In production, you'd upload to your own server or use Twilio Functions
        return "http://demo.twilio.com/docs/voice.xml"
    
    def make_lead_call(self, phone_number, lead_data):
        """Make a call to a specific lead"""
        
        address = lead_data.get('address', 'your property')
        city = lead_data.get('city', 'your area')
        lead_type = lead_data.get('type', 'expired')
        
        # Create custom TwiML for this lead
        twiml = self.create_twiml_script(lead_type, address, city)
        
        # For now, use demo URL (we'll enhance this)
        twiml_url = "http://demo.twilio.com/docs/voice.xml"
        
        try:
            url = f'https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls.json'
            
            data = {
                'From': self.from_number,
                'To': phone_number,
                'Url': twiml_url,
                'StatusCallback': '',  # Optional: webhook for call status
                'StatusCallbackEvent': ['initiated', 'answered', 'completed']
            }
            
            response = requests.post(url, auth=(self.account_sid, self.auth_token), data=data, timeout=15)
            
            if response.status_code == 201:
                call_data = response.json()
                print(f"✅ Call initiated to {phone_number}")
                print(f"   Address: {address}, {city}")
                print(f"   Call SID: {call_data['sid']}")
                print(f"   Status: {call_data['status']}")
                return call_data['sid']
            else:
                print(f"❌ Call failed to {phone_number}: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error calling {phone_number}: {e}")
            return None
    
    def bulk_call_leads(self, csv_file, max_calls=10, delay_seconds=30):
        """Call multiple leads from CSV file with rate limiting"""
        
        print(f"📞 STARTING BULK LEAD CALLING")
        print("=" * 50)
        print(f"Source file: {csv_file}")
        print(f"Max calls: {max_calls}")
        print(f"Delay between calls: {delay_seconds} seconds")
        print()
        
        if not os.path.exists(csv_file):
            print(f"❌ CSV file not found: {csv_file}")
            return
        
        # Load leads with phone numbers
        leads_to_call = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('owner_phone') and row.get('contact_found') == 'True':
                    leads_to_call.append(row)
        
        print(f"Found {len(leads_to_call)} leads with phone numbers")
        
        if not leads_to_call:
            print("❌ No leads with phone numbers found")
            return
        
        # Limit number of calls
        leads_to_call = leads_to_call[:max_calls]
        
        call_results = []
        
        for i, lead in enumerate(leads_to_call, 1):
            phone = lead.get('owner_phone')
            address = lead.get('address', 'Unknown')
            
            print(f"\n[{i}/{len(leads_to_call)}] Calling {address}")
            print(f"   Phone: {phone}")
            
            call_sid = self.make_lead_call(phone, lead)
            
            call_results.append({
                'phone': phone,
                'address': address,
                'call_sid': call_sid,
                'success': call_sid is not None,
                'timestamp': datetime.now().isoformat()
            })
            
            # Rate limiting
            if i < len(leads_to_call):
                print(f"   Waiting {delay_seconds} seconds before next call...")
                time.sleep(delay_seconds)
        
        # Summary
        successful_calls = len([r for r in call_results if r['success']])
        print(f"\n📊 CALLING SUMMARY:")
        print(f"✅ Successful calls: {successful_calls}/{len(call_results)}")
        print(f"📱 Total leads contacted: {len(call_results)}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        results_file = f"/Users/claw1/.openclaw/workspace/call_results_{timestamp}.csv"
        
        with open(results_file, 'w', newline='') as f:
            fieldnames = ['phone', 'address', 'call_sid', 'success', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(call_results)
        
        print(f"📄 Results saved: {results_file}")
        
        return call_results
    
    def test_voice_system(self, test_phone="+18439024325"):
        """Test the voice calling system"""
        print("📞 TESTING VOICE CALL SYSTEM")
        print("=" * 40)
        
        test_lead = {
            'address': '123 Test Street',
            'city': 'Myrtle Beach',
            'type': 'expired',
            'owner_phone': test_phone
        }
        
        print(f"Making test call to {test_phone}...")
        call_sid = self.make_lead_call(test_phone, test_lead)
        
        if call_sid:
            print("✅ Test call successful!")
            print("📞 Your phone should be ringing with a demo message")
            return True
        else:
            print("❌ Test call failed")
            return False

def main():
    try:
        voice_system = VoiceCallAutomation()
        
        # Test the system
        success = voice_system.test_voice_system()
        
        if success:
            print("\n🚀 VOICE AUTOMATION IS READY!")
            print("\nNext steps:")
            print("1. Run the MLS scraper to get fresh leads")
            print("2. Use bulk_call_leads() to call all leads with phone numbers")
            print("3. Monitor results and follow up on callbacks")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()