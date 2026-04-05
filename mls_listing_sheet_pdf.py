#!/usr/bin/env python3
"""
MLS Listing Sheet PDF Generator v3
Toggles Paragon to PDF view, finds the actual PDF URL, downloads it.
Usage: python3 mls_listing_sheet_pdf.py "123 Main St"
       python3 mls_listing_sheet_pdf.py "123 Main St" --output /path/to/output.pdf
"""

import sys
import time
import os
import re
import base64
import requests
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')
MLS_USERNAME = os.getenv('MLS_USERNAME')
MLS_PASSWORD = os.getenv('MLS_PASSWORD')

OUTPUT_DIR = "/Users/claw1/.openclaw/workspace/pdfs for birdy"


def dismiss_popups(driver):
    """Kill any modal dialogs, colorbox overlays, notification popups"""
    driver.execute_script("""
        // Close colorbox
        if (document.getElementById('cboxOverlay')) document.getElementById('cboxOverlay').style.display='none';
        if (document.getElementById('colorbox')) document.getElementById('colorbox').style.display='none';
        if (typeof jQuery !== 'undefined' && jQuery.colorbox) jQuery.colorbox.close();
        // Close jQuery UI dialogs
        var dialogs = document.querySelectorAll('.ui-dialog');
        dialogs.forEach(function(d) { d.style.display = 'none'; });
        // Click any close buttons
        var closeButtons = document.querySelectorAll('.ui-dialog-titlebar-close, [title="Close"], button.close');
        closeButtons.forEach(function(btn) { try { btn.click(); } catch(e) {} });
    """)


