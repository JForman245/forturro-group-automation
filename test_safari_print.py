#!/usr/bin/env python3
"""
Test Safari Print Dialog Automation
This just tests the AppleScript print dialog handling on any page
"""

import subprocess, time

AS = '/Users/claw1/Desktop/MLSHelper.app/Contents/MacOS/MLSHelper'

def run_applescript(script, timeout=30):
    """Run AppleScript via MLSHelper.app"""
    try:
        r = subprocess.run([AS, '-e', script], capture_output=True, text=True, timeout=timeout)
        print(f"AppleScript output: {r.stdout}")
        if r.stderr:
            print(f"AppleScript errors: {r.stderr}")
        return r.returncode == 0
    except Exception as e:
        print(f"❌ AppleScript error: {e}")
        return False

def test_safari_print():
    """Test Safari print dialog automation"""
    
    # 1. Open Safari to any page
    print("1. Opening Safari...")
    open_safari = '''
        tell application "Safari"
            activate
            if (count of windows) = 0 then make new document
            set URL of front document to "https://example.com"
            delay 3
        end tell
    '''
    run_applescript(open_safari)
    
    # 2. Trigger print dialog
    print("2. Opening print dialog...")
    print_dialog = '''
        tell application "Safari" to activate
        delay 1
        tell application "System Events"
            tell process "Safari"
                set frontmost to true
                keystroke "p" using command down
                delay 4
            end tell
        end tell
    '''
    run_applescript(print_dialog)
    
    # 3. Check what print dialog elements are available
    print("3. Inspecting print dialog...")
    inspect_dialog = '''
        tell application "System Events"
            tell process "Safari"
                try
                    set dialogElements to entire contents of sheet 1 of window 1
                    return "Found print dialog: " & (count of dialogElements) & " elements"
                on error
                    try
                        set windowElements to entire contents of window 1
                        return "No sheet, found window: " & (count of windowElements) & " elements"
                    on error
                        return "No print dialog found"
                    end try
                end try
            end tell
        end tell
    '''
    result = run_applescript(inspect_dialog)
    
    # 4. Look for PDF button specifically
    print("4. Looking for PDF options...")
    find_pdf = '''
        tell application "System Events"
            tell process "Safari"
                try
                    set pdfButtons to buttons whose name contains "PDF"
                    if (count of pdfButtons) > 0 then
                        return "Found PDF buttons: " & (count of pdfButtons)
                    else
                        set allButtons to buttons of sheet 1 of window 1
                        set buttonNames to ""
                        repeat with btn in allButtons
                            set buttonNames to buttonNames & (name of btn) & ", "
                        end repeat
                        return "No PDF button. All buttons: " & buttonNames
                    end if
                on error errMsg
                    return "Error finding PDF button: " & errMsg
                end try
            end tell
        end tell
    '''
    result = run_applescript(find_pdf)
    
    # 5. Cancel the dialog
    print("5. Canceling dialog...")
    cancel_dialog = '''
        tell application "System Events"
            tell process "Safari"
                try
                    click button "Cancel" of sheet 1 of window 1
                on error
                    keystroke escape
                end try
            end tell
        end tell
    '''
    run_applescript(cancel_dialog)
    
    print("✅ Safari print test complete")

if __name__ == "__main__":
    test_safari_print()