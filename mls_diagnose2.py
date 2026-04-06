#!/usr/bin/env python3
"""Diagnostic 2: Explore date filtering, daysLink, and form submission."""

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
    for i, iframe in enumerate(iframes):
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(iframe)
            has_status = driver.execute_script(
                "return document.getElementById('f_11__1-2-3-4-5-6-7') !== null;"
            )
            if has_status:
                print(f"✅ In search form iframe [{i}]")
                return True
        except:
            pass
    return False

def main():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1400,1000")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        login(driver)
        go_to_search(driver)
        
        if not find_search_iframe(driver):
            print("❌ No search iframe")
            return
        
        # 1. Explore the daysLink and mmdaysback area more thoroughly
        area_html = driver.execute_script("""
            var el = document.getElementById('mmdaysback');
            if (!el) return 'mmdaysback NOT FOUND';
            // Get the entire section around mmdaysback
            var parent = el.parentElement;
            while (parent && !parent.classList.contains('f-panel') && parent.tagName !== 'TABLE' && parent.tagName !== 'FORM') {
                parent = parent.parentElement;
            }
            if (parent) return parent.innerHTML.substring(0, 2000);
            return el.parentElement.innerHTML.substring(0, 1000);
        """)
        print(f"\n📋 MMDAYSBACK AREA HTML:\n{area_html}\n")
        
        # 2. Look for ALL hidden sections / expandable areas
        sections = driver.execute_script("""
            var result = [];
            // Check for any section headers or expand buttons
            var headers = document.querySelectorAll('.f-panel-header, .section-header, [class*="expand"], [class*="toggle"], [class*="collapse"]');
            for (var i = 0; i < headers.length; i++) {
                result.push({
                    tag: headers[i].tagName,
                    text: headers[i].textContent.trim().substring(0, 100),
                    className: headers[i].className,
                    visible: headers[i].offsetParent !== null
                });
            }
            return result;
        """)
        print(f"\n📋 SECTIONS/HEADERS ({len(sections)}):")
        for s in sections:
            print(f"  {s['tag']} class={s['className'][:60]} text={s['text'][:60]} visible={s['visible']}")
        
        # 3. Look at the form structure - find the form element and its action
        form_info = driver.execute_script("""
            var forms = document.querySelectorAll('form');
            var result = [];
            for (var i = 0; i < forms.length; i++) {
                result.push({
                    action: forms[i].action,
                    method: forms[i].method,
                    id: forms[i].id,
                    className: forms[i].className,
                    inputCount: forms[i].querySelectorAll('input').length
                });
            }
            return result;
        """)
        print(f"\n📋 FORMS: {form_info}")
        
        # 4. Check what functions are available - look for search-related JS functions
        js_funcs = driver.execute_script("""
            var result = [];
            // Check for known Paragon functions
            var checks = ['doSearch', 'doCount', 'submitSearch', 'searchForm', 'getSearchCriteria', 
                          'buildCriteria', 'mmDaysBack', 'setDaysBack', 'changeDays'];
            for (var i = 0; i < checks.length; i++) {
                if (typeof window[checks[i]] === 'function') {
                    result.push(checks[i] + ': exists');
                }
            }
            // Also check jQuery if available
            if (typeof jQuery !== 'undefined') {
                result.push('jQuery: available');
            }
            return result;
        """)
        print(f"\n📋 JS FUNCTIONS: {js_funcs}")
        
        # 5. Look at what the Search button actually does
        search_btn = driver.execute_script("""
            var buttons = document.querySelectorAll('input[type="button"], button, a');
            for (var i = 0; i < buttons.length; i++) {
                var val = (buttons[i].value || buttons[i].textContent || '').trim();
                if (val === 'Search') {
                    return {
                        tag: buttons[i].tagName,
                        value: val,
                        onclick: buttons[i].getAttribute('onclick') || '',
                        href: buttons[i].getAttribute('href') || '',
                        id: buttons[i].id,
                        className: buttons[i].className,
                        title: buttons[i].getAttribute('title') || ''
                    };
                }
            }
            return null;
        """)
        print(f"\n📋 SEARCH BUTTON: {search_btn}")
        
        # 6. Look at Count button too
        count_btn = driver.execute_script("""
            var buttons = document.querySelectorAll('input[type="button"], button, a');
            for (var i = 0; i < buttons.length; i++) {
                var val = (buttons[i].value || buttons[i].textContent || '').trim();
                if (val === 'Count') {
                    return {
                        tag: buttons[i].tagName,
                        value: val,
                        onclick: buttons[i].getAttribute('onclick') || '',
                        id: buttons[i].id,
                        className: buttons[i].className
                    };
                }
            }
            return null;
        """)
        print(f"\n📋 COUNT BUTTON: {count_btn}")
        
        # 7. Check the daysLink behavior
        days_link = driver.execute_script("""
            var el = document.getElementById('daysLink');
            if (!el) return 'NOT FOUND';
            return {
                tag: el.tagName,
                text: el.textContent.trim(),
                onclick: el.getAttribute('onclick') || '',
                href: el.getAttribute('href') || '',
                className: el.className,
                nextSibling: el.nextSibling ? el.nextSibling.textContent : '',
                prevSibling: el.previousSibling ? el.previousSibling.textContent : ''
            };
        """)
        print(f"\n📋 DAYSLINK: {days_link}")
        
        # 8. Look for date-related elements more broadly
        date_elements = driver.execute_script("""
            var result = [];
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                var el = all[i];
                var text = el.textContent.trim().toLowerCase();
                var id = (el.id || '').toLowerCase();
                var className = (el.className || '').toString().toLowerCase();
                // Only check leaf-ish elements
                if (el.children.length < 3) {
                    if (text.match(/status.?date|expir.?date|change.?date|date.?range|list.?date|off.?market/i) ||
                        id.match(/date|expir|statusdate/) ||
                        className.match(/date-range|datepicker/)) {
                        result.push({
                            tag: el.tagName,
                            id: el.id || '',
                            text: text.substring(0, 80),
                            className: className.substring(0, 60)
                        });
                    }
                }
            }
            return result.slice(0, 30);
        """)
        print(f"\n📋 DATE-RELATED ELEMENTS ({len(date_elements)}):")
        for e in date_elements:
            print(f"  {e['tag']} id={e['id']} class={e['className'][:40]} text={e['text'][:60]}")
        
        # 9. Dump the entire "days back" section more completely
        daysback_section = driver.execute_script("""
            var el = document.getElementById('mmdaysback');
            if (!el) return 'NOT FOUND';
            // Walk up to find the fieldset or table row
            var p = el.parentElement;
            for (var i = 0; i < 5; i++) {
                if (p.parentElement) p = p.parentElement;
            }
            return p.outerHTML.substring(0, 3000);
        """)
        print(f"\n📋 DAYSBACK SECTION (5 levels up):\n{daysback_section[:2000]}\n")
        
        # 10. Now set status to Expired, set mmdaysback, and look at what form data would be submitted
        print("\n🔍 Setting status to Expired...")
        field = driver.find_element(By.ID, 'f_11__1-2-3-4-5-6-7')
        field.send_keys("Expired")
        time.sleep(2)
        driver.execute_script("""
            var items = document.querySelectorAll('.ac_results li, .acfb-data li, .ui-autocomplete li');
            for (var i = 0; i < items.length; i++) {
                if (items[i].textContent.trim().toLowerCase().indexOf('expired') >= 0) {
                    items[i].click(); return;
                }
            }
        """)
        time.sleep(1)
        
        # Check what hidden field got set
        hidden_val = driver.execute_script("""
            return document.getElementById('hdnf_11__1-2-3-4-5-6-7').value;
        """)
        print(f"  Hidden status value: {hidden_val}")
        
        # Get ALL form data that would be submitted
        form_data = driver.execute_script("""
            var form = document.querySelector('form');
            if (!form) return 'NO FORM';
            var data = new FormData(form);
            var result = {};
            for (var pair of data.entries()) {
                if (pair[1] && pair[1].length < 200) {
                    result[pair[0]] = pair[1];
                }
            }
            return result;
        """)
        print(f"\n📋 FORM DATA (would be submitted):")
        for k, v in sorted(form_data.items()):
            if v and v != '000' and len(v) < 100:
                print(f"  {k} = {v}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot('/tmp/mls_error2.png')
    finally:
        driver.quit()
        print("\n🔒 Done")

if __name__ == "__main__":
    main()
