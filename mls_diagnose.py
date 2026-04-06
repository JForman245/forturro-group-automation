#!/usr/bin/env python3
"""Diagnostic script to explore Paragon search form fields and iframe structure."""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')
MLS_USERNAME = os.getenv('MLS_USERNAME')
MLS_PASSWORD = os.getenv('MLS_PASSWORD')

def dismiss_popups(driver):
    driver.execute_script("""
        if (document.getElementById('cboxOverlay')) document.getElementById('cboxOverlay').style.display='none';
        if (document.getElementById('colorbox')) document.getElementById('colorbox').style.display='none';
        if (typeof jQuery !== 'undefined' && jQuery.colorbox) jQuery.colorbox.close();
        var dialogs = document.querySelectorAll('.ui-dialog');
        dialogs.forEach(function(d) { d.style.display = 'none'; });
        var closeButtons = document.querySelectorAll('.ui-dialog-titlebar-close, [title="Close"], button.close');
        closeButtons.forEach(function(btn) { try { btn.click(); } catch(e) {} });
    """)

def login(driver):
    print("⏳ Loading CCAR portal...")
    driver.get("https://ccar.mysolidearth.com/portal")
    time.sleep(5)
    radio_containers = driver.find_elements(By.CSS_SELECTOR, ".v-radio")
    radio_containers[1].click()
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, "input[type='email'][name='email']").send_keys(MLS_USERNAME)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(MLS_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    print("⏳ Logging in...")
    time.sleep(10)
    
    all_links = driver.find_elements(By.TAG_NAME, "a")
    for link in all_links:
        href = (link.get_attribute("href") or "").lower()
        if "paragon" in href:
            link.click()
            break
    time.sleep(10)
    
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
    time.sleep(3)
    dismiss_popups(driver)
    time.sleep(3)
    dismiss_popups(driver)
    time.sleep(1)
    print("✅ Logged into Paragon")

def go_to_search(driver):
    print("🔍 Opening Property Search...")
    driver.execute_script("""
        var links = document.querySelectorAll('a');
        for (var i = 0; i < links.length; i++) {
            if (links[i].textContent.trim() === 'Search') { links[i].click(); return; }
        }
    """)
    time.sleep(2)
    driver.execute_script("""
        var links = document.querySelectorAll('a');
        for (var i = 0; i < links.length; i++) {
            var text = links[i].textContent.trim();
            var href = links[i].getAttribute('href') || '';
            if (text === 'Property' || href.includes('Property.mvc')) { links[i].click(); return; }
        }
    """)
    time.sleep(5)

def find_search_iframe(driver):
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"\n📋 Found {len(iframes)} iframes:")
    for i, iframe in enumerate(iframes):
        src = iframe.get_attribute("src") or ""
        name = iframe.get_attribute("name") or ""
        id_ = iframe.get_attribute("id") or ""
        print(f"  [{i}] id={id_}, name={name}, src={src[:120]}")
    
    for i, iframe in enumerate(iframes):
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(iframe)
            has_status = driver.execute_script(
                "return document.getElementById('f_11__1-2-3-4-5-6-7') !== null;"
            )
            if has_status:
                print(f"\n✅ Search form in iframe [{i}]")
                return True
        except:
            pass
    return False

def dump_form_fields(driver):
    """Dump all input/select fields in the search form"""
    fields = driver.execute_script("""
        var result = [];
        // All inputs
        var inputs = document.querySelectorAll('input, select, textarea');
        for (var i = 0; i < inputs.length; i++) {
            var el = inputs[i];
            result.push({
                tag: el.tagName,
                type: el.type || '',
                id: el.id || '',
                name: el.name || '',
                value: el.value || '',
                placeholder: el.placeholder || '',
                className: el.className || '',
                visible: el.offsetParent !== null
            });
        }
        return result;
    """)
    
    print(f"\n📋 Form fields ({len(fields)} total):")
    # Show fields that look date-related
    date_fields = []
    status_fields = []
    interesting = []
    for f in fields:
        fid = f['id'].lower()
        fname = f['name'].lower()
        fclass = f['className'].lower()
        fph = f['placeholder'].lower()
        
        if any(x in fid or x in fname or x in fph for x in ['date', 'day', 'time', 'period', 'from', 'to', 'range', 'back', 'mm']):
            date_fields.append(f)
        if any(x in fid or x in fname for x in ['status', 'stat', 'f_11']):
            status_fields.append(f)
        if f['visible'] and f['id']:
            interesting.append(f)
    
    print(f"\n🗓️ DATE-RELATED FIELDS ({len(date_fields)}):")
    for f in date_fields:
        print(f"  id={f['id']}, name={f['name']}, type={f['type']}, value={f['value']}, placeholder={f['placeholder']}, visible={f['visible']}")
    
    print(f"\n📊 STATUS FIELDS ({len(status_fields)}):")
    for f in status_fields:
        print(f"  id={f['id']}, name={f['name']}, type={f['type']}, value={f['value']}, class={f['className'][:60]}")
    
    print(f"\n📝 ALL VISIBLE FIELDS WITH IDs ({len([f for f in interesting])}):")
    for f in interesting:
        print(f"  id={f['id']}, type={f['type']}, value={f['value'][:50] if f['value'] else ''}, placeholder={f['placeholder']}")
    
    # Also check for labels near date fields
    labels = driver.execute_script("""
        var result = [];
        var labels = document.querySelectorAll('label, .f-label, td.fieldLabel, span.field-label');
        for (var i = 0; i < labels.length; i++) {
            var text = labels[i].textContent.trim();
            if (text.toLowerCase().match(/date|day|time|period|from|to|expire|withdraw|status|list/)) {
                result.push({
                    text: text,
                    forId: labels[i].getAttribute('for') || '',
                    className: labels[i].className
                });
            }
        }
        return result;
    """)
    print(f"\n🏷️ DATE/STATUS LABELS ({len(labels)}):")
    for l in labels:
        print(f"  text='{l['text']}', for={l['forId']}, class={l['className']}")
    
    # Check for the mmdaysback field specifically
    mmdaysback = driver.execute_script("""
        var el = document.getElementById('mmdaysback');
        if (!el) return 'NOT FOUND';
        return {
            id: el.id,
            tag: el.tagName,
            type: el.type || '',
            value: el.value || '',
            visible: el.offsetParent !== null,
            parent: el.parentElement ? el.parentElement.innerHTML.substring(0, 200) : ''
        };
    """)
    print(f"\n🔍 mmdaysback field: {mmdaysback}")

