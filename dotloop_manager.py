#!/usr/bin/env python3
"""
Dotloop Management Tool
Read-only interface to view and manage dotloop transactions.
Usage: python3 dotloop_manager.py [command] [options]

Commands:
  auth          - Authenticate with dotloop (OAuth flow)
  profile       - Show account profile
  loops         - List all loops
  loop [id]     - Show loop details
  contacts      - List contacts
  templates     - List loop templates
  folders       - List folders in a loop
  documents     - List documents in a loop/folder
  help          - Show this help

Examples:
  python3 dotloop_manager.py auth
  python3 dotloop_manager.py loops --status active
  python3 dotloop_manager.py loop 123456 --details
  python3 dotloop_manager.py documents 123456 --folder contracts
"""

import os
import sys
import json
import requests
import webbrowser
import urllib.parse
import time
from datetime import datetime
import argparse

# Load environment
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.dotloop')
CLIENT_ID = None
CLIENT_SECRET = None

if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith('DOTLOOP_CLIENT_ID='):
                CLIENT_ID = line.split('=', 1)[1]
            elif line.startswith('DOTLOOP_CLIENT_SECRET='):
                CLIENT_SECRET = line.split('=', 1)[1]

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: Could not load DOTLOOP_CLIENT_ID and DOTLOOP_CLIENT_SECRET from .env.dotloop")
    sys.exit(1)

# OAuth config
REDIRECT_URI = "http://localhost:8080/callback"
AUTH_URL = "https://auth.dotloop.com/oauth/authorize"
TOKEN_URL = "https://auth.dotloop.com/oauth/token"
API_BASE = "https://api-gateway.dotloop.com/public/v2"

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.dotloop_tokens.json')

