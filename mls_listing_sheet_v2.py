#!/usr/bin/env python3
"""
Pull an MLS listing sheet PDF from CCAR Paragon 5
Uses visible browser + macOS native print dialog (matches Jeff's workflow exactly)

Steps:
1. Open visible Chrome → login to CCAR SSO
2. Navigate to Paragon → Power Search for address
3. Click the ACTIVE listing → All Fields Detail loads
4. Cmd+P → macOS print dialog opens
5. AppleScript clicks PDF → Save as PDF → rename → save to Desktop
"""

import os, sys, time, subprocess
from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options


def save_via_print_dialog(filename, save_dir="/Users/claw1/Desktop"):
    """Use AppleScript to interact with macOS print dialog: PDF → Save as PDF → rename → save"""
    
    filepath = os.path.join(save_dir, filename)
    
    # Wait for print dialog to appear, click PDF menu, Save as PDF, set filename, save
    applescript = f'''
    tell application "System Events"
        -- Wait for print dialog
        delay 2
        
        -- Click the "PDF" dropdown button at bottom-left of print dialog
        tell process "Google Chrome"
            set frontmost to true
            delay 0.5
            
            -- Click the PDF popup button
            try
                click menu button "PDF" of sheet 1 of window 1
                delay 1
            on error
                -- Try alternate: look for PDF button
                try
                    click pop up button 1 of sheet 1 of window 1
                    delay 1
                end try
            end try
            
            -- Click "Save as PDF..." menu item
            try
                click menu item "Save as PDF…" of menu 1 of menu button "PDF" of sheet 1 of window 1
                delay 2
            on error
                try
                    click menu item "Save as PDF…" of menu of menu button "PDF" of sheet 1 of window 1
                    delay 2
                end try
            end try
            
            -- Now in the Save dialog — set filename
            delay 1
            
            -- Clear the current filename and type the new one
            keystroke "a" using command down
            delay 0.3
            keystroke "{filename.replace('.pdf', '')}"
            delay 0.5
            
            -- Navigate to Desktop using Cmd+D
            keystroke "d" using command down
            delay 1
            
            -- Click Save
            click button "Save" of sheet 1 of sheet 1 of window 1
            delay 3
            
        end tell
    end tell
    '''
    
    result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"  AppleScript error: {result.stderr}")
        # Try simpler keyboard-based approach as fallback
        return save_via_keyboard(filename, save_dir)
    
    # Verify the file was saved
    time.sleep(2)
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ PDF saved: {filepath} ({size/1024:.0f} KB)")
        return filepath
    else:
        print("  AppleScript method didn't produce file, trying keyboard fallback...")
        return save_via_keyboard(filename, save_dir)


def save_via_keyboard(filename, save_dir="/Users/claw1/Desktop"):
    """Fallback: use keyboard shortcuts to navigate print dialog"""
    filepath = os.path.join(save_dir, filename)
    
    applescript = f'''
    tell application "System Events"
        tell process "Google Chrome"
            set frontmost to true
            delay 1
            
            -- In print dialog, press Cmd+P might already be done
            -- Navigate to PDF button using keyboard
            -- On macOS, the PDF button is accessible
            
            -- Try: click the PDF menu button by position or accessibility
            try
                -- Look for any sheet on the front window
                set theSheet to sheet 1 of window 1
                
                -- Find and click the PDF menu button
                set pdfButton to menu button "PDF" of theSheet
                click pdfButton
                delay 1
                
                -- Click "Save as PDF..."
                click menu item "Save as PDF…" of menu 1 of pdfButton  
                delay 2
                
                -- Set filename
                keystroke "a" using {{command down}}
                delay 0.2
                keystroke "{filename.replace('.pdf', '')}"
                delay 0.5
                
                -- Go to Desktop
                keystroke "d" using {{command down}}
                delay 1
                
                -- Save
                keystroke return
                delay 3
                
            end try
        end tell
    end tell
    '''
    
    result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True, timeout=30)
    
    time.sleep(3)
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ PDF saved: {filepath} ({size/1024:.0f} KB)")
        return filepath
    
    print(f"❌ Could not save PDF to {filepath}")
    return None


