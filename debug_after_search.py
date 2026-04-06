#!/usr/bin/env python3
"""
Debug After Search - See what happens after search submission
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

def debug_after_search():
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    
    options = Options()
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        # Login and navigate (same as working code)
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
            var closeButtons = document.querySelectorAll('.ui-dialog-titlebar-close, [title="Close"], button.close');
            closeButtons.forEach(function(btn) { try { btn.click(); } catch(e) {} });
        """)
        time.sleep(2)
        
        # Switch to main iframe
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        if len(frames) >= 3:
            driver.switch_to.frame(frames[2])
            time.sleep(3)
        
        print("🔍 Performing search...")
        search_field = driver.find_element(By.CSS_SELECTOR, "input[name*='search']")
        
        # Search using JavaScript
        driver.execute_script("arguments[0].value = '';", search_field)
        driver.execute_script("arguments[0].focus();", search_field)
        driver.execute_script("arguments[0].value = '403 3rd Ave N';", search_field)
        driver.execute_script("""
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, search_field)
        
        # Submit form
        try:
            form = search_field.find_element(By.XPATH, "./ancestor::form[1]")
            driver.execute_script("arguments[0].submit();", form)
            print("✅ Form submitted")
        except:
            print("⚠️ Form submit failed")
        
        time.sleep(10)  # Wait longer for page change
        
        print("\n📊 ANALYZING POST-SEARCH PAGE:")
        print("="*60)
        
        # Check basic page info
        current_url = driver.current_url
        page_title = driver.title
        print(f"URL: {current_url}")
        print(f"Title: {page_title}")
        
        # Check if we're in a different iframe now
        try:
            driver.switch_to.default_content()
            frames_after = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"\nFrames after search: {len(frames_after)}")
            
            for i, frame in enumerate(frames_after):
                src = frame.get_attribute('src') or 'no src'
                print(f"  [{i}] {src}")
        except:
            pass
        
        # Try each iframe to find search results
        for i in range(len(frames_after)):
            try:
                print(f"\n🔍 Checking iframe {i} for results...")
                driver.switch_to.default_content()
                driver.switch_to.frame(frames_after[i])
                time.sleep(2)
                
                # Look for tables
                tables = driver.find_elements(By.TAG_NAME, "table")
                print(f"   Tables found: {len(tables)}")
                
                # Look for rows with data
                rows = driver.find_elements(By.CSS_SELECTOR, "tr")
                data_rows = 0
                
                for row in rows[:10]:  # Check first 10 rows
                    row_text = row.text.strip()
                    if row_text and len(row_text) > 10:  # Substantial content
                        data_rows += 1
                        if '403' in row_text or '3rd' in row_text or any(term in row_text for term in ['$', 'MLS', 'Bed', 'Bath']):
                            print(f"   🎯 POTENTIAL RESULT ROW: '{row_text[:100]}...'")
                
                print(f"   Data rows found: {data_rows}")
                
                # Look for common search result elements
                result_indicators = driver.find_elements(By.XPATH, "//*[contains(text(), 'result') or contains(text(), 'listing') or contains(text(), 'property')]")
                if result_indicators:
                    print(f"   Result indicators: {len(result_indicators)}")
                    for ind in result_indicators[:3]:
                        print(f"     '{ind.text.strip()[:50]}...'")
                        
            except Exception as e:
                print(f"   Error checking iframe {i}: {e}")
                continue
        
        print("\n⏸️ Analysis complete. Browser staying open for manual inspection...")
        input("Press Enter to close...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_after_search()