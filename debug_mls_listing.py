#!/usr/bin/env python3
"""
Debug MLS Listing Page
Opens the listing page and shows what elements are available
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

def debug_listing_page():
    """Login and navigate to listing, then show available elements"""
    
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    
    # Setup driver for debugging (NOT headless)
    options = Options()
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print("🔐 Logging in...")
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
        
        print("✅ Logged in - now navigate manually to 403 3rd Ave N listing")
        print("📋 Instructions:")
        print("1. Click Paragon link")
        print("2. Search for '403 3rd Ave N'") 
        print("3. Open the listing detail page")
        print("4. Press Enter here when you're on the listing page...")
        
        input("Press Enter when on the listing page...")
        
        print("\n🔍 ANALYZING LISTING PAGE ELEMENTS...")
        print("=" * 60)
        
        # Find all images with titles (likely toolbar icons)
        images_with_titles = driver.find_elements(By.XPATH, "//img[@title]")
        print(f"📸 Found {len(images_with_titles)} images with titles:")
        for i, img in enumerate(images_with_titles[:10]):  # Show first 10
            title = img.get_attribute('title')
            src = img.get_attribute('src')
            print(f"   [{i+1}] Title: '{title}' | Src: {src}")
            
            if 'doc' in title.lower() or 'associated' in title.lower():
                print(f"      🎯 POTENTIAL TARGET: {title}")
        
        print("\n📄 Looking for document-related elements:")
        doc_related = driver.find_elements(By.XPATH, "//img[contains(@title, 'Doc')] | //a[contains(text(), 'Doc')] | //span[contains(text(), 'Doc')]")
        for element in doc_related:
            tag = element.tag_name
            text = element.text or element.get_attribute('title') or element.get_attribute('alt')
            print(f"   {tag}: '{text}'")
        
        print("\n🔗 All clickable elements with 'doc' or 'file':")
        clickable_docs = driver.find_elements(By.XPATH, "//*[@onclick or @href][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'doc') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'file')]")
        for element in clickable_docs:
            tag = element.tag_name
            text = element.text or element.get_attribute('title') or element.get_attribute('onclick') or element.get_attribute('href')
            print(f"   {tag}: '{text[:50]}...'")
        
        print("\n⏸️ Browser will stay open for manual inspection...")
        print("Press Ctrl+C to close when done.")
        
        # Keep browser open for manual inspection
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Closing browser...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_listing_page()