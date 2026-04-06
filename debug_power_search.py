#!/usr/bin/env python3
"""
Debug Power Search - Find the power search field in Paragon
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
        
        # Re-fetch iframes AFTER popup dismissal
        print("\n📊 SCANNING ALL IFRAMES FOR POWER SEARCH:")
        print("="*60)
        
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Total iframes: {len(frames)}")
        
        # Get frame srcs first
        frame_srcs = []
        for i, frame in enumerate(frames):
            try:
                src = frame.get_attribute('src') or 'no src'
                frame_srcs.append(src)
                print(f"  [{i}] {src}")
            except:
                frame_srcs.append('stale')
                print(f"  [{i}] STALE")
        
        # Now check each iframe by re-finding them
        for i in range(len(frame_srcs)):
            if frame_srcs[i] == 'stale':
                continue
                
            try:
                driver.switch_to.default_content()
                # Re-find frames fresh each time
                fresh_frames = driver.find_elements(By.TAG_NAME, "iframe")
                if i >= len(fresh_frames):
                    continue
                    
                driver.switch_to.frame(fresh_frames[i])
                time.sleep(2)
                
                print(f"\n🔍 Checking iframe [{i}]:")
                
                # Look for ALL input fields
                inputs = driver.find_elements(By.TAG_NAME, "input")
                print(f"   Input fields: {len(inputs)}")
                
                for j, inp in enumerate(inputs):
                    try:
                        inp_type = inp.get_attribute('type') or ''
                        inp_name = inp.get_attribute('name') or ''
                        inp_id = inp.get_attribute('id') or ''
                        inp_placeholder = inp.get_attribute('placeholder') or ''
                        inp_class = inp.get_attribute('class') or ''
                        inp_title = inp.get_attribute('title') or ''
                        visible = inp.is_displayed()
                        
                        if visible:
                            print(f"   [{j}] type={inp_type} name='{inp_name}' id='{inp_id}' placeholder='{inp_placeholder}' class='{inp_class[:60]}' title='{inp_title}'")
                    except:
                        continue
                
                # Look for elements with "power" anywhere
                power_els = driver.execute_script("""
                    var results = [];
                    var all = document.querySelectorAll('*');
                    for (var i = 0; i < all.length; i++) {
                        var el = all[i];
                        var text = (el.textContent || '').toLowerCase();
                        var id = (el.id || '').toLowerCase();
                        var cls = (el.className || '').toLowerCase();
                        var placeholder = (el.placeholder || '').toLowerCase();
                        var title = (el.title || '').toLowerCase();
                        var name = (el.name || '').toLowerCase();
                        
                        if (text.indexOf('power') >= 0 || id.indexOf('power') >= 0 || 
                            cls.indexOf('power') >= 0 || placeholder.indexOf('power') >= 0 ||
                            title.indexOf('power') >= 0 || name.indexOf('power') >= 0) {
                            results.push({
                                tag: el.tagName,
                                id: el.id,
                                cls: (el.className || '').substring(0, 60),
                                text: (el.textContent || '').substring(0, 80).trim(),
                                placeholder: el.placeholder || '',
                                title: el.title || '',
                                name: el.name || ''
                            });
                        }
                    }
                    return results.slice(0, 20);
                """)
                
                if power_els:
                    print(f"\n   🎯 POWER elements: {len(power_els)}")
                    for pe in power_els:
                        print(f"      <{pe['tag']}> id='{pe['id']}' class='{pe['cls']}' name='{pe['name']}' placeholder='{pe['placeholder']}' title='{pe['title']}' text='{pe['text'][:60]}'")
                
                # Also search for "quick search" or "address" fields
                search_els = driver.execute_script("""
                    var results = [];
                    var inputs = document.querySelectorAll('input');
                    for (var i = 0; i < inputs.length; i++) {
                        var el = inputs[i];
                        var all_attrs = (el.id + ' ' + el.name + ' ' + el.className + ' ' + (el.placeholder || '') + ' ' + (el.title || '')).toLowerCase();
                        if (all_attrs.indexOf('search') >= 0 || all_attrs.indexOf('address') >= 0 || all_attrs.indexOf('quick') >= 0) {
                            results.push({
                                tag: 'input',
                                id: el.id,
                                name: el.name || '',
                                cls: (el.className || '').substring(0, 60),
                                placeholder: el.placeholder || '',
                                title: el.title || '',
                                type: el.type || '',
                                visible: el.offsetParent !== null
                            });
                        }
                    }
                    return results;
                """)
                
                if search_els:
                    print(f"\n   🎯 SEARCH/ADDRESS inputs: {len(search_els)}")
                    for se in search_els:
                        print(f"      <input> type={se['type']} id='{se['id']}' name='{se['name']}' placeholder='{se['placeholder']}' title='{se['title']}' visible={se['visible']}")
                        
            except Exception as e:
                err_msg = str(e)[:100]
                print(f"   Error: {err_msg}")
                continue
        
        print("\n✅ Scan complete")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
