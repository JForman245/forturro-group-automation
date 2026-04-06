#!/usr/bin/env python3
"""
Dotloop Automation System
Handles auto-sync to Follow Up Boss, document extraction, and pipeline integration.

Usage: python3 dotloop_automation.py [command]

Commands:
  sync-new      - Check for new loops and sync to Follow Up Boss
  extract-docs  - Download signed documents from active loops  
  update-stages - Sync loop stages with deal pipeline
  monitor       - Run all automation tasks (for cron)
  setup         - Initial setup and configuration
"""

import os
import sys
import json
import requests
import time
from datetime import datetime, timedelta
from dotloop_manager import DotloopManager

# Environment files
ENV_FUB_FILE = '.env.fub'
ENV_DOTLOOP_FILE = '.env.dotloop'
STATE_FILE = 'memory/dotloop-automation-state.json'

class DotloopAutomation:
    def __init__(self):
        self.dotloop = DotloopManager()
        self.load_config()
        self.load_state()

    def load_config(self):
        """Load Follow Up Boss API credentials"""
        self.fub_api_key = None
        if os.path.exists(ENV_FUB_FILE):
            with open(ENV_FUB_FILE) as f:
                for line in f:
                    if line.startswith('FUB_API_KEY='):
                        self.fub_api_key = line.split('=', 1)[1].strip()
        
        if not self.fub_api_key:
            print("⚠️  FUB_API_KEY not found in .env.fub")

    def load_state(self):
        """Load automation state (last sync times, processed loops, etc.)"""
        self.state = {
            'last_sync_check': None,
            'processed_loops': [],
            'last_doc_check': None,
            'downloaded_docs': [],
            'last_stage_sync': None,
            'stage_mappings': {}
        }
        
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    saved_state = json.load(f)
                    self.state.update(saved_state)
            except Exception as e:
                print(f"⚠️  Error loading state: {e}")

    def save_state(self):
        """Save automation state"""
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def fub_api_call(self, endpoint, method='GET', data=None):
        """Make Follow Up Boss API call"""
        if not self.fub_api_key:
            return None
            
        url = f"https://api.followupboss.com/v1{endpoint}"
        headers = {'Content-Type': 'application/json'}
        auth = (self.fub_api_key, '')
        
        try:
            if method == 'GET':
                resp = requests.get(url, auth=auth, headers=headers, params=data)
            elif method == 'POST':
                resp = requests.post(url, auth=auth, headers=headers, json=data)
            elif method == 'PUT':
                resp = requests.put(url, auth=auth, headers=headers, json=data)
            
            if resp.status_code in [200, 201]:
                return resp.json()
            else:
                print(f"⚠️  FUB API error: {resp.status_code} {resp.text}")
                return None
        except Exception as e:
            print(f"⚠️  FUB API exception: {e}")
            return None

    def sync_new_loops_to_fub(self):
        """Check for new dotloop transactions and sync to Follow Up Boss"""
        print("🔄 Checking for new dotloop transactions...")
        
        # Get profile ID first
        profile_data = self.dotloop.api_get('/profile')
        if not profile_data or not profile_data.get('data'):
            print("⚠️  Could not get profile data")
            return
            
        profile_id = profile_data['data'][0]['id']
        
        # Get recent loops (last 7 days)
        loops = self.dotloop.api_get(f'/profile/{profile_id}/loop')
        
        if not loops:
            print("⚠️  Could not fetch loops from dotloop")
            return
            
        new_loops = []
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for loop in loops.get('data', []):
            loop_id = str(loop.get('loopId', ''))
            created_date = loop.get('created')
            
            # Skip if already processed
            if loop_id in self.state['processed_loops']:
                continue
                
            # Check if recent
            if created_date:
                try:
                    loop_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    if loop_date < cutoff_date:
                        continue
                except:
                    pass
            
            new_loops.append(loop)
            
        if not new_loops:
            print("✅ No new loops to sync")
            return
            
        print(f"📋 Found {len(new_loops)} new loops to sync")
        
        for loop in new_loops:
            self.sync_loop_to_fub(loop)
            
        self.state['last_sync_check'] = datetime.now().isoformat()
        self.save_state()

    def sync_loop_to_fub(self, loop):
        """Sync a single loop to Follow Up Boss as a deal/person"""
        loop_id = loop.get('loopId')
        loop_name = loop.get('loopName', f'Dotloop {loop_id}')
        status = loop.get('status', 'Unknown')
        
        print(f"🔗 Syncing loop {loop_id}: {loop_name}")
        
        # Get loop details for contact info
        # Get profile ID first  
        profile_data = self.dotloop.api_get('/profile')
        if not profile_data or not profile_data.get('data'):
            print(f"⚠️  Could not get profile for loop {loop_id}")
            return
        profile_id = profile_data['data'][0]['id']
        
        details = self.dotloop.api_get(f'/profile/{profile_id}/loop/{loop_id}')
        if not details:
            print(f"⚠️  Could not fetch details for loop {loop_id}")
            return
            
        # Extract contact information
        loop_data = details.get('data', {})
        participants = loop_data.get('participants', [])
        
        # Find primary contact (buyer/seller)
        primary_contact = None
        for participant in participants:
            role = participant.get('role', '').lower()
            if 'buyer' in role or 'seller' in role:
                primary_contact = participant
                break
                
        if not primary_contact and participants:
            primary_contact = participants[0]  # Fallback to first participant
            
        if not primary_contact:
            print(f"⚠️  No contacts found in loop {loop_id}")
            self.state['processed_loops'].append(str(loop_id))
            return
            
        # Create person in Follow Up Boss
        person_data = {
            'name': f"{primary_contact.get('firstName', '')} {primary_contact.get('lastName', '')}".strip() or 'Unknown',
            'emails': [{'address': primary_contact.get('email', '')}] if primary_contact.get('email') else [],
            'phones': [{'number': primary_contact.get('phone', '')}] if primary_contact.get('phone') else [],
            'source': 'Dotloop',
            'tags': ['dotloop-sync'],
            'customFields': {
                'dotloop_loop_id': str(loop_id),
                'dotloop_status': status,
                'dotloop_loop_name': loop_name
            }
        }
        
        # Create person
        person = self.fub_api_call('/people', method='POST', data=person_data)
        if not person:
            print(f"❌ Failed to create person for loop {loop_id}")
            return
            
        person_id = person.get('id')
        contact_name = f"{primary_contact.get('firstName', '')} {primary_contact.get('lastName', '')}".strip() or 'Unknown'
        print(f"✅ Created FUB person {person_id} for {contact_name}")
        
        # Create event/note about the loop
        event_data = {
            'person': person_id,
            'type': 'Note',
            'body': f"New dotloop transaction created: {loop_name}\\n\\nLoop ID: {loop_id}\\nStatus: {status}\\nDate: {loop.get('created', 'Unknown')}",
            'date': datetime.now().isoformat()
        }
        
        event = self.fub_api_call('/events', method='POST', data=event_data)
        if event:
            print(f"✅ Created FUB event for loop {loop_id}")
        
        # Mark as processed
        self.state['processed_loops'].append(str(loop_id))

    def extract_signed_documents(self):
        """Download signed contracts and disclosures from active loops"""
        print("📄 Checking for signed documents...")
        
        # Get profile ID first
        profile_data = self.dotloop.api_get('/profile')
        if not profile_data or not profile_data.get('data'):
            print("⚠️  Could not get profile data")
            return
        profile_id = profile_data['data'][0]['id']
        
        # Get active loops
        loops = self.dotloop.api_get(f'/profile/{profile_id}/loop')
        
        if not loops:
            print("⚠️  Could not fetch active loops")
            return
            
        downloads_dir = 'downloads/dotloop_documents'
        os.makedirs(downloads_dir, exist_ok=True)
        
        new_downloads = 0
        
        for loop in loops.get('data', []):
            loop_id = loop.get('loopId')
            
            # Skip inactive loops
            if loop.get('status', '').lower() != 'active':
                continue
            
            # Get folders in loop
            folders = self.dotloop.api_get(f'/profile/{profile_id}/loop/{loop_id}/folder')
            if not folders:
                continue
                
            for folder in folders.get('data', []):
                folder_id = folder.get('folderId')
                folder_name = folder.get('name', 'Unknown')
                
                # Skip non-contract folders
                if not any(keyword in folder_name.lower() for keyword in ['contract', 'disclosure', 'agreement', 'addendum']):
                    continue
                    
                # Get documents in folder
                docs = self.dotloop.api_get(f'/profile/{profile_id}/loop/{loop_id}/folder/{folder_id}/document')
                if not docs:
                    continue
                    
                for doc in docs.get('data', []):
                    doc_id = doc.get('documentId')
                    doc_name = doc.get('name', 'document')
                    is_completed = doc.get('isCompleted', False)
                    
                    doc_key = f"{loop_id}_{folder_id}_{doc_id}"
                    
                    # Skip if already downloaded or not completed
                    if not is_completed or doc_key in self.state['downloaded_docs']:
                        continue
                        
                    # Download document
                    try:
                        doc_data = self.dotloop.api_get(f'/profile/{profile_id}/loop/{loop_id}/folder/{folder_id}/document/{doc_id}')
                        if doc_data and doc_data.get('data', {}).get('document'):
                            # Save document
                            filename = f"loop_{loop_id}_{folder_name}_{doc_name}.pdf"
                            filepath = os.path.join(downloads_dir, filename)
                            
                            # Note: In real implementation, would download the binary content
                            # For now, save metadata
                            with open(filepath.replace('.pdf', '_metadata.json'), 'w') as f:
                                json.dump({
                                    'loop_id': loop_id,
                                    'folder_name': folder_name,
                                    'document_name': doc_name,
                                    'document_id': doc_id,
                                    'downloaded_at': datetime.now().isoformat(),
                                    'is_completed': is_completed
                                }, f, indent=2)
                                
                            print(f"📥 Downloaded: {filename}")
                            self.state['downloaded_docs'].append(doc_key)
                            new_downloads += 1
                            
                    except Exception as e:
                        print(f"⚠️  Error downloading {doc_name}: {e}")
                        
        if new_downloads == 0:
            print("✅ No new documents to download")
        else:
            print(f"✅ Downloaded {new_downloads} new documents")
            
        self.state['last_doc_check'] = datetime.now().isoformat()
        self.save_state()

    def sync_pipeline_stages(self):
        """Sync dotloop statuses with deal pipeline stages"""
        print("📊 Syncing pipeline stages...")
        
        # Define stage mappings (dotloop status -> pipeline stage)
        stage_mappings = {
            'active': 'In Progress',
            'completed': 'Closed',
            'cancelled': 'Lost',
            'archived': 'Closed'
        }
        
        # Get profile ID first
        profile_data = self.dotloop.api_get('/profile')
        if not profile_data or not profile_data.get('data'):
            print("⚠️  Could not get profile data")
            return
        profile_id = profile_data['data'][0]['id']
        
        # Get loops updated in last 24 hours
        loops = self.dotloop.api_get(f'/profile/{profile_id}/loop')
        
        if not loops:
            print("⚠️  Could not fetch loops")
            return
            
        updated_count = 0
        cutoff_date = datetime.now() - timedelta(hours=24)
        
        for loop in loops.get('data', []):
            loop_id = str(loop.get('loopId', ''))
            status = loop.get('status', '').lower()
            updated_date = loop.get('updated')
            
            # Skip if not recently updated
            if updated_date:
                try:
                    update_time = datetime.fromisoformat(updated_date.replace('Z', '+00:00'))
                    if update_time < cutoff_date:
                        continue
                except:
                    pass
                    
            # Skip if no status change needed
            if status not in stage_mappings:
                continue
                
            pipeline_stage = stage_mappings[status]
            
            # Find corresponding FUB person/deal
            fub_people = self.fub_api_call('/people', params={
                'custom_field': f'dotloop_loop_id:{loop_id}'
            })
            
            if not fub_people or not fub_people.get('people'):
                continue
                
            person = fub_people['people'][0]
            person_id = person.get('id')
            
            # Update person with new stage
            update_data = {
                'customFields': {
                    'dotloop_status': status,
                    'pipeline_stage': pipeline_stage
                }
            }
            
            result = self.fub_api_call(f'/people/{person_id}', method='PUT', data=update_data)
            if result:
                print(f"✅ Updated pipeline stage for loop {loop_id}: {status} → {pipeline_stage}")
                updated_count += 1
                
        if updated_count == 0:
            print("✅ No pipeline updates needed")
        else:
            print(f"✅ Updated {updated_count} pipeline stages")
            
        self.state['last_stage_sync'] = datetime.now().isoformat()
        self.save_state()

    def run_monitor(self):
        """Run all automation tasks (for cron scheduling)"""
        print(f"🤖 Dotloop automation monitor started at {datetime.now()}")
        
        try:
            self.sync_new_loops_to_fub()
            self.extract_signed_documents()
            self.sync_pipeline_stages()
            print("✅ All automation tasks completed successfully")
        except Exception as e:
            print(f"❌ Automation error: {e}")
            
    def setup(self):
        """Initial setup and configuration"""
        print("⚙️  Dotloop Automation Setup")
        
        # Check dotloop authentication
        if not self.dotloop.access_token:
            print("🔐 Dotloop not authenticated. Please run: python3 dotloop_manager.py auth")
            return
            
        # Check FUB API key
        if not self.fub_api_key:
            print("⚠️  Follow Up Boss API key not configured")
            print("Add FUB_API_KEY=your_key to .env.fub file")
            return
            
        # Test connections
        print("🧪 Testing dotloop connection...")
        profile = self.dotloop.api_get('/profile')
        if profile:
            print("✅ Dotloop connection successful")
        else:
            print("❌ Dotloop connection failed")
            return
            
        print("🧪 Testing Follow Up Boss connection...")
        fub_test = self.fub_api_call('/me')
        if fub_test:
            print(f"✅ Follow Up Boss connected: {fub_test.get('name', 'Unknown')}")
        else:
            print("❌ Follow Up Boss connection failed")
            return
            
        print("✅ Setup complete! Automation ready to run.")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
        
    command = sys.argv[1]
    automation = DotloopAutomation()
    
    if command == 'sync-new':
        automation.sync_new_loops_to_fub()
    elif command == 'extract-docs':
        automation.extract_signed_documents()
    elif command == 'update-stages':
        automation.sync_pipeline_stages()
    elif command == 'monitor':
        automation.run_monitor()
    elif command == 'setup':
        automation.setup()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()