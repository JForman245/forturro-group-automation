#!/usr/bin/env python3
"""
Manual MLS Debug - No Input Required
Opens browser, logs in, then waits for manual navigation with periodic element scanning
"""

import os
import sys
import time
from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def scan_for_docs_elements(driver):
    """Scan current page for document-related elements"""
    try:
        print("\n🔍 SCANNING FOR DOCUMENT ELEMENTS...")
        print("=" * 50)
        
        # Check if we're on a listing page (look for listing indicators)
        listing_indicators = driver.find_elements(By.XPATH, "//text()[contains(., 'MLS')] | //text()[contains(., 'Listing')] | //text()[contains(., 'Property')]")
        if not listing_indicators:
            print("⏳ Not on listing page yet - waiting for navigation...")
            return False
        
        # Find all images with titles
        images_with_titles = driver.find_elements(By.XPATH, "//img[@title]")
        print(f"📸 Images with titles: {len(images_with_titles)}")
        
        doc_found = False
        for i, img in enumerate(images_with_titles):
            title = img.get_attribute('title') or ''
            src = img.get_attribute('src') or ''
            
            if title:
                print(f"   [{i+1}] '{title}' | {src}")
                
                if 'doc' in title.lower() or 'associated' in title.lower() or 'file' in title.lower():
                    print(f"      🎯 TARGET FOUND: {title}")
                    doc_found = True
        
        # Look for clickable document elements
        print("\n🔗 Clickable document elements:")
        clickable_docs = driver.find_elements(By.XPATH, 
            "//a[contains(@title, 'Doc')] | //button[contains(@title, 'Doc')] | //img[contains(@title, 'Doc')]")
        
        for element in clickable_docs:
            tag = element.tag_name
            title = element.get_attribute('title') or ''
            onclick = element.get_attribute('onclick') or ''
            href = element.get_attribute('href') or ''
            
            print(f"   {tag}: title='{title}'")
            if onclick:
                print(f"        onclick='{onclick[:50]}...'")
            if href:
                print(f"        href='{href[:50]}...'")
            
            doc_found = True
        
        if doc_found:
            print("\n✅ FOUND DOCUMENT ELEMENTS!")
            return True
        else:
            print("⏳ No document elements found yet...")
            return False
            
    except Exception as e:
        print(f"❌ Scan error: {e}")
        return False

def debug_with_periodic_scanning():
    """Login and periodically scan for document elements"""
    
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    
    # Setup driver (visible for manual navigation)
    options = Options()
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print("🔐 Logging into CCAR...")
        driver.get('https://ccar.mysolidearth.com')
        time.sleep(3)
        
        # Login process
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
        
        print("✅ Logged in successfully!")
        print("\n📋 MANUAL NAVIGATION INSTRUCTIONS:")
        print("1. Click the Paragon link in the browser")
        print("2. Search for '403 3rd Ave N'")
        print("3. Click on the listing to open the detail page")
        print("\n🤖 I'll automatically scan for document elements every 10 seconds...")
        print("   Once you're on the listing page, I'll find the Associated Docs icon!")
        
        # Periodic scanning for 5 minutes
        scan_count = 0
        max_scans = 30  # 5 minutes
        
        while scan_count < max_scans:
            scan_count += 1
            print(f"\n[Scan {scan_count}/{max_scans}] Current URL: {driver.current_url}")
            
            if scan_for_docs_elements(driver):
                print("\n🎉 SUCCESS! Found document elements. Check the output above for exact selectors.")
                print("\n⏸️ Browser will stay open for 60 seconds for manual inspection...")
                time.sleep(60)
                break
            
            # Wait 10 seconds before next scan
            time.sleep(10)
        else:
            print("\n⏰ Scan timeout reached. Browser will close.")
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted - closing browser...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("🧹 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    debug_with_periodic_scanning()