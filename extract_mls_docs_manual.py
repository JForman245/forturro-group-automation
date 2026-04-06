#!/usr/bin/env python3
"""
MLS Documents Extractor - Manual Navigation Version
Assumes you're already on the Associated Docs page and extracts all documents
"""

import os
import sys
import time
import base64
from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def extract_docs_from_current_page(address):
    """Extract all documents from the current Associated Docs page"""
    
    clean_address = address.replace(' ', '_').replace(',', '').replace('.', '').lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Use "Drop PDFs for Birdy" folder
    base_folder = Path("/Users/claw1/Desktop/Drop PDFs for Birdy")
    base_folder.mkdir(exist_ok=True)
    
    property_folder = base_folder / f"{clean_address}_{timestamp}"
    property_folder.mkdir(exist_ok=True)
    
    # Setup Chrome for the extraction
    options = Options()
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("🔗 Please navigate to the Associated Docs page manually")
        print("   1. Go to CCAR MLS")
        print("   2. Search for and open 403 3rd Ave N listing")
        print("   3. Click the Associated Docs icon")
        print("   4. Leave the browser on the Associated Docs page")
        print("   5. Press Enter here when ready...")
        
        input("Press Enter when on Associated Docs page...")
        
        # Now focus on the existing browser window
        current_url = driver.current_url
        print(f"📍 Current page: {current_url}")
        
        # Find all document links
        print("🔍 Finding document links...")
        
        link_selectors = [
            "//a[@target='_blank']",
            "//a[contains(@onclick, 'window.open')]",
            "//td//a",
            "//tr//a"
        ]
        
        document_links = []
        for selector in link_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
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
            return
        
        # Download each document
        downloaded_files = []
        original_window = driver.current_window_handle
        
        for i, doc_link in enumerate(unique_links, 1):
            try:
                print(f"\n[{i}/{len(unique_links)}] Processing: '{doc_link['text']}'")
                
                # Click the link
                driver.execute_script("arguments[0].click();", doc_link['element'])
                time.sleep(3)
                
                # Handle new tab
                all_windows = driver.window_handles
                if len(all_windows) > 1:
                    new_window = [w for w in all_windows if w != original_window][0]
                    driver.switch_to.window(new_window)
                    time.sleep(2)
                    
                    current_url = driver.current_url
                    print(f"   📄 PDF URL: {current_url}")
                    
                    # Download using Chrome DevTools
                    try:
                        pdf_data = driver.execute_cdp_cmd('Page.printToPDF', {
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
                        print(f"   ✅ Saved: {final_path.name} ({size_kb:.1f} KB)")
                        
                    except Exception as e:
                        print(f"   ❌ PDF generation failed: {e}")
                    
                    # Close tab and return
                    driver.close()
                    driver.switch_to.window(original_window)
                    time.sleep(1)
                else:
                    print("   ⚠️ No new tab opened")
                    
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                try:
                    driver.switch_to.window(original_window)
                except:
                    pass
                continue
        
        print("\n" + "="*60)
        print(f"🎉 EXTRACTION COMPLETE!")
        print(f"📁 Location: {property_folder}")
        print(f"📄 Downloaded {len(downloaded_files)} documents:")
        for file in downloaded_files:
            size_kb = file.stat().st_size / 1024
            print(f"   • {file.name} ({size_kb:.1f} KB)")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 extract_mls_docs_manual.py '403 3rd Ave N'")
        sys.exit(1)
    
    address = sys.argv[1]
    extract_docs_from_current_page(address)