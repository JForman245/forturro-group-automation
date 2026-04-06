#!/usr/bin/env python3
"""Inspect Paragon MLS after login to find search interface"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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

# Click email radio
radio_containers = driver.find_elements(By.CSS_SELECTOR, ".v-radio")
if len(radio_containers) >= 2:
    radio_containers[1].click()
time.sleep(2)

# Enter credentials
email_field = driver.find_element(By.CSS_SELECTOR, "input[type='email'][name='email']")
email_field.send_keys(MLS_USERNAME)
password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
password_field.send_keys(MLS_PASSWORD)
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

print("⏳ Logging in...")
time.sleep(10)

# Click MLS link
all_links = driver.find_elements(By.TAG_NAME, "a")
for link in all_links:
    href = (link.get_attribute("href") or "").lower()
    text = link.text.strip().lower()
    if "paragon" in href or "paragon" in text or "mls" in text:
        print(f"Clicking: text='{link.text}' href='{link.get_attribute('href')}'")
        link.click()
        break

time.sleep(8)

# Switch to MLS tab
if len(driver.window_handles) > 1:
    driver.switch_to.window(driver.window_handles[-1])
    print(f"Switched to tab: {driver.current_url}")

time.sleep(3)

# Now inspect the main Paragon page (NOT inside iframe)
print(f"\n=== MAIN PAGE ===")
print(f"URL: {driver.current_url}")
print(f"Title: {driver.title}")

# Screenshot the main page
driver.save_screenshot("/tmp/paragon_main.png")

# Look at all iframes
iframes = driver.find_elements(By.TAG_NAME, "iframe")
print(f"\n=== IFRAMES ({len(iframes)}) ===")
for i, f in enumerate(iframes):
    src = f.get_attribute("src") or ""
    print(f"  Iframe {i}: src={src[:120]}")

# Look at top-level nav/menu
print("\n=== TOP-LEVEL LINKS ===")
links = driver.find_elements(By.TAG_NAME, "a")
for i, l in enumerate(links[:30]):
    text = l.text.strip()
    href = l.get_attribute("href") or ""
    if text or "search" in href.lower() or "listing" in href.lower():
        print(f"  Link {i}: text='{text}' href='{href[:100]}'")

print("\n=== TOP-LEVEL BUTTONS ===")
buttons = driver.find_elements(By.TAG_NAME, "button")
for i, b in enumerate(buttons[:20]):
    print(f"  Button {i}: text='{b.text}' id='{b.get_attribute('id')}' class='{b.get_attribute('class')[:60]}'")

# Look for nav menus
print("\n=== NAV/MENU ELEMENTS ===")
navs = driver.find_elements(By.CSS_SELECTOR, "nav, .nav, .menu, .toolbar, [role='navigation'], [role='menu'], [role='menubar']")
for i, n in enumerate(navs[:10]):
    print(f"  Nav {i}: tag={n.tag_name} text='{n.text[:100]}' class='{n.get_attribute('class')[:60]}'")

# Look for tabs
print("\n=== TAB-LIKE ELEMENTS ===")
tabs = driver.find_elements(By.CSS_SELECTOR, ".tab, [role='tab'], .ui-tabs-anchor, li.ui-tab")
for i, t in enumerate(tabs[:15]):
    print(f"  Tab {i}: text='{t.text}' class='{t.get_attribute('class')[:60]}'")

# Check for quicksearch or address lookup
print("\n=== SEARCH-RELATED ELEMENTS (main frame) ===")
search_els = driver.find_elements(By.CSS_SELECTOR, "[id*='search' i], [id*='Search'], [class*='search' i], [placeholder*='search' i], [id*='quick' i], [id*='Quick']")
for i, s in enumerate(search_els[:10]):
    print(f"  Search {i}: tag={s.tag_name} id='{s.get_attribute('id')}' class='{s.get_attribute('class')[:60]}'")

driver.quit()
print("\n✅ Inspection complete!")
