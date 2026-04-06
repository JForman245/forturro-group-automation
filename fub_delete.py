#!/usr/bin/env python3
import subprocess, json, time

# Load API key
with open('/Users/claw1/.openclaw/workspace/.env.fub') as f:
    for line in f:
        if line.startswith('FUB_API_KEY='):
            api_key = line.strip().split('=', 1)[1]

# Load candidates
with open('/Users/claw1/.openclaw/workspace/fub_delete_ids.json') as f:
    candidates = json.load(f)

# Keep these (marked as Used)
keep_ids = {25, 23, 20, 29, 8}

to_delete = [c for c in candidates if c['id'] not in keep_ids]

print(f"Deleting {len(to_delete)} action plans (keeping {len(keep_ids)} marked as Used)...\n")

success = 0
failed = 0

for plan in to_delete:
    pid = plan['id']
    name = plan['name']
    
    result = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
         '-X', 'DELETE', '-u', f'{api_key}:', 
         f'https://api.followupboss.com/v1/actionPlans/{pid}'],
        capture_output=True, text=True
    )
    
    code = result.stdout.strip()
    if code in ('200', '204', ''):
        print(f"  ✅ Deleted ID {pid:>3}: {name}")
        success += 1
    else:
        print(f"  ❌ Failed ID {pid:>3} (HTTP {code}): {name}")
        failed += 1
    
    time.sleep(0.5)

print(f"\nDone. ✅ {success} deleted, ❌ {failed} failed")
