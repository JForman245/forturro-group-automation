#!/usr/bin/env python3
"""
MLS Daily Lead Scraper — Production Version
- Expired: Market Monitor (last 2 days, daysBack=2)
- Withdrawn: Quick Search + Status Date sort desc (filter last 2 days)
- Dedup: seen_leads.json + FUB address check
- Skip trace: Tracerfy (must have name + phone + address to qualify)
- FUB upload: EXPIRED / WITHDRAWN pond (ID 37)
- Email enriched CSV + Telegram alert

Usage: python3 mls_daily_scraper.py
       python3 mls_daily_scraper.py --skip-trace
       python3 mls_daily_scraper.py --no-email
"""

import sys
import time
import os
import csv
import json
import re
import glob
import subprocess
import requests
import argparse
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')
MLS_USERNAME = os.getenv('MLS_USERNAME')
MLS_PASSWORD = os.getenv('MLS_PASSWORD')

WORKSPACE = "/Users/claw1/.openclaw/workspace"
EXPORT_DIR = f"{WORKSPACE}/mls_exports"
SEEN_FILE = f"{WORKSPACE}/seen_leads.json"
GOG_ACCOUNT = "jeff@forturro.com"
FUB_POND_ID = 37  # EXPIRED / WITHDRAWN

# Load FUB key
FUB_KEY = None
with open(f"{WORKSPACE}/.env.fub") as f:
    for line in f:
        if line.startswith("FUB_API_KEY="):
            FUB_KEY = line.strip().split("=", 1)[1]


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1400,1000")
    return webdriver.Chrome(options=chrome_options)


