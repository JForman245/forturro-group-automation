#!/usr/bin/env python3
"""
MLS Listing Sheet PDF — follows Jeff's exact workflow:
1. Open visible Chrome → login to CCAR SSO
2. Navigate to Paragon → Power Search for address
3. Click the ACTIVE listing → All Fields Detail loads
4. Click Paragon's Print button (in toolbar)
5. Click "Print" (NOT "Print+") from the submenu
6. macOS printer dialog opens
7. Click PDF button at bottom
8. Click "Save as PDF..."
9. Rename to address
10. Save to Desktop
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

APPLESCRIPT_CMD = '/Users/claw1/Desktop/MLSHelper.app/Contents/MacOS/MLSHelper'


def run_applescript(script, timeout=30):
    """Run AppleScript via MLSHelper (has Accessibility permissions)"""
    result = subprocess.run(
        [APPLESCRIPT_CMD, '-e', script],
        capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0 and result.stderr.strip():
        print(f"  AppleScript error: {result.stderr.strip()}")
    return result.returncode == 0


def get_listing_sheet(address, output_dir="/Users/claw1/Desktop"):
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    if not username or not password:
        print("❌ MLS credentials not found in .env.mls")
        return None

    # VISIBLE Chrome — not headless
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1200')

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

            # Click Email radio
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
            print("❌ SSO login failed")
            return None

        # Step 2: Navigate to Paragon
        print("🏠 Navigating to Paragon MLS...")
        driver.get('http://ccar.paragonrels.com/')
        time.sleep(15)

        # Close overlays
        try:
            driver.execute_script(
                "var el=document.getElementById('cboxOverlay');if(el)el.style.display='none';"
                "var cb=document.getElementById('colorbox');if(cb)cb.style.display='none';"
            )
        except:
            pass

        if 'paragonrels.com' not in driver.current_url:
            print(f"❌ Failed to reach Paragon")
            return None
        print("✅ On Paragon")

        # Step 3: Power Search
        print(f"🔍 Searching for: {address}")
        try:
            search_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder*='Power Search'], input[placeholder*='search'], #powerSearchInput")
            ))
            search_input.clear()
            search_input.send_keys(address)
        except TimeoutException:
            search_input = driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[type='text']")
            search_input.clear()
            search_input.send_keys(address)

        time.sleep(1)
        search_input.send_keys(Keys.RETURN)
        print("✅ Search submitted")
        time.sleep(4)

        # Step 4: Click the listing from dropdown
        print("📋 Looking for listing...")
        addr_num = address.strip().split()[0]
        clicked = False

        for status in ['ACTIVE', 'PENDING', 'WITHDRAWN', 'EXPIRED', 'SOLD']:
            try:
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(),'({status})')]")
                for el in elements:
                    text = el.text.strip()
                    if addr_num in text:
                        print(f"  Clicking: {text[:80]}")
                        el.click()
                        clicked = True
                        break
                if clicked:
                    break
                if not clicked and elements and status == 'ACTIVE':
                    print(f"  Clicking first ACTIVE: {elements[0].text[:80]}")
                    elements[0].click()
                    clicked = True
                    break
            except:
                pass

        if not clicked:
            print("❌ Could not find listing")
            return None

        # Step 5: Wait for All Fields Detail to load
        print("⏳ Waiting for listing detail to load...")
        time.sleep(10)

        for attempt in range(15):
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            if any(kw in page_text for kw in ['Asking Price', 'MLS #', 'Bedrooms', 'List Price', 'Sq Ft']):
                print("✅ Listing detail loaded")
                break
            time.sleep(2)
            print(f"  Waiting... attempt {attempt+1}")

        time.sleep(3)

        # Step 6: Switch into the search iframe to access Paragon's Print button
        print("🖨️ Clicking Paragon Print button...")
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        search_iframe = None
        for iframe in iframes:
            src = iframe.get_attribute('src') or ''
            iframe_id = iframe.get_attribute('id') or ''
            if 'Search' in src or 'listingIds' in src or iframe_id.startswith('tab1'):
                search_iframe = iframe
                break

        if search_iframe:
            driver.switch_to.frame(search_iframe)
            time.sleep(2)

        # Click the Print button in Paragon's toolbar
        # This opens a submenu with "Print" and "Print+" options
        driver.execute_script("""
            var found = false;
            // Look for the Print menu/button in the Reports toolbar
            var elements = document.querySelectorAll('a, span, button, li, div');
            for (var el of elements) {
                var text = el.textContent.trim();
                var id = el.id || '';
                var cls = el.className || '';
                // The Print button in Paragon toolbar
                if (text === 'Print' && el.offsetParent !== null && !found) {
                    el.click();
                    found = true;
                    break;
                }
            }
        """)
        time.sleep(2)

        # Step 7: Click "Print" (NOT "Print+") from the submenu
        print("  Clicking 'Print' (not Print+)...")
        driver.execute_script("""
            var items = document.querySelectorAll('a, li, span, div');
            for (var item of items) {
                var text = item.textContent.trim();
                // Match exactly "Print" not "Print+" or "Print Plus"
                if (text === 'Print' && item.offsetParent !== null) {
                    item.click();
                    break;
                }
            }
        """)
        time.sleep(5)

        # Check if a new window opened (print view)
        handles = driver.window_handles
        if len(handles) > 1:
            driver.switch_to.window(handles[-1])
            time.sleep(5)
            print(f"  Print window opened: {driver.current_url[:80]}")

        # Step 8: Use AppleScript to handle the macOS print dialog
        # First, bring Chrome to front and trigger Cmd+P
        print("  Triggering Cmd+P...")
        run_applescript('''
            tell application "Google Chrome" to activate
            delay 1
        ''')

        run_applescript('''
            tell application "System Events"
                keystroke "p" using command down
            end tell
        ''')
        time.sleep(4)

        # Step 9: Click the PDF button at bottom of print dialog
        print("  Clicking PDF button...")
        safe_name = address.replace('/', '-').replace('\\', '-').strip()

        success = run_applescript(f'''
            tell application "System Events"
                tell process "Google Chrome"
                    set frontmost to true
                    delay 1
                    
                    -- Click the PDF menu button at bottom of print dialog
                    click menu button "PDF" of sheet 1 of window 1
                    delay 1
                    
                    -- Click "Save as PDF..."
                    click menu item "Save as PDF…" of menu 1 of menu button "PDF" of sheet 1 of window 1
                    delay 2
                    
                    -- Now in Save dialog: clear filename and type the address
                    keystroke "a" using command down
                    delay 0.3
                    keystroke "{safe_name}"
                    delay 0.5
                    
                    -- Navigate to Desktop (Cmd+D)
                    keystroke "d" using command down
                    delay 1
                    
                    -- Click Save
                    click button "Save" of sheet 1 of sheet 1 of window 1
                    delay 3
                end tell
            end tell
        ''')

        if not success:
            # Try alternate approach: keyboard-only navigation
            print("  Trying keyboard fallback...")
            run_applescript(f'''
                tell application "System Events"
                    tell process "Google Chrome"
                        set frontmost to true
                        delay 1
                        
                        -- PDF button might need different accessor
                        try
                            click menu button "PDF" of sheet 1 of window 1
                        on error
                            -- Try clicking by position or tab navigation
                            key code 48 -- Tab
                            delay 0.3
                            key code 48
                            delay 0.3
                            keystroke return
                        end try
                        delay 1
                        
                        -- Save as PDF
                        try
                            click menu item "Save as PDF…" of menu 1 of menu button "PDF" of sheet 1 of window 1
                        on error
                            keystroke return
                        end try
                        delay 2
                        
                        -- Filename
                        keystroke "a" using command down
                        delay 0.2
                        keystroke "{safe_name}"
                        delay 0.5
                        
                        -- Desktop
                        keystroke "d" using command down
                        delay 1
                        
                        -- Save
                        keystroke return
                        delay 3
                    end tell
                end tell
            ''')

        # Step 10: Verify file saved
        time.sleep(5)
        pdf_path = os.path.join(output_dir, f"{safe_name}.pdf")
        if os.path.exists(pdf_path):
            size = os.path.getsize(pdf_path)
            print(f"✅ PDF saved: {pdf_path} ({size/1024:.0f} KB)")
            return pdf_path
        else:
            print(f"❌ PDF not found at {pdf_path}")
            # Check if saved with .pdf extension automatically
            pdf_path2 = os.path.join(output_dir, f"{safe_name}")
            if os.path.exists(pdf_path2):
                os.rename(pdf_path2, pdf_path)
                size = os.path.getsize(pdf_path)
                print(f"✅ PDF saved (renamed): {pdf_path} ({size/1024:.0f} KB)")
                return pdf_path
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        driver.quit()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 mls_listing_sheet_native.py '<address>'")
        sys.exit(1)
    address = ' '.join(sys.argv[1:])
    result = get_listing_sheet(address)
    if not result:
        sys.exit(1)
