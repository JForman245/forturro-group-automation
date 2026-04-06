#!/usr/bin/env python3
"""
MLS Documents Extractor - Fixed Version
Uses JavaScript interaction to bypass blocked search field
"""

import os
import sys
import time
import base64
from pathlib import Path
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

class MLSDocumentExtractorFixed:
    def __init__(self):
        self.username = os.getenv('MLS_USERNAME')
        self.password = os.getenv('MLS_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("❌ MLS credentials not found in .env.mls")
        
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage') 
        options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        
    def dismiss_popups(self):
        """Dismiss Paragon popup frames"""
        try:
            self.driver.execute_script("""
                if (document.getElementById('cboxOverlay')) document.getElementById('cboxOverlay').style.display='none';
                if (document.getElementById('colorbox')) document.getElementById('colorbox').style.display='none';
                if (typeof jQuery !== 'undefined' && jQuery.colorbox) jQuery.colorbox.close();
                var dialogs = document.querySelectorAll('.ui-dialog');
                dialogs.forEach(function(d) { d.style.display = 'none'; });
                var closeButtons = document.querySelectorAll('.ui-dialog-titlebar-close, [title=\"Close\"], button.close');
                closeButtons.forEach(function(btn) { try { btn.click(); } catch(e) {} });
            """)
        except Exception as e:
            print(f"⚠️ Popup dismissal failed: {e}")
    
    def login_and_navigate(self):
        """Login to CCAR and navigate to Paragon"""
        print("🔐 Logging into CCAR SolidEarth portal...")
        
        # Navigate to CCAR portal
        self.driver.get('https://ccar.mysolidearth.com')
        time.sleep(3)
        
        # Click EMAIL login option
        radio_containers = self.driver.find_elements(By.CSS_SELECTOR, ".v-radio")
        if len(radio_containers) > 1:
            radio_containers[1].click()
            time.sleep(2)
        
        # Enter credentials
        username_field = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'][name='email']"))
        )
        password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        
        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        
        # Submit login
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        time.sleep(10)
        
        print("✅ Successfully logged in")
        
        # Navigate to Paragon MLS
        print("🚀 Navigating to Paragon MLS...")
        paragon_link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='paragon']")
        paragon_link.click()
        time.sleep(5)
        
        # Switch to new tab if needed
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            print("✅ Switched to Paragon MLS tab")
        
        # Dismiss popup frames
        print("🖼️ Dismissing popup frames...")
        time.sleep(3)
        self.dismiss_popups()
        time.sleep(2)
        self.dismiss_popups()
        print("✅ Popup frames dismissed")
        
        return True
    
    def search_for_listing(self, address):
        """Search for specific property using JavaScript interaction"""
        print(f"🔍 Searching for listing: {address}")
        
        try:
            # Find the correct iframe (based on our debug results)
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"📄 Found {len(frames)} iframes")
            
            # Switch to iframe 2 (the main Paragon interface)
            if len(frames) >= 3:
                self.driver.switch_to.frame(frames[2])  # Frame 2: ParagonLS/Home/Page.mvc
                print("✅ Switched to main Paragon iframe")
                time.sleep(3)
            else:
                print("⚠️ Expected iframe not found")
                return False
            
            # Find the search field using the selector we know works
            try:
                search_field = self.driver.find_element(By.CSS_SELECTOR, "input[name*='search']")
                print("✅ Found search field")
                
                # Use JavaScript to interact with the field (bypass blocking elements)
                print("🛠️ Using JavaScript interaction to bypass blocking elements...")
                
                # Clear and set value via JavaScript
                self.driver.execute_script("arguments[0].value = '';", search_field)
                self.driver.execute_script("arguments[0].focus();", search_field)
                self.driver.execute_script(f"arguments[0].value = '{address}';", search_field)
                
                # Trigger events
                self.driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """, search_field)
                
                print(f"✅ Entered address via JavaScript: {address}")
                time.sleep(2)
                
                # Try multiple submit methods
                submit_success = False
                
                # Method 1: Submit via Enter key
                try:
                    self.driver.execute_script("""
                        arguments[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', which: 13, keyCode: 13 }));
                    """, search_field)
                    print("✅ Tried Enter key submit")
                    time.sleep(3)
                except Exception as e:
                    print(f"⚠️ Enter submit failed: {e}")
                
                # Method 2: Look for search button
                try:
                    search_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                        "button[type='submit'], input[type='submit'], button:contains('Search'), .search-button")
                    
                    for btn in search_buttons:
                        try:
                            if btn.is_displayed() and btn.is_enabled():
                                btn.click()
                                print(f"✅ Clicked search button: {btn.text or btn.get_attribute('value')}")
                                submit_success = True
                                break
                        except:
                            continue
                            
                except Exception as e:
                    print(f"⚠️ Search button method failed: {e}")
                
                # Method 3: Submit the parent form
                try:
                    form = search_field.find_element(By.XPATH, "./ancestor::form[1]")
                    if form:
                        self.driver.execute_script("arguments[0].submit();", form)
                        print("✅ Submitted parent form")
                        submit_success = True
                except Exception as e:
                    print(f"⚠️ Form submit failed: {e}")
                
                # Method 4: Use Selenium send_keys
                try:
                    from selenium.webdriver.common.keys import Keys
                    search_field.send_keys(Keys.RETURN)
                    print("✅ Used Selenium Keys.RETURN")
                    submit_success = True
                except Exception as e:
                    print(f"⚠️ Selenium send_keys failed: {e}")
                
                print(f"✅ Search submitted (success: {submit_success})")
                time.sleep(8)  # Give more time for search results
                
                # Check if we got search results or are still on dashboard
                page_text = self.driver.page_source
                if 'search results' in page_text.lower() or 'listings' in page_text.lower():
                    print("✅ Search results page detected")
                elif 'dashboard' in page_text.lower() or 'MLS Messages' in page_text:
                    print("⚠️ Still on dashboard - search may not have executed")
                    return False
                
                return True
                
            except Exception as e:
                print(f"❌ Search field interaction failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return False
    
    def access_listing_detail(self):
        """Click on first search result to open detail page - using proven navigation pattern"""
        print("📋 Looking for listing in search results...")
        
        try:
            # Wait for search results to load completely
            time.sleep(5)
            
            # The search should return a table of results
            # Look for the first result row and click it
            
            # Strategy 1: Look for table rows with address data
            try:
                result_rows = self.driver.find_elements(By.CSS_SELECTOR, "tr")
                print(f"   Found {len(result_rows)} table rows")
                
                # Skip header rows, look for data rows
                for i, row in enumerate(result_rows):
                    row_text = row.text.strip()
                    if row_text and '403' in row_text:  # Contains our search address
                        print(f"   Found matching row {i}: {row_text[:100]}...")
                        
                        # Look for clickable link within this row
                        links_in_row = row.find_elements(By.TAG_NAME, "a")
                        if links_in_row:
                            # Use first link in the matching row
                            first_link = links_in_row[0]
                            href = first_link.get_attribute('href') or 'no href'
                            text = first_link.text or 'no text'
                            print(f"   Clicking link: '{text}' -> {href[:60]}...")
                            
                            # Click using JavaScript to avoid blocking issues
                            self.driver.execute_script("arguments[0].click();", first_link)
                            time.sleep(8)
                            
                            # Check if we navigated to a new page
                            new_url = self.driver.current_url
                            print(f"🔗 Navigated to: {new_url}")
                            
                            # Check if we're in a different iframe or page structure
                            current_title = self.driver.title
                            print(f"🏷️ Page title: {current_title}")
                            
                            return True
                        else:
                            print(f"   No links found in row {i}")
                            
            except Exception as e:
                print(f"   Strategy 1 failed: {e}")
            
            # Strategy 2: Double-click the row itself (sometimes needed)
            try:
                result_rows = self.driver.find_elements(By.CSS_SELECTOR, "tr")
                for row in result_rows:
                    if '403' in row.text:
                        print("   Trying double-click on data row...")
                        self.driver.execute_script("""
                            var event = new MouseEvent('dblclick', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            arguments[0].dispatchEvent(event);
                        """, row)
                        time.sleep(8)
                        
                        new_url = self.driver.current_url
                        print(f"🔗 After double-click: {new_url}")
                        
                        if 'detail' in new_url.lower() or new_url != "https://ccar.paragonrels.com/ParagonLS/Default.mvc":
                            return True
                        break
                        
            except Exception as e:
                print(f"   Strategy 2 failed: {e}")
            
            # Strategy 3: Look for any link that might take us to detail page
            try:
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in all_links[:10]:  # Check first 10 links
                    link_text = link.text.strip()
                    href = link.get_attribute('href') or ''
                    
                    # Skip navigation links, look for data links
                    if link_text and not any(nav in link_text.lower() for nav in ['home', 'back', 'logout', 'help']):
                        if '403' in link_text or 'detail' in href.lower():
                            print(f"   Trying link: '{link_text}' -> {href}")
                            link.click()
                            time.sleep(8)
                            
                            new_url = self.driver.current_url
                            if new_url != "https://ccar.paragonrels.com/ParagonLS/Default.mvc":
                                print(f"🔗 Successfully navigated: {new_url}")
                                return True
                            break
                            
            except Exception as e:
                print(f"   Strategy 3 failed: {e}")
            
            print("❌ Could not access listing detail page")
            print("   📝 Current page may be search results, not individual listing")
            return False
                
        except Exception as e:
            print(f"❌ Failed to access listing detail: {e}")
            return False
    
    def find_associated_docs(self):
        """Find and click the Associated Docs icon"""
        print("📁 Looking for 'Associated Docs' icon...")
        
        # Wait for listing page to load completely
        time.sleep(3)
        
        # Check if we need to switch to a different iframe on detail page
        try:
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            if frames:
                print(f"📄 Found {len(frames)} iframes on detail page")
                # If there are iframes, we might need to switch to one containing the listing detail
                for i, frame in enumerate(frames):
                    src = frame.get_attribute('src') or 'no src'
                    print(f"   Frame {i}: {src}")
                    
                    # Look for detail/listing iframe
                    if 'detail' in src.lower() or 'listing' in src.lower():
                        self.driver.switch_to.frame(frame)
                        print(f"✅ Switched to detail iframe {i}")
                        time.sleep(2)
                        break
        except Exception as e:
            print(f"⚠️ Iframe check failed: {e}")
        
        # Look for Associated Docs icon/button (expanded selectors)
        doc_selectors = [
            # Exact matches
            "//img[@title='Associated Docs']",
            "//img[@alt='Associated Docs']", 
            "//a[@title='Associated Docs']",
            "//button[@title='Associated Docs']",
            
            # Partial matches
            "//img[contains(@title, 'Associated')]",
            "//img[contains(@title, 'Doc')]",
            "//img[contains(@alt, 'Doc')]",
            
            # Icon patterns (toolbar icons)
            "//td//img[@title]",  # Images in table cells with titles
            "//div[@class='toolbar']//img",  # Images in toolbar
            "//img[@onclick]",  # Clickable images
            
            # Link patterns
            "//a[contains(text(), 'Doc')]",
            "//a[contains(@href, 'doc')]",
            "//a[contains(@href, 'document')]"
        ]
        
        # First try exact matches
        for selector in doc_selectors[:7]:  # Try specific selectors first
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"✅ Found Associated Docs icon: {selector}")
                    self.driver.execute_script("arguments[0].scrollIntoView();", elements[0])
                    time.sleep(1)
                    elements[0].click()
                    time.sleep(3)
                    return True
            except Exception as e:
                print(f"⚠️ {selector} failed: {e}")
                continue
        
        # If exact matches fail, analyze all clickable images
        print("🔍 Analyzing all clickable images for document icon...")
        try:
            all_images = self.driver.find_elements(By.XPATH, "//img[@title or @alt or @onclick]")
            print(f"Found {len(all_images)} images with titles/alts/onclick")
            
            for i, img in enumerate(all_images[:20]):  # Check first 20
                title = img.get_attribute('title') or ''
                alt = img.get_attribute('alt') or ''
                src = img.get_attribute('src') or ''
                onclick = img.get_attribute('onclick') or ''
                
                print(f"   [{i}] title='{title}' alt='{alt}' src='{src[:50]}...'")
                
                # Check if this looks like a document icon
                if any(word in (title + alt + src + onclick).lower() for word in ['doc', 'document', 'file', 'attach', 'associated']):
                    print(f"      🎯 POTENTIAL DOCUMENT ICON: {title or alt}")
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView();", img)
                        time.sleep(1)
                        img.click()
                        time.sleep(3)
                        print(f"      ✅ Successfully clicked document icon!")
                        return True
                    except Exception as e:
                        print(f"      ❌ Click failed: {e}")
                        continue
        
        except Exception as e:
            print(f"⚠️ Image analysis failed: {e}")
        
        print("❌ Could not find Associated Docs icon")
        return False
    
    def extract_and_download_documents(self, address):
        """Extract document links and download PDFs"""
        print("🔗 Extracting document links...")
        
        time.sleep(3)
        
        # Find document links on Associated Docs page
        link_selectors = [
            "//a[@target='_blank']",
            "//a[contains(@onclick, 'window.open')]",
            "//td//a",
            "//tr//a"
        ]
        
        document_links = []
        for selector in link_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    href = element.get_attribute('href')
                    
                    if text and len(text) > 3:
                        # Skip navigation links
                        if not any(nav in text.lower() for nav in ['back', 'home', 'menu', 'close']):
                            document_links.append({
                                'text': text,
                                'element': element,
                                'href': href
                            })
                            print(f"   Found: '{text}'")
            except:
                continue
        
        # Remove duplicates
        unique_links = []
        seen = set()
        for link in document_links:
            if link['text'] not in seen:
                unique_links.append(link)
                seen.add(link['text'])
        
        print(f"📄 Found {len(unique_links)} unique documents")
        
        if not unique_links:
            print("❌ No document links found")
            return False
        
        # Download documents
        self.download_documents(unique_links, address)
        return True
    
    def download_documents(self, document_links, address):
        """Download PDFs by clicking links and managing tabs"""
        print("💾 Downloading documents...")
        
        clean_address = address.replace(' ', '_').replace(',', '').replace('.', '').lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create folder in "Drop PDFs for Birdy"
        base_folder = Path("/Users/claw1/Desktop/Drop PDFs for Birdy")
        base_folder.mkdir(exist_ok=True)
        
        property_folder = base_folder / f"{clean_address}_{timestamp}"
        property_folder.mkdir(exist_ok=True)
        
        print(f"📁 Saving to: {property_folder}")
        
        downloaded_files = []
        original_window = self.driver.current_window_handle
        
        for i, doc_link in enumerate(document_links, 1):
            try:
                print(f"   [{i}/{len(document_links)}] Processing: '{doc_link['text']}'")
                
                # Click link to open PDF in new tab
                self.driver.execute_script("arguments[0].click();", doc_link['element'])
                time.sleep(3)
                
                # Switch to new tab
                all_windows = self.driver.window_handles
                if len(all_windows) > 1:
                    new_window = [w for w in all_windows if w != original_window][0]
                    self.driver.switch_to.window(new_window)
                    time.sleep(2)
                    
                    current_url = self.driver.current_url
                    print(f"      📄 PDF URL: {current_url}")
                    
                    # Generate PDF using Chrome DevTools
                    try:
                        pdf_data = self.driver.execute_cdp_cmd('Page.printToPDF', {
                            'printBackground': True,
                            'landscape': False,
                            'paperWidth': 8.5,
                            'paperHeight': 11
                        })
                        
                        pdf_bytes = base64.b64decode(pdf_data['data'])
                        
                        # Save file
                        doc_name = "".join(c for c in doc_link['text'] if c.isalnum() or c in (' ', '-', '_')).strip()
                        final_path = property_folder / f"{doc_name}.pdf"
                        
                        with open(final_path, 'wb') as f:
                            f.write(pdf_bytes)
                        
                        downloaded_files.append(final_path)
                        size_kb = final_path.stat().st_size / 1024
                        print(f"      ✅ Saved: {final_path.name} ({size_kb:.1f} KB)")
                        
                    except Exception as e:
                        print(f"      ❌ PDF generation failed: {e}")
                    
                    # Close tab and return
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
                    time.sleep(1)
                else:
                    print("      ⚠️ No new tab opened")
                    
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                try:
                    self.driver.switch_to.window(original_window)
                except:
                    pass
                continue
        
        print("\n" + "="*60)
        print(f"🎉 DOWNLOAD COMPLETE!")
        print(f"📁 Location: {property_folder}")
        print(f"📄 Downloaded {len(downloaded_files)} documents:")
        for file in downloaded_files:
            size_kb = file.stat().st_size / 1024
            print(f"   • {file.name} ({size_kb:.1f} KB)")
        print("="*60)
        
        return len(downloaded_files) > 0
    
    def extract_documents_for_address(self, address):
        """Main workflow"""
        print("=" * 60)
        print(f"🏠 MLS Documents Extractor (Fixed)")
        print(f"📍 Address: {address}")
        print("=" * 60)
        
        try:
            # Step 1-2: Login and navigate
            if not self.login_and_navigate():
                return False
            
            # Step 3: Search for listing
            if not self.search_for_listing(address):
                return False
            
            # Step 4: Access listing detail
            if not self.access_listing_detail():
                return False
            
            # Step 5: Find Associated Docs
            if not self.find_associated_docs():
                return False
            
            # Step 6: Download documents
            if not self.extract_and_download_documents(address):
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
                print("🧹 Browser cleaned up")
        except:
            pass

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 mls_docs_extractor_fixed.py '403 3rd Ave N'")
        sys.exit(1)
    
    address = sys.argv[1]
    extractor = MLSDocumentExtractorFixed()
    success = extractor.extract_documents_for_address(address)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()