def login_to_paragon(driver):
    """Log into CCAR portal and navigate to Paragon"""
    print("⏳ Loading CCAR portal...")
    driver.get("https://ccar.mysolidearth.com/portal")
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(3)

    # Select email/password login (second radio)
    radio_containers = driver.find_elements(By.CSS_SELECTOR, ".v-radio")
    radio_containers[1].click()
    time.sleep(2)

    driver.find_element(By.CSS_SELECTOR, "input[type='email'][name='email']").send_keys(MLS_USERNAME)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(MLS_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    print("⏳ Logging in...")
    time.sleep(10)

    # Click Paragon link
    all_links = driver.find_elements(By.TAG_NAME, "a")
    for link in all_links:
        href = (link.get_attribute("href") or "").lower()
        if "paragon" in href:
            link.click()
            break
    time.sleep(10)

    # Switch to Paragon tab
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
    time.sleep(3)

    # Dismiss popups (Expiring Notifications, etc.)
    dismiss_popups(driver)
    time.sleep(3)
    dismiss_popups(driver)
    time.sleep(1)
    print("✅ Logged into Paragon")


def lookup_mls_number(address):
    """Search real estate websites to find MLS number for a condo/unit address"""
    import urllib.parse
    query = urllib.parse.quote(f"{address} MLS number site:zillow.com OR site:realtor.com OR site:redfin.com")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    # Try DuckDuckGo HTML search
    try:
        resp = requests.get(f"https://html.duckduckgo.com/html/?q={query}", headers=headers, timeout=15)
        text = resp.text
        
        # Look for MLS patterns in results
        mls_patterns = [
            r'MLS[#:\s]*\s*(\d{5,10})',
            r'MLS\s*(?:ID|Number|No\.?|#)?[:\s]*(\d{5,10})',
            r'#\s*(\d{7,10})',  # Common MLS format
        ]
        for pattern in mls_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                mls = matches[0]
                print(f"🔍 Found MLS# {mls} from web search")
                return mls
    except Exception as e:
        print(f"⚠️ Web search failed: {e}")
    
    # Try Zillow directly
    try:
        search_addr = address.replace(' ', '-').replace('#', '').replace(',', '')
        resp = requests.get(f"https://www.zillow.com/homes/{search_addr}_rb/", headers=headers, timeout=15)
        mls_matches = re.findall(r'MLS[#:\s]*\s*(\d{5,10})', resp.text, re.IGNORECASE)
        if mls_matches:
            mls = mls_matches[0]
            print(f"🔍 Found MLS# {mls} from Zillow")
            return mls
    except Exception as e:
        print(f"⚠️ Zillow lookup failed: {e}")
    
    return None


def has_unit_number(address):
    """Check if address looks like it has a unit/apt number"""
    patterns = [
        r'#\d+', r'\bunit\b', r'\bapt\b', r'\bsuite\b',
        r'\b\d{1,5}\s+[A-Z]?$',  # ends with a number that could be unit
        r'\b(?:N|S|E|W|NE|NW|SE|SW)\s+\w+\s+(?:Blvd|Ave|St|Dr|Rd|Ln|Way|Ct)\s+\d+',  # address + number at end
    ]
    for p in patterns:
        if re.search(p, address, re.IGNORECASE):
            return True
    # Simple heuristic: if last token is a number and address has 4+ tokens, likely unit
    parts = address.strip().split()
    if len(parts) >= 4 and parts[-1].isdigit():
        return True
    return False


def search_listing(driver, address):
    """Power search for a listing by address"""
    print(f"🔍 Searching for: {address}")
    search_input = driver.find_element(By.CSS_SELECTOR, "input.select2-search__field")
    driver.execute_script("arguments[0].click();", search_input)
    time.sleep(1)
    search_input.send_keys(address)
    time.sleep(3)
    search_input.send_keys(Keys.RETURN)
    print("⏳ Waiting for results...")
    time.sleep(8)


def switch_to_listing_iframe(driver):
    """Find and switch to the listing results iframe"""
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for i, iframe in enumerate(iframes):
        src = iframe.get_attribute("src") or ""
        if "Search" in src or "listingIds" in src:
            driver.switch_to.frame(iframe)
            print(f"✅ Switched to listing iframe {i}")
            return True
    print("❌ No listing iframe found")
    return False


def get_selenium_cookies(driver):
    """Get cookies from Selenium session for use with requests"""
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
    return session


def click_toggle_pdf_and_capture(driver, output_path):
    """
    Click Toggle PDF, then intercept the actual PDF.
    After toggling, Paragon loads a PDF — we need to find its URL and download it.
    """
    
    # Enable network logging to catch PDF requests
    driver.execute_cdp_cmd("Network.enable", {})
    
    # Click Toggle PDF
    all_links = driver.find_elements(By.TAG_NAME, "a")
    toggle_pdf_link = None
    for link in all_links:
        title = link.get_attribute("title") or ""
        if "Toggle PDF" in title:
            toggle_pdf_link = link
            break
    
    if not toggle_pdf_link:
        print("❌ 'Toggle PDF' button not found")
        return False
    
    driver.execute_script("arguments[0].click();", toggle_pdf_link)
    print("✅ Clicked 'Toggle PDF'")
    print("⏳ Waiting for PDF to load...")
    time.sleep(8)
    
    # Strategy 1: Check for PDF embed/object/iframe elements
    # Switch back to default content to scan everything
    driver.switch_to.default_content()
    time.sleep(1)
    
    # Look in all frames for PDF content
    pdf_url = find_pdf_url_in_page(driver)
    
    if not pdf_url:
        # Re-enter listing iframe and look there
        switch_to_listing_iframe(driver)
        pdf_url = find_pdf_url_in_page(driver)
    
    if not pdf_url:
        # Strategy 2: Check network logs for PDF requests
        driver.switch_to.default_content()
        switch_to_listing_iframe(driver)
        
        # Look for any sub-iframes that might contain the PDF
        sub_iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"📋 Sub-iframes in listing: {len(sub_iframes)}")
        for i, sf in enumerate(sub_iframes):
            src = sf.get_attribute("src") or ""
            print(f"  sub-iframe {i}: {src[:150]}")
            if src and ('pdf' in src.lower() or 'report' in src.lower() or 'print' in src.lower()):
                pdf_url = src
                break
            # Try switching into sub-iframe to find PDF
            try:
                driver.switch_to.frame(sf)
                inner_url = find_pdf_url_in_page(driver)
                if inner_url:
                    pdf_url = inner_url
                    driver.switch_to.parent_frame()
                    break
                driver.switch_to.parent_frame()
            except:
                driver.switch_to.parent_frame()
    
    if not pdf_url:
        # Strategy 3: Inspect the page for PDF.js viewer or blob URLs
        driver.switch_to.default_content()
        switch_to_listing_iframe(driver)
        
        pdf_info = driver.execute_script("""
            // Check for PDF object/embed
            var embeds = document.querySelectorAll('embed, object, iframe');
            var results = [];
            for (var i = 0; i < embeds.length; i++) {
                var el = embeds[i];
                results.push({
                    tag: el.tagName,
                    src: el.src || el.data || '',
                    type: el.type || '',
                    cls: el.className || '',
                    id: el.id || ''
                });
            }
            
            // Check for any links to PDF files
            var links = document.querySelectorAll('a[href*=".pdf"], a[href*="PDF"], a[href*="Report"]');
            for (var i = 0; i < links.length; i++) {
                results.push({
                    tag: 'A',
                    src: links[i].href,
                    type: 'link',
                    cls: links[i].className,
                    id: links[i].id
                });
            }
            
            return results;
        """)
        print(f"📋 PDF-related elements found: {len(pdf_info)}")
        for info in pdf_info:
            print(f"  {info['tag']}: src={info['src'][:120]} type={info['type']} cls={info['cls']} id={info['id']}")
            if info['src'] and ('.pdf' in info['src'].lower() or 'report' in info['src'].lower()):
                pdf_url = info['src']
    
    if not pdf_url:
        # Strategy 4: Check for dynamically loaded content / XHR PDF
        # The Toggle PDF button might load PDF content into a div
        driver.switch_to.default_content()
        switch_to_listing_iframe(driver)
        
        # Get the full page source and look for PDF indicators
        page_source = driver.execute_script("return document.body.innerHTML;")
        
        # Look for common PDF viewer patterns
        import re
        pdf_patterns = [
            r'src="([^"]*\.pdf[^"]*)"',
            r'data="([^"]*\.pdf[^"]*)"',
            r'href="([^"]*Report[^"]*\.pdf[^"]*)"',
            r'url\(["\']?([^"\']*\.pdf[^"\']*)["\']?\)',
            r'"(https?://[^"]*\.pdf[^"]*)"',
            r'"(/ParagonLS/[^"]*Report[^"]*)"',
            r'"(/ParagonLS/[^"]*PDF[^"]*)"',
            r'"(/ParagonLS/[^"]*Print[^"]*)"',
        ]
        for pattern in pdf_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                print(f"📋 Pattern match [{pattern[:30]}...]: {matches[:3]}")
                for m in matches:
                    if 'pdf' in m.lower() or 'report' in m.lower() or 'print' in m.lower():
                        pdf_url = m
                        if not pdf_url.startswith('http'):
                            pdf_url = "https://ccar.paragonrels.com" + pdf_url
                        break
            if pdf_url:
                break
    
    if pdf_url:
        print(f"📄 Found PDF URL: {pdf_url[:150]}")
        return download_pdf(driver, pdf_url, output_path)
    
    # Strategy 5: Use Chrome's download interception
    # If toggle PDF changes the view to show a PDF inline, we can use
    # CDP to capture the PDF content
    print("📄 No direct PDF URL found. Attempting CDP download interception...")
    driver.switch_to.default_content()
    switch_to_listing_iframe(driver)
    
    # Take screenshot to see current state
    driver.switch_to.default_content()
    screenshot_path = output_path.replace('.pdf', '_debug.png')
    driver.save_screenshot(screenshot_path)
    print(f"📸 Debug screenshot: {screenshot_path}")
    
    # Check what the Toggle PDF actually changed — maybe it adds a download link
    switch_to_listing_iframe(driver)
    toggle_state = driver.execute_script("""
        // Look for checked/active PDF toggle state
        var pdfToggle = document.querySelector('.pdf_html_checked, .pdf_checked, [class*="pdf"][class*="check"]');
        if (pdfToggle) {
            return {
                found: true,
                tag: pdfToggle.tagName,
                cls: pdfToggle.className,
                parent: pdfToggle.parentElement ? pdfToggle.parentElement.outerHTML.substring(0, 300) : 'none'
            };
        }
        return {found: false};
    """)
    print(f"📋 PDF toggle state: {toggle_state}")
    
    # As absolute last resort: use CDP printToPDF on the listing iframe content
    # But first navigate directly to the iframe URL for a clean capture
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for iframe in iframes:
        src = iframe.get_attribute("src") or ""
        if "Search" in src or "listingIds" in src:
            # Add PDF parameter to URL
            pdf_src = src
            if '?' in pdf_src:
                pdf_src += "&viewType=pdf"
            else:
                pdf_src += "?viewType=pdf"
            print(f"📄 Trying iframe URL with PDF param: {pdf_src[:120]}")
            driver.get(pdf_src)
            time.sleep(5)
            
            # Check if this gave us a PDF
            content_type = driver.execute_script("return document.contentType || '';")
            print(f"📋 Content type: {content_type}")
            
            if 'pdf' in (content_type or '').lower():
                # It's a PDF! Use CDP to get it
                result = driver.execute_cdp_cmd("Page.printToPDF", {
                    "landscape": False,
                    "displayHeaderFooter": False,
                    "printBackground": True,
                })
                if result.get("data"):
                    save_pdf(result["data"], output_path)
                    return True
            break
    
    print("⚠️ Could not find downloadable PDF. Falling back to CDP printToPDF...")
    # Navigate to the original iframe URL clean
    driver.switch_to.default_content()
    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
        src = iframe.get_attribute("src") or ""
        if "Search" in src or "listingIds" in src:
            driver.get(src)
            time.sleep(5)
            dismiss_popups(driver)
            time.sleep(1)
            # Hide nav elements
            driver.execute_script("""
                var hide = document.querySelectorAll('#header, #nav, .navbar, #f-head, .f-panel-menu');
                hide.forEach(function(el) { el.style.display = 'none'; });
            """)
            result = driver.execute_cdp_cmd("Page.printToPDF", {
                "landscape": False,
                "displayHeaderFooter": False,
                "printBackground": True,
                "preferCSSPageSize": True,
                "paperWidth": 8.5,
                "paperHeight": 11,
                "marginTop": 0.2,
                "marginBottom": 0.2,
                "marginLeft": 0.2,
                "marginRight": 0.2,
            })
            if result.get("data"):
                save_pdf(result["data"], output_path)
                return True
            break
    
    return False


