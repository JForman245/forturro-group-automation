#!/usr/bin/env python3
"""
Step by step search debugging
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
from selenium.webdriver.common.keys import Keys

def test_search_step_by_step():
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    
    options = Options()
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print("🔐 Step 1: Login to CCAR...")
        driver.get('https://ccar.mysolidearth.com')
        time.sleep(3)
        
        # Login
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
        print("✅ Login completed")
        
        print("\n🚀 Step 2: Navigate to Paragon...")
        paragon_link = driver.find_element(By.CSS_SELECTOR, "a[href*='paragon']")
        paragon_link.click()
        time.sleep(5)
        
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            print("✅ Switched to Paragon tab")
        
        print(f"Current URL: {driver.current_url}")
        
        print("\n🧹 Step 3: Dismiss popups...")
        driver.execute_script("""
            if (document.getElementById('cboxOverlay')) document.getElementById('cboxOverlay').style.display='none';
            if (document.getElementById('colorbox')) document.getElementById('colorbox').style.display='none';
            if (typeof jQuery !== 'undefined' && jQuery.colorbox) jQuery.colorbox.close();
            var dialogs = document.querySelectorAll('.ui-dialog');
            dialogs.forEach(function(d) { d.style.display = 'none'; });
            var closeButtons = document.querySelectorAll('.ui-dialog-titlebar-close, [title=\"Close\"], button.close');
            closeButtons.forEach(function(btn) { try { btn.click(); } catch(e) {} });
        """)
        time.sleep(3)
        print("✅ Popups dismissed")
        
        print("\n📄 Step 4: Analyze iframes...")
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Found {len(frames)} iframes:")
        
        for i, frame in enumerate(frames):
            src = frame.get_attribute('src') or 'no src'
            print(f"  [{i}] {src}")
        
        # Try each iframe to find search functionality
        search_found = False
        for i, frame in enumerate(frames):
            if search_found:
                break
                
            try:
                print(f"\n🔍 Testing iframe {i}...")
                driver.switch_to.frame(frame)
                time.sleep(2)
                
                # Look for search elements
                search_selectors = ["#search", ".search-input", "input[name*='search']", "input[placeholder*='search']", "input[placeholder*='address']"]
                
                for selector in search_selectors:
                    try:
                        search_field = driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"   ✅ Found search field: {selector}")
                        
                        # Test if it's interactable
                        try:
                            search_field.click()
                            search_field.send_keys("TEST")
                            search_field.clear()
                            print("   ✅ Search field is interactable!")
                            search_found = True
                            break
                        except Exception as e:
                            print(f"   ❌ Not interactable: {e}")
                            
                    except:
                        continue
                
                if not search_found:
                    # Switch back to main content
                    driver.switch_to.default_content()
                    
            except Exception as e:
                print(f"   ❌ Iframe {i} failed: {e}")
                driver.switch_to.default_content()
                continue
        
        if search_found:
            print("\n🎉 SUCCESS! Found working search field")
            print("Now testing actual search...")
            
            # Clear and search for our address
            search_field.clear()
            search_field.send_keys("403 3rd Ave N")
            search_field.send_keys(Keys.RETURN)
            time.sleep(5)
            
            print("✅ Search submitted! Check browser for results...")
        else:
            print("\n❌ No working search field found in any iframe")
            
        print("\n⏸️ Browser staying open for inspection...")
        input("Press Enter to close...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    test_search_step_by_step()