def login(driver):
    print("⏳ Logging into CCAR...")
    driver.get("https://ccar.mysolidearth.com/portal")
    time.sleep(5)
    driver.find_elements(By.CSS_SELECTOR, ".v-radio")[1].click()
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, "input[type='email'][name='email']").send_keys(MLS_USERNAME)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(MLS_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(10)
    for link in driver.find_elements(By.TAG_NAME, "a"):
        if "paragon" in (link.get_attribute("href") or "").lower():
            link.click()
            break
    time.sleep(10)
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
    time.sleep(3)
    driver.execute_script("""
        if(document.getElementById('cboxOverlay'))document.getElementById('cboxOverlay').style.display='none';
        if(document.getElementById('colorbox'))document.getElementById('colorbox').style.display='none';
        document.querySelectorAll('.ui-dialog').forEach(function(d){d.style.display='none';});
        document.querySelectorAll('.ui-dialog-titlebar-close').forEach(function(b){try{b.click();}catch(e){}});
    """)
    time.sleep(3)
    print("✅ Logged into Paragon")


def scrape_expired(driver):
    """Scrape expired via Market Monitor (last 2 days)"""
    print("\n🔍 Scraping EXPIRED (last 2 days)...")
    
    # Set daysBack to 2 first
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    driver.switch_to.frame(iframes[2])  # HomeTab
    
    driver.execute_script("""
        var db = document.getElementById('mmdaysback');
        if(db){ db.value = '2'; db.dispatchEvent(new Event('change',{bubbles:true})); }
    """)
    time.sleep(1)
    
    driver.execute_script('document.getElementById("mm_1").click();')
    print("  Clicked Market Monitor > Expired (daysBack=2)")
    time.sleep(12)
    
    # Navigate to results > Spreadsheet sub-iframe
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    
    data = None
    for i, iframe in enumerate(iframes):
        src = iframe.get_attribute("src") or ""
        if "MarketMonitor" in src:
            driver.switch_to.frame(iframe)
            subs = driver.find_elements(By.TAG_NAME, "iframe")
            for j, sf in enumerate(subs):
                ssrc = sf.get_attribute("src") or ""
                if "Spreadsheet" in ssrc:
                    driver.switch_to.frame(sf)
                    time.sleep(3)
                    data = driver.execute_script("""
                        if(typeof jQuery==='undefined') return null;
                        var g = jQuery('table.ui-jqgrid-btable, [id*=jqGrid]');
                        if(!g.length) return null;
                        var ids = g.jqGrid('getDataIDs');
                        var rows = [];
                        for(var i=0; i<ids.length; i++) rows.push(g.jqGrid('getRowData', ids[i]));
                        return rows;
                    """)
                    driver.switch_to.parent_frame()
                    break
            driver.switch_to.default_content()
            break
    
    if data:
        clean = [clean_row(r, "EXPIRED") for r in data]
        print(f"  ✅ {len(clean)} expired listings")
        return clean
    print("  ❌ No expired data")
    return []


def scrape_withdrawn(driver):
    """Scrape withdrawn via Quick Search + Status Date sort (last 2 days)"""
    print("\n🔍 Scraping WITHDRAWN (last 2 days)...")
    
    # Navigate to Search > Property
    driver.switch_to.default_content()
    driver.execute_script('var l=document.querySelectorAll("a");for(var i=0;i<l.length;i++){if(l[i].textContent.trim()==="Search"){l[i].click();return;}}')
    time.sleep(2)
    driver.execute_script('var l=document.querySelectorAll("a");for(var i=0;i<l.length;i++){if(l[i].textContent.trim()==="Property"){l[i].click();return;}}')
    time.sleep(5)
    
    # Find search form iframe
    for i, iframe in enumerate(driver.find_elements(By.TAG_NAME, "iframe")):
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(iframe)
            if driver.execute_script("return document.getElementById('f_11__1-2-3-4-5-6-7') !== null;"):
                break
        except:
            pass
    
    # Set Withdrawn status
    field = driver.find_element(By.ID, 'f_11__1-2-3-4-5-6-7')
    field.click()
    time.sleep(0.5)
    field.send_keys('With')
    time.sleep(2)
    driver.execute_script("""
        var lis = document.querySelectorAll('.ac_results li');
        for(var i=0;i<lis.length;i++){
            if(lis[i].textContent.indexOf('WITHDRAWN')>=0){lis[i].click();return;}
        }
    """)
    time.sleep(1)
    
    # Click Search
    driver.execute_script("""
        var btns = document.querySelectorAll('input[type=button],button');
        for(var i=0;i<btns.length;i++){
            if((btns[i].value||btns[i].textContent||'').trim()==='Search'){btns[i].click();return;}
        }
    """)
    print("  Search submitted")
    time.sleep(15)
    
    # Navigate to Spreadsheet: iframe[3] > sub[1]
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if len(iframes) < 4:
        print("  ❌ Results iframe not found")
        return []
    
    driver.switch_to.frame(iframes[3])
    subs = driver.find_elements(By.TAG_NAME, "iframe")
    if len(subs) < 2:
        print("  ❌ Spreadsheet sub-iframe not found")
        return []
    
    driver.switch_to.frame(subs[1])
    time.sleep(5)
    
    # Sort by Status Date: click header once (asc), then again (desc)
    driver.execute_script("""
        var headers = document.querySelectorAll('.ui-jqgrid-sortable, th div');
        for(var i=0;i<headers.length;i++){
            if(headers[i].textContent.trim().indexOf('Status Date')>=0){
                headers[i].click(); return;
            }
        }
    """)
    time.sleep(10)
    driver.execute_script("""
        var headers = document.querySelectorAll('.ui-jqgrid-sortable, th div');
        for(var i=0;i<headers.length;i++){
            if(headers[i].textContent.trim().indexOf('Status Date')>=0){
                headers[i].click(); return;
            }
        }
    """)
    print("  Sorted by Status Date desc")
    time.sleep(15)
    
    # Get data
    data = driver.execute_script("""
        if(typeof jQuery==='undefined') return null;
        var g = jQuery('table.ui-jqgrid-btable, [id*=jqGrid]');
        if(!g.length) return null;
        var ids = g.jqGrid('getDataIDs');
        var rows = [];
        for(var i=0; i<ids.length; i++) rows.push(g.jqGrid('getRowData', ids[i]));
        return rows;
    """)
    
    if not data:
        print("  ❌ No withdrawn data")
        return []
    
    # Filter to last 2 days
    cutoff = datetime.now() - timedelta(days=2)
    clean_rows = []
    for row in data:
        cleaned = clean_row(row, "WITHDRAWN")
        sd_str = cleaned.get("StatusDate", "")
        if sd_str:
            try:
                sd = datetime.strptime(sd_str, "%m/%d/%Y")
                if sd >= cutoff:
                    clean_rows.append(cleaned)
            except:
                pass
    
    print(f"  ✅ {len(clean_rows)} withdrawn listings (last 2 days)")
    return clean_rows


def clean_row(row_dict, category):
    """Clean jqGrid row into flat dict"""
    clean = {}
    for k, v in row_dict.items():
        if k.startswith("INTEGRATION") or k.startswith("LISTING_PICTURES") or k.startswith("row_highlight"):
            continue
        ck = re.sub(r'__[\d_]+$', '', k).rstrip('_')
        cv = re.sub(r'<[^>]+>', '', str(v)).strip()
        if 'price' in ck.lower():
            cv = cv.replace('$', '').replace(',', '').strip()
        if ck and cv:
            clean[ck] = cv
    clean['Category'] = category
    return clean


def dedup(leads):
    """Remove duplicates against seen_leads.json"""
    with open(SEEN_FILE) as f:
        seen = json.load(f)
    seen_mls = set(seen.get("mls_numbers", []))
    
    new = []
    dupes = 0
    for lead in leads:
        mls = lead.get("_DisplayId", lead.get("display_id", "")).strip()
        if mls in seen_mls:
            dupes += 1
        else:
            new.append(lead)
            if mls:
                seen_mls.add(mls)
    
    # Save updated seen
    seen["mls_numbers"] = list(seen_mls)
    seen["stats"]["total_seen"] = len(seen_mls)
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)
    
    print(f"  Dedup: {len(new)} new, {dupes} duplicates removed")
    return new