def get_listing_sheet(address, output_dir="/Users/claw1/Desktop"):
    """Login to Paragon MLS, search for address, print listing sheet via native macOS dialog"""
    
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    
    if not username or not password:
        print("❌ MLS credentials not found in .env.mls")
        return None
    
    # Setup VISIBLE Chrome (not headless — need native print dialog)
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1200')
    options.add_argument('--disable-gpu')
    # Explicitly NOT headless
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        # Step 1: Login via SSO
        print("🔑 Logging into MLS...")
        driver.get('https://ccar.mysolidearth.com')
        time.sleep(5)
        
        try:
            wait.until(EC.presence_of_element_located((By.NAME, 'member_login_id')))
            time.sleep(2)
            
            # Click "Email" radio button
            driver.execute_script("""
                var radios = document.querySelectorAll('.v-radio');
                for (var r of radios) {
                    if (r.textContent.includes('Email')) {
                        r.querySelector('input').click();
                        break;
                    }
                }
            """)
            time.sleep(2)
            
            email_field = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            email_field.send_keys(username)
            password_field.send_keys(password)
            
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            wait.until(EC.url_changes(driver.current_url))
            time.sleep(3)
            print("✅ SSO login successful")
        except TimeoutException:
            print("❌ SSO login failed - timeout")
            return None
        
        # Step 2: Navigate to Paragon
        print("🏠 Navigating to Paragon MLS...")
        driver.get('http://ccar.paragonrels.com/')
        time.sleep(15)
        
        # Close any overlay/popup
        try:
            driver.execute_script(
                "var el = document.getElementById('cboxOverlay'); if(el) el.style.display='none';"
                "var cb = document.getElementById('colorbox'); if(cb) cb.style.display='none';"
            )
        except:
            pass
        
        if 'paragonrels.com' not in driver.current_url:
            print(f"❌ Failed to reach Paragon. URL: {driver.current_url}")
            return None
        print(f"✅ On Paragon: {driver.current_url}")
        
        # Step 3: Power Search
        print(f"🔍 Searching for: {address}")
        try:
            search_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder*='Power Search'], input[placeholder*='search'], input.power-search, #powerSearchInput")
            ))
            search_input.clear()
            search_input.send_keys(address)
            time.sleep(1)
            search_input.send_keys(Keys.RETURN)
            print("✅ Search submitted")
        except TimeoutException:
            try:
                search_input = driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[type='text']")
                search_input.clear()
                search_input.send_keys(address)
                search_input.send_keys(Keys.RETURN)
                print("✅ Search submitted (alternate)")
            except:
                print("❌ Could not find search field")
                return None
        
        # Step 4: Click the ACTIVE listing from dropdown
        time.sleep(4)
        print("📋 Looking for listing in dropdown...")
        clicked = False
        
        try:
            elements = driver.find_elements(By.XPATH, "//*[contains(text(),'(ACTIVE)')]")
            if elements:
                for el in elements:
                    text = el.text.strip()
                    if '(ACTIVE)' in text:
                        # Match the street number from address
                        addr_num = address.strip().split()[0]
                        if addr_num in text:
                            print(f"  Clicking: {text[:80]}")
                            el.click()
                            clicked = True
                            break
                if not clicked and elements:
                    print(f"  Clicking first ACTIVE: {elements[0].text[:80]}")
                    elements[0].click()
                    clicked = True
        except Exception as e:
            print(f"  Search error: {e}")
        
        if not clicked:
            # Try any listing status
            try:
                results = driver.find_elements(By.XPATH, 
                    "//*[contains(text(),'ACTIVE') or contains(text(),'WITHDRAWN') or contains(text(),'EXPIRED') or contains(text(),'PENDING') or contains(text(),'SOLD')]")
                for r in results:
                    text = r.text.strip()
                    addr_num = address.strip().split()[0]
                    if addr_num in text:
                        print(f"  Clicking: {text[:80]}")
                        r.click()
                        clicked = True
                        break
            except:
                pass
        
        if not clicked:
            print("❌ Could not find listing in dropdown")
            driver.save_screenshot('/tmp/mls_debug.png')
            return None
        
        # Step 5: Wait for All Fields Detail to load
        print("⏳ Waiting for listing detail to load...")
        time.sleep(10)
        
        # Verify listing loaded by checking page content
        for attempt in range(10):
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            if any(kw in page_text for kw in ['Asking Price', 'MLS #', 'Bedrooms', 'ALL FIELDS', 'List Price']):
                print("✅ Listing detail loaded")
                break
            time.sleep(2)
            print(f"  Waiting... attempt {attempt+1}")
        
        # Extra wait for images and full render
        time.sleep(5)
        
        # Step 6: Trigger Cmd+P (native print dialog)
        print("🖨️ Opening print dialog (Cmd+P)...")
        
        # Use AppleScript to send Cmd+P to Chrome
        subprocess.run(['osascript', '-e', '''
            tell application "Google Chrome" to activate
            delay 0.5
            tell application "System Events"
                keystroke "p" using command down
            end tell
        '''], capture_output=True, text=True, timeout=10)
        
        time.sleep(3)
        
        # Step 7: Use AppleScript to click PDF → Save as PDF → rename → save
        safe_name = address.replace('/', '-').replace('\\', '-').strip() + '.pdf'
        print(f"💾 Saving as: {safe_name}")
        
        result = save_via_print_dialog(safe_name, output_dir)
        
        if result:
            return result
        
        # If print dialog approach failed, try one more time
        print("  Retrying print dialog...")
        time.sleep(2)
        result = save_via_print_dialog(safe_name, output_dir)
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 mls_listing_sheet_v2.py '<address>'")
        sys.exit(1)
    
    address = ' '.join(sys.argv[1:])
    result = get_listing_sheet(address)
    if not result:
        sys.exit(1)
