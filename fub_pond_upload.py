#!/usr/bin/env python3
"""
Upload enriched MLS leads to Follow Up Boss → EXPIRED / WITHDRAWN pond.
- Reads enriched CSV (Tracerfy output)
- Creates contacts in FUB with tag Expired or Withdrawn
- Assigns to pond ID 37 (EXPIRED / WITHDRAWN)
- Tracks uploaded leads to avoid duplicates via seen_fub_uploads.json
"""

import os, sys, csv, json, time, requests
from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.fub')

FUB_API_KEY = os.getenv('FUB_API_KEY')
FUB_URL = 'https://api.followupboss.com/v1/people'
POND_ID = 37  # EXPIRED / WITHDRAWN
TRACKER_FILE = '/Users/claw1/.openclaw/workspace/seen_fub_uploads.json'


def load_tracker():
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE) as f:
            return json.load(f)
    return {'uploaded_mls': []}


def save_tracker(tracker):
    with open(TRACKER_FILE, 'w') as f:
        json.dump(tracker, f)


def upload_to_fub(csv_path):
    if not FUB_API_KEY:
        print("❌ FUB_API_KEY not found")
        return 0

    tracker = load_tracker()
    already_uploaded = set(tracker.get('uploaded_mls', []))

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"📋 {len(rows)} leads in {os.path.basename(csv_path)}")

    uploaded = 0
    skipped = 0
    errors = 0

    for row in rows:
        mls = row.get('mls_number', '').strip()
        if not mls:
            continue
        if mls in already_uploaded:
            skipped += 1
            continue

        # Skip if no phone number — must have at least one phone to upload
        first_name = row.get('first_name', '').strip()
        last_name = row.get('last_name', '').strip()
        primary_phone = row.get('primary_phone', '').strip()
        any_phone = primary_phone or any(row.get(k, '').strip() for k in ['Mobile-1', 'Mobile-2', 'Landline-1'])
        if not any_phone:
            skipped += 1
            already_uploaded.add(mls)
            continue

        # Build contact data
        category = row.get('category', 'expired').strip().lower()

        # Tag based on category
        if 'withdrawn' in category:
            tag = 'Withdrawn'
        else:
            tag = 'Expired'

        # Build address
        address = row.get('address', '').strip()
        city = row.get('city', '').strip()
        zipcode = row.get('zip', '').strip()

        # Phones
        phones = []
        primary = row.get('primary_phone', '').strip()
        if primary:
            phones.append({'value': primary, 'type': 'mobile'})
        for key in ['Mobile-1', 'Mobile-2', 'Mobile-3', 'Landline-1', 'Landline-2']:
            ph = row.get(key, '').strip()
            if ph and ph != primary:
                ptype = 'mobile' if 'Mobile' in key else 'home'
                phones.append({'value': ph, 'type': ptype})
                if len(phones) >= 4:
                    break

        # Emails
        emails = []
        for key in ['Email-1', 'Email-2', 'Email-3']:
            em = row.get(key, '').strip()
            if em:
                emails.append({'value': em})
                if len(emails) >= 3:
                    break

        # Build FUB payload
        payload = {
            'source': 'MLS Scraper',
            'tags': [tag, 'MLS Scraper'],
            'assignedPondId': POND_ID,
        }

        if first_name:
            payload['firstName'] = first_name
        if last_name:
            payload['lastName'] = last_name
        if not first_name and not last_name:
            # Use "Owner" as placeholder if no name from Tracerfy
            payload['firstName'] = 'Owner'
            payload['lastName'] = address[:30] if address else mls

        if phones:
            payload['phones'] = phones
        if emails:
            payload['emails'] = emails

        if address:
            payload['addresses'] = [{
                'street': address,
                'city': city,
                'state': 'SC',
                'code': zipcode,
                'type': 'home'
            }]

        # Add MLS info as a note via custom fields or just tags
        payload['tags'].append(f'MLS#{mls}')

        # Create in FUB
        try:
            resp = requests.post(
                FUB_URL,
                auth=(FUB_API_KEY, ''),
                json=payload,
                timeout=10
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                uploaded += 1
                already_uploaded.add(mls)
                if uploaded % 25 == 0:
                    print(f"  Uploaded {uploaded}...")
                    # Save progress periodically
                    tracker['uploaded_mls'] = list(already_uploaded)
                    save_tracker(tracker)
                # Rate limit: FUB allows ~5/sec for registered systems
                time.sleep(0.25)
            elif resp.status_code == 429:
                print(f"  Rate limited — waiting 5s...")
                time.sleep(5)
                # Retry
                resp = requests.post(FUB_URL, auth=(FUB_API_KEY, ''), json=payload, timeout=10)
                if resp.status_code in (200, 201):
                    uploaded += 1
                    already_uploaded.add(mls)
                else:
                    errors += 1
                    print(f"  ❌ Retry failed for MLS#{mls}: {resp.status_code}")
            else:
                errors += 1
                if errors <= 3:
                    print(f"  ❌ MLS#{mls}: {resp.status_code} {resp.text[:100]}")
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  ❌ MLS#{mls}: {e}")

    # Save final state
    tracker['uploaded_mls'] = list(already_uploaded)
    save_tracker(tracker)

    print(f"✅ Done: {uploaded} uploaded, {skipped} already in FUB, {errors} errors")
    return uploaded


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 fub_pond_upload.py <enriched_leads.csv> [more.csv ...]")
        sys.exit(1)

    total = 0
    for csv_path in sys.argv[1:]:
        if os.path.exists(csv_path):
            total += upload_to_fub(csv_path)
        else:
            print(f"❌ File not found: {csv_path}")

    print(f"\n📊 Total uploaded: {total}")
