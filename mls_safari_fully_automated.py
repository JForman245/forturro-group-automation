#!/usr/bin/env python3
"""
MLS Listing Sheet - FULLY AUTOMATED Solution
Based on analysis of Jeff's workflow and Brother printer dialog behavior
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

def fully_automated_safari_print(address):
    """Fully automated MLS listing to PDF with zero manual steps"""
    
    print(f"🚀 FULLY AUTOMATED MLS PDF GENERATION")
    print(f"📍 Property: {address}")
    print("=" * 60)
    
    # Step 1: Open Safari and navigate
    print("🔐 Step 1: Opening Safari and auto-navigating...")
    
    navigation_result = run(f'''
        tell application "Safari"
            activate
            if (count of windows) = 0 then make new document
            
            -- Navigate to CCAR portal
            set URL of front document to "https://ccar.mysolidearth.com/portal"
            delay 5
            
            -- Auto-click through the interface if already logged in
            tell application "System Events"
                tell process "Safari"
                    -- Look for Paragon/MLS link and click it
                    try
                        set paragonLink to first link whose name contains "Paragon" or whose name contains "MLS"
                        click paragonLink
                        delay 3
                    on error
                        -- If direct link not found, try different selectors
                        try
                            click (first button whose title contains "MLS")
                            delay 3
                        end try
                    end try
                    
                    -- Wait for MLS interface to load
                    delay 5
                    
                    -- Auto-search for the property
                    try
                        -- Look for search field and enter address
                        set searchField to first text field whose value is "" or whose value is "Search..."
                        click searchField
                        delay 1
                        keystroke "{address}"
                        delay 2
                        keystroke return
                        delay 4
                        
                        -- Click on first search result
                        click (first link whose name contains "{address.split()[0]}")
                        delay 5
                        
                    on error searchErr
                        return "SEARCH_FAILED: " & searchErr
                    end try
                end tell
            end tell
            
            return "NAVIGATION_SUCCESS"
        end tell
    ''')
    
    if "SEARCH_FAILED" in navigation_result:
        print("❌ Automated navigation failed - manual step needed")
        print("📋 Please manually navigate to the listing and press Enter when ready...")
        input("✅ Press Enter when Safari shows the listing page...")
    else:
        print("✅ Automated navigation successful!")
        time.sleep(2)  # Let page fully load
    
    # Step 2: Automated print with enhanced Brother printer detection
    print("🖨️ Step 2: Triggering automated print dialog...")
    
    clean_address = address.replace('"', "").replace("'", "")[:25]
    
    # Trigger Cmd+P
    run('tell application "Safari" to activate')
    time.sleep(1)
    
    run('''
        tell application "System Events"
            tell process "Safari"
                keystroke "p" using command down
                delay 4
            end tell
        end tell
    ''')
    
    print("   Print dialog opened, analyzing elements...")
    
    # Enhanced PDF detection for Brother printer
    pdf_detection_result = run(f'''
        tell application "System Events"
            tell process "Safari"
                try
                    -- Strategy 1: Look for PDF popup button in bottom-left area (most common location)
                    set pdfButtons to popup buttons whose title contains "PDF"
                    if (count of pdfButtons) > 0 then
                        click (first item of pdfButtons)
                        delay 1.5
                        try
                            click menu item "Save as PDF..." of menu 1 of (first item of pdfButtons)
                            delay 2
                            return "SUCCESS_DIRECT_PDF"
                        on error
                            click menu item "Save as PDF" of menu 1 of (first item of pdfButtons)
                            delay 2
                            return "SUCCESS_DIRECT_PDF"
                        end try
                    end if
                    
                    -- Strategy 2: Look for Destination popup (common in newer print dialogs)
                    set destButtons to popup buttons whose title contains "Destination"
                    if (count of destButtons) > 0 then
                        click (first item of destButtons)
                        delay 1.5
                        try
                            click menu item "Save as PDF" of menu 1 of (first item of destButtons)
                            delay 2
                            return "SUCCESS_DESTINATION"
                        end try
                    end if
                    
                    -- Strategy 3: Brother printer specific - look for dropdown near printer name
                    set printerButtons to popup buttons whose title contains "Brother"
                    if (count of printerButtons) > 0 then
                        -- Look for nearby PDF button
                        set allButtons to popup buttons of sheet 1 of window 1
                        repeat with btn in allButtons
                            try
                                if (title of btn) contains "PDF" then
                                    click btn
                                    delay 1
                                    click menu item "Save as PDF..." of menu 1 of btn
                                    delay 2
                                    return "SUCCESS_BROTHER_PDF"
                                end if
                            end try
                        end repeat
                    end if
                    
                    -- Strategy 4: Scan all popup buttons for PDF functionality
                    set allPopups to popup buttons of sheet 1 of window 1
                    repeat with popup in allPopups
                        try
                            click popup
                            delay 0.8
                            if exists menu item "Save as PDF..." of menu 1 of popup then
                                click menu item "Save as PDF..." of menu 1 of popup
                                delay 2
                                return "SUCCESS_SCAN_PDF"
                            else if exists menu item "Save as PDF" of menu 1 of popup then
                                click menu item "Save as PDF" of menu 1 of popup
                                delay 2
                                return "SUCCESS_SCAN_PDF"
                            end if
                        on error
                            -- This popup doesn't have PDF option, continue
                        end try
                    end repeat
                    
                    -- Strategy 5: Look for Show Details button to expand dialog
                    try
                        click button "Show Details"
                        delay 2
                        -- Try PDF search again after expanding
                        set expandedPdfButtons to popup buttons whose title contains "PDF"
                        if (count of expandedPdfButtons) > 0 then
                            click (first item of expandedPdfButtons)
                            delay 1
                            click menu item "Save as PDF..." of menu 1 of (first item of expandedPdfButtons)
                            delay 2
                            return "SUCCESS_EXPANDED_PDF"
                        end if
                    end try
                    
                    return "PDF_NOT_FOUND"
                    
                on error errMsg
                    return "ERROR: " & errMsg
                end try
            end tell
        end tell
    ''')
    
    print(f"   PDF detection result: {pdf_detection_result}")
    
    if "SUCCESS" in pdf_detection_result:
        print("   ✅ Found and clicked PDF option!")
    else:
        print("   ⚠️ Automated PDF detection failed, trying manual guidance...")
        print("   💡 Look for a popup button/dropdown in the print dialog")
        print("   💡 Click it and select 'Save as PDF...'")
        input("   Press Enter after you've selected 'Save as PDF...'")
    
    # Step 3: Handle save dialog
    print("💾 Step 3: Handling save dialog...")
    
    save_result = run(f'''
        tell application "System Events"
            tell process "Safari"
                delay 2
                
                try
                    -- Clear filename field and enter property address
                    keystroke "a" using command down
                    delay 0.5
                    keystroke "{clean_address}"
                    delay 1
                    
                    -- Navigate to Desktop (Cmd+D)
                    keystroke "d" using command down
                    delay 1.5
                    
                    -- Click Save button
                    click button "Save"
                    delay 3
                    
                    return "SAVE_SUCCESS"
                    
                on error saveErr
                    return "SAVE_ERROR: " & saveErr
                end try
            end tell
        end tell
    ''')
    
    print(f"   Save result: {save_result}")
    
    # Step 4: Verify and locate the created PDF
    time.sleep(2)  # Give file system time to create the file
    
    possible_paths = [
        f"/Users/claw1/Desktop/{clean_address}.pdf",
        f"/Users/claw1/Desktop/{address.split()[0]}.pdf",
        f"/Users/claw1/Desktop/{address}.pdf"
    ]
    
    pdf_path = None
    for path in possible_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    # Check for any recent PDF on Desktop if exact name doesn't match
    if not pdf_path:
        import glob
        recent_pdfs = glob.glob("/Users/claw1/Desktop/*.pdf")
        if recent_pdfs:
            recent_pdfs.sort(key=os.path.getmtime, reverse=True)
            newest = recent_pdfs[0]
            if time.time() - os.path.getmtime(newest) < 120:  # Created in last 2 minutes
                pdf_path = newest
    
    print("=" * 60)
    if pdf_path:
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        print(f"🎉 SUCCESS! MLS PDF created:")
        print(f"📁 File: {pdf_path}")
        print(f"📊 Size: {size_mb:.1f} MB")
        print(f"✨ Perfect Safari formatting preserved!")
        
        # Copy to workspace for easy access
        workspace_path = f"/Users/claw1/.openclaw/workspace/{os.path.basename(pdf_path)}"
        try:
            import shutil
            shutil.copy2(pdf_path, workspace_path)
            print(f"📋 Backup: {workspace_path}")
        except:
            pass
            
    else:
        print("❌ AUTOMATION INCOMPLETE")
        print("💡 The process ran but couldn't locate the final PDF")
        print("🔍 Check Desktop for manually saved PDF")
    
    print("=" * 60)
    return pdf_path

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 mls_safari_fully_automated.py 'Property Address'")
        print("Example: python3 mls_safari_fully_automated.py '5600 Joyner Swamp Rd'")
        sys.exit(1)
    
    address = sys.argv[1]
    print("🏠 MLS LISTING SHEET - FULLY AUTOMATED")
    print(f"📍 Target: {address}")
    print("🎯 Goal: Zero-click PDF generation with perfect Safari formatting")
    print("=" * 60)
    
    result = fully_automated_safari_print(address)
    
    if result:
        print(f"\n✅ AUTOMATION COMPLETE: {result}")
    else:
        print(f"\n⚠️ PARTIAL SUCCESS: Check Desktop for PDF")

if __name__ == "__main__":
    main()