def dedup_fub(leads):
    """Check FUB for existing contacts at same address"""
    new = []
    fub_dupes = 0
    for lead in leads:
        addr = lead.get("Address", "").strip()
        if not addr:
            new.append(lead)
            continue
        search = re.sub(r'[^\w\s]', '', addr)[:25]
        try:
            resp = requests.get(
                "https://api.followupboss.com/v1/people",
                auth=(FUB_KEY, ""),
                params={"query": search, "limit": 3},
                timeout=10
            )
            if resp.status_code == 200:
                people = resp.json().get("people", [])
                found = False
                for p in people:
                    # Check if notes mention this exact address
                    notes_resp = requests.get(
                        f"https://api.followupboss.com/v1/notes?personId={p['id']}&limit=5",
                        auth=(FUB_KEY, ""),
                        timeout=10
                    )
                    if notes_resp.status_code == 200:
                        for note in notes_resp.json().get("notes", []):
                            if addr.split('.')[0].lower() in note.get("body", "").lower():
                                found = True
                                break
                    if found:
                        break
                if found:
                    fub_dupes += 1
                    print(f"    FUB dupe: {addr}")
                else:
                    new.append(lead)
            else:
                new.append(lead)
        except:
            new.append(lead)
        time.sleep(0.3)
    
    print(f"  FUB dedup: {len(new)} new, {fub_dupes} already in FUB")
    return new


def skip_trace(csv_path):
    """Run Tracerfy skip trace"""
    print("\n🔍 Running Tracerfy skip trace...")
    result = subprocess.run(
        ["python3", f"{WORKSPACE}/tracerfy_skip_trace.py", csv_path],
        capture_output=True, text=True, cwd=WORKSPACE
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"⚠️ Tracerfy error: {result.stderr[:200]}")
    
    # Find the enriched file
    enriched = sorted(glob.glob(f"{WORKSPACE}/enriched_leads_*.csv"), key=os.path.getmtime, reverse=True)
    return enriched[0] if enriched else None


def upload_to_fub(enriched_path):
    """Upload qualified leads to FUB EXPIRED/WITHDRAWN pond"""
    print("\n📤 Uploading to FUB...")
    with open(enriched_path) as f:
        rows = list(csv.DictReader(f))
    
    uploaded = 0
    skipped = 0
    
    for row in rows:
        first = row.get("first_name", "").strip()
        last = row.get("last_name", "").strip()
        phone = row.get("primary_phone", "").strip()
        address = row.get("address", "").strip()
        
        if not (first and last and phone and len(phone) >= 7 and address):
            skipped += 1
            continue
        
        phones = [{"value": phone}]
        for i in range(1, 6):
            for pt in ["Mobile", "Landline"]:
                p = row.get(f"{pt}-{i}", "").strip()
                if p and p != phone:
                    phones.append({"value": p})
        
        emails = []
        for i in range(1, 6):
            e = row.get(f"Email-{i}", "").strip()
            if e:
                emails.append({"value": e})
        
        category = row.get("category", "EXPIRED").upper()
        data = {
            "firstName": first,
            "lastName": last,
            "phones": phones,
            "source": "MLS",
            "tags": ["Investor", f"{category.title()} Lead", "MLS Scraper"],
            "assignedPondId": FUB_POND_ID,
        }
        if emails:
            data["emails"] = emails
        
        resp = requests.post("https://api.followupboss.com/v1/people", auth=(FUB_KEY, ""), json=data)
        if resp.status_code in (200, 201):
            pid = resp.json().get("id")
            price = row.get("price", "")
            price_str = f"${int(price):,}" if price and price.isdigit() else "N/A"
            city = row.get("city", "")
            mls = row.get("mls_number", "")
            
            requests.post("https://api.followupboss.com/v1/notes", auth=(FUB_KEY, ""), json={
                "personId": pid,
                "subject": f"{category} - {address}, {city}",
                "body": f"{category} listing at {address}, {city}, SC {row.get('zip','')}\nMLS# {mls} | Price: {price_str}\nProperty Type: {row.get('class','')} / {row.get('type','')}"
            })
            print(f"  ✅ {first} {last} → FUB #{pid} | {address} | {price_str}")
            uploaded += 1
        time.sleep(0.5)
    
    print(f"\n✅ FUB: {uploaded} uploaded, {skipped} skipped (missing name/phone/address)")
    return uploaded


