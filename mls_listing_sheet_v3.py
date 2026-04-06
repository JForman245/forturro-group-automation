#!/usr/bin/env python3
"""
MLS Listing Sheet PDF — Version 3 (Fixed Print Dialog)

Based on test results:
- Print dialog has 69 elements but no "PDF" button
- PDF option is likely in a popup menu/dropdown
- Need different approach to find PDF save option
"""

import os, sys, time, subprocess
from dotenv import load_dotenv

load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

AS = '/Users/claw1/Desktop/MLSHelper.app/Contents/MacOS/MLSHelper'

def run(script, timeout=60):
    """Run AppleScript"""
    r = subprocess.run([AS, '-e', script], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 and r.stderr.strip():
        print(f"⚠️ {r.stderr.strip()}")
    return r.stdout.strip()

def safari_navigate_to_listing(address):
    """Open Safari and navigate to listing (assuming already logged in)"""
    print(f"🧭 Navigating to listing: {address}")
    
    # Open Safari to CCAR portal
    run('''
        tell application "Safari"
            activate
            if (count of windows) = 0 then make new document
            set URL of front document to "https://ccar.mysolidearth.com/portal"
            delay 5
        end tell
    ''')
    
    print("✅ Please manually navigate to your listing in Safari")
    print("   1. Click Paragon link")
    print("   2. Search for the address") 
    print(f"   3. Open listing: {address}")
    print("   4. Press Enter when ready for print...")
    
    input("Press Enter when Safari shows the listing page...")

def safari_print_fixed(address):
    """Handle print dialog with improved PDF detection"""
    print("🖨️ Starting Safari print process...")
    
    # Trigger print
    run('''
        tell application "Safari" to activate
        delay 1
        tell application "System Events"
            tell process "Safari"
                keystroke "p" using command down
                delay 4
            end tell
        end tell
    ''')
    
    # Analyze the print dialog structure
    print("   Analyzing print dialog...")
    dialog_info = run('''
        tell application "System Events"
            tell process "Safari"
                try
                    -- Look for popup buttons (common for PDF dropdowns)
                    set popupButtons to popup buttons of sheet 1 of window 1
                    set popupInfo to ""
                    repeat with popup in popupButtons
                        set popupInfo to popupInfo & (title of popup) & "; "
                    end repeat
                    
                    -- Also check regular buttons
                    set regularButtons to buttons of sheet 1 of window 1
                    set buttonInfo to ""
                    repeat with btn in regularButtons
                        set buttonInfo to buttonInfo & (name of btn) & "; "
                    end repeat
                    
                    return "Popups: " & popupInfo & " | Buttons: " & buttonInfo
                    
                on error errMsg
                    return "Error: " & errMsg
                end try
            end tell
        end tell
    ''')
    
    print(f"   Dialog elements: {dialog_info}")
    
    # Try multiple approaches to find PDF option
    clean_address = address.replace('"', "").replace("'", "")[:25]
    
    approaches = [
        # Approach 1: Look for destination popup
        '''
        tell application "System Events"
            tell process "Safari"
                try
                    set destPopup to first popup button whose title contains "Destination"
                    click destPopup
                    delay 1
                    click menu item "Save as PDF" of menu 1 of destPopup
                    delay 2
                    return "SUCCESS_DEST"
                on error
                    return "FAILED_DEST"
                end try
            end tell
        end tell
        ''',
        
        # Approach 2: Look for any PDF-related popup
        '''
        tell application "System Events"
            tell process "Safari"
                try
                    set allPopups to popup buttons of sheet 1 of window 1
                    repeat with popup in allPopups
                        click popup
                        delay 1
                        try
                            click menu item "Save as PDF" of menu 1 of popup
                            delay 2
                            return "SUCCESS_POPUP"
                        on error
                            -- This popup doesn't have Save as PDF, try next
                        end try
                    end repeat
                    return "FAILED_POPUP"
                on error
                    return "FAILED_POPUP_ERROR"
                end try
            end tell
        end tell
        ''',
        
        # Approach 3: Look in lower-left corner (traditional PDF location)
        '''
        tell application "System Events"
            tell process "Safari"
                try
                    set bottomButtons to buttons of sheet 1 of window 1
                    repeat with btn in bottomButtons
                        set btnPos to position of btn
                        -- Check if button is in lower portion of dialog
                        if (item 2 of btnPos) > 400 then
                            if (name of btn) contains "PDF" then
                                click btn
                                delay 1
                                click menu item "Save as PDF..." of menu 1 of btn
                                delay 2
                                return "SUCCESS_CORNER"
                            end if
                        end if
                    end repeat
                    return "FAILED_CORNER"
                on error
                    return "FAILED_CORNER_ERROR" 
                end try
            end tell
        end tell
        '''
    ]
    
    # Try each approach
    for i, approach in enumerate(approaches, 1):
        print(f"   Trying approach {i}...")
        result = run(approach)
        print(f"   Result: {result}")
        
        if "SUCCESS" in result:
            print("   ✅ Found PDF option!")
            # Handle the save dialog
            save_result = run(f'''
                tell application "System Events"
                    tell process "Safari"
                        delay 2
                        -- Clear filename field
                        keystroke "a" using command down
                        keystroke "{clean_address}"
                        delay 1
                        
                        -- Go to Desktop
                        keystroke "d" using command down
                        delay 1
                        
                        -- Save
                        click button "Save"
                        delay 3
                        return "SAVED"
                    end tell
                end tell
            ''')
            
            # Check if PDF was created
            expected_files = [
                f"/Users/claw1/Desktop/{clean_address}.pdf",
                f"/Users/claw1/Desktop/{address.split()[0]}.pdf"
            ]
            
            for pdf_path in expected_files:
                if os.path.exists(pdf_path):
                    return pdf_path
            
            # Check for any recent PDF
            import glob
            recent_pdfs = glob.glob("/Users/claw1/Desktop/*.pdf")
            if recent_pdfs:
                recent_pdfs.sort(key=os.path.getmtime, reverse=True)
                newest = recent_pdfs[0]
                if time.time() - os.path.getmtime(newest) < 60:  # Created in last minute
                    return newest
            
            break
    
    # If all approaches failed, cancel dialog
    print("   ❌ All approaches failed, canceling...")
    run('''
        tell application "System Events"
            tell process "Safari"
                try
                    click button "Cancel" of sheet 1 of window 1
                on error
                    key code 53  -- ESC key
                end try
            end tell
        end tell
    ''')
    
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 mls_listing_sheet_v3.py '308 62nd Ave N'")
        sys.exit(1)
    
    address = sys.argv[1]
    print("=" * 60)
    print(f"🏠 MLS Listing Sheet PDF (v3 - Fixed Print Dialog)")
    print(f"📍 Address: {address}")
    print("=" * 60)
    
    # Navigate (with manual steps)
    safari_navigate_to_listing(address)
    
    # Print with improved dialog handling
    pdf_path = safari_print_fixed(address)
    
    print("=" * 60)
    if pdf_path:
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        print(f"🎉 SUCCESS! PDF: {pdf_path}")
        print(f"📊 Size: {size_mb:.1f} MB")
        print(f"🎯 Perfect Safari formatting achieved!")
    else:
        print("❌ FAILED: PDF not created")
        print("💡 Try manual: Cmd+P → look for PDF dropdown → Save as PDF")
    print("=" * 60)

if __name__ == "__main__":
    main()