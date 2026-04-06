#!/usr/bin/env python3
import subprocess, json, os

# Load API key
with open('/Users/claw1/.openclaw/workspace/.env.fub') as f:
    for line in f:
        if line.startswith('FUB_API_KEY='):
            api_key = line.strip().split('=', 1)[1]

cutoff = '2025-04-01'
candidates = []
next_token = None

while True:
    url = "https://api.followupboss.com/v1/actionPlans?limit=100"
    if next_token:
        url += f"&next={next_token}"
    
    result = subprocess.run(
        ['curl', '-s', '-u', f'{api_key}:', url],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    plans = data.get('actionPlans', [])
    
    for p in plans:
        updated = p.get('updated', '')[:10]
        created = p.get('created', '')[:10]
        running = p.get('contactsRunningCount', 0)
        used = p.get('isUsed', False)
        status = p.get('status', '')
        name = p.get('name', '')
        pid = p.get('id', '')
        steps = p.get('stepCount', 0)
        
        if status == 'Active' and running == 0 and updated < cutoff:
            candidates.append({
                'id': pid, 'name': name, 'updated': updated, 
                'created': created, 'used': used, 'steps': steps
            })
    
    next_token = data.get('_metadata', {}).get('next', '')
    if not next_token:
        break

print(f"Found {len(candidates)} plans: Active, 0 contacts running, not updated since April 2025\n")
for c in candidates:
    print(f"  ID {c['id']:>3} | Updated: {c['updated']} | Steps: {c['steps']:>3} | Used: {str(c['used']):>5} | {c['name']}")

print(f"\nTotal to delete: {len(candidates)}")

# Save IDs for deletion
with open('/Users/claw1/.openclaw/workspace/fub_delete_ids.json', 'w') as f:
    json.dump(candidates, f, indent=2)
