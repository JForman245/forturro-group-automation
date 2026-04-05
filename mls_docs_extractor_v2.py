#!/usr/bin/env python3
"""
MLS Document Extractor v2 - Using Power Search
Uses the POWER SEARCH (Select2 autocomplete) on the main Paragon page
to navigate directly to listing detail, then extract Associated Docs.
"""

import os, sys, time, glob

# Force unbuffered output
class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

sys.stdout = Unbuffered(sys.stdout)
sys.stderr = Unbuffered(sys.stderr)

from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class MLSDocExtractor:
    def __init__(self, address, output_dir=None):
        self.address = address
        self.output_dir = output_dir or os.path.expanduser("~/Desktop/Drop PDFs for Birdy")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.username = os.getenv('MLS_USERNAME')
        self.password = os.getenv('MLS_PASSWORD')
        
        options = Options()
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option('prefs', {
            'download.default_directory': self.output_dir,
            'download.prompt_for_download': False,
            'plugins.always_open_pdf_externally': True,
        })
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        self._docs_frame_index = None
    
    def login(self):
        """Login to CCAR portal"""
        print("🔐 Logging into CCAR...")
        self.driver.get('https://ccar.mysolidearth.com')
        time.sleep(3)
        
        radio_containers = self.driver.find_elements(By.CSS_SELECTOR, ".v-radio")
        if len(radio_containers) > 1:
            radio_containers[1].click()
            time.sleep(2)
        
        username_field = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'][name='email']"))
        )
        password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        
        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(10)
        
        if 'authenticate' not in self.driver.current_url:
            print("✅ Logged in")
            return True
        else:
            print("❌ Login failed")
            return False
    
    def navigate_to_paragon(self):
        """Click Paragon link and switch to that tab"""
        print("🚀 Navigating to Paragon...")
        paragon_link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='paragon']")
        paragon_link.click()
        time.sleep(5)
        
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])
        
        # Dismiss popups aggressively
        time.sleep(5)
        self.driver.execute_script("""
            // Remove overlay completely
            var overlay = document.getElementById('cboxOverlay');
            if (overlay) overlay.remove();
            var colorbox = document.getElementById('colorbox');
            if (colorbox) colorbox.remove();
            
            // Close via jQuery if available
            if (typeof jQuery !== 'undefined' && jQuery.colorbox) jQuery.colorbox.close();
            
            // Remove UI dialogs
            var dialogs = document.querySelectorAll('.ui-dialog, .ui-widget-overlay');
            dialogs.forEach(function(d) { d.remove(); });
            
            // Click any close buttons
            var closeButtons = document.querySelectorAll('.ui-dialog-titlebar-close, [title="Close"], button.close, .cboxClose');
            closeButtons.forEach(function(btn) { try { btn.click(); } catch(e) {} });
            
            // Remove any remaining modal overlays
            var modals = document.querySelectorAll('[class*="overlay"], [class*="modal"]');
            modals.forEach(function(m) { 
                if (m.style.display === 'block' || m.style.opacity) m.remove(); 
            });
        """)
        time.sleep(3)
        print("✅ On Paragon main page")
        return True
    
    def power_search(self):
        """Use Power Search (Select2) to find and navigate to listing"""
        print(f"🔍 Power Search for: {self.address}")
        
        # Make sure we're on the main page (not inside an iframe)
        self.driver.switch_to.default_content()
        
        # Find the Power Search field (Select2 autocomplete)
        power_search = self.driver.find_element(By.CSS_SELECTOR, "input.select2-search__field[placeholder='POWER SEARCH']")
        
        if not power_search:
            # Fallback
            power_search = self.driver.find_element(By.CSS_SELECTOR, "input[type='search'][placeholder='POWER SEARCH']")
        
        print("✅ Found Power Search field")
        
        # Use JavaScript to focus and interact (bypass any remaining overlays)
        self.driver.execute_script("arguments[0].focus(); arguments[0].click();", power_search)
        time.sleep(1)
        
        # Type address character by character to trigger Select2 AJAX search
        self.driver.execute_script("arguments[0].value = '';", power_search)
        
        # Send keys one at a time with small delays to trigger Select2 properly
        for char in self.address:
            power_search.send_keys(char)
            time.sleep(0.05)
        
        print(f"✅ Typed: {self.address}")
        
        # Wait for Select2 AJAX request and dropdown to populate
        print("⏳ Waiting for dropdown results...")
        time.sleep(8)
        
        # Look for dropdown results - try multiple Select2 selectors
        dropdown_selectors = [
            ".select2-results__option",
            ".select2-results li",
            "li.select2-results__option",
            ".select2-dropdown li",
            "ul.select2-results__options li",
        ]
        
        dropdown_options = []
        for selector in dropdown_selectors:
            options = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if options:
                dropdown_options = options
                print(f"📋 Found {len(options)} dropdown options via '{selector}'")
                break
        
        if not dropdown_options:
            # Debug: check what Select2 elements exist
            s2_debug = self.driver.execute_script("""
                var results = [];
                var all = document.querySelectorAll('[class*="select2"]');
                for (var i = 0; i < all.length; i++) {
                    var el = all[i];
                    results.push({
                        tag: el.tagName,
                        cls: el.className.substring(0, 80),
                        text: (el.textContent || '').substring(0, 100).trim(),
                        childCount: el.children.length
                    });
                }
                return results;
            """)
            print(f"\n🔍 Select2 debug ({len(s2_debug)} elements):")
            for el in s2_debug:
                print(f"   <{el['tag']}> class='{el['cls']}' children={el['childCount']} text='{el['text'][:60] if el['text'] else '(empty)'}'")
            
            # Try triggering Select2 search programmatically
            print("\n🔧 Trying to trigger Select2 search via jQuery...")
            try:
                trigger_result = self.driver.execute_script("""
                    // Try to find the Select2 instance and trigger search
                    var input = document.querySelector('input.select2-search__field[placeholder="POWER SEARCH"]');
                    if (!input) return 'no input found';
                    
                    // Check if Select2 container exists
                    var container = document.querySelector('.select2-container');
                    if (!container) return 'no select2 container';
                    
                    // Try to find the original select element that Select2 wraps
                    var selects = document.querySelectorAll('select');
                    var selectInfo = [];
                    for (var i = 0; i < selects.length; i++) {
                        selectInfo.push({
                            id: selects[i].id,
                            name: selects[i].name,
                            cls: selects[i].className
                        });
                    }
                    
                    // Try jQuery trigger
                    if (typeof jQuery !== 'undefined') {
                        try {
                            jQuery('.select2').select2('open');
                            return 'opened via jQuery, selects: ' + JSON.stringify(selectInfo);
                        } catch(e) {
                            return 'jQuery error: ' + e.message + ', selects: ' + JSON.stringify(selectInfo);
                        }
                    }
                    
                    return 'no jQuery, selects: ' + JSON.stringify(selectInfo);
                """)
                print(f"   Result: {trigger_result}")
                
                time.sleep(3)
                
                # Check for dropdown again
                for selector in dropdown_selectors:
                    options = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if options:
                        dropdown_options = options
                        print(f"   🎉 Found {len(options)} options after trigger!")
                        break
                        
            except Exception as e:
                print(f"   Trigger error: {e}")
            
            if not dropdown_options:
                print("❌ No dropdown options appeared")
                return False
        
        # Show all options
        for i, option in enumerate(dropdown_options):
            option_text = option.text.strip()
            option_class = option.get_attribute('class') or ''
            print(f"   [{i}] {option_text[:100]} (class: {option_class[:40]})")
        
        # Find the ACTIVE listing option specifically
        # Must match "MLS# - Address (ACTIVE)" pattern AND not be a header/group item
        active_option = None
        for option in dropdown_options:
            text = option.text.strip()
            option_class = option.get_attribute('class') or ''
            
            # Skip group headers (they contain all child text including ACTIVE)
            # Real options start with a number (MLS#)
            if '(ACTIVE)' in text and text[0].isdigit() and ' - ' in text:
                active_option = option
                print(f"🎯 Found ACTIVE listing: {text[:80]}")
                break
        
        # Fallback: skip header rows (LISTING, RUN CLASSIC SEARCH), take first real result
        if not active_option:
            for option in dropdown_options:
                text = option.text.strip()
                if text and ' - ' in text and ('403' in text):
                    active_option = option
                    print(f"🎯 Using first matching result: {text[:80]}")
                    break
        
        if active_option:
            active_option.click()
            time.sleep(10)
            print("✅ Power Search loaded listing in results")
            
            # Now we need to click INTO the listing to open detail view
            # The listing loads in an iframe — switch to it
            self.driver.switch_to.default_content()
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            
            for i, frame in enumerate(frames):
                try:
                    src = frame.get_attribute('src') or ''
                    if 'Search' in src and 'listingIds' in src:
                        self.driver.switch_to.frame(frame)
                        print(f"   Switched to search results frame [{i}]")
                        time.sleep(2)
                        
                        # Click on the listing row to open detail view
                        # Try finding the listing row in the grid
                        listing_clicked = False
                        
                        # Method 1: Double-click the first data row in the grid
                        try:
                            rows = self.driver.find_elements(By.CSS_SELECTOR, "tr.jqgrow, tr[role='row'], tbody tr")
                            print(f"   Found {len(rows)} grid rows")
                            for row in rows:
                                row_text = row.text.strip()
                                if row_text and ('403' in row_text or 'Ave' in row_text or '2606413' in row_text):
                                    print(f"   🎯 Clicking listing row: {row_text[:60]}")
                                    # Double-click to open detail view
                                    from selenium.webdriver.common.action_chains import ActionChains
                                    ActionChains(self.driver).double_click(row).perform()
                                    listing_clicked = True
                                    time.sleep(8)
                                    break
                        except Exception as e:
                            print(f"   Row click failed: {str(e)[:60]}")
                        
                        # Method 2: If no row found, try clicking any link in the grid
                        if not listing_clicked:
                            try:
                                grid_links = self.driver.find_elements(By.CSS_SELECTOR, "td a, .grid-cell a")
                                if grid_links:
                                    print(f"   Trying grid link click...")
                                    self.driver.execute_script("arguments[0].click();", grid_links[0])
                                    listing_clicked = True
                                    time.sleep(8)
                            except:
                                pass
                        
                        if listing_clicked:
                            print("✅ Opened listing detail view")
                        else:
                            print("⚠️ Could not click into listing detail")
                        
                        break
                except:
                    continue
            
            self.driver.switch_to.default_content()
            return True
        
        print("❌ No suitable listing option found")
        return False
    
    def find_associated_docs(self):
        """Find and click Associated Docs icon on the listing detail page"""
        print("📁 Looking for Associated Docs icon...")
        
        # After Power Search click, the listing loads in an iframe
        # Need to check the right iframe
        self.driver.switch_to.default_content()
        
        frames = self.driver.find_elements(By.TAG_NAME, "iframe")
        print(f"   Found {len(frames)} iframes")
        
        for i, frame in enumerate(frames):
            try:
                src = frame.get_attribute('src') or 'no src'
                print(f"   [{i}] {src[:80]}")
            except:
                continue
        
        # Try each iframe
        for i, frame in enumerate(frames):
            try:
                self.driver.switch_to.default_content()
                fresh_frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                if i >= len(fresh_frames):
                    continue
                self.driver.switch_to.frame(fresh_frames[i])
                time.sleep(2)
                
                # First do a comprehensive scan of what's available
                page_scan = self.driver.execute_script("""
                    var results = {images: [], links: [], buttons: []};
                    
                    // Scan all images
                    var imgs = document.querySelectorAll('img');
                    for (var j = 0; j < imgs.length; j++) {
                        var img = imgs[j];
                        var t = (img.title || img.alt || '').toLowerCase();
                        var s = (img.src || '').toLowerCase();
                        if (t.indexOf('doc') >= 0 || t.indexOf('assoc') >= 0 || 
                            s.indexOf('doc') >= 0 || s.indexOf('assoc') >= 0 ||
                            t.indexOf('attach') >= 0 || s.indexOf('attach') >= 0) {
                            results.images.push({title: img.title || img.alt, src: img.src, cls: img.className});
                        }
                    }
                    
                    // Scan all links
                    var links = document.querySelectorAll('a');
                    for (var j = 0; j < links.length; j++) {
                        var a = links[j];
                        var t = ((a.title || '') + ' ' + (a.textContent || '') + ' ' + (a.href || '')).toLowerCase();
                        if (t.indexOf('doc') >= 0 || t.indexOf('assoc') >= 0 || t.indexOf('attach') >= 0) {
                            results.links.push({text: (a.textContent || '').trim().substring(0, 60), href: a.href || '', title: a.title || '', cls: a.className});
                        }
                    }
                    
                    // Scan toolbar/icon areas
                    var toolItems = document.querySelectorAll('.toolbar img, .icon-bar img, .action-bar img, [class*="tool"] img, [class*="icon"] img, [class*="action"] img');
                    for (var j = 0; j < toolItems.length; j++) {
                        var ti = toolItems[j];
                        results.buttons.push({title: ti.title || ti.alt || '', src: ti.src || '', cls: ti.className});
                    }
                    
                    return results;
                """)
                
                if page_scan['images']:
                    print(f"   Frame [{i}] doc images: {len(page_scan['images'])}")
                    for img in page_scan['images']:
                        print(f"      img: title='{img['title']}' src='{img['src'][-40:]}'")
                
                if page_scan['links']:
                    print(f"   Frame [{i}] doc links: {len(page_scan['links'])}")
                    for lnk in page_scan['links']:
                        print(f"      link: text='{lnk['text']}' title='{lnk['title']}' href='{lnk['href'][-60:]}'")
                
                if page_scan['buttons']:
                    print(f"   Frame [{i}] toolbar icons: {len(page_scan['buttons'])}")
                    for btn in page_scan['buttons']:
                        print(f"      icon: title='{btn['title']}' src='{btn['src'][-40:]}'")
                
                # Now try to click the Associated Docs icon
                found = self._look_for_docs_icon()
                if found:
                    self._docs_frame_index = i
                    return True
                    
            except Exception as e:
                err = str(e)[:80]
                print(f"   Frame [{i}] error: {err}")
                continue
        
        # Also check main page
        self.driver.switch_to.default_content()
        found = self._look_for_docs_icon()
        if found:
            self._docs_frame_index = None  # main page
            return True
        
        print("❌ Associated Docs icon not found")
        return False
    
    def _look_for_docs_icon(self):
        """Look for Associated Docs icon/link on current page/frame"""
        
        # Direct approach: find link/element with exact text "Associated Docs"
        try:
            found = self.driver.execute_script("""
                var links = document.querySelectorAll('a, span, div, button, td');
                for (var i = 0; i < links.length; i++) {
                    var el = links[i];
                    var text = (el.textContent || '').trim();
                    // Match exact "Associated Docs" text (not a parent with lots of other text)
                    if (text === 'Associated Docs' || text === 'Associated Documents') {
                        return {found: true, tag: el.tagName, text: text, id: el.id || '', cls: el.className || ''};
                    }
                }
                return {found: false};
            """)
            
            if found and found.get('found'):
                print(f"   🎯 Found '{found['text']}' as <{found['tag']}> id='{found['id']}' class='{found['cls'][:40]}'")
                
                # Click it via JavaScript
                self.driver.execute_script("""
                    var links = document.querySelectorAll('a, span, div, button, td');
                    for (var i = 0; i < links.length; i++) {
                        var text = (links[i].textContent || '').trim();
                        if (text === 'Associated Docs' || text === 'Associated Documents') {
                            links[i].click();
                            break;
                        }
                    }
                """)
                
                time.sleep(3)
                
                # Dismiss any CMA dialog that pops up
                try:
                    ok_btn = self.driver.find_element(By.XPATH, "//div[contains(@class, 'ui-dialog-buttonset')]//button[contains(text(), 'OK')]")
                    if ok_btn.is_displayed():
                        ok_btn.click()
                        print("   ✅ Dismissed CMA dialog")
                        time.sleep(3)
                except:
                    pass
                
                time.sleep(5)
                print("   ✅ Clicked Associated Docs!")
                return True
        except Exception as e:
            print(f"   Direct search error: {e}")
        
        # Fallback: look for img with title containing doc/assoc
        try:
            doc_imgs = self.driver.find_elements(By.XPATH, "//img[contains(@title, 'Associated') or contains(@title, 'Document')]")
            if doc_imgs:
                for img in doc_imgs:
                    title = img.get_attribute('title') or ''
                    print(f"   Trying img: {title}")
                    self.driver.execute_script("arguments[0].click();", img)
                    time.sleep(5)
                    return True
        except:
            pass
        
        return False
    
    def extract_documents(self, docs_frame_index=None):
        """Download all documents from the Associated Docs page.
        
        After clicking Associated Docs, the documents load in a sub-iframe
        within the search frame. Documents are in a table with clickable links
        that open PDFs in new tabs.
        """
        print("📄 Extracting documents...")
        
        # Dismiss any alerts
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except:
            pass
        
        # Navigate to the search frame, then into the sub-iframe with documents
        self.driver.switch_to.default_content()
        frames = self.driver.find_elements(By.TAG_NAME, "iframe")
        
        # Find the search frame
        search_frame = None
        for i, f in enumerate(frames):
            try:
                src = f.get_attribute('src') or ''
                if 'Search' in src and 'listingIds' in src:
                    search_frame = i
                    break
            except:
                continue
        
        if search_frame is None:
            search_frame = docs_frame_index or 2
        
        print(f"   Using search frame [{search_frame}]")
        self.driver.switch_to.frame(frames[search_frame])
        time.sleep(2)
        
        # Look for sub-iframes (the docs table loads in a sub-iframe)
        sub_frames = self.driver.find_elements(By.TAG_NAME, "iframe")
        print(f"   Found {len(sub_frames)} sub-iframes")
        
        doc_links = []
        docs_sub_frame = None
        
        for i, sf in enumerate(sub_frames):
            try:
                src = sf.get_attribute('src') or 'no src'
                print(f"      Sub [{i}]: {src[:80]}")
                
                # Switch into sub-iframe to look for document table
                self.driver.switch_to.frame(sf)
                time.sleep(2)
                
                # Look for the document table (Document, File Type, File Size, File Date)
                table_check = self.driver.execute_script("""
                    var tables = document.querySelectorAll('table');
                    for (var t = 0; t < tables.length; t++) {
                        var text = tables[t].textContent.toLowerCase();
                        if (text.indexOf('file type') >= 0 || text.indexOf('file size') >= 0 || 
                            text.indexOf('file date') >= 0 || text.indexOf('.pdf') >= 0) {
                            // Found the document table! Get all document links
                            var links = tables[t].querySelectorAll('a');
                            var docs = [];
                            for (var j = 0; j < links.length; j++) {
                                var linkText = (links[j].textContent || '').trim();
                                var href = links[j].href || '';
                                // Skip empty or navigation links
                                if (linkText && linkText.length > 1) {
                                    docs.push({
                                        text: linkText,
                                        href: href,
                                        index: j
                                    });
                                }
                            }
                            return {found: true, docs: docs, tableIndex: t};
                        }
                    }
                    
                    // Also check for links with .pdf in text or href
                    var allLinks = document.querySelectorAll('a');
                    var pdfLinks = [];
                    for (var j = 0; j < allLinks.length; j++) {
                        var text = (allLinks[j].textContent || '').trim();
                        var href = (allLinks[j].href || '').toLowerCase();
                        if (text.length > 1 && (href.indexOf('.pdf') >= 0 || href.indexOf('document') >= 0 || href.indexOf('ViewDoc') >= 0)) {
                            pdfLinks.push({text: text, href: allLinks[j].href, index: j});
                        }
                    }
                    if (pdfLinks.length > 0) return {found: true, docs: pdfLinks};
                    
                    return {found: false, linkCount: allLinks.length};
                """)
                
                if table_check.get('found'):
                    doc_links = table_check['docs']
                    docs_sub_frame = i
                    print(f"   🎉 Found document table in sub-iframe [{i}]!")
                    for d in doc_links:
                        print(f"      📄 {d['text']}")
                    break
                else:
                    print(f"      No doc table (links: {table_check.get('linkCount', 0)})")
                
                # Switch back to parent frame to check next sub-iframe
                self.driver.switch_to.parent_frame()
                
            except Exception as e:
                print(f"      Sub [{i}] error: {str(e)[:60]}")
                try:
                    self.driver.switch_to.parent_frame()
                except:
                    pass
                continue
        
        if not doc_links:
            print("⚠️ No documents found for this listing")
            return []
        
        # Download each document
        downloaded = []
        main_window = self.driver.current_window_handle
        
        for doc in doc_links:
            print(f"\n   📥 Downloading: {doc['text']}")
            
            try:
                # Make sure we're in the right sub-iframe
                self.driver.switch_to.default_content()
                fresh_frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                self.driver.switch_to.frame(fresh_frames[search_frame])
                time.sleep(1)
                fresh_sub = self.driver.find_elements(By.TAG_NAME, "iframe")
                self.driver.switch_to.frame(fresh_sub[docs_sub_frame])
                time.sleep(1)
                
                # Track tabs before click
                before_handles = set(self.driver.window_handles)
                
                # Find the document link - try multiple approaches
                target = None
                
                # Approach 1: Find by link text
                try:
                    targets = self.driver.find_elements(By.LINK_TEXT, doc['text'])
                    if targets:
                        target = targets[0]
                except:
                    pass
                
                # Approach 2: Find by partial link text
                if not target:
                    try:
                        targets = self.driver.find_elements(By.PARTIAL_LINK_TEXT, doc['text'])
                        if targets:
                            target = targets[0]
                    except:
                        pass
                
                # Approach 3: JavaScript find
                if not target:
                    try:
                        found_idx = self.driver.execute_script(f"""
                            var links = document.querySelectorAll('a');
                            for (var i = 0; i < links.length; i++) {{
                                if (links[i].textContent.trim() === '{doc["text"]}') return i;
                            }}
                            return -1;
                        """)
                        if found_idx >= 0:
                            all_links = self.driver.find_elements(By.TAG_NAME, "a")
                            if found_idx < len(all_links):
                                target = all_links[found_idx]
                    except:
                        pass
                
                # Approach 4: Just click via JavaScript directly
                if not target:
                    try:
                        clicked = self.driver.execute_script(f"""
                            var links = document.querySelectorAll('a');
                            for (var i = 0; i < links.length; i++) {{
                                if (links[i].textContent.trim() === '{doc["text"]}') {{
                                    links[i].click();
                                    return true;
                                }}
                            }}
                            return false;
                        """)
                        if clicked:
                            print(f"      Clicked via JS directly")
                            time.sleep(5)
                            after_handles = set(self.driver.window_handles)
                            new_handles = after_handles - before_handles
                            if new_handles:
                                new_tab = list(new_handles)[0]
                                self.driver.switch_to.window(new_tab)
                                time.sleep(3)
                                pdf_url = self.driver.current_url
                                print(f"      🔗 PDF URL: {pdf_url[:100]}")
                                safe_name = doc['text'].replace('/', '_').replace('\\', '_').replace(':', '_').strip()[:60]
                                self.driver.execute_script(f"""
                                    var a = document.createElement('a');
                                    a.href = window.location.href;
                                    a.download = '{safe_name}.pdf';
                                    document.body.appendChild(a);
                                    a.click();
                                    a.remove();
                                """)
                                time.sleep(3)
                                self.driver.close()
                                self.driver.switch_to.window(main_window)
                                downloaded.append(doc['text'])
                                print(f"      ✅ Downloaded: {safe_name}.pdf")
                            else:
                                print(f"      ⚠️ JS click worked but no new tab")
                            continue
                    except:
                        pass
                
                if target:
                    # Click the document link
                    self.driver.execute_script("arguments[0].click();", target)
                    time.sleep(5)
                    
                    # Check for new tab
                    after_handles = set(self.driver.window_handles)
                    new_handles = after_handles - before_handles
                    
                    if new_handles:
                        new_tab = list(new_handles)[0]
                        self.driver.switch_to.window(new_tab)
                        time.sleep(3)
                        
                        pdf_url = self.driver.current_url
                        print(f"      🔗 PDF URL: {pdf_url[:100]}")
                        
                        # Trigger download
                        safe_name = doc['text'].replace('/', '_').replace('\\', '_').replace(':', '_').strip()[:60]
                        self.driver.execute_script(f"""
                            var a = document.createElement('a');
                            a.href = window.location.href;
                            a.download = '{safe_name}.pdf';
                            document.body.appendChild(a);
                            a.click();
                            a.remove();
                        """)
                        time.sleep(3)
                        
                        # Close PDF tab
                        self.driver.close()
                        self.driver.switch_to.window(main_window)
                        
                        downloaded.append(doc['text'])
                        print(f"      ✅ Downloaded: {safe_name}.pdf")
                    else:
                        # Check if auto-downloaded
                        time.sleep(3)
                        recent = glob.glob(f"{self.output_dir}/*.pdf") + glob.glob(f"{self.output_dir}/*.PDF")
                        if recent:
                            newest = max(recent, key=os.path.getmtime)
                            if time.time() - os.path.getmtime(newest) < 30:
                                downloaded.append(doc['text'])
                                print(f"      ✅ Auto-downloaded: {os.path.basename(newest)}")
                            else:
                                print(f"      ⚠️ No new tab, no recent download")
                        else:
                            print(f"      ⚠️ No new tab, no downloads found")
                else:
                    print(f"      ❌ Could not find link element")
                    
                time.sleep(2)
                
            except Exception as e:
                print(f"      ❌ Error: {str(e)[:100]}")
                try:
                    alert = self.driver.switch_to.alert
                    alert.accept()
                except:
                    pass
                try:
                    self.driver.switch_to.window(main_window)
                except:
                    pass
        
        return downloaded
    
    def run(self):
        """Execute full workflow"""
        print("="*60)
        print(f"🏠 MLS Document Extractor v2 (Power Search)")
        print(f"📍 Address: {self.address}")
        print(f"📂 Output: {self.output_dir}")
        print("="*60)
        
        try:
            if not self.login():
                return False
            
            if not self.navigate_to_paragon():
                return False
            
            if not self.power_search():
                return False
            
            if not self.find_associated_docs():
                # Debug: show what's on the page
                print("\n🔍 Debug - Current page analysis:")
                self.driver.switch_to.default_content()
                url = self.driver.current_url
                title = self.driver.title
                print(f"   URL: {url}")
                print(f"   Title: {title}")
                
                # Check iframes
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                print(f"   Iframes: {len(frames)}")
                for i, f in enumerate(frames):
                    try:
                        src = f.get_attribute('src') or 'no src'
                        print(f"      [{i}] {src[:80]}")
                    except:
                        pass
                
                return False
            
            docs = self.extract_documents(docs_frame_index=getattr(self, '_docs_frame_index', None))
            
            print("\n" + "="*60)
            if docs:
                print(f"🎉 Downloaded {len(docs)} documents:")
                for d in docs:
                    print(f"   📄 {d}")
                print(f"📂 Saved to: {self.output_dir}")
            else:
                print("⚠️ No documents were downloaded")
            print("="*60)
            
            return len(docs) > 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.driver.quit()
            print("🧹 Browser closed")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mls_docs_extractor_v2.py '403 3rd Ave N'")
        sys.exit(1)
    
    address = sys.argv[1]
    extractor = MLSDocExtractor(address)
    success = extractor.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
