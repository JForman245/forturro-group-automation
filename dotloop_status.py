#!/usr/bin/env python3
"""
Quick status check for Dotloop automation
Shows current loops and automation state
"""

import json
from dotloop_manager import DotloopManager

def main():
    manager = DotloopManager()
    
    # Get profile
    profile = manager.api_get('/profile')
    if not profile or not profile.get('data'):
        print("❌ Could not get profile")
        return
        
    profile_id = profile['data'][0]['id']
    print(f"📋 Profile: {profile['data'][0]['name']} (ID: {profile_id})")
    
    # Get loops
    loops = manager.api_get(f'/profile/{profile_id}/loop')
    if not loops or not loops.get('data'):
        print("📋 No loops found")
        return
        
    print(f"\n📋 Found {len(loops['data'])} loops:")
    for loop in loops['data'][:10]:  # Show first 10
        loop_id = loop.get('loopId')
        loop_name = loop.get('loopName', 'Unnamed')
        status = loop.get('status', 'Unknown')
        created = loop.get('created', 'Unknown')
        print(f"   {loop_id:>8} | {loop_name[:40]:<40} | {status:<10} | {created[:10]}")
        
    if len(loops['data']) > 10:
        print(f"   ... and {len(loops['data']) - 10} more")
        
    # Show automation state
    try:
        with open('memory/dotloop-automation-state.json', 'r') as f:
            state = json.load(f)
            print(f"\n🤖 Automation State:")
            print(f"   Last sync check: {state.get('last_sync_check', 'Never')}")
            print(f"   Processed loops: {len(state.get('processed_loops', []))}")
            print(f"   Downloaded docs: {len(state.get('downloaded_docs', []))}")
            print(f"   Last doc check: {state.get('last_doc_check', 'Never')}")
            print(f"   Last stage sync: {state.get('last_stage_sync', 'Never')}")
    except FileNotFoundError:
        print("\n🤖 Automation State: Not initialized")

if __name__ == '__main__':
    main()