def email_report(csv_path, expired_ct, withdrawn_ct, uploaded_ct):
    total = expired_ct + withdrawn_ct
    today = datetime.now().strftime("%A, %B %d, %Y")
    subject = f"MLS Daily Report - {datetime.now().strftime('%m/%d/%Y')} - {total} Leads"
    body = f"MLS Daily Lead Report — {today}\n\nExpired: {expired_ct}\nWithdrawn: {withdrawn_ct}\nTotal: {total}\nUploaded to FUB: {uploaded_ct}\n\nEnriched CSV attached.\n\n— Birdy 🐦"
    
    subprocess.run(
        ["gog", "gmail", "send", "--to", "jeff@forturro.com",
         "--subject", subject, "--body-file", "-", "--attach", csv_path],
        input=body, capture_output=True, text=True,
        env={**os.environ, "GOG_ACCOUNT": GOG_ACCOUNT}
    )
    print("✅ Report emailed")


def telegram_alert(expired_ct, withdrawn_ct, uploaded_ct):
    total = expired_ct + withdrawn_ct
    msg = f"📊 MLS Daily Report — {datetime.now().strftime('%m/%d/%Y')}\n\n"
    msg += f"Expired: {expired_ct}\nWithdrawn: {withdrawn_ct}\nTotal: {total}\n"
    msg += f"Uploaded to FUB: {uploaded_ct}\n\nEnriched CSV emailed."
    
    subprocess.run(
        ["openclaw", "message", "send", "--channel", "telegram",
         "--target", "8685619460", "--message", msg],
        capture_output=True, text=True
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-trace", action="store_true", help="Auto-run skip trace")
    parser.add_argument("--no-email", action="store_true")
    args = parser.parse_args()
    
    today = datetime.now().strftime("%Y%m%d")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    driver = setup_driver()
    
    try:
        login(driver)
        
        # 1. Scrape Expired (Market Monitor, last 2 days)
        expired = scrape_expired(driver)
        
        # 2. Scrape Withdrawn (Quick Search + sort, last 2 days)
        withdrawn = scrape_withdrawn(driver)
        
        all_leads = expired + withdrawn
        print(f"\n📊 Raw total: {len(expired)} expired + {len(withdrawn)} withdrawn = {len(all_leads)}")
        
        if not all_leads:
            print("No leads found")
            telegram_alert(0, 0, 0)
            return
        
        # 3. Dedup against seen_leads.json
        all_leads = dedup(all_leads)
        
        # 4. Dedup against FUB
        all_leads = dedup_fub(all_leads)
        
        print(f"\n✅ After all dedup: {len(all_leads)} new leads")
        
        if not all_leads:
            print("All leads were duplicates")
            telegram_alert(len(expired), len(withdrawn), 0)
            return
        
        # 5. Save clean CSV for trace
        trace_csv = f"{EXPORT_DIR}/mls_leads_{today}_trace.csv"
        with open(trace_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["address", "city", "state", "zip", "mls_number", "price", "category", "class", "type"])
            for lead in all_leads:
                writer.writerow([
                    lead.get("Address", ""), lead.get("City", ""), "SC",
                    lead.get("Zip", ""), lead.get("_DisplayId", lead.get("display_id", "")),
                    lead.get("SystemPrice", ""), lead.get("Category", ""),
                    lead.get("Class", ""), lead.get("Type", "")
                ])
        
        # 6. Skip trace
        if args.skip_trace:
            enriched_path = skip_trace(trace_csv)
        else:
            enriched_path = None
            print("\n⏸️ Skip trace not requested (use --skip-trace)")
        
        # 7. Upload to FUB
        uploaded = 0
        if enriched_path:
            uploaded = upload_to_fub(enriched_path)
        
        # 8. Email + alert
        report_path = enriched_path or trace_csv
        if not args.no_email:
            exp_ct = len([l for l in all_leads if l.get("Category") == "EXPIRED"])
            wth_ct = len([l for l in all_leads if l.get("Category") == "WITHDRAWN"])
            email_report(report_path, exp_ct, wth_ct, uploaded)
            telegram_alert(exp_ct, wth_ct, uploaded)
        
        print(f"\n🎉 Done! {len(all_leads)} leads processed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("/tmp/mls_scraper_error.png")
    finally:
        driver.quit()
        print("🔒 Browser closed")


if __name__ == "__main__":
    main()
