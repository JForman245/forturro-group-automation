#!/usr/bin/env python3
"""
MLS Listing Sheet PDF — FINAL Safari Solution

Based on testing:
- Your manual process creates perfect 1.6MB PDFs ✅
- Print dialog has 69 elements but no obvious "PDF" button
- Need to look for popup buttons and menus
- Brother printer creates classic macOS print dialog

This version uses the insights from our testing to target the right elements.
"""

import os, sys, time, subprocess
from dotenv import load_dotenv

load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

AS = '/Users/claw1/Desktop/MLSHelper.app/Contents/MacOS/MLSHelper'

def run(script, timeout=60):
    """Run AppleScript via MLSHelper"""
    try:
        r = subprocess.run([AS, '-e', script], capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0 and r.stderr.strip():
            print(f"⚠️ {r.stderr.strip()}")
        return r.stdout.strip()
    except Exception as e:
        print(f"❌ AppleScript error: {e}")
        return ""

def open_safari_to_listing(address):
    """Open Safari and navigate to listing (with manual login step)"""
    print(f"🔐 Step 1: Opening Safari and navigating to listing")
    
    # Open Safari to CCAR
    run('''
        tell application "Safari"
            activate
            if (count of windows) = 0 then make new document
            set URL of front document to "https://ccar.mysolidearth.com/portal"
            delay 3
        end tell
    ''')
    
    print("📋 Manual steps required:")
    print("   1. If not logged in, log in to CCAR")
    print("   2. Click Paragon/MLS link") 
    print(f"   3. Search for: {address}")
    print("   4. Open the listing in All Fields Detail view")
    print("   5. Make sure the listing is fully loaded")
    print("")
    
    input("✅ Press Enter when Safari shows the listing page and you're ready to print...")

def safari_print_with_smart_pdf_detection(address):
    """Enhanced print dialog handling based on our testing"""
    print("🖨️ Step 2: Safari native print with enhanced PDF detection")
    
    # Ensure Safari is active
    run('tell application "Safari" to activate')
    time.sleep(1)
    
    # Trigger Cmd+P
    print("   Opening print dialog...")
    run('''
        tell application "System Events"
            tell process "Safari"
                keystroke "p" using command down
                delay 4
            end tell
        end tell
    ''')
    
    # Smart PDF detection based on our testing insights
    clean_address = address.replace('"', "").replace("'", "")[:25]
    print(f"   Searching for PDF option (targeting Brother printer dialog)...")
    
    # Strategy: Try multiple approaches based on common macOS print dialog patterns
    pdf_strategies = [
        # Strategy 1: Classic "PDF" popup button (bottom-left)
        '''
        tell application "System Events"
            tell process "Safari"
                try
                    -- Look for PDF popup button
                    set pdfButtons to popup buttons whose title contains "PDF"
                    if (count of pdfButtons) > 0 then
                        click (first item of pdfButtons)
                        delay 1
                        click menu item "Save as PDF..." of menu 1 of (first item of pdfButtons)
                        delay 2
                        return "SUCCESS_PDF_POPUP"
                    end if
                    return "NO_PDF_POPUP"
                on error errMsg
                    return "ERROR_PDF_POPUP: " & errMsg
                end try
            end tell
        end tell
        ''',
        
        # Strategy 2: Look in all popup buttons for "Save as PDF"
        '''
        tell application "System Events"
            tell process "Safari"
                try
                    set allPopups to popup buttons of sheet 1 of window 1
                    repeat with popup in allPopups
                        try
                            click popup
                            delay 0.5
                            if exists menu item "Save as PDF..." of menu 1 of popup then
                                click menu item "Save as PDF..." of menu 1 of popup
                                delay 2
                                return "SUCCESS_POPUP_SCAN"
                            end if
                        on error
                            -- This popup doesn't have Save as PDF, continue
                        end try
                    end repeat
                    return "NO_SAVE_PDF_FOUND"
                on error errMsg
                    return "ERROR_POPUP_SCAN: " & errMsg
                end try
            end tell
        end tell
        ''',
        
        # Strategy 3: Look for "Destination" or printer-related popups
        '''
        tell application "System Events"
            tell process "Safari"
                try
                    -- Check for destination popup
                    set destPopups to popup buttons whose title contains "Destination"
                    if (count of destPopups) > 0 then
                        click (first item of destPopups)
                        delay 1
                        if exists menu item "Save as PDF" of menu 1 of (first item of destPopups) then
                            click menu item "Save as PDF" of menu 1 of (first item of destPopups)
                            delay 2
                            return "SUCCESS_DESTINATION"
                        end if
                    end if
                    
                    -- Check for printer name popup (Brother)
                    set printerPopups to popup buttons whose title contains "Brother"
                    if (count of printerPopups) > 0 then
                        -- Look for a separate PDF button near printer
                        set nearbyPDFButtons to popup buttons whose title contains "PDF"
                        if (count of nearbyPDFButtons) > 0 then
                            click (first item of nearbyPDFButtons)
                            delay 1
                            click menu item "Save as PDF..." of menu 1 of (first item of nearbyPDFButtons)
                            delay 2
                            return "SUCCESS_PRINTER_PDF"
                        end if
                    end if
                    
                    return "NO_DESTINATION_OR_PRINTER"
                on error errMsg
                    return "ERROR_DESTINATION: " & errMsg
                end try
            end tell
        end tell
        ''',
        
        # Strategy 4: Manual approach - show all available options
        '''
        tell application "System Events"
            tell process "Safari"
                try
                    set allPopups to popup buttons of sheet 1 of window 1
                    set popupInfo to ""
                    repeat with popup in allPopups
                        set popupTitle to (title of popup) as string
                        set popupInfo to popupInfo & popupTitle & "; "
                    end repeat
                    return "MANUAL_NEEDED - Available popups: " & popupInfo
                on error errMsg
                    return "ERROR_MANUAL: " & errMsg
                end try
            end tell
        end tell
        '''
    ]
    
    # Try each strategy
    for i, strategy in enumerate(pdf_strategies, 1):
        print(f"   Trying approach {i}...")
        result = run(strategy)
        print(f"   Result: {result}")
        
        if "SUCCESS" in result:
            print("   ✅ Found PDF option! Handling save dialog...")
            break
        elif i == len(pdf_strategies):
            print("   ⚠️ All automated approaches failed. Showing manual guidance...")
            print(f"   Available elements: {result}")
            
            print("\n💡 Manual intervention needed:")
            print("   Look for a popup button/dropdown in the print dialog")
            print("   Click it and select 'Save as PDF...'")
            print("   Then continue manually with the save dialog")
            
            input("   Press Enter after you've clicked 'Save as PDF...'")
    
    # Handle the save dialog
    print("   Handling file save dialog...")
    save_result = run(f'''
        tell application "System Events"
            tell process "Safari"
                delay 2
                
                try
                    -- Clear and enter filename
                    keystroke "a" using command down
                    delay 0.5
                    keystroke "{clean_address}"
                    delay 1
                    
                    -- Navigate to Desktop
                    keystroke "d" using command down
                    delay 1
                    
                    -- Click Save button
                    click button "Save"
                    delay 3
                    
                    return "SAVE_COMPLETED"
                on error saveErr
                    return "SAVE_ERROR: " & saveErr
                end try
            end tell
        end tell
    ''')
    
    print(f"   Save dialog result: {save_result}")
    
    # Check for created PDF
    expected_paths = [
        f"/Users/claw1/Desktop/{clean_address}.pdf",
        f"/Users/claw1/Desktop/{address.split()[0]}.pdf"
    ]
    
    for pdf_path in expected_paths:
        if os.path.exists(pdf_path):
            return pdf_path
    
    # Check for any recent PDF on Desktop
    import glob
    recent_pdfs = glob.glob("/Users/claw1/Desktop/*.pdf")
    if recent_pdfs:
        recent_pdfs.sort(key=os.path.getmtime, reverse=True)
        newest = recent_pdfs[0]
        if time.time() - os.path.getmtime(newest) < 120:  # Created in last 2 minutes
            return newest
    
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 mls_safari_print_FINAL.py '308 62nd Ave N North Myrtle Beach'")
        print("Example: python3 mls_safari_print_FINAL.py '1704 Hillside Dr'")
        sys.exit(1)
    
    address = sys.argv[1]
    print("=" * 70)
    print("🏠 MLS LISTING SHEET PDF GENERATOR - FINAL VERSION")
    print(f"📍 Property: {address}")
    print("🎯 Goal: Perfect formatting via Safari native print (like your manual process)")
    print("=" * 70)
    
    # Step 1: Navigate to listing
    open_safari_to_listing(address)
    
    # Step 2: Smart PDF printing
    pdf_path = safari_print_with_smart_pdf_detection(address)
    
    # Results
    print("=" * 70)
    if pdf_path:
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        print(f"🎉 SUCCESS! PDF created: {pdf_path}")
        print(f"📊 File size: {size_mb:.1f} MB")
        print(f"✨ Perfect Safari formatting achieved!")
        
        # Move to workspace for easy access
        workspace_path = f"/Users/claw1/.openclaw/workspace/{os.path.basename(pdf_path)}"
        try:
            import shutil
            shutil.copy2(pdf_path, workspace_path)
            print(f"📁 Copy saved to workspace: {workspace_path}")
        except:
            pass
    else:
        print("❌ AUTOMATION INCOMPLETE")
        print("💡 The print dialog opened, but automated PDF creation needs refinement.")
        print("🔧 Your manual process still works perfectly for now.")
        print("📹 Next step: Analyze the video to perfect the automation.")
    print("=" * 70)

if __name__ == "__main__":
    main()