#!/usr/bin/env python3
"""Diagnostic 3: Find date fields in Paragon search - check expandable sections and Customize."""

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
    driver.get("https://ccar.mysolidearth.com/portal")
    time.sleep(5)
    radio_containers = driver.find_elements(By.CSS_SELECTOR, ".v-radio")
    radio_containers[1].click()
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, "input[type='email'][name='email']").send_keys(MLS_USERNAME)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(MLS_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
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
    print("✅ Logged in")

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
        
        # The search form at Property.mvc - let's find the actual form and ALL its sections
        # Check for expand links in the form
        print("\n=== EXPAND LINKS ===")
        expand_info = driver.execute_script("""
            var result = [];
            var links = document.querySelectorAll('a.expand, ins.expand, a.collapse, .f-section-header, .f-form-section');
            for (var i = 0; i < links.length; i++) {
                result.push({
                    tag: links[i].tagName,
                    text: links[i].textContent.trim().substring(0, 60),
                    className: links[i].className,
                    parentText: links[i].parentElement ? links[i].parentElement.textContent.trim().substring(0, 80) : ''
                });
            }
            return result;
        """)
        for e in expand_info:
            print(f"  {e}")
        
        # The real search form - let's look at ALL the field labels/groups
        print("\n=== ALL LABELS IN SEARCH FORM ===")
        labels = driver.execute_script("""
            var form = document.querySelector('form.f-form-search, form');
            if (!form) return [];
            var result = [];
            var labels = form.querySelectorAll('label, td.fieldLabel, .f-label');
            for (var i = 0; i < labels.length; i++) {
                result.push({
                    text: labels[i].textContent.trim().substring(0, 60),
                    forId: labels[i].getAttribute('for') || '',
                    visible: labels[i].offsetParent !== null
                });
            }
            return result;
        """)
        for l in labels:
            print(f"  text='{l['text']}' for={l['forId']} visible={l['visible']}")
        
        # Check the full form HTML structure to find sections
        print("\n=== SEARCH FORM STRUCTURE ===")
        form_structure = driver.execute_script("""
            var form = document.querySelector('form.f-form-search, form');
            if (!form) return 'NO FORM';
            // Get all direct children sections
            var result = [];
            var sections = form.querySelectorAll('.f-section, .f-fieldset, fieldset, .f-form-field-row, tr');
            for (var i = 0; i < sections.length; i++) {
                var el = sections[i];
                var text = el.textContent.trim().substring(0, 100);
                if (text.length > 0) {
                    result.push({
                        tag: el.tagName,
                        className: (el.className || '').substring(0, 60),
                        text: text,
                        display: window.getComputedStyle(el).display,
                        hidden: el.hidden
                    });
                }
            }
            return result.slice(0, 30);
        """)
        for s in form_structure:
            print(f"  {s['tag']} class={s['className'][:40]} display={s['display']} text={s['text'][:60]}")
        
        # Look for the Customize search link that might reveal more fields
        print("\n=== CUSTOMIZE / ADD FIELDS ===")
        customize = driver.execute_script("""
            var result = [];
            var all = document.querySelectorAll('a, button');
            for (var i = 0; i < all.length; i++) {
                var text = (all[i].textContent || '').trim();
                var title = all[i].getAttribute('title') || '';
                if (text.match(/custom|add|more|field|criteria|advanc/i) || 
                    title.match(/custom|add|more|field|criteria|advanc/i)) {
                    result.push({
                        tag: all[i].tagName,
                        text: text.substring(0, 60),
                        title: title.substring(0, 60),
                        href: (all[i].getAttribute('href') || '').substring(0, 100),
                        id: all[i].id
                    });
                }
            }
            return result;
        """)
        for c in customize:
            print(f"  {c}")

        # Try to find the "Add Field" or field selection mechanism
        print("\n=== LOOKING FOR DATE FIELDS IN HIDDEN AREAS ===")
        hidden_date = driver.execute_script("""
            var result = [];
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                var id = all[i].id || '';
                var name = all[i].getAttribute('name') || '';
                // Look for any field with date-like patterns
                if (id.match(/date|expir|off_market|status_change|dom/i) || 
                    name.match(/date|expir|off_market|status_change|dom/i)) {
                    result.push({
                        tag: all[i].tagName,
                        id: id,
                        name: name,
                        type: all[i].type || '',
                        display: window.getComputedStyle(all[i]).display,
                        value: (all[i].value || '').substring(0, 50)
                    });
                }
            }
            return result.slice(0, 20);
        """)
        for d in hidden_date:
            print(f"  {d}")
        
        # Let's also dump the full HTML of the search form - trimmed
        print("\n=== SEARCH FORM HTML (first 5000 chars) ===")
        form_html = driver.execute_script("""
            var form = document.querySelector('form.f-form-search');
            if (!form) {
                var forms = document.querySelectorAll('form');
                for (var i = 0; i < forms.length; i++) {
                    if (forms[i].action && forms[i].action.includes('Property')) {
                        form = forms[i];
                        break;
                    }
                }
            }
            if (!form) return 'NO FORM';
            return form.outerHTML;
        """)
        print(form_html[:5000])

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot('/tmp/mls_error3.png')
    finally:
        driver.quit()
        print("\n🔒 Done")

if __name__ == "__main__":
    main()
