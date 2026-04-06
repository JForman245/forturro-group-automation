#!/usr/bin/env python3
"""
Tracerfy Skip Tracing Integration
Submits MLS lead CSVs to Tracerfy's Advanced Trace API for owner contact enrichment.
Advanced trace: address + city + state only → returns owner name, phones, emails, mailing address.
2 credits per lead ($0.04/lead at $0.02/credit).

Usage:
    python3 tracerfy_skip_trace.py <input_csv>
    python3 tracerfy_skip_trace.py  (uses latest mls_leads_*.csv)
"""

import os
import sys
import csv
import json
import time
import glob
import requests
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────

WORKSPACE = os.path.dirname(os.path.abspath(__file__))

def load_env(filename):
    """Load env vars from a dotenv file"""
    env_path = os.path.join(WORKSPACE, filename)
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env('.env.tracerfy')

API_TOKEN = os.getenv('TRACERFY_API_TOKEN')
BASE_URL = os.getenv('TRACERFY_BASE_URL', 'https://tracerfy.com/v1/api')

if not API_TOKEN:
    print("❌ TRACERFY_API_TOKEN not set. Check .env.tracerfy")
    sys.exit(1)

HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
}

STATE = 'SC'  # All CCMLS leads are in South Carolina


# ── API Functions ───────────────────────────────────────────────────────────

