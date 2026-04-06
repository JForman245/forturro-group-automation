#!/usr/bin/env python3
"""Debug: what happens after clicking Associated Docs"""

import os, sys, time
sys.stdout.reconfigure(line_buffering=True)

from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

username = os.getenv('MLS_USERNAME')
password = os.getenv('MLS_PASSWORD')

options = Options()
options.add_argument('--window-size=1920,1080')
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)

try:
    # Login
    print("🔐 Logging in...")
    driver.get('https://ccar.mysolidearth.com')
    time.sleep(3)
    radios = driver.find_elements(By.CSS_SELECTOR, ".v-radio")
    if len(radios) > 1: radios[1].click()
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))).send_keys(username)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(10)

    # Paragon
    print("🚀 Going to Paragon...")
    driver.find_element(By.CSS_SELECTOR, "a[href*='paragon']").click()
    time.sleep(5)
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
    time.sleep(5)
    
    driver.execute_script("""
        var o = document.getElementById('cboxOverlay'); if (o) o.remove();
        var c = document.getElementById('colorbox'); if (c) c.remove();
        if (typeof jQuery !== 'undefined' && jQuery.colorbox) jQuery.colorbox.close();
        document.querySelectorAll('.ui-dialog, .ui-widget-overlay').forEach(function(d) { d.remove(); });
    """)
    time.sleep(3)

    # Power Search
    print("🔍 Power Search...")
    driver.switch_to.default_content()
    ps = driver.find_element(By.CSS_SELECTOR, "input.select2-search__field[placeholder='POWER SEARCH']")
    driver.execute_script("arguments[0].focus(); arguments[0].click();", ps)
    time.sleep(1)
    driver.execute_script("arguments[0].value = '';", ps)
    for c in "403 3rd Ave N":
        ps.send_keys(c)
        time.sleep(0.05)
    time.sleep(8)

    # Click ACTIVE
    for opt in driver.find_elements(By.CSS_SELECTOR, ".select2-results__option"):
        t = opt.text.strip()
        if '(ACTIVE)' in t and t[0].isdigit():
            print(f"🎯 Clicking: {t[:60]}")
            opt.click()
            break
    time.sleep(10)

    # Switch to search frame
    driver.switch_to.default_content()
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    search_frame_idx = None
    for i, f in enumerate(frames):
        try:
            src = f.get_attribute('src') or ''
            if 'Search' in src and 'listingIds' in src:
                search_frame_idx = i
                driver.switch_to.frame(f)
                print(f"✅ In search frame [{i}]")
                break
        except:
            continue
    
    # Find the Associated Docs link
    print("\n📋 Finding Associated Docs...")
    ad_info = driver.execute_script("""
        var el = document.getElementById('v_associated_docs');
        if (!el) return {found: false};
        
        return {
            found: true,
            tag: el.tagName,
            text: el.textContent.trim(),
            href: el.href || '',
            onclick: el.getAttribute('onclick') || '',
            cls: el.className || '',
            parent_tag: el.parentElement ? el.parentElement.tagName : '',
            parent_cls: el.parentElement ? el.parentElement.className : '',
            parent_id: el.parentElement ? el.parentElement.id : ''
        };
    """)
    print(f"Associated Docs element: {ad_info}")
    
    # Take screenshot BEFORE clicking
    driver.save_screenshot('/tmp/before_assoc_docs.png')
    print("📸 Screenshot saved: /tmp/before_assoc_docs.png")
    
    # Count windows before
    windows_before = len(driver.window_handles)
    print(f"Windows before click: {windows_before}")
    
    # Click Associated Docs
    print("\n🖱️ Clicking Associated Docs...")
    driver.execute_script("document.getElementById('v_associated_docs').click();")
    time.sleep(8)
    
    # Check what changed
    windows_after = len(driver.window_handles)
    print(f"Windows after click: {windows_after}")
    
    if windows_after > windows_before:
        print("🎉 NEW WINDOW/TAB OPENED!")
        new_handle = [h for h in driver.window_handles if h != driver.current_window_handle][-1]
        driver.switch_to.window(new_handle)
        print(f"   URL: {driver.current_url}")
        print(f"   Title: {driver.title}")
        
        # Screenshot new page
        driver.save_screenshot('/tmp/assoc_docs_page.png')
        print("📸 Screenshot: /tmp/assoc_docs_page.png")
        
        # Dump page content
        page_text = driver.execute_script("return document.body.innerText.substring(0, 3000);")
        print(f"\nPage text:\n{page_text[:2000]}")
        
        # Find all links
        links = driver.execute_script("""
            var results = [];
            var links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {
                var text = (links[i].textContent || '').trim();
                var href = links[i].href || '';
                if (text && text.length > 2) {
                    results.push({text: text.substring(0, 80), href: href.substring(0, 100)});
                }
            }
            return results;
        """)
        print(f"\nLinks on page: {len(links)}")
        for l in links[:20]:
            print(f"   {l['text']} -> {l['href']}")
    else:
        print("⚠️ No new window opened")
        
        # Check if content changed in the frame
        driver.switch_to.default_content()
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Frames now: {len(frames)}")
        for i, f in enumerate(frames):
            try:
                src = f.get_attribute('src') or 'no src'
                print(f"  [{i}] {src[:80]}")
            except:
                print(f"  [{i}] STALE")
        
        # Check for new iframes or popups
        if search_frame_idx is not None:
            driver.switch_to.frame(frames[search_frame_idx])
            
            # Check for sub-iframes
            sub_frames = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"\nSub-iframes in search frame: {len(sub_frames)}")
            for i, sf in enumerate(sub_frames):
                try:
                    src = sf.get_attribute('src') or 'no src'
                    print(f"  Sub [{i}] {src[:80]}")
                except:
                    pass
            
            # Check for modals/dialogs
            modals = driver.execute_script("""
                var results = [];
                var dialogs = document.querySelectorAll('.ui-dialog, .modal, [role="dialog"], .popup, .overlay, [class*="modal"], [class*="dialog"]');
                for (var i = 0; i < dialogs.length; i++) {
                    var d = dialogs[i];
                    var visible = d.offsetParent !== null || d.style.display !== 'none';
                    results.push({
                        tag: d.tagName,
                        cls: d.className.substring(0, 80),
                        id: d.id || '',
                        visible: visible,
                        text: d.textContent.substring(0, 200).trim()
                    });
                }
                return results;
            """)
            print(f"\nModals/dialogs: {len(modals)}")
            for m in modals:
                print(f"  <{m['tag']}> id='{m['id']}' visible={m['visible']} class='{m['cls'][:40]}'")
                if m['text']:
                    print(f"    text: {m['text'][:100]}")
        
        # Take screenshot AFTER
        driver.switch_to.default_content()
        driver.save_screenshot('/tmp/after_assoc_docs.png')
        print("📸 Screenshot after: /tmp/after_assoc_docs.png")

except Exception as e:
    print(f"❌ {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("Done")
