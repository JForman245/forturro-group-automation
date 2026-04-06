#!/usr/bin/env python3
"""
Debug Power Search v2 - Look for top nav power search bar
"""

import os, time
from dotenv import load_dotenv
load_dotenv('/Users/claw1/.openclaw/workspace/.env.mls')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def main():
    username = os.getenv('MLS_USERNAME')
    password = os.getenv('MLS_PASSWORD')
    
    options = Options()
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        # Login
        print("🔐 Logging in...")
        driver.get('https://ccar.mysolidearth.com')
        time.sleep(3)
        
        radio_containers = driver.find_elements(By.CSS_SELECTOR, ".v-radio")
        if len(radio_containers) > 1:
            radio_containers[1].click()
            time.sleep(2)
        
        username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'][name='email']")))
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        username_field.send_keys(username)
        password_field.send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(10)
        
        # Navigate to Paragon
        print("🚀 Going to Paragon...")
        paragon_link = driver.find_element(By.CSS_SELECTOR, "a[href*='paragon']")
        paragon_link.click()
        time.sleep(5)
        
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        
        # Dismiss popups
        time.sleep(5)
        driver.execute_script("""
            if (document.getElementById('cboxOverlay')) document.getElementById('cboxOverlay').style.display='none';
            if (document.getElementById('colorbox')) document.getElementById('colorbox').style.display='none';
            if (typeof jQuery !== 'undefined' && jQuery.colorbox) jQuery.colorbox.close();
            var dialogs = document.querySelectorAll('.ui-dialog');
            dialogs.forEach(function(d) { d.style.display = 'none'; });
            var closeButtons = document.querySelectorAll('.ui-dialog-titlebar-close, [title="Close"], button.close');
            closeButtons.forEach(function(btn) { try { btn.click(); } catch(e) {} });
        """)
        time.sleep(3)
        
        # Check MAIN PAGE (outside iframes) for power search bar at top
        print("\n📊 CHECKING MAIN PAGE (top nav area):")
        print("="*60)
        
        # Dump ALL visible input/text fields on the main page
        main_inputs = driver.execute_script("""
            var results = [];
            var inputs = document.querySelectorAll('input, textarea');
            for (var i = 0; i < inputs.length; i++) {
                var el = inputs[i];
                results.push({
                    tag: el.tagName,
                    type: el.type || '',
                    id: el.id || '',
                    name: el.name || '',
                    cls: (el.className || '').substring(0, 80),
                    placeholder: el.placeholder || '',
                    title: el.title || '',
                    visible: el.offsetParent !== null,
                    value: (el.value || '').substring(0, 30)
                });
            }
            return results;
        """)
        
        print(f"Main page inputs: {len(main_inputs)}")
        for inp in main_inputs:
            vis = "✅" if inp['visible'] else "  "
            print(f"  {vis} <{inp['tag']}> type={inp['type']} id='{inp['id']}' name='{inp['name']}' placeholder='{inp['placeholder']}' title='{inp['title']}' class='{inp['cls']}'")
        
        # Look for anything containing "power" text on main page
        power_text = driver.execute_script("""
            var results = [];
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
            while (walker.nextNode()) {
                var text = walker.currentNode.textContent.trim().toLowerCase();
                if (text.indexOf('power') >= 0 && text.length < 100) {
                    var parent = walker.currentNode.parentElement;
                    results.push({
                        text: walker.currentNode.textContent.trim(),
                        parentTag: parent.tagName,
                        parentId: parent.id || '',
                        parentClass: (parent.className || '').substring(0, 60)
                    });
                }
            }
            return results.slice(0, 20);
        """)
        
        if power_text:
            print(f"\n🎯 'Power' text on main page: {len(power_text)}")
            for pt in power_text:
                print(f"  '{pt['text']}' in <{pt['parentTag']}> id='{pt['parentId']}' class='{pt['parentClass']}'")
        else:
            print("\n  No 'power' text found on main page")
        
        # Now check iframe[2] (main Paragon) for power search
        print("\n📊 CHECKING IFRAME[2] (main Paragon):")
        print("="*60)
        
        fresh_frames = driver.find_elements(By.TAG_NAME, "iframe")
        driver.switch_to.frame(fresh_frames[2])
        time.sleep(2)
        
        # Look for power search text and elements
        power_in_frame = driver.execute_script("""
            var results = [];
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                var el = all[i];
                var allText = ((el.id || '') + ' ' + (el.className || '') + ' ' + (el.textContent || '') + ' ' + (el.placeholder || '') + ' ' + (el.title || '')).toLowerCase();
                if (allText.indexOf('power') >= 0) {
                    results.push({
                        tag: el.tagName,
                        id: el.id || '',
                        cls: (el.className || '').substring(0, 80),
                        text: (el.textContent || '').substring(0, 60).trim(),
                        placeholder: el.placeholder || '',
                        title: el.title || ''
                    });
                }
            }
            return results.slice(0, 30);
        """)
        
        if power_in_frame:
            print(f"🎯 'Power' elements in iframe: {len(power_in_frame)}")
            for pe in power_in_frame:
                print(f"  <{pe['tag']}> id='{pe['id']}' class='{pe['cls']}' title='{pe['title']}' text='{pe['text']}'")
        else:
            print("  No 'power' elements found")
        
        # Dump the top part of the iframe page to see the nav/header area
        top_html = driver.execute_script("""
            var header = document.querySelector('header, nav, .header, .nav, .toolbar, #header, #nav, #toolbar');
            if (header) return header.outerHTML.substring(0, 2000);
            
            // Otherwise get the first 3000 chars of body
            return document.body.innerHTML.substring(0, 3000);
        """)
        
        print(f"\n📄 Top of page HTML (first 2000 chars):")
        print(top_html[:2000])
        
        print("\n✅ Done")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
