#!/usr/bin/env python3
"""
MLS Listing Sheet PDF — Safari + AppleScript (native print)
Matches Jeff's workflow exactly:
1. Navigate Safari to Paragon (must already be logged in via CCAR SSO)
2. Power Search → click listing → All Fields Detail
3. Navigate to report iframe URL for clean content
4. Cmd+P → PDF → Save as PDF → rename → Desktop
"""

import os, sys, time, subprocess
from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

AS = '/Users/claw1/Desktop/MLSHelper.app/Contents/MacOS/MLSHelper'

def run(script, timeout=60):
    r = subprocess.run([AS, '-e', script], capture_output=True, text=True, timeout=timeout)
    out = r.stdout.strip()
    if r.returncode != 0 and r.stderr.strip():
        print(f"  err: {r.stderr.strip()[:200]}")
    return out


def login_if_needed():
    """Check if logged in, login via keyboard if not."""
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    
    run('tell application "Safari" to activate')
    run('''
        tell application "Safari"
            if (count of windows) = 0 then make new document
            set URL of front document to "https://ccar.mysolidearth.com"
        end tell
    ''')
    time.sleep(6)
    
    url = run('tell application "Safari" to return URL of front document')
    if 'paragonrels' in url or 'resources/panels' in url or 'dashboard' in url:
        print("✅ Already logged in")
        return True
    
    if 'enter' in url or 'login' in url or 'mysolidearth' in url:
        print("🔑 Logging in...")
        # Click Email radio and focus email field
        run('''
            tell application "Safari"
                do JavaScript "
                    var radios = document.querySelectorAll('.v-radio');
                    for (var r of radios) {
                        if (r.textContent.includes('Email')) { r.querySelector('input').click(); break; }
                    }
                    setTimeout(function() {
                        var e = document.querySelector('input[type=email]');
                        if (e) { e.focus(); e.click(); }
                    }, 1000);
                " in front document
            end tell
        ''')
        time.sleep(2)
        
        # Type credentials via keyboard
        run(f'''
            tell application "Safari" to activate
            delay 0.5
            tell application "System Events"
                tell process "Safari"
                    set frontmost to true
                    delay 0.5
                    keystroke "{username}"
                    delay 0.5
                    keystroke tab
                    delay 0.5
                    keystroke "{password}"
                    delay 0.5
                    keystroke return
                end tell
            end tell
        ''')
        time.sleep(10)
        
        url = run('tell application "Safari" to return URL of front document')
        if 'enter' in url or 'login' in url:
            print("❌ Login failed")
            return False
        print("✅ Login successful")
        return True
    
    return False


