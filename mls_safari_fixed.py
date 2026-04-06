#!/usr/bin/env python3
"""
MLS Safari PDF - Fixed AppleScript version
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

def simple_mls_automation(address):
    """Simplified MLS automation with working AppleScript"""
    
    print(f"🏠 MLS PDF Generator - Fixed Version")
    print(f"📍 Property: {address}")
    print("=" * 50)
    
    # Step 1: Open Safari to CCAR
    print("🔐 Opening Safari...")
    
    run('''
        tell application "Safari"
            activate
            if (count of windows) = 0 then make new document
            set URL of front document to "https://ccar.mysolidearth.com/portal"
        end tell
    ''')
    
    print("📋 Manual steps:")
    print("   1. Login to CCAR if needed")
    print("   2. Click Paragon/MLS")
    print(f"   3. Search for: {address}")
    print("   4. Open the listing")
    print("")
    
    input("✅ Press Enter when you see the listing page...")
    
    # Step 2: Trigger print
    print("🖨️ Triggering print dialog...")
    
    run('tell application "Safari" to activate')
    time.sleep(1)
    
    run('''
        tell application "System Events"
            tell process "Safari"
                keystroke "p" using command down
            end tell
        end tell
    ''')
    
    time.sleep(3)
    
    # Step 3: Simple PDF detection
    print("📄 Looking for PDF option...")
    
    result = run('''
        tell application "System Events"
            tell process "Safari"
                try
                    set pdfButtons to popup buttons whose title contains "PDF"
                    if (count of pdfButtons) > 0 then
                        click (first item of pdfButtons)
                        delay 1
                        click menu item "Save as PDF..." of menu 1 of (first item of pdfButtons)
                        return "PDF_FOUND"
                    else
                        return "PDF_NOT_FOUND"
                    end if
                on error errMsg
                    return "ERROR"
                end try
            end tell
        end tell
    ''')
    
    if "PDF_FOUND" in result:
        print("✅ Found PDF option!")
    else:
        print("⚠️ Manual PDF selection needed")
        print("💡 Look for PDF popup/dropdown and select 'Save as PDF...'")
        input("Press Enter after selecting Save as PDF...")
    
    # Step 4: Handle save dialog
    print("💾 Saving file...")
    
    clean_address = address.replace('"', '').replace("'", '')[:20]
    
    time.sleep(2)
    
    run(f'''
        tell application "System Events"
            tell process "Safari"
                keystroke "a" using command down
                delay 0.5
                keystroke "{clean_address}"
                delay 1
                keystroke "d" using command down
                delay 1
                click button "Save"
            end tell
        end tell
    ''')
    
    print("✅ Save command sent!")
    
    # Check for created file
    time.sleep(3)
    
    pdf_path = f"/Users/claw1/Desktop/{clean_address}.pdf"
    if os.path.exists(pdf_path):
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        print(f"🎉 SUCCESS! PDF created:")
        print(f"📁 {pdf_path}")
        print(f"📊 Size: {size_mb:.1f} MB")
        return pdf_path
    else:
        print("❓ Check Desktop for the PDF file")
        return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 mls_safari_fixed.py 'Property Address'")
        sys.exit(1)
    
    address = sys.argv[1]
    result = simple_mls_automation(address)
    
    if result:
        print(f"\n✅ COMPLETE: {result}")
    else:
        print(f"\n⚠️ Check Desktop manually")

if __name__ == "__main__":
    main()