def check_balance():
    """Check current credit balance"""
    resp = requests.get(f'{BASE_URL}/analytics/', headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    print(f"💰 Tracerfy balance: {data['balance']} credits")
    print(f"   Total queues: {data['total_queues']}, Completed: {data['queues_completed']}, Pending: {data['queues_pending']}")
    return data


def submit_trace(csv_path):
    """Submit a CSV for Advanced Trace (address-only, no owner name needed)"""
    print(f"\n📤 Submitting {csv_path} to Tracerfy Advanced Trace...")

    # Check balance first
    analytics = check_balance()
    
    # Count rows to estimate cost
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        row_count = sum(1 for _ in reader)
    
    credits_needed = row_count * 2  # Advanced trace = 2 credits/lead
    print(f"   Rows: {row_count}, Credits needed: ~{credits_needed}")
    
    if analytics['balance'] < credits_needed:
        print(f"❌ Insufficient credits. Have {analytics['balance']}, need ~{credits_needed}")
        print(f"   Load more credits at tracerfy.com or reduce the list size")
        return None

    with open(csv_path, 'rb') as f:
        files = {'csv_file': (os.path.basename(csv_path), f, 'text/csv')}
        data = {
            'address_column': 'address',
            'city_column': 'city',
            'state_column': 'state',
            'zip_column': 'zip',
            'first_name_column': '',
            'last_name_column': '',
            'mail_address_column': '',
            'mail_city_column': '',
            'mail_state_column': '',
            'trace_type': 'advanced',
        }
        
        resp = requests.post(
            f'{BASE_URL}/trace/',
            headers=HEADERS,
            files=files,
            data=data,
            timeout=60
        )

    if resp.status_code in (200, 201):
        result = resp.json()
        queue_id = result.get('queue_id') or result.get('id')
        est_wait = result.get('estimated_wait_seconds', 'unknown')
        print(f"✅ Trace submitted! Queue ID: {queue_id}")
        print(f"   Estimated wait: {est_wait} seconds")
        return queue_id
    else:
        print(f"❌ Trace submission failed: {resp.status_code}")
        print(f"   Response: {resp.text[:500]}")
        return None


def check_queue_status(queue_id=None):
    """Check status of all queues or a specific one"""
    resp = requests.get(f'{BASE_URL}/queues/', headers=HEADERS, timeout=15)
    resp.raise_for_status()
    queues = resp.json()
    
    if queue_id:
        queues = [q for q in queues if q['id'] == queue_id]
    
    for q in queues:
        status = "⏳ Pending" if q['pending'] else "✅ Complete"
        print(f"  Queue {q['id']}: {status} | Type: {q.get('trace_type', 'normal')} | "
              f"Rows: {q.get('rows_uploaded', '?')} | Credits: {q.get('credits_deducted', '?')}")
        if q.get('download_url'):
            print(f"    📥 Download: {q['download_url']}")
    
    return queues


def wait_for_completion(queue_id, max_wait=600, poll_interval=15):
    """Poll until queue is complete, then return results"""
    print(f"\n⏳ Waiting for queue {queue_id} to complete (max {max_wait}s)...")
    
    start = time.time()
    while time.time() - start < max_wait:
        try:
            resp = requests.get(f'{BASE_URL}/queues/', headers=HEADERS, timeout=15)
            if resp.status_code == 503:
                elapsed = int(time.time() - start)
                print(f"   Server busy (503), retrying... ({elapsed}s elapsed)")
                time.sleep(poll_interval)
                continue
            resp.raise_for_status()
            queues = resp.json()
        except requests.exceptions.RequestException as e:
            elapsed = int(time.time() - start)
            print(f"   Request error: {e}, retrying... ({elapsed}s elapsed)")
            time.sleep(poll_interval)
            continue
        
        for q in queues:
            if q['id'] == queue_id:
                if not q['pending']:
                    elapsed = int(time.time() - start)
                    print(f"✅ Queue {queue_id} complete in {elapsed}s!")
                    print(f"   Rows: {q.get('rows_uploaded', '?')}, Credits used: {q.get('credits_deducted', '?')}")
                    return q
                break
        
        elapsed = int(time.time() - start)
        print(f"   Still processing... ({elapsed}s elapsed)")
        time.sleep(poll_interval)
    
    print(f"❌ Timeout waiting for queue {queue_id} after {max_wait}s")
    return None


def download_results(queue_id_or_url, output_path=None):
    """Download trace results — either from download_url or by fetching queue records"""
    
    # If it's a URL, download directly
    if isinstance(queue_id_or_url, str) and queue_id_or_url.startswith('http'):
        url = queue_id_or_url
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            output_path = os.path.join(WORKSPACE, f'traced_leads_{timestamp}.csv')
        
        print(f"📥 Downloading results from CDN...")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(resp.content)
        print(f"✅ Saved to {output_path}")
        return output_path
    
    # Otherwise fetch via API
    queue_id = queue_id_or_url
    print(f"📥 Fetching results for queue {queue_id}...")
    resp = requests.get(f'{BASE_URL}/queue/{queue_id}', headers=HEADERS, timeout=30)
    resp.raise_for_status()
    records = resp.json()
    
    if not records:
        print("⚠️  No records returned")
        return None
    
    if not output_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        output_path = os.path.join(WORKSPACE, f'traced_leads_{timestamp}.csv')
    
    # Write to CSV
    fieldnames = list(records[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"✅ Saved {len(records)} traced records to {output_path}")
    return output_path


def prepare_mls_csv(input_csv, output_csv=None):
    """
    Prepare MLS lead CSV for Tracerfy submission.
    Adds 'state' column (SC), deduplicates by address, removes rows missing address/city.
    """
    if not output_csv:
        output_csv = os.path.join(WORKSPACE, 'tracerfy_input.csv')
    
    seen_addresses = set()
    rows = []
    skipped = 0
    
    with open(input_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            address = row.get('address', '').strip()
            city = row.get('city', '').strip()
            zip_code = row.get('zip', '').strip()
            
            if not address or not city:
                skipped += 1
                continue
            
            # Deduplicate
            key = f"{address.lower()}|{city.lower()}"
            if key in seen_addresses:
                skipped += 1
                continue
            seen_addresses.add(key)
            
            rows.append({
                'address': address,
                'city': city,
                'state': STATE,
                'zip': zip_code,
            })
    
    # Write prepared CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['address', 'city', 'state', 'zip'])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"📋 Prepared {len(rows)} unique addresses for tracing (skipped {skipped})")
    return output_csv, len(rows)


def merge_results(original_csv, traced_csv, output_csv=None):
    """
    Merge Tracerfy results back with original MLS data.
    Joins on address+city. Output is the enriched lead file.
    """
    if not output_csv:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        output_csv = os.path.join(WORKSPACE, f'enriched_leads_{timestamp}.csv')
    
    # Load traced data keyed by address
    traced = {}
    with open(traced_csv) as f:
        reader = csv.DictReader(f)
        traced_fields = reader.fieldnames or []
        for row in reader:
            addr = row.get('address', '').strip().lower()
            city = row.get('city', '').strip().lower()
            key = f"{addr}|{city}"
            traced[key] = row
    
    # Load original and merge
    merged = []
    matched = 0
    with open(original_csv) as f:
        reader = csv.DictReader(f)
        original_fields = reader.fieldnames or []
        
        # Determine extra fields from traced data
        # Tracerfy uses mixed casing: Email-1, Mobile-1, Landline-1, etc.
        contact_fields = [
            'first_name', 'last_name',
            'primary_phone', 'primary_phone_type',
            'Mobile-1', 'Mobile-2', 'Mobile-3', 'Mobile-4', 'Mobile-5',
            'Landline-1', 'Landline-2', 'Landline-3',
            'Email-1', 'Email-2', 'Email-3', 'Email-4', 'Email-5',
            'mail_address', 'mail_city', 'mail_state', 'mailing_zip',
        ]
        
        for row in reader:
            addr = row.get('address', '').strip().lower()
            city = row.get('city', '').strip().lower()
            key = f"{addr}|{city}"
            
            if key in traced:
                trace_data = traced[key]
                for field in contact_fields:
                    row[field] = trace_data.get(field, '')
                matched += 1
            else:
                for field in contact_fields:
                    row[field] = ''
            
            merged.append(row)
    
    # Write merged CSV
    all_fields = original_fields + [f for f in contact_fields if f not in original_fields]
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(merged)
    
    print(f"\n🔗 Merged results: {matched}/{len(merged)} leads enriched with contact data")
    print(f"📄 Enriched file: {output_csv}")
    return output_csv


def find_latest_mls_csv():
    """Find the most recent mls_leads_*.csv file"""
    pattern = os.path.join(WORKSPACE, 'mls_leads_*.csv')
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def run_full_pipeline(input_csv=None):
    """
    Full pipeline: prepare CSV → submit to Tracerfy → wait → download → merge
    """
    if not input_csv:
        input_csv = find_latest_mls_csv()
        if not input_csv:
            print("❌ No MLS lead CSV found")
            return None
    
    print(f"🚀 Tracerfy Skip Trace Pipeline")
    print(f"   Input: {input_csv}")
    print(f"   Trace type: Advanced (address-only, 2 credits/lead)")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Step 1: Prepare CSV
    prepared_csv, count = prepare_mls_csv(input_csv)
    if count == 0:
        print("❌ No valid addresses to trace")
        return None
    
    # Step 2: Submit to Tracerfy
    queue_id = submit_trace(prepared_csv)
    if not queue_id:
        return None
    
    # Step 3: Wait for completion
    result = wait_for_completion(queue_id)
    if not result:
        return None
    
    # Step 4: Download results
    download_url = result.get('download_url')
    if download_url:
        traced_csv = download_results(download_url)
    else:
        traced_csv = download_results(queue_id)
    
    if not traced_csv:
        return None
    
    # Step 5: Merge with original data
    enriched_csv = merge_results(input_csv, traced_csv)
    
    # Step 6: Check remaining balance
    check_balance()
    
    # Clean up temp file
    try:
        os.remove(prepared_csv)
    except:
        pass
    
    return enriched_csv


# ── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == '--balance':
            check_balance()
        elif arg == '--queues':
            check_queue_status()
        elif arg == '--download' and len(sys.argv) > 2:
            download_results(int(sys.argv[2]))
        else:
            # Treat as input CSV path
            run_full_pipeline(arg)
    else:
        # Auto-find latest MLS CSV and run
        run_full_pipeline()
