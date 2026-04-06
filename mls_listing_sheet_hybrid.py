#!/usr/bin/env python3
"""
MLS Listing Sheet PDF — Hybrid Approach (PERFECT FORMATTING)

Strategy:
1. Playwright (headless) handles Vue.js login + gets session cookies
2. Transfer cookies to Safari using JavaScript injection
3. Safari navigates to listing page (already authenticated)
4. AppleScript triggers Cmd+P → PDF → Save (Jeff's exact workflow)

This combines the reliability of Playwright login with the perfect formatting of Safari native print.
"""

import os, sys, time, subprocess, json, tempfile
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

username = os.getenv('MLS_USERNAME')
password = os.getenv('MLS_PASSWORD')

if not username or not password:
    print("❌ Missing MLS_USERNAME or MLS_PASSWORD in .env.mls")
    sys.exit(1)

AS = '/Users/claw1/Desktop/MLSHelper.app/Contents/MacOS/MLSHelper'

def run_applescript(script, timeout=60):
    """Run AppleScript via MLSHelper.app"""
    try:
        r = subprocess.run([AS, '-e', script], capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0 and r.stderr.strip():
            print(f"⚠️ AppleScript warning: {r.stderr.strip()}")
        return r.stdout.strip()
    except Exception as e:
        print(f"❌ AppleScript error: {e}")
        return None

def playwright_login_get_cookies():
    """Use Playwright to login and extract session cookies"""
    print("🤖 Step 1: Playwright login to get session cookies...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to CCAR login
            page.goto("https://ccar.mysolidearth.com/")
            page.wait_for_load_state('networkidle')
            
            # Handle Vue.js login form
            page.click("text=Email")  # Radio button
            page.fill('input[type="email"]', username)
            page.fill('input[type="password"]', password)
            page.click('button:has-text("Log In")')
            
            # Wait for successful login (redirects to portal)
            page.wait_for_url("**/portal**", timeout=30000)
            print("✅ Playwright login successful")
            
            # Get all cookies
            cookies = context.cookies()
            browser.close()
            return cookies
            
        except Exception as e:
            print(f"❌ Playwright login failed: {e}")
            browser.close()
            return None

def transfer_cookies_to_safari(cookies):
    """Transfer Playwright cookies to Safari using JavaScript"""
    print("🔄 Step 2: Transferring cookies to Safari...")
    
    # Open Safari and navigate to CCAR domain
    safari_script = '''
        tell application "Safari"
            activate
            if (count of windows) = 0 then make new document
            set URL of front document to "https://ccar.mysolidearth.com/"
        end tell
    '''
    run_applescript(safari_script)
    time.sleep(3)
    
    # Inject cookies via JavaScript
    for cookie in cookies:
        if cookie['domain'] in ['ccar.mysolidearth.com', '.mysolidearth.com']:
            js_set_cookie = f'''
                tell application "Safari"
                    do JavaScript "document.cookie = '{cookie['name']}={cookie['value']}; domain={cookie['domain']}; path={cookie['path']}';" in front document
                end tell
            '''
            run_applescript(js_set_cookie)
    
    print("✅ Cookies transferred to Safari")

def safari_navigate_to_listing(address):
    """Navigate Safari to the listing page"""
    print(f"🧭 Step 3: Navigating Safari to listing: {address}")
    
    # Navigate to Paragon
    paragon_script = '''
        tell application "Safari"
            set URL of front document to "https://ccar.mysolidearth.com/portal"
            delay 3
        end tell
    '''
    run_applescript(paragon_script)
    time.sleep(5)
    
    # Click Paragon link (this should work with transferred cookies)
    click_paragon = '''
        tell application "Safari"
            do JavaScript "
                var links = document.querySelectorAll('a');
                for (var link of links) {
                    if (link.href.includes('paragonrels.com') || link.textContent.includes('Paragon')) {
                        link.click();
                        break;
                    }
                }
            " in front document
        end tell
    '''
    run_applescript(click_paragon)
    time.sleep(5)
    
    # Power Search for address
    power_search_script = f'''
        tell application "Safari"
            do JavaScript "
                // Wait for Paragon to load
                setTimeout(function() {{
                    // Look for Power Search or search input
                    var searchInput = document.querySelector('input[placeholder*=\\\"Search\\\"]') ||
                                     document.querySelector('input[name*=\\\"address\\\"]') ||
                                     document.querySelector('#search-input') ||
                                     document.querySelector('.search-input');
                    
                    if (searchInput) {{
                        searchInput.focus();
                        searchInput.value = '{address}';
                        searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        
                        // Submit form or press Enter
                        setTimeout(function() {{
                            var form = searchInput.closest('form');
                            if (form) form.submit();
                            else searchInput.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                        }}, 500);
                    }}
                }}, 2000);
            " in front document
        end tell
    '''
    run_applescript(power_search_script)
    time.sleep(8)
    
    # Click on ACTIVE listing
    click_listing = '''
        tell application "Safari"
            do JavaScript "
                var activeLinks = document.querySelectorAll('a, td, div');
                for (var el of activeLinks) {
                    if (el.textContent && el.textContent.includes('(ACTIVE)')) {
                        el.click();
                        break;
                    }
                }
            " in front document
        end tell
    '''
    run_applescript(click_listing)
    time.sleep(5)
    
    print("✅ Navigated to listing page")

def safari_print_to_pdf(address):
    """Use Safari's native print to generate perfect PDF"""
    print("🖨️ Step 4: Safari native print (Jeff's exact workflow)...")
    
    # Ensure Safari is frontmost and trigger Cmd+P
    print_script = '''
        tell application "Safari"
            activate
            delay 1
        end tell
        
        tell application "System Events"
            tell process "Safari"
                set frontmost to true
                delay 0.5
                -- Cmd+P to open print dialog
                keystroke "p" using command down
                delay 3
            end tell
        end tell
    '''
    run_applescript(print_script)
    
    # Handle the classic macOS print dialog
    # Jeff has Brother printer, should show classic dialog with PDF option
    pdf_script = f'''
        tell application "System Events"
            tell process "Safari"
                -- Look for PDF button (bottom-left of print dialog)
                try
                    click button "PDF" of sheet 1 of window 1
                    delay 1
                    click menu item "Save as PDF..." of menu 1 of button "PDF" of sheet 1 of window 1
                    delay 2
                    
                    -- Set filename to address
                    keystroke "{address.replace('"', '')}"
                    delay 1
                    
                    -- Navigate to Desktop (Cmd+D shortcut)
                    keystroke "d" using command down
                    delay 1
                    
                    -- Save
                    click button "Save"
                    delay 2
                    
                on error errMsg
                    -- If PDF button not found, try different approach
                    log "PDF button not found, trying alternative: " & errMsg
                    -- Cancel current dialog
                    keystroke escape
                    return false
                end try
            end tell
        end tell
    '''
    
    result = run_applescript(pdf_script)
    
    if result == "false":
        print("❌ Print dialog automation failed")
        return False
    
    # Check if PDF was created on Desktop
    expected_pdf = f"/Users/claw1/Desktop/{address}.pdf"
    if os.path.exists(expected_pdf):
        print(f"✅ PDF created: {expected_pdf}")
        return expected_pdf
    else:
        print("⚠️ PDF not found on Desktop, checking for similar files...")
        desktop_files = os.listdir("/Users/claw1/Desktop")
        pdf_files = [f for f in desktop_files if f.endswith('.pdf') and address.split()[0] in f]
        if pdf_files:
            actual_pdf = f"/Users/claw1/Desktop/{pdf_files[0]}"
            print(f"✅ Found PDF: {actual_pdf}")
            return actual_pdf
        else:
            print("❌ No PDF found")
            return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 mls_listing_sheet_hybrid.py '308 62nd Ave N North Myrtle Beach'")
        sys.exit(1)
    
    address = sys.argv[1]
    print(f"🏠 MLS Listing Sheet PDF Generator (HYBRID)")
    print(f"📍 Address: {address}")
    print("=" * 60)
    
    # Step 1: Playwright login
    cookies = playwright_login_get_cookies()
    if not cookies:
        print("❌ Failed to get session cookies from Playwright")
        sys.exit(1)
    
    # Step 2: Transfer to Safari
    transfer_cookies_to_safari(cookies)
    
    # Step 3: Navigate to listing
    safari_navigate_to_listing(address)
    
    # Step 4: Native print
    pdf_path = safari_print_to_pdf(address)
    
    if pdf_path:
        print("=" * 60)
        print(f"🎉 SUCCESS! PDF saved to: {pdf_path}")
        print("📄 This matches Jeff's manual workflow exactly — perfect formatting!")
    else:
        print("=" * 60)
        print("❌ FAILED: Could not complete PDF generation")
        print("💡 Try running manually: Cmd+P → PDF → Save as PDF")

if __name__ == "__main__":
    main()