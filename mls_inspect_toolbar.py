#!/usr/bin/env python3
"""Inspect Paragon toolbar dropdown menus to find PDF option"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')
MLS_USERNAME = os.getenv('MLS_USERNAME')
MLS_PASSWORD = os.getenv('MLS_PASSWORD')

chrome_options = Options()
chrome_options.add_argument("--window-size=1400,1000")
driver = webdriver.Chrome(options=chrome_options)

# Login
driver.get("https://ccar.mysolidearth.com/portal")
WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
time.sleep(3)
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

# Dismiss overlay
driver.execute_script("""
    if (document.getElementById('cboxOverlay')) document.getElementById('cboxOverlay').style.display='none';
    if (document.getElementById('colorbox')) document.getElementById('colorbox').style.display='none';
    if (typeof jQuery !== 'undefined' && jQuery.colorbox) jQuery.colorbox.close();
""")
time.sleep(2)

# Power search
search_input = driver.find_element(By.CSS_SELECTOR, "input.select2-search__field")
driver.execute_script("arguments[0].click();", search_input)
time.sleep(1)
search_input.send_keys("5600 Joyner Swamp Rd")
time.sleep(3)
from selenium.webdriver.common.keys import Keys
search_input.send_keys(Keys.RETURN)
print("⏳ Searching...")
time.sleep(8)

# Find listing iframe
iframes = driver.find_elements(By.TAG_NAME, "iframe")
listing_iframe = None
for i, iframe in enumerate(iframes):
    src = iframe.get_attribute("src") or ""
    if "Search" in src or "listingIds" in src:
        listing_iframe = i
        break

if listing_iframe is not None:
    driver.switch_to.frame(iframes[listing_iframe])
    print(f"✅ In listing iframe {listing_iframe}")
else:
    print("❌ No listing iframe")
    driver.quit()
    exit()

# Now thoroughly inspect the toolbar
print("\n=== ALL ELEMENTS IN TOOLBAR AREA ===")

# Get the full HTML of the toolbar
toolbar_html = driver.execute_script("""
    var toolbar = document.querySelector('.toolbar, .action-bar, .btn-toolbar, [class*="toolbar"], [class*="action"]');
    if (toolbar) return toolbar.outerHTML;
    // Try getting parent of Print link
    var printEl = document.querySelector('a[title*="Print"]');
    if (printEl) return printEl.parentElement.parentElement.outerHTML;
    return 'NOT FOUND';
""")
print(f"Toolbar HTML snippet: {str(toolbar_html)[:500]}")

# Find all links and their parent elements
print("\n=== DETAILED LINK ANALYSIS ===")
all_links = driver.find_elements(By.TAG_NAME, "a")
for i, link in enumerate(all_links[:40]):
    text = link.text.strip().replace('\n', ' ')
    href = link.get_attribute("href") or ""
    cls = link.get_attribute("class") or ""
    title = link.get_attribute("title") or ""
    parent_tag = driver.execute_script("return arguments[0].parentElement.tagName;", link)
    parent_cls = driver.execute_script("return arguments[0].parentElement.className;", link) or ""
    onclick = link.get_attribute("onclick") or ""
    print(f"  Link {i}: text='{text}' cls='{cls[:50]}' title='{title}' href='{href[:80]}' onclick='{onclick[:80]}' parent={parent_tag}.{parent_cls[:30]}")

# Specifically look at Print link
print("\n=== PRINT LINK DETAILS ===")
for link in all_links:
    if "Print" in (link.text or ""):
        print(f"  Text: '{link.text}'")
        print(f"  Class: '{link.get_attribute('class')}'")
        print(f"  Onclick: '{link.get_attribute('onclick')}'")
        print(f"  Href: '{link.get_attribute('href')}'")
        
        # Get sibling/child elements
        children = link.find_elements(By.XPATH, "./*")
        print(f"  Children: {len(children)}")
        for c in children:
            print(f"    Child: tag={c.tag_name} text='{c.text}' class='{c.get_attribute('class')}'")
        
        # Get parent and siblings
        parent_html = driver.execute_script("return arguments[0].parentElement.outerHTML;", link)
        print(f"  Parent HTML: {parent_html[:300]}")
        
        # Get next sibling (likely the dropdown menu)
        next_sib = driver.execute_script("""
            var el = arguments[0];
            var parent = el.parentElement;
            var siblings = parent.children;
            for (var i = 0; i < siblings.length; i++) {
                if (siblings[i] === el && i+1 < siblings.length) {
                    return siblings[i+1].outerHTML;
                }
            }
            // Also check parent's next sibling
            if (parent.nextElementSibling) return parent.nextElementSibling.outerHTML;
            return 'NO NEXT SIBLING';
        """, link)
        print(f"  Next sibling HTML: {str(next_sib)[:500]}")

# Also check for More link
print("\n=== MORE LINK DETAILS ===")
for link in all_links:
    if "More" in (link.text or ""):
        print(f"  Text: '{link.text}'")
        parent_html = driver.execute_script("return arguments[0].parentElement.outerHTML;", link)
        print(f"  Parent HTML: {parent_html[:300]}")
        
        next_sib = driver.execute_script("""
            var el = arguments[0];
            var parent = el.parentElement;
            if (parent.nextElementSibling) return parent.nextElementSibling.outerHTML;
            var siblings = parent.children;
            for (var i = 0; i < siblings.length; i++) {
                if (siblings[i] === el && i+1 < siblings.length) return siblings[i+1].outerHTML;
            }
            return 'NO SIBLING';
        """, link)
        print(f"  Next sibling: {str(next_sib)[:500]}")

driver.quit()
print("\n✅ Inspection complete!")
