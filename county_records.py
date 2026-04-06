#!/usr/bin/env python3
"""
Horry County Register of Deeds lookup via Playwright.
Searches by owner name, returns deed/mortgage records.
Wired into MLS scraper pipeline for lead enrichment.
"""

import os, sys, re, json, time, csv
from playwright.sync_api import sync_playwright

BASE = 'https://acclaimweb.horrycounty.org/AcclaimWeb'
CACHE_FILE = '/Users/claw1/.openclaw/workspace/county_records_cache.json'


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def search_owner(page, name):
    """Search for a name on the already-loaded search form. Returns list of record dicts."""
    
    # Clear and fill name
    page.fill('input[name="SearchOnName"]', '')
    page.wait_for_timeout(500)
    page.fill('input[name="SearchOnName"]', name)
    page.wait_for_timeout(1000)
    
    # Click Search to trigger name popup
    page.click('text=Search')
    page.wait_for_timeout(4000)
    
    # Click "All / None" to select all name variants
    try:
        all_none = page.locator(':text-is("All / None")')
        for i in range(all_none.count()):
            if all_none.nth(i).is_visible():
                all_none.nth(i).click()
                break
    except:
        pass
    page.wait_for_timeout(1000)
    
    # Click "Done" to close name popup
    try:
        done = page.locator(':text-is("Done")')
        for i in range(done.count()):
            if done.nth(i).is_visible():
                done.nth(i).click()
                break
    except:
        pass
    page.wait_for_timeout(8000)
    
    # Parse results from page text
    text = page.evaluate('document.body.innerText')
    records = []
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Match result rows: number, $amount, From/To, name1, name2, book/page, date, type, booktype, description
        # Pattern: starts with a number (row index)
        match = re.match(r'^\d+\t+\$?([\d,\.]+)\t+(From|To)\t+(.+?)\t+(.+?)\t+(\d+/\d+)\t+(\d{2}/\d{2}/\d{4})\t+(.+?)\t+([A-Z]+)\t*(.*)', line)
        if match:
            records.append({
                'consideration': match.group(1),
                'direction': match.group(2),
                'party1': match.group(3).strip(),
                'party2': match.group(4).strip(),
                'book_page': match.group(5),
                'date': match.group(6),
                'doc_type': match.group(7).strip(),
                'book_type': match.group(8).strip(),
                'description': match.group(9).strip(),
            })
    
    return records


def get_latest_deed_and_mortgage(records, owner_name=''):
    """Extract the most recent deed (purchase) and mortgage from records."""
    owner_upper = owner_name.upper()
    
    latest_deed = None
    latest_mortgage = None
    
    for r in records:
        doc = r['doc_type'].upper()
        
        # Look for deeds where the owner is the grantee (To = they received it)
        if 'DEED' in doc and 'SATISFACTION' not in doc and 'CERTIFICATE' not in doc:
            if r['direction'] == 'To' or (not latest_deed):
                if not latest_deed or r['date'] > latest_deed['date']:
                    latest_deed = r
        
        # Look for mortgages (not satisfactions)
        if ('MORTGAGE' in doc or doc == 'MTG') and 'SATISFACTION' not in doc and 'ASSIGNMENT' not in doc:
            if r['direction'] == 'From':  # Borrower is "From" in mortgage
                if not latest_mortgage or r['date'] > latest_mortgage['date']:
                    latest_mortgage = r
    
    return latest_deed, latest_mortgage


def lookup_leads(csv_path, output_path=None):
    """Look up county records for all leads in an enriched CSV."""
    cache = load_cache()
    
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"📋 Looking up {len(rows)} leads in Horry County Register of Deeds...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 900})
        
        # Accept disclaimer and get to search form
        page.goto(f'{BASE}/Search/Disclaimer?st=/AcclaimWeb/search/SearchTypeName', wait_until='networkidle')
        page.wait_for_timeout(2000)
        page.click('input[value="I accept the conditions above."]')
        page.wait_for_timeout(2000)
        
        looked_up = 0
        cached_count = 0
        enriched = []
        
        for row in rows:
            first = row.get('first_name', '').strip()
            last = row.get('last_name', '').strip()
            mls = row.get('mls_number', '').strip()
            
            if not last:
                enriched.append({**row, 'deed_date': '', 'deed_price': '', 'mortgage_amount': '', 'mortgage_lender': ''})
                continue
            
            search_name = f"{last}, {first}" if first else last
            
            # Check cache
            if search_name in cache:
                records = cache[search_name]
                cached_count += 1
            else:
                try:
                    records = search_owner(page, search_name)
                    cache[search_name] = records
                    looked_up += 1
                    
                    if looked_up % 10 == 0:
                        print(f"  Looked up {looked_up}... ({len(records)} records for {search_name})")
                        save_cache(cache)
                    
                    time.sleep(1)  # Don't hammer the server
                except Exception as e:
                    print(f"  Error looking up {search_name}: {e}")
                    records = []
            
            # Extract latest deed and mortgage
            deed, mortgage = get_latest_deed_and_mortgage(records, search_name)
            
            enriched.append({
                **row,
                'deed_date': deed['date'] if deed else '',
                'deed_price': deed['consideration'] if deed else '',
                'deed_from': deed['party1'] if deed else '',
                'mortgage_amount': mortgage['consideration'] if mortgage else '',
                'mortgage_lender': mortgage['party2'] if mortgage else '',
                'mortgage_date': mortgage['date'] if mortgage else '',
            })
        
        browser.close()
    
    save_cache(cache)
    print(f"✅ Done: {looked_up} looked up, {cached_count} cached")
    
    # Write enriched output
    if output_path and enriched:
        fieldnames = list(enriched[0].keys())
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched)
        print(f"📄 Enriched CSV: {output_path}")
    
    return enriched


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 county_records.py '<Last, First>'          # Single lookup")
        print("  python3 county_records.py --csv <input.csv> [output.csv]  # Batch")
        sys.exit(1)
    
    if sys.argv[1] == '--csv':
        input_csv = sys.argv[2]
        output_csv = sys.argv[3] if len(sys.argv) > 3 else input_csv.replace('.csv', '_county.csv')
        lookup_leads(input_csv, output_csv)
    else:
        name = ' '.join(sys.argv[1:])
        print(f"🔍 Searching: {name}")
        
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            page.goto(f'{BASE}/Search/Disclaimer?st=/AcclaimWeb/search/SearchTypeName', wait_until='networkidle')
            page.wait_for_timeout(2000)
            page.click('input[value="I accept the conditions above."]')
            page.wait_for_timeout(2000)
            
            records = search_owner(page, name)
            browser.close()
        
        print(f"Found {len(records)} records:")
        deed, mortgage = get_latest_deed_and_mortgage(records, name)
        
        if deed:
            print(f"\n📜 Latest Deed:")
            print(f"   Date: {deed['date']}")
            print(f"   Price: ${deed['consideration']}")
            print(f"   From: {deed['party1']} → To: {deed['party2']}")
            print(f"   Book/Page: {deed['book_page']}")
            print(f"   Description: {deed['description']}")
        
        if mortgage:
            print(f"\n🏦 Latest Mortgage:")
            print(f"   Date: {mortgage['date']}")
            print(f"   Amount: ${mortgage['consideration']}")
            print(f"   Lender: {mortgage['party2']}")
            print(f"   Book/Page: {mortgage['book_page']}")
        
        if not deed and not mortgage:
            print("  No deeds or mortgages found")
            for r in records[:5]:
                print(f"  {r['date']} | {r['doc_type']} | ${r['consideration']} | {r['party1']} → {r['party2']}")
