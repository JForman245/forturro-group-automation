#!/usr/bin/env python3
"""
Inspect CCAR login page to find exact element selectors
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

chrome_options = Options()
chrome_options.add_argument("--window-size=1400,1000")

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://ccar.mysolidearth.com/portal")

WebDriverWait(driver, 15).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)

time.sleep(3)

# Save screenshot
driver.save_screenshot("/tmp/ccar_login_page.png")
print("📸 Screenshot saved: /tmp/ccar_login_page.png")

# Dump ALL clickable elements
print("\n=== ALL BUTTONS ===")
buttons = driver.find_elements(By.TAG_NAME, "button")
for i, b in enumerate(buttons):
    print(f"  Button {i}: text='{b.text}' | class='{b.get_attribute('class')}' | id='{b.get_attribute('id')}' | type='{b.get_attribute('type')}'")

print("\n=== ALL LINKS ===")
links = driver.find_elements(By.TAG_NAME, "a")
for i, a in enumerate(links):
    print(f"  Link {i}: text='{a.text}' | href='{a.get_attribute('href')}' | class='{a.get_attribute('class')}'")

print("\n=== ALL INPUTS ===")
inputs = driver.find_elements(By.TAG_NAME, "input")
for i, inp in enumerate(inputs):
    print(f"  Input {i}: type='{inp.get_attribute('type')}' | name='{inp.get_attribute('name')}' | id='{inp.get_attribute('id')}' | placeholder='{inp.get_attribute('placeholder')}' | class='{inp.get_attribute('class')}'")

print("\n=== ALL DIVS WITH ONCLICK ===")
divs = driver.find_elements(By.CSS_SELECTOR, "div[onclick], div[role='button'], span[role='button']")
for i, d in enumerate(divs):
    print(f"  Clickable {i}: text='{d.text}' | class='{d.get_attribute('class')}' | role='{d.get_attribute('role')}'")

# Get full page source snippet around login area
print("\n=== PAGE TITLE ===")
print(f"  {driver.title}")

print("\n=== CURRENT URL ===")
print(f"  {driver.current_url}")

# Check for iframes
print("\n=== IFRAMES ===")
iframes = driver.find_elements(By.TAG_NAME, "iframe")
for i, f in enumerate(iframes):
    print(f"  Iframe {i}: src='{f.get_attribute('src')}' | id='{f.get_attribute('id')}'")

driver.quit()
print("\n✅ Inspection complete!")
