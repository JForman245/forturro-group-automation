#!/usr/bin/env python3
"""
Lead Deduplication Tracker
Tracks MLS numbers and addresses we've already scraped/traced.
Prevents duplicate scrape results and wasted Tracerfy credits.

Storage: JSON file at ~/.openclaw/workspace/seen_leads.json
Keys by both MLS number and normalized address.
"""

import os
import json
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(WORKSPACE, 'seen_leads.json')


def _load():
    """Load the seen leads database"""
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {'mls_numbers': {}, 'addresses': {}, 'stats': {'total_seen': 0, 'duplicates_skipped': 0}}


def _save(db):
    """Save the seen leads database"""
    with open(SEEN_FILE, 'w') as f:
        json.dump(db, f, indent=2)


def normalize_address(address, city):
    """Normalize address for dedup matching"""
    addr = address.lower().strip().rstrip('.')
    # Normalize common abbreviations
    for old, new in [(' dr.', ' dr'), (' st.', ' st'), (' rd.', ' rd'), 
                     (' ave.', ' ave'), (' blvd.', ' blvd'), (' ln.', ' ln'),
                     (' ct.', ' ct'), (' cir.', ' cir'), (' hwy.', ' hwy')]:
        addr = addr.replace(old, new)
    city_norm = city.lower().strip()
    return f"{addr}|{city_norm}"


def is_seen(mls_number=None, address=None, city=None):
    """Check if a lead has been seen before (by MLS# or address)"""
    db = _load()
    
    if mls_number and str(mls_number) in db['mls_numbers']:
        return True
    
    if address and city:
        key = normalize_address(address, city)
        if key in db['addresses']:
            return True
    
    return False


def mark_seen(mls_number=None, address=None, city=None, category=None):
    """Mark a lead as seen"""
    db = _load()
    today = datetime.now().strftime('%Y-%m-%d')
    
    if mls_number:
        db['mls_numbers'][str(mls_number)] = {
            'first_seen': today,
            'category': category or '',
        }
    
    if address and city:
        key = normalize_address(address, city)
        db['addresses'][key] = {
            'first_seen': today,
            'mls_number': str(mls_number) if mls_number else '',
        }
    
    db['stats']['total_seen'] = len(db['mls_numbers'])
    _save(db)


def mark_batch_seen(leads):
    """Mark a batch of leads as seen (single write)"""
    db = _load()
    today = datetime.now().strftime('%Y-%m-%d')
    
    for lead in leads:
        mls = lead.get('mls_number', '').strip()
        address = lead.get('address', '').strip()
        city = lead.get('city', '').strip()
        category = lead.get('category', '')
        
        if mls:
            db['mls_numbers'][str(mls)] = {
                'first_seen': today,
                'category': category,
            }
        
        if address and city:
            key = normalize_address(address, city)
            db['addresses'][key] = {
                'first_seen': today,
                'mls_number': str(mls) if mls else '',
            }
    
    db['stats']['total_seen'] = len(db['mls_numbers'])
    _save(db)


def filter_new(leads):
    """
    Filter a list of lead dicts, returning only ones we haven't seen.
    Also marks the new ones as seen.
    """
    db = _load()
    today = datetime.now().strftime('%Y-%m-%d')
    new_leads = []
    dupes = 0
    
    for lead in leads:
        mls = lead.get('mls_number', '').strip()
        address = lead.get('address', '').strip()
        city = lead.get('city', '').strip()
        
        # Check MLS number
        if mls and str(mls) in db['mls_numbers']:
            dupes += 1
            continue
        
        # Check address
        if address and city:
            key = normalize_address(address, city)
            if key in db['addresses']:
                dupes += 1
                continue
        
        # New lead — mark it
        category = lead.get('category', '')
        if mls:
            db['mls_numbers'][str(mls)] = {
                'first_seen': today,
                'category': category,
            }
        if address and city:
            key = normalize_address(address, city)
            db['addresses'][key] = {
                'first_seen': today,
                'mls_number': str(mls) if mls else '',
            }
        
        new_leads.append(lead)
    
    db['stats']['total_seen'] = len(db['mls_numbers'])
    db['stats']['duplicates_skipped'] = db['stats'].get('duplicates_skipped', 0) + dupes
    _save(db)
    
    print(f"🔍 Dedup: {len(new_leads)} new leads, {dupes} duplicates skipped")
    return new_leads


def get_stats():
    """Get dedup statistics"""
    db = _load()
    return {
        'total_mls_tracked': len(db['mls_numbers']),
        'total_addresses_tracked': len(db['addresses']),
        'duplicates_skipped': db['stats'].get('duplicates_skipped', 0),
    }


def seed_from_csv(csv_path):
    """Seed the seen database from an existing CSV (for bootstrapping)"""
    import csv
    leads = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(row)
    mark_batch_seen(leads)
    print(f"🌱 Seeded {len(leads)} leads from {csv_path}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == '--stats':
            stats = get_stats()
            print(f"MLS numbers tracked: {stats['total_mls_tracked']}")
            print(f"Addresses tracked: {stats['total_addresses_tracked']}")
            print(f"Duplicates skipped: {stats['duplicates_skipped']}")
        elif sys.argv[1] == '--seed':
            if len(sys.argv) > 2:
                seed_from_csv(sys.argv[2])
            else:
                print("Usage: lead_dedup.py --seed <csv_file>")
    else:
        stats = get_stats()
        print(f"Tracking {stats['total_mls_tracked']} MLS numbers, {stats['total_addresses_tracked']} addresses")