class DotloopManager:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.load_tokens()

    def load_tokens(self):
        """Load stored access/refresh tokens"""
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get('access_token')
                    self.refresh_token = tokens.get('refresh_token')
                    expires_at = tokens.get('expires_at')
                    if expires_at and datetime.now().timestamp() > expires_at:
                        print("⚠️  Access token expired, need to refresh")
                        if self.refresh_token:
                            self.refresh_access_token()
                        else:
                            print("⚠️  No refresh token, need to re-authenticate")
                            self.access_token = None
            except Exception as e:
                print(f"⚠️  Error loading tokens: {e}")

    def save_tokens(self, access_token, refresh_token, expires_in):
        """Save access/refresh tokens"""
        tokens = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': datetime.now().timestamp() + expires_in - 300  # 5 min buffer
        }
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
        os.chmod(TOKEN_FILE, 0o600)  # Secure permissions
        self.access_token = access_token
        self.refresh_token = refresh_token

    def authenticate(self):
        """Start OAuth flow"""
        params = {
            'response_type': 'code',
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'scope': 'account'
        }
        auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
        
        print(f"🔐 Opening browser for dotloop authentication...")
        print(f"Auth URL: {auth_url}")
        webbrowser.open(auth_url)
        
        print(f"\n📋 After authorizing, copy the 'code' parameter from the redirect URL")
        print(f"It will look like: http://localhost:8080/callback?code=ABC123...")
        auth_code = input("Enter the authorization code: ").strip()
        
        if not auth_code:
            print("❌ No authorization code provided")
            return False
            
        return self.exchange_code_for_token(auth_code)

    def exchange_code_for_token(self, auth_code):
        """Exchange auth code for access token"""
        data = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'code': auth_code
        }
        
        try:
            resp = requests.post(TOKEN_URL, data=data)
            if resp.status_code == 200:
                tokens = resp.json()
                self.save_tokens(
                    tokens['access_token'],
                    tokens.get('refresh_token'),
                    tokens.get('expires_in', 3600)
                )
                print("✅ Authentication successful!")
                return True
            else:
                print(f"❌ Token exchange failed: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            print(f"❌ Token exchange error: {e}")
            return False

    def refresh_access_token(self):
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            print("❌ No refresh token available")
            return False
            
        data = {
            'grant_type': 'refresh_token',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': self.refresh_token
        }
        
        try:
            resp = requests.post(TOKEN_URL, data=data)
            if resp.status_code == 200:
                tokens = resp.json()
                self.save_tokens(
                    tokens['access_token'],
                    tokens.get('refresh_token', self.refresh_token),
                    tokens.get('expires_in', 3600)
                )
                print("✅ Token refreshed")
                return True
            else:
                print(f"❌ Token refresh failed: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
            return False

    def api_get(self, endpoint, params=None):
        """Make authenticated GET request to dotloop API"""
        if not self.access_token:
            print("❌ Not authenticated. Run: python3 dotloop_manager.py auth")
            return None
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            resp = requests.get(f"{API_BASE}{endpoint}", headers=headers, params=params)
            if resp.status_code == 401:
                print("🔄 Token expired, refreshing...")
                if self.refresh_access_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    resp = requests.get(f"{API_BASE}{endpoint}", headers=headers, params=params)
                else:
                    print("❌ Token refresh failed. Re-authenticate with: python3 dotloop_manager.py auth")
                    return None
                    
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"❌ API error: {resp.status_code} {resp.text}")
                return None
        except Exception as e:
            print(f"❌ API request error: {e}")
            return None

    def get_profile(self):
        """Get account profile"""
        return self.api_get('/profile')

    def get_loops(self, status=None):
        """Get all loops, optionally filtered by status"""
        params = {}
        if status:
            params['filter[loop_status]'] = status
        return self.api_get('/loop', params)

    def get_loop(self, loop_id):
        """Get specific loop details"""
        return self.api_get(f'/loop/{loop_id}')

    def get_contacts(self):
        """Get all contacts"""
        return self.api_get('/contact')

    def get_templates(self):
        """Get loop templates"""
        return self.api_get('/loop-template')

    def get_folders(self, loop_id):
        """Get folders in a loop"""
        return self.api_get(f'/loop/{loop_id}/folder')

    def get_documents(self, loop_id, folder_id=None):
        """Get documents in a loop/folder"""
        if folder_id:
            return self.api_get(f'/loop/{loop_id}/folder/{folder_id}/document')
        else:
            return self.api_get(f'/loop/{loop_id}/document')

def print_profile(profile):
    """Pretty print profile"""
    if not profile:
        return
    print("\n👤 PROFILE")
    print(f"   Name: {profile.get('firstName', '')} {profile.get('lastName', '')}")
    print(f"   Email: {profile.get('email', '')}")
    if profile.get('phone'):
        print(f"   Phone: {profile['phone']}")

def print_loops(loops):
    """Pretty print loops list"""
    if not loops or not loops.get('data'):
        print("📋 No loops found")
        return
        
    print(f"\n📋 LOOPS ({len(loops['data'])} total)")
    for loop in loops['data']:
        created = datetime.fromisoformat(loop['created'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
        print(f"   {loop['loopId']:>8} | {loop['loopName'][:50]:<50} | {loop['status']:<12} | {created}")

def print_loop_details(loop):
    """Pretty print loop details"""
    if not loop:
        return
    print(f"\n🔍 LOOP {loop['loopId']}")
    print(f"   Name: {loop['loopName']}")
    print(f"   Status: {loop['status']}")
    print(f"   Created: {loop['created']}")
    if loop.get('address'):
        print(f"   Address: {loop['address']}")
    if loop.get('participants'):
        print(f"   Participants: {len(loop['participants'])}")

def print_contacts(contacts):
    """Pretty print contacts"""
    if not contacts or not contacts.get('data'):
        print("👥 No contacts found")
        return
        
    print(f"\n👥 CONTACTS ({len(contacts['data'])} total)")
    for contact in contacts['data']:
        print(f"   {contact['contactId']:>8} | {contact['firstName']} {contact['lastName']} | {contact.get('email', '')}")

def print_templates(templates):
    """Pretty print templates"""
    if not templates or not templates.get('data'):
        print("📄 No templates found")
        return
        
    print(f"\n📄 TEMPLATES ({len(templates['data'])} total)")
    for template in templates['data']:
        print(f"   {template['loopTemplateId']:>8} | {template['name']}")

def print_folders(folders):
    """Pretty print folders"""
    if not folders or not folders.get('data'):
        print("📁 No folders found")
        return
        
    print(f"\n📁 FOLDERS ({len(folders['data'])} total)")
    for folder in folders['data']:
        print(f"   {folder['folderId']:>8} | {folder['name']}")

def print_documents(documents, loop_id, folder_name=None):
    """Pretty print documents"""
    if not documents or not documents.get('data'):
        folder_str = f" in {folder_name}" if folder_name else ""
        print(f"📄 No documents found in loop {loop_id}{folder_str}")
        return
        
    folder_str = f" in {folder_name}" if folder_name else ""
    print(f"\n📄 DOCUMENTS in loop {loop_id}{folder_str} ({len(documents['data'])} total)")
    for doc in documents['data']:
        created = datetime.fromisoformat(doc['created'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
        print(f"   {doc['documentId']:>8} | {doc['name']:<40} | {created}")

def main():
    parser = argparse.ArgumentParser(description='Dotloop Management Tool (Read-Only)')
    parser.add_argument('command', nargs='?', default='help', 
                       choices=['auth', 'profile', 'loops', 'loop', 'contacts', 'templates', 'folders', 'documents', 'help'])
    parser.add_argument('id', nargs='?', help='Loop ID, Contact ID, etc.')
    parser.add_argument('--status', help='Filter loops by status')
    parser.add_argument('--folder', help='Folder name for documents command')
    parser.add_argument('--details', action='store_true', help='Show detailed information')
    
    args = parser.parse_args()
    
    if args.command == 'help':
        print(__doc__)
        return
        
    manager = DotloopManager()
    
    if args.command == 'auth':
        manager.authenticate()
        
    elif args.command == 'profile':
        profile = manager.get_profile()
        print_profile(profile)
        
    elif args.command == 'loops':
        loops = manager.get_loops(args.status)
        print_loops(loops)
        
    elif args.command == 'loop':
        if not args.id:
            print("❌ Loop ID required. Usage: python3 dotloop_manager.py loop 123456")
            return
        loop = manager.get_loop(args.id)
        print_loop_details(loop)
        
    elif args.command == 'contacts':
        contacts = manager.get_contacts()
        print_contacts(contacts)
        
    elif args.command == 'templates':
        templates = manager.get_templates()
        print_templates(templates)
        
    elif args.command == 'folders':
        if not args.id:
            print("❌ Loop ID required. Usage: python3 dotloop_manager.py folders 123456")
            return
        folders = manager.get_folders(args.id)
        print_folders(folders)
        
    elif args.command == 'documents':
        if not args.id:
            print("❌ Loop ID required. Usage: python3 dotloop_manager.py documents 123456")
            return
        documents = manager.get_documents(args.id)
        print_documents(documents, args.id)

if __name__ == '__main__':
    main()