#!/usr/bin/env python3
"""
Debug Search Results - See what's actually returned from search
"""

import os
import time
from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def debug_search_results():
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    
    options = Options()
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        # Login to CCAR
        print("🔐 Logging in...")
        driver.get('https://ccar.mysolidearth.com')
        time.sleep(3)
        
        radio_containers = driver.find_elements(By.CSS_SELECTOR, ".v-radio")
        if len(radio_containers) > 1:
            radio_containers[1].click()
            time.sleep(2)
        
        username_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'][name='email']"))
        )
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        time.sleep(10)
        
        # Navigate to Paragon
        print("🚀 Going to Paragon...")
        paragon_link = driver.find_element(By.CSS_SELECTOR, "a[href*='paragon']")
        paragon_link.click()
        time.sleep(5)
        
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        
        # Dismiss popups
        time.sleep(3)
        driver.execute_script("""
            if (document.getElementById('cboxOverlay')) document.getElementById('cboxOverlay').style.display='none';
            if (document.getElementById('colorbox')) document.getElementById('colorbox').style.display='none';
            if (typeof jQuery !== 'undefined' && jQuery.colorbox) jQuery.colorbox.close();
            var dialogs = document.querySelectorAll('.ui-dialog');
            dialogs.forEach(function(d) { d.style.display = 'none'; });
            var closeButtons = document.querySelectorAll('.ui-dialog-titlebar-close, [title=\"Close\"], button.close');
            closeButtons.forEach(function(btn) { try { btn.click(); } catch(e) {} });
        """)
        time.sleep(2)
        
        # Switch to main iframe
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        if len(frames) >= 3:
            driver.switch_to.frame(frames[2])
            time.sleep(3)
        
        # Search
        print("🔍 Searching...")
        search_field = driver.find_element(By.CSS_SELECTOR, "input[name*='search']")
        
        driver.execute_script("arguments[0].value = '';", search_field)
        driver.execute_script("arguments[0].focus();", search_field)
        driver.execute_script("arguments[0].value = '403 3rd Ave N';", search_field)
        driver.execute_script("""
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, search_field)
        
        driver.execute_script("""
            arguments[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', which: 13, keyCode: 13 }));
        """, search_field)
        
        time.sleep(8)  # Wait for results
        
        print("\n📊 ANALYZING SEARCH RESULTS:")
        print("="*60)
        
        # Find all table rows
        result_rows = driver.find_elements(By.CSS_SELECTOR, "tr")
        print(f"Found {len(result_rows)} table rows total")
        
        for i, row in enumerate(result_rows[:15]):  # Show first 15
            row_text = row.text.strip()
            if row_text:  # Only show rows with text
                print(f"\n[{i}] Row text ({len(row_text)} chars):")
                print(f"    '{row_text[:200]}{'...' if len(row_text) > 200 else ''}'")
                
                # Check for links in this row
                links = row.find_elements(By.TAG_NAME, "a")
                if links:
                    print(f"    Links in row: {len(links)}")
                    for j, link in enumerate(links):
                        link_text = link.text.strip()
                        href = link.get_attribute('href') or 'no href'
                        print(f"      [{j}] '{link_text}' -> {href[:80]}{'...' if len(href) > 80 else ''}")
                
                # Check if this row contains our search term
                if '403' in row_text or '3rd' in row_text:
                    print(f"    🎯 POTENTIAL MATCH! Contains search terms")
        
        print("\n🔍 Looking for any data rows with property info...")
        
        # Look for rows that look like property data (MLS numbers, prices, addresses)
        for i, row in enumerate(result_rows):
            row_text = row.text.strip()
            # Look for patterns that suggest property data
            if any(pattern in row_text for pattern in ['$', 'MLS', 'Ave', 'St', 'Rd', 'Dr', 'Ct']):
                print(f"\n[{i}] PROPERTY DATA ROW:")
                print(f"    '{row_text}'")
                
                # Check if clickable
                try:
                    is_clickable = row.is_enabled() and row.is_displayed()
                    print(f"    Clickable: {is_clickable}")
                except:
                    print("    Clickable: unknown")
        
        print(f"\n⏸️ Browser staying open for manual inspection...")
        input("Press Enter to close...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_search_results()