def find_pdf_url_in_page(driver):
    """Search current page context for PDF URLs"""
    result = driver.execute_script("""
        // Check embed/object/iframe with PDF
        var els = document.querySelectorAll('embed[src*=".pdf"], object[data*=".pdf"], iframe[src*=".pdf"], embed[type="application/pdf"], object[type="application/pdf"]');
        for (var i = 0; i < els.length; i++) {
            var url = els[i].src || els[i].data || '';
            if (url) return url;
        }
        // Check for any blob URLs
        var allEls = document.querySelectorAll('[src^="blob:"], [data^="blob:"]');
        for (var i = 0; i < allEls.length; i++) {
            return allEls[i].src || allEls[i].data;
        }
        return null;
    """)
    return result


def download_pdf(driver, url, output_path):
    """Download PDF using the Selenium session cookies"""
    session = get_selenium_cookies(driver)
    
    # If it's a blob URL, we can't download via requests - use CDP
    if url.startswith('blob:'):
        print("📄 Blob URL detected, using CDP approach...")
        # Navigate to the blob URL won't work, but we can try fetching via JS
        pdf_data = driver.execute_script("""
            return new Promise(function(resolve) {
                fetch(arguments[0]).then(function(r) {
                    return r.blob();
                }).then(function(blob) {
                    var reader = new FileReader();
                    reader.onload = function() {
                        resolve(reader.result.split(',')[1]); // base64
                    };
                    reader.readAsDataURL(blob);
                });
            });
        """, url)
        if pdf_data:
            save_pdf(pdf_data, output_path)
            return True
        return False
    
    # Regular URL - download with session cookies (with retries)
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"📥 Download attempt {attempt}/{max_retries}...")
            resp = session.get(url, stream=True, timeout=120)
            resp.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=32768):
                    f.write(chunk)
            size_kb = os.path.getsize(output_path) / 1024
            if size_kb < 5:
                print(f"⚠️ File too small ({size_kb:.0f} KB), retrying...")
                os.remove(output_path)
                time.sleep(3)
                continue
            print(f"✅ PDF downloaded: {output_path} ({size_kb:.0f} KB)")
            return True
        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait_time = attempt * 5
                print(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                # Last resort: try downloading via Selenium JavaScript fetch
                print("📄 Trying JavaScript fetch fallback...")
                try:
                    pdf_base64 = driver.execute_script("""
                        var url = arguments[0];
                        var xhr = new XMLHttpRequest();
                        xhr.open('GET', url, false);
                        xhr.responseType = 'arraybuffer';
                        xhr.send();
                        if (xhr.status === 200) {
                            var bytes = new Uint8Array(xhr.response);
                            var binary = '';
                            for (var i = 0; i < bytes.length; i++) {
                                binary += String.fromCharCode(bytes[i]);
                            }
                            return btoa(binary);
                        }
                        return null;
                    """, url)
                    if pdf_base64:
                        save_pdf(pdf_base64, output_path)
                        return True
                except Exception as js_err:
                    print(f"⚠️ JS fallback also failed: {js_err}")
                print(f"❌ All download attempts failed")
                return False
    return False


def save_pdf(pdf_base64, output_path):
    """Decode and save base64 PDF data"""
    pdf_bytes = base64.b64decode(pdf_base64)
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ PDF saved: {output_path} ({size_kb:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Generate MLS listing sheet PDF")
    parser.add_argument("address", help="Property address to search")
    parser.add_argument("--output", "-o", default=None, help="Output PDF path")
    args = parser.parse_args()

    address = args.address
    # Default: save to "pdfs for birdy" folder with listing name
    safe_name = address.replace('/', '-').strip()
    if args.output:
        output_path = args.output
    else:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.pdf")

    chrome_options = Options()
    chrome_options.add_argument("--window-size=1400,1000")
    
    # Set download directory to capture any auto-downloads
    prefs = {
        "download.default_directory": OUTPUT_DIR,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,  # Download PDFs instead of viewing
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        login_to_paragon(driver)
        search_listing(driver, address)
        
        if not switch_to_listing_iframe(driver):
            # If address has a unit number, try web lookup for MLS#
            if has_unit_number(address):
                print("⚠️ No results — condo unit? Looking up MLS# online...")
                mls_num = lookup_mls_number(address)
                if mls_num:
                    print(f"🔄 Retrying with MLS# {mls_num}")
                    # Navigate back to Paragon search
                    driver.get(driver.current_url)
                    time.sleep(5)
                    dismiss_popups(driver)
                    time.sleep(2)
                    search_listing(driver, mls_num)
                    if not switch_to_listing_iframe(driver):
                        print("❌ Failed: MLS# search also returned no results")
                        driver.quit()
                        sys.exit(1)
                    # Update output filename to include MLS#
                    safe_name = f"{address.replace('/', '-').strip()} (MLS {mls_num})"
                    output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.pdf")
                else:
                    print("❌ Could not find MLS# online either")
                    driver.quit()
                    sys.exit(1)
            else:
                print("❌ Failed: could not find listing iframe")
                driver.quit()
                sys.exit(1)

        if click_toggle_pdf_and_capture(driver, output_path):
            print(f"\n🎉 Success! Listing sheet saved to: {output_path}")
        else:
            print("\n❌ Failed to capture PDF")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        driver.quit()
        print("🔒 Browser closed")


if __name__ == "__main__":
    main()
