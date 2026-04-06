#!/usr/bin/env python3
"""Quick debug: see what's in the search results grid after Power Search"""

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
    
    # Remove overlays
    driver.execute_script("""
        var overlay = document.getElementById('cboxOverlay'); if (overlay) overlay.remove();
        var colorbox = document.getElementById('colorbox'); if (colorbox) colorbox.remove();
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

    # Click ACTIVE option
    options_els = driver.find_elements(By.CSS_SELECTOR, ".select2-results__option")
    for opt in options_els:
        t = opt.text.strip()
        if '(ACTIVE)' in t and t[0].isdigit():
            print(f"🎯 Clicking: {t[:60]}")
            opt.click()
            break
    time.sleep(10)

    # Switch to search frame
    print("\n📊 ANALYZING SEARCH RESULTS FRAME:")
    driver.switch_to.default_content()
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for i, f in enumerate(frames):
        try:
            src = f.get_attribute('src') or 'no src'
            if 'Search' in src and 'listingIds' in src:
                driver.switch_to.frame(f)
                print(f"Switched to frame [{i}]: {src[:80]}")
                break
        except:
            continue
    
    time.sleep(3)
    
    # Dump EVERYTHING in the grid area
    grid_html = driver.execute_script("""
        // Look for jqGrid or any table with data
        var grid = document.querySelector('.ui-jqgrid, #gview_grid, table.ui-jqgrid-btable, table');
        if (grid) return grid.outerHTML.substring(0, 5000);
        return document.body.innerHTML.substring(0, 5000);
    """)
    print(f"\nGrid HTML (first 3000):\n{grid_html[:3000]}")
    
    # Check all TR elements
    print("\n\nAll TR elements:")
    trs = driver.find_elements(By.TAG_NAME, "tr")
    for i, tr in enumerate(trs[:20]):
        text = tr.text.strip()
        cls = tr.get_attribute('class') or ''
        rid = tr.get_attribute('id') or ''
        print(f"  [{i}] class='{cls}' id='{rid}' text='{text[:100]}'")
    
    # Check for clickable elements in the data area
    print("\n\nClickable data elements:")
    clickables = driver.execute_script("""
        var results = [];
        // Check table cells
        var tds = document.querySelectorAll('td');
        for (var i = 0; i < Math.min(tds.length, 30); i++) {
            var td = tds[i];
            var text = (td.textContent || '').trim();
            if (text && text.length > 2) {
                results.push({tag: 'td', text: text.substring(0, 60), cls: td.className || ''});
            }
        }
        return results;
    """)
    for c in clickables[:20]:
        print(f"  <{c['tag']}> class='{c['cls'][:40]}' text='{c['text']}'")

except Exception as e:
    print(f"❌ {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("Done")
