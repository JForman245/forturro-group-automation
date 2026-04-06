#!/usr/bin/env python3
"""Inspect CCAR login AFTER clicking email radio"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

chrome_options = Options()
chrome_options.add_argument("--window-size=1400,1000")
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://ccar.mysolidearth.com/portal")
WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
time.sleep(3)

print("=== BEFORE clicking radio ===")
inputs = driver.find_elements(By.TAG_NAME, "input")
for i, inp in enumerate(inputs):
    print(f"  Input {i}: type={inp.get_attribute('type')} name={inp.get_attribute('name')} ph={inp.get_attribute('placeholder')} visible={inp.is_displayed()}")

# Screenshot before
driver.save_screenshot("/tmp/ccar_before_radio.png")

# Click second radio button (email)
radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
print(f"\nFound {len(radios)} radio buttons")
for i, r in enumerate(radios):
    print(f"  Radio {i}: name={r.get_attribute('name')} value={r.get_attribute('value')} checked={r.is_selected()}")

if len(radios) >= 2:
    # Try clicking the parent element instead
    radio_containers = driver.find_elements(By.CSS_SELECTOR, ".v-radio")
    print(f"\nFound {len(radio_containers)} v-radio containers")
    for i, rc in enumerate(radio_containers):
        print(f"  Container {i}: text='{rc.text}' class='{rc.get_attribute('class')}'")
    
    if len(radio_containers) >= 2:
        print(f"\nClicking radio container 1 (email)...")
        radio_containers[1].click()
    else:
        print(f"\nClicking radio 1 via JS...")
        driver.execute_script("arguments[0].click();", radios[1])

time.sleep(3)

print("\n=== AFTER clicking radio ===")
inputs = driver.find_elements(By.TAG_NAME, "input")
for i, inp in enumerate(inputs):
    print(f"  Input {i}: type={inp.get_attribute('type')} name={inp.get_attribute('name')} ph={inp.get_attribute('placeholder')} visible={inp.is_displayed()} id={inp.get_attribute('id')} class={inp.get_attribute('class')}")

# Also check for any labels
labels = driver.find_elements(By.TAG_NAME, "label")
for i, l in enumerate(labels):
    print(f"  Label {i}: text='{l.text}' for='{l.get_attribute('for')}'")

# Check divs with v-text-field
vtf = driver.find_elements(By.CSS_SELECTOR, ".v-text-field")
print(f"\nFound {len(vtf)} v-text-field elements")
for i, v in enumerate(vtf):
    print(f"  VTF {i}: text='{v.text}'")

# Screenshot after
driver.save_screenshot("/tmp/ccar_after_radio.png")

# Also dump buttons
buttons = driver.find_elements(By.TAG_NAME, "button")
for i, b in enumerate(buttons):
    print(f"  Button {i}: text='{b.text}' type='{b.get_attribute('type')}' visible={b.is_displayed()}")

driver.quit()
print("\n✅ Done!")