def set_status_and_count(driver, status_value):
    """Set status and click Count to see how many results"""
    print(f"\n🔍 Setting status to {status_value}...")
    
    # Type in the status field
    driver.execute_script("""
        var field = document.getElementById('f_11__1-2-3-4-5-6-7');
        field.value = '';
        field.focus();
    """)
    time.sleep(0.5)
    
    field = driver.find_element(By.ID, 'f_11__1-2-3-4-5-6-7')
    field.send_keys(status_value)
    time.sleep(2)
    
    # Screenshot the autocomplete
    driver.save_screenshot('/tmp/mls_autocomplete.png')
    
    # Select from dropdown
    selected = driver.execute_script("""
        var items = document.querySelectorAll('.ac_results li, .acfb-data li, .ui-autocomplete li, ul.acfb-data li');
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim();
            if (text.toLowerCase().indexOf(arguments[0].toLowerCase()) >= 0) {
                items[i].click();
                return 'selected: ' + text;
            }
        }
        return 'no dropdown found, items count: ' + items.length;
    """, status_value)
    print(f"  Autocomplete result: {selected}")
    time.sleep(1)
    
    # Screenshot after status set
    driver.save_screenshot('/tmp/mls_status_set.png')
    
    # Click Count
    count_result = driver.execute_script("""
        var buttons = document.querySelectorAll('input[type="button"], button, a');
        for (var i = 0; i < buttons.length; i++) {
            var val = (buttons[i].value || buttons[i].textContent || '').trim();
            if (val === 'Count') { buttons[i].click(); return 'clicked'; }
        }
        return 'not found';
    """)
    print(f"  Count button: {count_result}")
    time.sleep(5)
    
    count = driver.execute_script("""
        var el = document.getElementById('CountResult') || document.getElementById('CountResult1');
        if (el) return el.value || el.textContent;
        return 'unknown';
    """)
    print(f"  📊 Count = {count}")
    
    # Now click Search
    print(f"  Clicking Search...")
    driver.execute_script("""
        var buttons = document.querySelectorAll('input[type="button"], button, a');
        for (var i = 0; i < buttons.length; i++) {
            var val = (buttons[i].value || buttons[i].textContent || '').trim();
            var title = buttons[i].getAttribute('title') || '';
            if (val === 'Search' || title === 'Search') { buttons[i].click(); return; }
        }
    """)
    time.sleep(10)
    
    # Screenshot after search
    driver.save_screenshot('/tmp/mls_after_search.png')
    
    # Now enumerate ALL iframes again
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"\n📋 After search: {len(iframes)} iframes:")
    for i, iframe in enumerate(iframes):
        src = iframe.get_attribute("src") or ""
        name = iframe.get_attribute("name") or ""
        id_ = iframe.get_attribute("id") or ""
        print(f"  [{i}] id={id_}, name={name}, src={src[:150]}")
    
    # Try each iframe to find results
    for i, iframe in enumerate(iframes):
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(iframe)
            info = driver.execute_script("""
                var result = {};
                result.title = document.title;
                result.url = window.location.href;
                result.hasGrid = document.querySelector('.ui-jqgrid, table.jqgTable, #grid, .grid-container, table') !== null;
                result.hasExport = document.querySelector('a[title*="Export"], a[title*="CSV"]') !== null;
                result.rowCount = document.querySelectorAll('tr.jqgrow, tr[role="row"]').length;
                result.bodyText = document.body ? document.body.innerText.substring(0, 300) : '';
                return result;
            """)
            if info.get('hasGrid') or info.get('hasExport') or info.get('rowCount', 0) > 0:
                print(f"  🎯 Iframe [{i}] has results! {info}")
                driver.save_screenshot(f'/tmp/mls_results_iframe_{i}.png')
        except Exception as e:
            print(f"  Iframe [{i}] error: {e}")
    
    return count

def main():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1400,1000")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        login(driver)
        driver.save_screenshot('/tmp/mls_after_login.png')
        
        go_to_search(driver)
        driver.save_screenshot('/tmp/mls_search_page.png')
        
        if find_search_iframe(driver):
            dump_form_fields(driver)
            driver.save_screenshot('/tmp/mls_search_form.png')
            
            # Try setting Expired and counting
            set_status_and_count(driver, "Expired")
        else:
            print("❌ Could not find search iframe")
            driver.save_screenshot('/tmp/mls_no_iframe.png')
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot('/tmp/mls_error.png')
    finally:
        driver.quit()
        print("🔒 Done")

if __name__ == "__main__":
    main()
