#!/usr/bin/env python3
"""Pull an MLS listing sheet PDF from CCAR Paragon 5"""

import os, sys, time, json, base64

# Load env
from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

def get_listing_sheet(address, output_dir="/Users/claw1/Desktop"):
    """Login to Paragon MLS, search for address, save listing detail as PDF"""
    
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    
    if not username or not password:
        print("❌ MLS credentials not found in .env.mls")
        return None
    
    # Setup headless Chrome with PDF printing
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    
    # Enable PDF printing via DevTools
    options.add_experimental_option('prefs', {
        'printing.print_preview_sticky_settings.appState': json.dumps({
            'recentDestinations': [{'id': 'Save as PDF', 'origin': 'local', 'account': ''}],
            'selectedDestinationId': 'Save as PDF',
            'version': 2
        }),
        'savefile.default_directory': output_dir,
    })
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        # Step 1: Login via SSO
        print(f"🔑 Logging into MLS...")
        driver.get('https://ccar.mysolidearth.com')
        time.sleep(3)
        
        try:
            # Wait for login form (Vue-based)
            wait.until(EC.presence_of_element_located((By.NAME, 'member_login_id')))
            time.sleep(2)
            
            # Click "Email" radio button (form defaults to MLS Username)
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
            
            # Fill email and password
            email_field = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            email_field.send_keys(username)
            password_field.send_keys(password)
            
            # Submit
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            wait.until(EC.url_changes(driver.current_url))
            time.sleep(3)
            print("✅ SSO login successful")
        except TimeoutException:
            print("❌ SSO login failed - timeout")
            return None
        
        # Step 2: Navigate to Paragon
        print("🏠 Navigating to Paragon MLS...")
        driver.get('http://ccar.paragonrels.com/')
        time.sleep(12)
        
        # Close any overlay/popup
        try:
            driver.execute_script(
                "var el = document.getElementById('cboxOverlay'); if(el) el.style.display='none';"
                "var cb = document.getElementById('colorbox'); if(cb) cb.style.display='none';"
            )
        except:
            pass
        
        if 'paragonrels.com' not in driver.current_url:
            print(f"❌ Failed to reach Paragon. Current URL: {driver.current_url}")
            return None
        
        print(f"✅ On Paragon: {driver.current_url}")
        
        # Step 3: Search via Power Search
        print(f"🔍 Searching for: {address}")
        try:
            # Find the Power Search input
            search_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder*='Power Search'], input[placeholder*='search'], input.power-search, #powerSearchInput, input[name='powerSearch']")
            ))
            search_input.clear()
            search_input.send_keys(address)
            time.sleep(1)
            search_input.send_keys(Keys.RETURN)
            print("✅ Search submitted")
        except TimeoutException:
            try:
                search_input = driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[type='text']")
                search_input.clear()
                search_input.send_keys(address)
                search_input.send_keys(Keys.RETURN)
                print("✅ Search submitted (alternate)")
            except:
                print("❌ Could not find search field")
                driver.save_screenshot('/tmp/mls_debug.png')
                return None
        
        # Step 4: Wait for Power Search dropdown results to appear
        time.sleep(4)
        
        # Click on the ACTIVE listing in the dropdown
        print("📋 Looking for listing in dropdown...")
        clicked = False
        
        try:
            # The dropdown shows results like "2607109 - 308 62nd Ave. N, ... (ACTIVE)"
            # Try to click the one containing "(ACTIVE)" first
            elements = driver.find_elements(By.XPATH, "//*[contains(text(),'(ACTIVE)')]")
            if elements:
                for el in elements:
                    text = el.text.strip()
                    if '(ACTIVE)' in text and address.split()[0] in text:
                        print(f"  Clicking ACTIVE listing: {text[:80]}")
                        el.click()
                        clicked = True
                        break
                if not clicked and elements:
                    print(f"  Clicking first ACTIVE result: {elements[0].text[:80]}")
                    elements[0].click()
                    clicked = True
        except Exception as e:
            print(f"  ACTIVE search error: {e}")
        
        if not clicked:
            try:
                # Try clicking the highlighted/first result in the dropdown
                # Results contain MLS numbers like "2607109 - address..."
                results = driver.find_elements(By.XPATH, 
                    "//*[contains(text(),'ACTIVE') or contains(text(),'WITHDRAWN') or contains(text(),'EXPIRED')]")
                for r in results:
                    text = r.text.strip()
                    if address.split()[0] in text:
                        print(f"  Clicking result: {text[:80]}")
                        r.click()
                        clicked = True
                        break
            except Exception as e:
                print(f"  Fallback search error: {e}")
        
        if not clicked:
            print("❌ Could not find listing in dropdown results")
            driver.save_screenshot('/tmp/mls_debug_results.png')
            return None
        
        # Step 5: Wait for "All Fields Detail" view to fully render
        print("⏳ Waiting for listing detail to load...")
        time.sleep(8)
        
        # Wait for the detail content to appear - look for key listing fields
        for attempt in range(10):
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            if 'Asking Price' in page_text or 'MLS #' in page_text or 'Bedrooms' in page_text or 'ALL FIELDS' in page_text.upper():
                print("✅ Listing detail loaded")
                break
            time.sleep(2)
            print(f"  Waiting... attempt {attempt+1}")
        else:
            print("⚠️ Detail may not have fully loaded")
        
        # Additional wait for all content/images to render
        time.sleep(5)
        
        # Click Paragon's Print button to generate the print-formatted report
        # This produces the proper 8-page listing sheet (not just the viewport)
        try:
            # Try clicking via JavaScript since elements may not be interactable in headless
            driver.execute_script("""
                // Find and click the Print button in Paragon toolbar
                var printBtns = document.querySelectorAll('a, button, span, div');
                for (var btn of printBtns) {
                    var text = btn.textContent.trim();
                    var title = btn.getAttribute('title') || '';
                    if ((text === 'Print' || title.includes('Print')) && btn.offsetParent !== null) {
                        btn.click();
                        break;
                    }
                }
            """)
            time.sleep(3)
            
            # Click the Print submenu item
            driver.execute_script("""
                var items = document.querySelectorAll('a, li, div, span');
                for (var item of items) {
                    var text = item.textContent.trim();
                    if (text === 'Print' && item.offsetParent !== null) {
                        item.click();
                        break;
                    }
                }
            """)
            time.sleep(5)
            print("  Triggered Paragon Print via JS")
            
            # Check if a new window/tab opened with the print view
            handles = driver.window_handles
            if len(handles) > 1:
                driver.switch_to.window(handles[-1])
                time.sleep(5)
                print(f"  Switched to print window: {driver.current_url}")
        except Exception as e:
            print(f"  Paragon print trigger issue: {e}")
        
        print(f"📄 Current URL: {driver.current_url}")
        driver.save_screenshot('/tmp/mls_before_print.png')
        
        # Debug: dump DOM info about iframes and scrollable containers
        dom_info = driver.execute_script("""
            var info = [];
            // Check for iframes
            var iframes = document.querySelectorAll('iframe');
            info.push('Iframes: ' + iframes.length);
            for (var i = 0; i < iframes.length; i++) {
                info.push('  iframe[' + i + ']: src=' + (iframes[i].src || 'none') + ' id=' + (iframes[i].id || 'none'));
            }
            // Check scrollable elements
            var allEl = document.querySelectorAll('*');
            var scrollable = [];
            for (var el of allEl) {
                if (el.scrollHeight > el.clientHeight + 50 && el.tagName !== 'HTML' && el.tagName !== 'BODY') {
                    scrollable.push(el.tagName + '#' + el.id + '.' + el.className.split(' ').slice(0,2).join('.') + ' scrollH=' + el.scrollHeight + ' clientH=' + el.clientHeight);
                }
            }
            info.push('Scrollable elements: ' + scrollable.length);
            for (var s of scrollable.slice(0, 10)) {
                info.push('  ' + s);
            }
            return info.join('\\n');
        """)
        print(f"🔍 DOM debug:\n{dom_info}")
        
        # Step 5: Print page to PDF using Chrome DevTools Protocol
        print("🖨️ Generating PDF...")
        
        # Paragon renders listing detail inside an iframe
        # Find the iframe URL and navigate directly to it for clean PDF printing
        iframe_url = driver.execute_script("""
            var iframes = document.querySelectorAll('iframe');
            for (var i = 0; i < iframes.length; i++) {
                var src = iframes[i].src || '';
                if (src.includes('Search') || src.includes('listingIds') || (iframes[i].id && iframes[i].id.startsWith('tab1'))) {
                    return src;
                }
            }
            return '';
        """)
        
        # Extract listing ID from the iframe URL
        listing_id = None
        if iframe_url and 'listingIds=' in iframe_url:
            listing_id = iframe_url.split('listingIds=')[1].split('&')[0]
            print(f"  Listing ID: {listing_id}")
        
        if listing_id:
            # Switch into the search iframe (tab1_1)
            iframes = driver.find_elements(By.TAG_NAME, 'iframe')
            for iframe in iframes:
                src = iframe.get_attribute('src') or ''
                if 'listingIds' in src:
                    driver.switch_to.frame(iframe)
                    print("  Switched to search iframe")
                    break
            
            time.sleep(2)
            
            # Get the source code of the print functions to understand them
            fn_source = driver.execute_script("""
                var info = [];
                try { info.push('DoPrintWithBrowserCheck: ' + DoPrintWithBrowserCheck.toString().substring(0, 500)); } catch(e) { info.push('DoPrint: ' + e); }
                try { info.push('loadPrintPlus: ' + loadPrintPlus.toString().substring(0, 500)); } catch(e) { info.push('loadPrintPlus: ' + e); }
                return info.join('\\n\\n');
            """)
            print(f"  Print functions:\n{fn_source}")
            
            # Build the print URL manually using Paragon's variables
            print_view_url = driver.execute_script("""
                try {
                    var u = printUrl + (printUrl.indexOf('?')>0?'&selectedCount=':'?selectedCount=');
                    u += dataController.SelectedIDs.length;
                    u += '&totalCount=' + dataController.TotalRecords;
                    u += '&currentID=' + dataController.CurrentID;
                    u += '&searchID=' + frameElement.id;
                    u += '&viewID=' + dataController.CurrentViewID;
                    u += '&showStats=false';
                    u += '&classid=' + classID;
                    return u;
                } catch(e) {
                    return 'ERROR: ' + e.message;
                }
            """)
            print(f"  Print URL: {print_view_url[:150]}")
            
            # Skip PrintPlus (requires form submission that generates download)
            # Use ifView content with CSS fixes instead
            pass
            
            # Check if ifPrintView iframe is now populated
            print_iframe = None
            nested = driver.find_elements(By.TAG_NAME, 'iframe')
            for nf in nested:
                nid = nf.get_attribute('id') or ''
                nsrc = nf.get_attribute('src') or ''
                print(f"  iframe: id={nid} src={nsrc[:80]}")
                if nid == 'ifPrintView' and nsrc:
                    print_iframe = nf
            
            if print_iframe:
                # Switch to the print view iframe and extract its HTML
                driver.switch_to.frame(print_iframe)
                time.sleep(5)
                
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                print(f"  Print view content: {len(page_text)} chars")
                
                inner_html = driver.execute_script("return document.documentElement.outerHTML;")
                print(f"  Print view HTML: {len(inner_html)} chars")
                
                driver.switch_to.default_content()
                
                # Load the print-formatted HTML as standalone page
                temp_html = '/tmp/mls_listing_print.html'
                with open(temp_html, 'w') as f:
                    f.write(inner_html)
                driver.get(f'file://{temp_html}')
                time.sleep(5)
                print("✅ Loaded print-formatted listing")
            else:
                # Fallback: use ifView content
                print("  ifPrintView not populated, using ifView...")
                view_iframe = None
                for nf in nested:
                    nid = nf.get_attribute('id') or ''
                    if nid == 'ifView':
                        view_iframe = nf
                        break
                
                if view_iframe:
                    driver.switch_to.frame(view_iframe)
                    time.sleep(3)
                    inner_html = driver.execute_script("return document.documentElement.outerHTML;")
                    print(f"  ifView HTML: {len(inner_html)} chars")
                    driver.switch_to.default_content()
                    
                    # Paragon uses position:absolute with hardcoded px values for EVERY element
                    # Strip all inline position:absolute to let content flow naturally
                    import re
                    
                    # Remove position:absolute from inline styles
                    inner_html = re.sub(r'position\s*:\s*absolute\s*;?', '', inner_html)
                    
                    # Remove hardcoded top/left positioning from inline styles  
                    inner_html = re.sub(r'top\s*:\s*\d+px\s*;?', '', inner_html)
                    inner_html = re.sub(r'left\s*:\s*\d+px\s*;?', '', inner_html)
                    
                    # Fix the container height (was hardcoded)
                    inner_html = re.sub(r'height\s*:\s*\d{3,}px', 'height:auto', inner_html)
                    
                    # Scale images down
                    inner_html = inner_html.replace('width="640" ', 'width="192" ')
                    inner_html = inner_html.replace('height="480" ', 'height="144" ')
                    
                    # Add print-friendly CSS
                    css_fixes = """
                    <style>
                    * { position: relative !important; overflow: visible !important; }
                    body { width: 768px !important; margin: 0 auto; font-family: Tahoma, Arial, sans-serif; font-size: 11px; }
                    #divHtmlReport { height: auto !important; }
                    .hideWhenPrinted { display: none !important; }
                    .listingCheckBox { display: none !important; }
                    img.listingImage:first-of-type { display: block; margin-bottom: 8px; }
                    .mls3 { font-weight: bold; display: inline-block; width: 180px; }
                    .mls4 { display: inline-block; }
                    .mls13, .mls14 { display: inline-block; }
                    table { width: 100%; }
                    img { max-width: 192px; max-height: 144px; }
                    </style>
                    """
                    
                    if '</head>' in inner_html:
                        inner_html = inner_html.replace('</head>', css_fixes + '</head>')
                    else:
                        inner_html = css_fixes + inner_html
                    
                    temp_html = '/tmp/mls_listing_print.html'
                    with open(temp_html, 'w') as f:
                        f.write(inner_html)
                    driver.get(f'file://{temp_html}')
                    time.sleep(5)
                    print("✅ Loaded ifView content with CSS fixes")
        else:
            print("⚠️ Could not extract listing ID")
        
        # Remove fixed-height containers and overflow:hidden so full content is visible for PDF
        driver.execute_script("""
            // Remove all scroll containers - make everything flow naturally for print
            var allElements = document.querySelectorAll('*');
            for (var el of allElements) {
                var style = window.getComputedStyle(el);
                if (style.overflow === 'auto' || style.overflow === 'scroll' || 
                    style.overflowY === 'auto' || style.overflowY === 'scroll' ||
                    style.overflow === 'hidden') {
                    el.style.overflow = 'visible';
                    el.style.overflowY = 'visible';
                    el.style.overflowX = 'visible';
                }
                if (style.maxHeight && style.maxHeight !== 'none') {
                    el.style.maxHeight = 'none';
                }
                if (style.height && el.scrollHeight > el.clientHeight) {
                    el.style.height = 'auto';
                }
            }
            
            // Also remove any fixed positioning that might clip content
            document.body.style.overflow = 'visible';
            document.documentElement.style.overflow = 'visible';
            
            // Hide the toolbar/header to get a cleaner print
            var header = document.querySelector('header, .toolbar, #toolbar, .navbar, nav');
            if (header) header.style.display = 'none';
        """)
        time.sleep(3)
        
        # Scroll through to trigger lazy loading
        driver.execute_script("""
            var height = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
            for (var i = 0; i < height; i += 500) {
                window.scrollTo(0, i);
            }
            window.scrollTo(0, 0);
        """)
        time.sleep(3)
        
        # Use Chrome DevTools Protocol to print to PDF
        result = driver.execute_cdp_cmd('Page.printToPDF', {
            'landscape': False,
            'displayHeaderFooter': False,
            'printBackground': True,
            'preferCSSPageSize': False,
            'paperWidth': 8.5,
            'paperHeight': 11,
            'marginTop': 0.4,
            'marginBottom': 0.4,
            'marginLeft': 0.4,
            'marginRight': 0.4,
        })
        
        # Save PDF
        safe_name = address.replace('/', '-').replace('\\', '-').strip()
        pdf_path = os.path.join(output_dir, f"{safe_name}.pdf")
        
        with open(pdf_path, 'wb') as f:
            f.write(base64.b64decode(result['data']))
        
        file_size = os.path.getsize(pdf_path)
        print(f"✅ PDF saved: {pdf_path} ({file_size/1024:.0f} KB)")
        return pdf_path
        
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            driver.save_screenshot('/tmp/mls_debug.png')
            print("📸 Debug screenshot saved to /tmp/mls_debug.png")
        except:
            pass
        return None
    finally:
        driver.quit()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 mls_listing_sheet.py '<address>'")
        sys.exit(1)
    
    address = ' '.join(sys.argv[1:])
    result = get_listing_sheet(address)
    if not result:
        sys.exit(1)
