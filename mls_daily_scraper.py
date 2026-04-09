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
from selenium.webdriver import ActionChains
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
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_experimental_option('prefs', {
        'download.default_directory': EXPORT_DIR,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing.enabled': True,
    })
    return webdriver.Chrome(options=chrome_options)


def login(driver):
    print("⏳ Logging into CCAR...")
    driver.get("https://ccar.mysolidearth.com/portal")
    time.sleep(5)
    driver.execute_script("document.querySelector(\"input[type='radio'][value='email']\").click()")
    time.sleep(1)
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
    try:
        driver.find_element(By.ID, 'Close').click()
        time.sleep(1)
    except:
        pass
    time.sleep(3)
    print("✅ Logged into Paragon")


def _export_results_csv(driver, category):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    before_files = {p: os.path.getmtime(p) for p in glob.glob(f"{EXPORT_DIR}/*.csv")}

    driver.switch_to.default_content()
    frames = driver.find_elements(By.TAG_NAME, 'iframe')
    target = None
    for i in range(len(frames)):
        try:
            driver.switch_to.default_content()
            frames = driver.find_elements(By.TAG_NAME, 'iframe')
            driver.switch_to.frame(frames[i])
            text = driver.find_element(By.TAG_NAME, 'body').text
            if 'Export' in text and 'BACK' in text:
                target = i
                break
        except:
            pass

    if target is None:
        print(f"  ❌ Could not find results frame for {category}")
        return []

    driver.switch_to.default_content()
    frames = driver.find_elements(By.TAG_NAME, 'iframe')
    driver.switch_to.frame(frames[target])
    export_link = driver.find_element(By.ID, 'Export')
    ActionChains(driver).move_to_element(export_link).pause(0.5).click(export_link).perform()
    time.sleep(1)
    try:
        driver.find_element(By.ID, 'ExportCSV').click()
    except Exception:
        driver.execute_script("var e=document.getElementById('ExportCSV'); if(e){e.click();}")
    time.sleep(2)

    driver.switch_to.default_content()
    popup_btn = None
    for _ in range(20):
        try:
            popup_btn = driver.find_element(By.CSS_SELECTOR, 'button#Export')
            if popup_btn.is_displayed():
                break
        except Exception:
            popup_btn = None
        time.sleep(0.5)
    try:
        if popup_btn:
            popup_btn.click()
        else:
            driver.execute_script("var b=document.querySelector('button#Export'); if(b) b.click();")
    except Exception:
        driver.execute_script("var b=document.querySelector('button#Export'); if(b) b.click();")

    for _ in range(40):
        after_files = {p: os.path.getmtime(p) for p in glob.glob(f"{EXPORT_DIR}/*.csv")}
        changed_files = [
            p for p, mtime in after_files.items()
            if p not in before_files or mtime > before_files.get(p, 0)
        ]
        if changed_files:
            break
        time.sleep(0.5)

    after_files = {p: os.path.getmtime(p) for p in glob.glob(f"{EXPORT_DIR}/*.csv")}
    changed_files = [
        p for p, mtime in after_files.items()
        if p not in before_files or mtime > before_files.get(p, 0)
    ]
    if not changed_files:
        print(f"  ❌ No CSV downloaded for {category}")
        return []

    csv_path = sorted(changed_files, key=os.path.getmtime)[-1]
    rows = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'Address': row.get('Address', '').strip(),
                'City': row.get('City', '').strip(),
                'Zip': row.get('Zip', '').strip(),
                '_DisplayId': row.get('MLS #', '').strip(),
                'SystemPrice': row.get('Price', '').replace('$', '').replace(',', '').strip(),
                'Class': row.get('Class', '').strip(),
                'Type': row.get('Type', '').strip(),
                'StatusDate': row.get('Status Date', '').strip(),
                'Category': category,
            })
    print(f"  ✅ Downloaded {len(rows)} {category.lower()} listings from CSV")
    return rows


def scrape_expired(driver):
    """Scrape expired via Market Monitor and CSV export"""
    print("\n🔍 Scraping EXPIRED (Market Monitor)...")
    driver.switch_to.default_content()
    driver.execute_script("if(document.getElementById('cboxOverlay')) document.getElementById('cboxOverlay').style.display='none'; if(document.getElementById('colorbox')) document.getElementById('colorbox').style.display='none';")
    try:
        driver.find_element(By.ID, 'Close').click()
        time.sleep(1)
    except:
        pass
    driver.switch_to.frame(driver.find_elements(By.TAG_NAME, 'iframe')[2])
    driver.execute_script("var db=document.getElementById('mmdaysback'); if(db){db.value='2'; db.dispatchEvent(new Event('change',{bubbles:true}));}")
    time.sleep(1)
    driver.execute_script("document.getElementById('mm_1').click();")
    print("  Clicked Market Monitor > Expired")
    time.sleep(10)
    return _export_results_csv(driver, 'EXPIRED')


def scrape_withdrawn(driver):
    """Scrape withdrawn via Quick Search and CSV export"""
    print("\n🔍 Scraping WITHDRAWN (last 7 days via Quick Search)...")
    driver.get('http://ccar.paragonrels.com/')
    time.sleep(8)
    driver.switch_to.default_content()
    driver.execute_script("if(document.getElementById('cboxOverlay')) document.getElementById('cboxOverlay').style.display='none'; if(document.getElementById('colorbox')) document.getElementById('colorbox').style.display='none';")
    try:
        driver.find_element(By.ID, 'Close').click()
        time.sleep(1)
    except:
        pass
    driver.switch_to.frame(driver.find_element(By.ID, 'HomeTab'))
    try:
        status = driver.find_element(By.ID, 'f_11__1-2-3-4-5-6-7')
        status.clear()
        status.send_keys('WD')
        time.sleep(1)
        driver.execute_script("""
            var lis = document.querySelectorAll('.ac_results li');
            for (var i = 0; i < lis.length; i++) {
                var t = lis[i].textContent || '';
                if (t.indexOf('WITHDRAWN') >= 0 || t.indexOf('WD') >= 0) { lis[i].click(); return; }
            }
        """)
        time.sleep(1)
        driver.execute_script("""
            var s = document.getElementById('fo_f_621');
            if (s) {
                s.value = '8';
                s.dispatchEvent(new Event('change', {bubbles: true}));
            }
        """)
        time.sleep(1)
        try:
            status_date_high = driver.find_element(By.ID, 'f_621_High')
            status_date_high.clear()
            status_date_high.send_keys('Today')
            time.sleep(1)
        except Exception:
            pass
        driver.find_element(By.ID, 'Search1').click()
        time.sleep(12)
    except Exception as e:
        print(f"  ❌ Quick Search fields not found: {e}")
        return []
    return _export_results_csv(driver, 'WITHDRAWN')


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

        exp_ct = len([l for l in all_leads if l.get("Category") == "EXPIRED"])
        wth_ct = len([l for l in all_leads if l.get("Category") == "WITHDRAWN"])
        print(f"\n📊 Verified counts: {exp_ct} expired, {wth_ct} withdrawn")
        
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
