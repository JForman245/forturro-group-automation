#!/usr/bin/env python3
"""
Debug Search Field Issues
Opens Paragon and analyzes what's blocking the search field
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

def debug_search_interaction():
    """Debug why search field is not interactable"""
    
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    
    # Setup visible driver for debugging
    options = Options()
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print("🔐 Logging into CCAR...")
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
        
        print("✅ Logged in, navigating to Paragon...")
        
        # Find Paragon link
        paragon_link = driver.find_element(By.CSS_SELECTOR, "a[href*='paragon']")
        paragon_link.click()
        time.sleep(5)
        
        # Switch to new tab
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        
        print("🔍 ANALYZING PARAGON INTERFACE...")
        time.sleep(5)
        
        # Dismiss popups
        driver.execute_script("""
            // Close colorbox overlays
            if (document.getElementById('cboxOverlay')) {
                document.getElementById('cboxOverlay').style.display='none';
            }
            if (document.getElementById('colorbox')) {
                document.getElementById('colorbox').style.display='none';
            }
            if (typeof jQuery !== 'undefined' && jQuery.colorbox) {
                jQuery.colorbox.close();
            }
            
            // Close jQuery UI dialogs
            var dialogs = document.querySelectorAll('.ui-dialog');
            dialogs.forEach(function(d) { d.style.display = 'none'; });
            
            // Click any close buttons
            var closeButtons = document.querySelectorAll('.ui-dialog-titlebar-close, [title="Close"], button.close');
            closeButtons.forEach(function(btn) { try { btn.click(); } catch(e) {} });
        """)
        time.sleep(2)
        
        # Check for iframes
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"📄 Found {len(frames)} iframes")
        
        for i, frame in enumerate(frames):
            src = frame.get_attribute('src') or 'no src'
            print(f"   Frame {i}: {src}")
        
        if frames:
            print("🖼️ Switching to first iframe...")
            driver.switch_to.frame(frames[0])
            time.sleep(2)
        
        # Look for search elements
        print("\n🔍 SEARCHING FOR INPUT ELEMENTS...")
        
        # Find all input elements
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(all_inputs)} input elements:")
        
        for i, inp in enumerate(all_inputs[:10]):  # Show first 10
            element_type = inp.get_attribute('type') or 'text'
            name = inp.get_attribute('name') or 'no name'
            placeholder = inp.get_attribute('placeholder') or 'no placeholder'
            element_id = inp.get_attribute('id') or 'no id'
            classes = inp.get_attribute('class') or 'no classes'
            displayed = inp.is_displayed()
            enabled = inp.is_enabled()
            
            print(f"   [{i}] type='{element_type}' name='{name}' id='{element_id}'")
            print(f"       placeholder='{placeholder}'")
            print(f"       classes='{classes}'")
            print(f"       displayed={displayed} enabled={enabled}")
            
            # Test if this could be the search field
            if any(word in name.lower() for word in ['search', 'address']) or \
               any(word in placeholder.lower() for word in ['search', 'address']) or \
               any(word in element_id.lower() for word in ['search', 'address']):
                print(f"       🎯 POTENTIAL SEARCH FIELD!")
                
                try:
                    # Test interaction
                    driver.execute_script("arguments[0].scrollIntoView();", inp)
                    time.sleep(1)
                    
                    # Check what's covering it
                    covering_element = driver.execute_script("""
                        var rect = arguments[0].getBoundingClientRect();
                        var centerX = rect.left + rect.width/2;
                        var centerY = rect.top + rect.height/2;
                        var topElement = document.elementFromPoint(centerX, centerY);
                        return topElement ? topElement.tagName + '.' + topElement.className : 'none';
                    """, inp)
                    
                    print(f"       Element at center: {covering_element}")
                    
                    if covering_element != inp.tag_name.upper():
                        print(f"       ❌ BLOCKED BY: {covering_element}")
                    else:
                        print("       ✅ Not blocked")
                        
                        # Try to click it
                        try:
                            inp.click()
                            print("       ✅ Click successful!")
                            inp.send_keys("TEST")
                            print("       ✅ Send keys successful!")
                            inp.clear()
                        except Exception as e:
                            print(f"       ❌ Interaction failed: {e}")
                    
                except Exception as e:
                    print(f"       ❌ Test failed: {e}")
            
            print()
        
        print("⏸️ Browser will stay open for manual inspection...")
        print("Check the browser window and press Enter when done...")
        input()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_search_interaction()