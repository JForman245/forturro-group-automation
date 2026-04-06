#!/usr/bin/env python3
"""
MLS Documents Extractor
Downloads actual PDF documents attached to listings (contracts, disclosures, etc.)
Uses same auth/navigation as listing sheet workflow but extracts real documents
"""

import os
import sys
import time
import requests
from urllib.parse import urljoin, urlparse
from datetime import datetime
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

class MLSDocumentExtractor:
    def __init__(self, output_dir="/Users/claw1/Desktop/Drop PDFs for Birdy"):
        self.username = os.getenv('MLS_USERNAME')
        self.password = os.getenv('MLS_PASSWORD')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        if not self.username or not self.password:
            raise ValueError("❌ MLS credentials not found in .env.mls")
        
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver for document downloads"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        # Configure download directory
        download_prefs = {
            "download.default_directory": str(self.output_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", download_prefs)
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        
    def dismiss_popups(self):
        """Dismiss Paragon popup frames that block interaction"""
        try:
            self.driver.execute_script("""
                // Close colorbox overlays
                if (document.getElementById('cboxOverlay')) {
                    document.getElementById('cboxOverlay').style.display='none';
                }
                if (document.getElementById('colorbox')) {
                    document.getElementById('colorbox').style.display='none';
                }
                if (typeof jQuery !== 'undefined' && jQuery.colorbox) {
                    jQuery.colorbox.close();
                }
                
                // Close jQuery UI dialogs
                var dialogs = document.querySelectorAll('.ui-dialog');
                dialogs.forEach(function(d) { d.style.display = 'none'; });
                
                // Click any close buttons
                var closeButtons = document.querySelectorAll(
                    '.ui-dialog-titlebar-close, [title="Close"], button.close, .close-btn, .modal-close'
                );
                closeButtons.forEach(function(btn) { 
                    try { btn.click(); } catch(e) {} 
                });
                
                // Remove modal overlays
                var modals = document.querySelectorAll('.modal-overlay, .overlay, .popup-overlay');
                modals.forEach(function(modal) { modal.remove(); });
                
                // Close notification popups
                var notifications = document.querySelectorAll('.notification, .alert-popup, .toast');
                notifications.forEach(function(notif) { notif.style.display = 'none'; });
            """);
        except Exception as e:
            print(f"⚠️ Popup dismissal failed: {e}")
        
    def login_to_mls(self):
        """Step 1 & 2: Login to CCAR and navigate to Paragon (same as listing sheet workflow)"""
        print("🔐 Logging into CCAR SolidEarth portal...")
        
        # Navigate to CCAR portal
        self.driver.get('https://ccar.mysolidearth.com')
        time.sleep(3)
        
        # Click EMAIL login option (second radio button) 
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
        
        # Wait for login completion
        time.sleep(10)
        print("✅ Successfully logged in")
        
        # Navigate to Paragon MLS
        print("🚀 Navigating to Paragon MLS...")
        paragon_selectors = [
            "a[href*='paragon']",
            "a[href*='mls']",
            "//a[contains(text(), 'Paragon')]",
            "//a[contains(text(), 'MLS')]"
        ]
        
        paragon_link = None
        for selector in paragon_selectors:
            try:
                if selector.startswith("//"):
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    paragon_link = elements[0]
                    print(f"✅ Found Paragon link with selector: {selector}")
                    break
            except:
                continue
        
        if paragon_link:
            paragon_link.click()
            time.sleep(5)
            
            # Switch to new tab if needed
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                print("✅ Switched to Paragon MLS tab")
            
            # CRITICAL: Dismiss popup frames that block interaction
            print("🖼️ Dismissing popup frames...")
            time.sleep(3)
            self.dismiss_popups()
            time.sleep(2)
            self.dismiss_popups()  # Run twice to catch all popups
            print("✅ Popup frames dismissed")
            
            return True
        else:
            print("❌ Could not find Paragon MLS link")
            return False
            
    def search_for_listing(self, address):
        """Step 3: Search for specific property (same as listing sheet workflow)"""
        print(f"🔍 Searching for listing: {address}")
        
        try:
            # Dismiss any remaining popups before searching
            print("🖼️ Final popup check before search...")
            self.dismiss_popups()
            time.sleep(2)
            
            # Look for search functionality
            search_elements = self.driver.find_elements(By.XPATH, 
                "//a[contains(text(), 'Search')] | //a[contains(text(), 'Market')] | //button[contains(text(), 'Search')]")
            
            if search_elements:
                search_elements[0].click()
                print("✅ Accessed search functionality")
                time.sleep(3)
                
                # Dismiss popups again after clicking search
                self.dismiss_popups()
                time.sleep(2)
            
            # CRITICAL: Switch to correct iframe (find the main Paragon interface)
            try:
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                print(f"📄 Found {len(frames)} iframes")
                
                # Try to find the main Paragon iframe (not alerts/warnings)
                main_frame = None
                for i, frame in enumerate(frames):
                    src = frame.get_attribute('src') or ''
                    print(f"   Frame {i}: {src}")
                    
                    # Look for main page iframe (not alerts or warnings)
                    if 'Home/Page.mvc' in src and 'ContactManager' not in src and 'SessionWarning' not in src:
                        main_frame = frame
                        print(f"✅ Found main Paragon iframe: {i}")
                        break
                
                if main_frame:
                    self.driver.switch_to.frame(main_frame)
                    print("✅ Switched to main Paragon iframe")
                    time.sleep(3)
                elif frames:
                    # Fallback to last frame (often the main content)
                    self.driver.switch_to.frame(frames[-1])
                    print(f"⚠️ Using fallback iframe: {len(frames)-1}")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"⚠️ Iframe switch failed: {e}")
            
            # Try multiple approaches to find and interact with search field
            search_approaches = [
                # Approach 1: Working selectors from successful MLS automation
                {
                    'selectors': ["#search", ".search-input", "input[name*='search']", "input[placeholder*='search']"],
                    'method': 'direct'
                },
                # Approach 2: Address-specific selectors
                {
                    'selectors': ["input[placeholder*='address']", "input[name*='address']", "input[id*='address']"],
                    'method': 'direct' 
                },
                # Approach 3: Generic search fields with wait
                {
                    'selectors': ["input[type='search']", "input[type='text']"],
                    'method': 'wait'
                }
            ]
            
            address_field = None
            for approach in search_approaches:
                print(f"   Trying {approach['method']} approach...")
                
                for selector in approach['selectors']:
                    try:
                        if approach['method'] == 'wait':
                            address_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                address_field = elements[0]
                                # Scroll to element and wait for it to be interactive
                                self.driver.execute_script("arguments[0].scrollIntoView();", address_field)
                                time.sleep(2)
                                
                                # Wait for element to be clickable
                                try:
                                    self.wait.until(EC.element_to_be_clickable(address_field))
                                except:
                                    print(f"   ⚠️ Element not clickable: {selector}")
                                    continue
                        
                        if address_field:
                            print(f"✅ Found search field: {selector}")
                            break
                    except Exception as e:
                        print(f"   ⚠️ {selector} failed: {e}")
                        continue
                
                if address_field:
                    break
            
            if address_field:
                try:
                    # Clear and enter address with retries
                    self.driver.execute_script("arguments[0].value = '';", address_field)
                    time.sleep(0.5)
                    
                    address_field.click()
                    time.sleep(0.5)
                    
                    address_field.send_keys(address)
                    print(f"✅ Entered address: {address}")
                    time.sleep(2)
                    
                    # Try multiple submit methods
                    submit_success = False
                    
                    # Method 1: Find submit button
                    submit_selectors = [
                        "button[type='submit']",
                        "input[type='submit']", 
                        "//button[contains(text(), 'Search')]",
                        "//input[@value='Search']"
                    ]
                    
                    for selector in submit_selectors:
                        try:
                            if selector.startswith("//"):
                                submit_btn = self.driver.find_element(By.XPATH, selector)
                            else:
                                submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            
                            submit_btn.click()
                            print(f"✅ Clicked submit: {selector}")
                            submit_success = True
                            break
                        except:
                            continue
                    
                    # Method 2: Press Enter key
                    if not submit_success:
                        from selenium.webdriver.common.keys import Keys
                        address_field.send_keys(Keys.RETURN)
                        print("✅ Pressed Enter to submit")
                        submit_success = True
                    
                    if submit_success:
                        time.sleep(5)
                        return True
                    else:
                        print("❌ Could not submit search")
                        return False
                        
                except Exception as e:
                    print(f"❌ Error entering address: {e}")
                    return False
            else:
                print("❌ Could not find any search field")
                return False
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return False
    
    def access_listing_detail(self):
        """Navigate to first search result's detail page"""
        print("📋 Accessing listing detail page...")
        
        try:
            # Find first listing result link
            result_selectors = [
                "a[href*='listing']",
                "a[href*='detail']",
                "a[href*='property']",
                "//a[contains(@href, 'mls')]",
                "//tr[1]//a"  # First row link in results table
            ]
            
            listing_link = None
            for selector in result_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        listing_link = elements[0]
                        print(f"✅ Found listing link with selector: {selector}")
                        break
                except:
                    continue
            
            if listing_link:
                listing_link.click()
                time.sleep(5)
                print("✅ Opened listing detail page")
                return True
            else:
                print("❌ Could not find listing detail link")
                return False
                
        except Exception as e:
            print(f"❌ Failed to access listing detail: {e}")
            return False
    
    def find_document_section(self):
        """NEW: Find the 'Associated Docs' icon on MLS listing page"""
        print("📁 Looking for 'Associated Docs' icon...")
        
        # Target the Associated Docs icon specifically (based on Jeff's screenshot)
        document_selectors = [
            # Look for Associated Docs icon/button
            "//img[@title='Associated Docs']",
            "//img[@alt='Associated Docs']", 
            "//a[@title='Associated Docs']",
            "//button[@title='Associated Docs']",
            "//span[contains(text(), 'Associated Docs')]",
            "//a[contains(text(), 'Associated Docs')]",
            
            # Look for document-like icons in the listing toolbar
            "//img[contains(@src, 'doc')]",
            "//img[contains(@src, 'document')]",
            "//img[contains(@title, 'Doc')]",
            
            # Generic document icons that might be clickable
            "//i[contains(@class, 'document')]",
            "//span[contains(@class, 'document-icon')]"
        ]
        
        for selector in document_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"✅ Found Associated Docs icon: {selector}")
                    
                    # Scroll to element and click
                    self.driver.execute_script("arguments[0].scrollIntoView();", elements[0])
                    time.sleep(1)
                    elements[0].click()
                    time.sleep(3)
                    return True
            except Exception as e:
                print(f"   ⚠️ {selector} failed: {e}")
                continue
        
        print("❌ Could not find 'Associated Docs' icon")
        print("💡 Looking for any clickable icons in the listing toolbar...")
        
        # Fallback: look for any clickable icons in what appears to be a toolbar
        toolbar_selectors = [
            "//div[contains(@class, 'toolbar')]//img",
            "//div[contains(@class, 'icon')]//img", 
            "//td//img[@title]",  # Icons in table cells with titles
            "//img[@onclick]",     # Any clickable images
        ]
        
        for selector in toolbar_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    title = element.get_attribute('title') or ''
                    src = element.get_attribute('src') or ''
                    
                    # Check if this looks like a document icon
                    if any(word in title.lower() for word in ['doc', 'document', 'file', 'attach']):
                        print(f"✅ Found potential document icon: {title}")
                        self.driver.execute_script("arguments[0].scrollIntoView();", element)
                        time.sleep(1)
                        element.click()
                        time.sleep(3)
                        return True
            except:
                continue
        
        return False
    
    def extract_document_links(self):
        """NEW: Extract all document links from the Associated Docs page"""
        print("🔗 Extracting document links from Associated Docs page...")
        
        document_links = []
        
        # Wait for the Associated Docs page to load
        time.sleep(3)
        
        # Look for document links on the Associated Docs page
        # These are clickable links that open PDFs in new tabs
        link_selectors = [
            "//a[contains(@href, 'pdf') or contains(@href, 'document') or contains(@href, 'file')]",
            "//a[@target='_blank']",  # Links that open in new tab
            "//a[contains(@onclick, 'window.open')]",  # JavaScript new window links
            "//td//a",  # Links in table cells (common for document lists)
            "//tr//a",  # Links in table rows
            "//div[contains(@class, 'document')]//a",
            "//div[contains(@class, 'file')]//a"
        ]
        
        for selector in link_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                
                for element in elements:
                    href = element.get_attribute('href')
                    text = element.text.strip()
                    onclick = element.get_attribute('onclick') or ''
                    
                    # Skip empty or navigation links
                    if not text or len(text) < 3:
                        continue
                        
                    # Skip obvious navigation links
                    if any(nav_word in text.lower() for nav_word in ['back', 'home', 'menu', 'close']):
                        continue
                    
                    # This looks like a document link
                    document_links.append({
                        'url': href,
                        'text': text,
                        'element': element,
                        'onclick': onclick
                    })
                    
                    print(f"   Found: '{text}'")
                        
            except Exception as e:
                print(f"⚠️ Error with selector {selector}: {e}")
                continue
        
        # Remove duplicates based on text
        unique_links = []
        seen_texts = set()
        for link in document_links:
            if link['text'] not in seen_texts:
                unique_links.append(link)
                seen_texts.add(link['text'])
        
        print(f"✅ Found {len(unique_links)} unique document links")
        return unique_links
    
    def download_documents(self, document_links, address):
        """NEW: Download PDFs by clicking links and managing tabs"""
        print("💾 Downloading documents using tab management...")
        
        clean_address = address.replace(' ', '_').replace(',', '').replace('.', '').lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use the existing "Drop PDFs for Birdy" folder structure
        base_folder = Path("/Users/claw1/Desktop/Drop PDFs for Birdy")
        base_folder.mkdir(exist_ok=True)
        
        property_folder = base_folder / f"{clean_address}_{timestamp}"
        property_folder.mkdir(exist_ok=True)
        
        print(f"   📁 Saving to: {property_folder}")
        
        downloaded_files = []
        original_window = self.driver.current_window_handle
        
        for i, doc_link in enumerate(document_links, 1):
            try:
                print(f"   [{i}/{len(document_links)}] Opening: '{doc_link['text']}'")
                
                # Click the link to open PDF in new tab
                self.driver.execute_script("arguments[0].click();", doc_link['element'])
                time.sleep(3)
                
                # Switch to the new tab
                all_windows = self.driver.window_handles
                if len(all_windows) > 1:
                    # Find the new tab (not the original window)
                    new_window = None
                    for window in all_windows:
                        if window != original_window:
                            new_window = window
                            break
                    
                    if new_window:
                        self.driver.switch_to.window(new_window)
                        time.sleep(2)
                        
                        # Check if this is a PDF URL
                        current_url = self.driver.current_url
                        print(f"      🔗 PDF URL: {current_url}")
                        
                        # Try to trigger download using Ctrl+S or right-click
                        try:
                            # Method 1: Use Chrome's print to PDF
                            pdf_data = self.driver.execute_cdp_cmd('Page.printToPDF', {
                                'printBackground': True,
                                'landscape': False,
                                'paperWidth': 8.5,
                                'paperHeight': 11
                            })
                            
                            # Save the PDF
                            import base64
                            pdf_bytes = base64.b64decode(pdf_data['data'])
                            
                            # Clean filename
                            doc_name = doc_link['text'] or f"document_{i}"
                            doc_name = "".join(c for c in doc_name if c.isalnum() or c in (' ', '-', '_')).strip()
                            
                            final_path = property_folder / f"{doc_name}.pdf"
                            with open(final_path, 'wb') as f:
                                f.write(pdf_bytes)
                            
                            downloaded_files.append(final_path)
                            size_kb = final_path.stat().st_size / 1024
                            print(f"      ✅ Saved: {final_path.name} ({size_kb:.1f} KB)")
                            
                        except Exception as pdf_error:
                            print(f"      ⚠️ PDF download failed: {pdf_error}")
                            
                            # Fallback: Try direct download request
                            try:
                                import requests
                                response = requests.get(current_url, timeout=30)
                                if response.status_code == 200:
                                    doc_name = doc_link['text'] or f"document_{i}"
                                    doc_name = "".join(c for c in doc_name if c.isalnum() or c in (' ', '-', '_')).strip()
                                    
                                    final_path = property_folder / f"{doc_name}.pdf"
                                    with open(final_path, 'wb') as f:
                                        f.write(response.content)
                                    
                                    downloaded_files.append(final_path)
                                    size_kb = final_path.stat().st_size / 1024
                                    print(f"      ✅ Downloaded: {final_path.name} ({size_kb:.1f} KB)")
                                else:
                                    print(f"      ❌ Download failed: {response.status_code}")
                            except Exception as req_error:
                                print(f"      ❌ Request failed: {req_error}")
                        
                        # Close the PDF tab and return to documents page
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
                        time.sleep(1)
                    else:
                        print(f"      ⚠️ Could not find new tab")
                else:
                    print(f"      ⚠️ No new tab opened")
                    
            except Exception as e:
                print(f"   ❌ Failed to process {doc_link['text']}: {e}")
                # Make sure we're back on the original window
                try:
                    self.driver.switch_to.window(original_window)
                except:
                    pass
                continue
        
        return downloaded_files, property_folder
    
    def extract_documents_for_address(self, address):
        """Main workflow: Extract all documents for a specific address"""
        print("=" * 60)
        print(f"🏠 MLS Documents Extractor")
        print(f"📍 Address: {address}")
        print("=" * 60)
        
        try:
            # Step 1 & 2: Login (same as listing sheet)
            if not self.login_to_mls():
                return False
            
            # Step 3: Search (same as listing sheet) 
            if not self.search_for_listing(address):
                return False
            
            # Step 4: Access listing detail (same as listing sheet)
            if not self.access_listing_detail():
                return False
            
            # NEW Step 5: Find documents section
            self.find_document_section()  # Optional - may not exist
            
            # NEW Step 6: Extract document links
            document_links = self.extract_document_links()
            
            if not document_links:
                print("❌ No documents found for this listing")
                return False
            
            # NEW Step 7: Download documents
            downloaded_files, property_folder = self.download_documents(document_links, address)
            
            print("=" * 60)
            print(f"🎉 SUCCESS! Downloaded {len(downloaded_files)} documents")
            print(f"📁 Location: {property_folder}")
            for file in downloaded_files:
                size_kb = file.stat().st_size / 1024
                print(f"   📄 {file.name} ({size_kb:.1f} KB)")
            print("=" * 60)
            
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
        print("Usage: python3 mls_docs_extractor.py '1234 Main St, Myrtle Beach'")
        sys.exit(1)
    
    address = sys.argv[1]
    extractor = MLSDocumentExtractor()
    success = extractor.extract_documents_for_address(address)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()