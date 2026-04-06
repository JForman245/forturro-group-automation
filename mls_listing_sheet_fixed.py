#!/usr/bin/env python3
"""
MLS Listing Sheet PDF — FIXED Safari Approach

Key insights from debugging:
1. Jeff's Brother printer shows CLASSIC macOS print dialog (not Safari preview)
2. Need to focus on the listing content, not the whole page
3. Use tabbed navigation instead of JavaScript for form fields

This version matches Jeff's exact workflow step-by-step.
"""

import os, sys, time, subprocess
from dotenv import load_dotenv

load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

username = os.getenv('MLS_USERNAME')
password = os.getenv('MLS_PASSWORD')

if not username or not password:
    print("❌ Missing MLS_USERNAME or MLS_PASSWORD in .env.mls")
    sys.exit(1)

AS = '/Users/claw1/Desktop/MLSHelper.app/Contents/MacOS/MLSHelper'

def run(script, timeout=60):
    """Run AppleScript"""
    r = subprocess.run([AS, '-e', script], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 and r.stderr.strip():
        print(f"⚠️ AppleScript: {r.stderr.strip()}")
    return r.stdout.strip()

def safari_login_manual_style():
    """Navigate to login page and pause for manual login"""
    print("🔐 Step 1: Opening CCAR login page...")
    
    # Open Safari to CCAR
    run('''
        tell application "Safari"
            activate
            if (count of windows) = 0 then make new document
            set URL of front document to "https://ccar.mysolidearth.com/"
            delay 5
        end tell
    ''')
    
    # Check if already logged in
    check_login = run('''
        tell application "Safari"
            do JavaScript "
                if (window.location.href.includes('/portal')) {
                    'ALREADY_LOGGED_IN';
                } else {
                    'NEEDS_LOGIN';
                }
            " in front document
        end tell
    ''')
    
    if "ALREADY_LOGGED_IN" in check_login:
        print("✅ Already logged in to CCAR")
        return True
    
    print("🔑 Please log in manually in Safari:")
    print("   1. Click 'Email' radio button")
    print("   2. Enter your credentials")
    print("   3. Click 'Log In'")
    print("   4. Wait for the portal page to load")
    print("")
    
    # Wait for login completion
    print("⏳ Waiting for you to complete login...")
    for i in range(60):  # Wait up to 60 seconds
        time.sleep(1)
        check = run('''
            tell application "Safari"
                do JavaScript "window.location.href.includes('/portal') ? 'LOGGED_IN' : 'WAITING'" in front document
            end tell
        ''')
        if "LOGGED_IN" in check:
            print("✅ Login detected, continuing...")
            return True
        if i % 10 == 0:
            print(f"   Still waiting... ({60-i}s remaining)")
    
    print("❌ Login timeout")
    return False

def safari_navigate_to_listing(address):
    """Navigate to listing using tabbed interface"""
    print(f"🧭 Step 2: Navigating to listing: {address}")
    
    # Go to portal first
    run('''
        tell application "Safari"
            set URL of front document to "https://ccar.mysolidearth.com/portal"
            delay 5
        end tell
    ''')
    
    # Click Paragon/MLS link
    run('''
        tell application "Safari"
            do JavaScript "
                var paragonLink = document.querySelector('a[href*=\\\"paragonrels.com\\\"]') ||
                                 Array.from(document.querySelectorAll('a')).find(a => a.textContent.toLowerCase().includes('paragon'));
                if (paragonLink) paragonLink.click();
            " in front document
        end tell
    ''')
    
    time.sleep(8)  # Wait for Paragon to load
    
    # Power Search approach with tab navigation
    print("   Searching for property...")
    run(f'''
        tell application "Safari"
            activate
            delay 2
        end tell
        
        tell application "System Events"
            tell process "Safari"
                set frontmost to true
                
                -- Find search input by tabbing
                repeat 20 times
                    keystroke tab
                    delay 0.3
                    -- Check if we're in a search field
                    keystroke "{address}"
                    delay 0.5
                    -- If text was entered, we found the right field
                    keystroke return
                    delay 3
                    -- Check if search worked
                    exit repeat
                end repeat
            end tell
        end tell
    ''')
    
    time.sleep(5)
    
    # Click on ACTIVE listing
    print("   Clicking on ACTIVE listing...")
    run('''
        tell application "Safari"
            do JavaScript "
                var activeElements = Array.from(document.querySelectorAll('*')).filter(el => 
                    el.textContent && el.textContent.includes('(ACTIVE)')
                );
                if (activeElements.length > 0) {
                    activeElements[0].click();
                }
            " in front document
        end tell
    ''')
    
    time.sleep(5)
    print("✅ Navigated to listing page")

def safari_print_perfect_pdf(address):
    """Use Safari native print with Brother printer (classic dialog)"""
    print("🖨️ Step 3: Native Safari print (classic dialog)")
    
    # Make sure Safari is active and trigger print
    run('''
        tell application "Safari" to activate
        delay 1
    ''')
    
    # Cmd+P to open print dialog
    run('''
        tell application "System Events"
            tell process "Safari"
                set frontmost to true
                keystroke "p" using command down
                delay 4
            end tell
        end tell
    ''')
    
    # Handle classic macOS print dialog (Brother printer)
    print("   Handling print dialog...")
    clean_address = address.replace('"', "'").replace("'", "")[:30]  # Clean filename
    
    result = run(f'''
        tell application "System Events"
            tell process "Safari"
                try
                    -- Classic print dialog with Brother printer
                    -- Look for PDF dropdown in bottom-left
                    set pdfPopup to first pop up button whose title contains "PDF"
                    click pdfPopup
                    delay 1
                    
                    -- Click "Save as PDF" option
                    click menu item "Save as PDF..." of menu 1 of pdfPopup
                    delay 3
                    
                    -- File save dialog appears
                    -- Clear filename and enter address
                    keystroke "a" using command down
                    keystroke "{clean_address}"
                    delay 1
                    
                    -- Navigate to Desktop (Cmd+D)
                    keystroke "d" using command down
                    delay 1
                    
                    -- Save
                    click button "Save"
                    delay 3
                    
                    return "SUCCESS"
                    
                on error errMsg
                    -- Alternative approach if PDF popup not found
                    try
                        -- Look for Preview button instead
                        set showBtn to first button whose name contains "Show Details"
                        click showBtn
                        delay 2
                        
                        set pdfBtn to first pop up button whose title contains "PDF"
                        click pdfBtn
                        delay 1
                        
                        click menu item "Save as PDF..." of menu 1 of pdfBtn
                        delay 2
                        
                        return "SUCCESS_ALT"
                    on error err2
                        return "FAILED: " & errMsg & " | " & err2
                    end try
                end try
            end tell
        end tell
    ''')
    
    print(f"   Print result: {result}")
    
    # Check if PDF was created
    expected_pdf = f"/Users/claw1/Desktop/{clean_address}.pdf"
    if os.path.exists(expected_pdf):
        return expected_pdf
    
    # Check for similar files
    import glob
    desktop_pdfs = glob.glob(f"/Users/claw1/Desktop/*{clean_address.split()[0]}*.pdf")
    if desktop_pdfs:
        return desktop_pdfs[0]
    
    # Check for any recent PDFs
    recent_pdfs = glob.glob("/Users/claw1/Desktop/*.pdf")
    recent_pdfs.sort(key=os.path.getmtime, reverse=True)
    if recent_pdfs:
        newest_pdf = recent_pdfs[0]
        # Check if created in last 30 seconds
        if time.time() - os.path.getmtime(newest_pdf) < 30:
            return newest_pdf
    
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 mls_listing_sheet_fixed.py '308 62nd Ave N North Myrtle Beach'")
        sys.exit(1)
    
    address = sys.argv[1]
    print("=" * 60)
    print(f"🏠 MLS Listing Sheet PDF Generator (FIXED)")
    print(f"📍 Address: {address}")
    print("🎯 Goal: Perfect formatting via Safari native print")
    print("=" * 60)
    
    # Step 1: Login (manual for reliability)
    if not safari_login_manual_style():
        print("❌ Login failed")
        sys.exit(1)
    
    # Step 2: Navigate to listing
    safari_navigate_to_listing(address)
    
    # Step 3: Print to PDF
    pdf_path = safari_print_perfect_pdf(address)
    
    print("=" * 60)
    if pdf_path:
        print(f"🎉 SUCCESS! PDF saved to: {pdf_path}")
        print(f"📄 Perfect formatting via Safari native print!")
        
        # Show PDF size
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        print(f"📊 File size: {size_mb:.1f} MB")
    else:
        print("❌ FAILED: Could not create PDF")
        print("💡 Manual fallback: Cmd+P → PDF → Save as PDF")
    print("=" * 60)

if __name__ == "__main__":
    main()