def get_listing_sheet(address, output_dir="/Users/claw1/Desktop"):
    safe_name = address.replace('/', '-').replace('\\', '-').strip()
    pdf_path = os.path.join(output_dir, f"{safe_name}.pdf")
    
    # Remove old file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    # 1. Ensure logged in
    if not login_if_needed():
        # Try going to Paragon directly — SSO might redirect and auto-login
        run('tell application "Safari" to set URL of front document to "http://ccar.paragonrels.com/"')
        time.sleep(15)
        url = run('tell application "Safari" to return URL of front document')
        if 'paragonrels' not in url:
            print("❌ Not logged in and can't reach Paragon")
            return None

    # 2. Navigate to Paragon
    print("🏠 Navigating to Paragon...")
    run('tell application "Safari" to set URL of front document to "http://ccar.paragonrels.com/"')
    time.sleep(15)
    
    # Close overlays
    run('''
        tell application "Safari"
            do JavaScript "var el=document.getElementById('cboxOverlay');if(el)el.style.display='none';var cb=document.getElementById('colorbox');if(cb)cb.style.display='none';" in front document
        end tell
    ''')
    
    url = run('tell application "Safari" to return URL of front document')
    if 'paragonrels' not in url:
        print(f"❌ Not on Paragon: {url}")
        return None
    print("✅ On Paragon")

    # 3. Power Search — focus field via JS, type via keyboard, arrow+Enter to select
    print(f"🔍 Searching for: {address}")
    run('''
        tell application "Safari"
            do JavaScript "
                var inputs = document.querySelectorAll('input');
                for (var i of inputs) {
                    var ph = (i.getAttribute('placeholder') || '').toUpperCase();
                    if (ph.includes('POWER') || ph.includes('SEARCH')) {
                        i.focus();
                        i.click();
                        i.value = '';
                        break;
                    }
                }
            " in front document
        end tell
    ''')
    time.sleep(1)
    run(f'''
        tell application "System Events"
            tell process "Safari"
                keystroke "{address}"
            end tell
        end tell
    ''')
    time.sleep(4)
    
    # Click the ACTIVE listing from Power Search dropdown
    addr_num = address.strip().split()[0]
    
    # Write JS to temp file to avoid AppleScript escaping nightmares
    js_code = '''(function() {
        // Paragon uses Select2 dropdown for Power Search results
        // Items are: LI.select2-results__option with text like "2607942 - 5600 Joyner... (ACTIVE)"
        var items = document.querySelectorAll('li.select2-results__option');
        var candidates = [];
        for (var item of items) {
            var t = item.textContent.trim();
            // Skip group headers (they contain multiple results)
            if (item.querySelectorAll('li').length > 0) continue;
            if (t.includes('ADDR_NUM') && (t.includes('(ACTIVE)') || t.includes('(PENDING)') || t.includes('(SOLD)') || t.includes('(WITHDRAWN)') || t.includes('(EXPIRED)'))) {
                candidates.push({el: item, text: t, active: t.includes('(ACTIVE)')});
            }
        }
        // Prefer ACTIVE
        candidates.sort(function(a, b) { return (b.active?1:0) - (a.active?1:0); });
        if (candidates.length > 0) {
            // Select2 needs mouseup event to register selection
            var el = candidates[0].el;
            el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            el.click();
            return 'clicked: ' + candidates[0].text.substring(0, 80);
        }
        return 'not found';
    })()'''.replace('ADDR_NUM', addr_num)
    
    with open('/tmp/mls_click.js', 'w') as f:
        f.write(js_code)
    
    click_result = run('''
        tell application "Safari"
            set jsCode to read POSIX file "/tmp/mls_click.js" as «class utf8»
            do JavaScript jsCode in front document
        end tell
    ''')
    print(f"  {click_result}")
    if 'not found' in click_result:
        # Fallback: arrow down + Enter
        run('''
            tell application "System Events"
                tell process "Safari"
                    key code 125
                    delay 0.5
                    keystroke return
                end tell
            end tell
        ''')
    time.sleep(15)
    
    # Check if the loaded listing is ACTIVE. If not, try next result.
    for nav_attempt in range(5):
        status_check = run('''
            tell application "Safari"
                set result to do JavaScript "
                    (function() {
                        var frame = document.getElementById('tab1_1');
                        if (!frame) return 'no_frame';
                        try {
                            var doc = frame.contentDocument || frame.contentWindow.document;
                            var text = doc.body.innerText;
                            if (text.includes('ACTIVE')) return 'ACTIVE';
                            if (text.includes('WITHDRAWN')) return 'WITHDRAWN';
                            if (text.includes('EXPIRED')) return 'EXPIRED';
                            if (text.includes('PENDING')) return 'PENDING';
                            if (text.includes('SOLD')) return 'SOLD';
                            return 'unknown';
                        } catch(e) { return 'error'; }
                    })()
                " in front document
                return result
            end tell
        ''')
        if status_check == 'ACTIVE' or status_check == 'no_frame' or status_check == 'error':
            break
        if status_check in ['WITHDRAWN', 'EXPIRED', 'SOLD']:
            print(f"  Listing is {status_check}, trying next...")
            # Click the forward arrow in Paragon to go to next result
            run('''
                tell application "Safari"
                    do JavaScript "
                        var frame = document.getElementById('tab1_1');
                        if (frame) {
                            var doc = frame.contentDocument || frame.contentWindow.document;
                            var btns = doc.querySelectorAll('a, span, img');
                            for (var b of btns) {
                                var t = (b.title || b.alt || b.className || '');
                                if (t.includes('Next') || t.includes('next') || t.includes('Forward') || t.includes('>')) {
                                    b.click();
                                    break;
                                }
                            }
                        }
                    " in front document
                end tell
            ''')
            time.sleep(5)
        else:
            break
    
    print(f"  Listing status: {status_check}")
    print("✅ Search submitted")

    # 4. Get the report iframe URL (listing content)
    print("📋 Getting report URL...")
    report_url = ''
    for attempt in range(10):
        report_url = run('''
            tell application "Safari"
                set result to do JavaScript "
                    (function() {
                        var searchFrame = document.getElementById('tab1_1');
                        if (!searchFrame) return '';
                        try {
                            var innerDoc = searchFrame.contentDocument || searchFrame.contentWindow.document;
                            var ifView = innerDoc.getElementById('ifView');
                            if (ifView && ifView.src) return ifView.src;
                            return '';
                        } catch(e) { return ''; }
                    })()
                " in front document
                return result
            end tell
        ''')
        if report_url and 'Report' in report_url:
            break
        time.sleep(3)
    
    if not report_url or 'Report' not in report_url:
        print("❌ Could not get report URL")
        return None
    print(f"  Report URL found")

    # 5. Stay on the main Paragon page (NOT the report URL)
    # The full listing renders inside Paragon's iframes — Cmd+P on the main page
    # captures all content properly (same as Jeff's workflow)
    print("📄 Ready to print from Paragon main page...")
    time.sleep(3)

    # 6. Cmd+P → PDF → Save as PDF → filename → Desktop → Save
    print(f"🖨️ Printing → {safe_name}.pdf")
    result = run(f'''
        tell application "Safari" to activate
        delay 1
        tell application "System Events"
            tell process "Safari"
                set frontmost to true
                delay 0.5
                keystroke "p" using command down
            end tell
        end tell
        delay 5
        tell application "System Events"
            tell process "Safari"
                set targetWindow to missing value
                repeat with w in every window
                    try
                        set s to sheet 1 of w
                        set targetWindow to w
                        exit repeat
                    end try
                end repeat
                if targetWindow is missing value then
                    return "no_dialog"
                end if
                set theSheet to sheet 1 of targetWindow
                -- Try classic print dialog first
                try
                    click menu button "PDF" of theSheet
                    delay 1
                    click menu item "Save as PDF\u2026" of menu 1 of menu button "PDF" of theSheet
                    delay 2
                    keystroke "a" using command down
                    delay 0.3
                    keystroke "{safe_name}"
                    delay 0.5
                    keystroke "d" using command down
                    delay 1
                    keystroke return
                    delay 5
                    return "saved"
                end try
                -- Modern Safari print dialog
                try
                    set sg to splitter group 1 of theSheet
                    repeat with g in every group of sg
                        if (count of menu buttons of g) > 0 then
                            click menu button 1 of g
                            delay 1
                            click menu item "Save as PDF\u2026" of menu 1 of menu button 1 of g
                            delay 2
                            keystroke "a" using command down
                            delay 0.3
                            keystroke "{safe_name}"
                            delay 0.5
                            keystroke "d" using command down
                            delay 1
                            keystroke return
                            delay 5
                            return "saved"
                        end if
                    end repeat
                end try
                return "failed"
            end tell
        end tell
    ''')
    print(f"  Result: {result}")

    # 7. Handle possible Replace dialog
    if not os.path.exists(pdf_path):
        # Check for Replace dialog
        replace_result = run('''
            tell application "System Events"
                tell process "Safari"
                    try
                        repeat with w in every window
                            try
                                set s1 to sheet 1 of w
                                set s2 to sheet 1 of s1
                                set s3 to sheet 1 of s2
                                click button "Replace" of s3
                                return "replaced"
                            end try
                        end repeat
                    end try
                    return "no_replace"
                end tell
            end tell
        ''')
        if replace_result == 'replaced':
            print("  Handled Replace dialog")
            time.sleep(5)

    # 8. Verify
    time.sleep(3)
    if os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path)
        print(f"✅ PDF saved: {pdf_path} ({size/1024:.0f} KB)")
        return pdf_path
    
    print(f"❌ PDF not found at {pdf_path}")
    return None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 mls_listing_sheet_safari.py '<address>'")
        sys.exit(1)
    result = get_listing_sheet(' '.join(sys.argv[1:]))
    if not result:
        sys.exit(1)
