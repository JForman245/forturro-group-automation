#!/usr/bin/env python3
"""
MLS Listing Sheet PDF via Playwright
Login → Paragon → Power Search → Toggle PDF → Download

Usage:
  python3 mls_listing_sheet_pw.py "308 62nd Ave N North Myrtle Beach"
  python3 mls_listing_sheet_pw.py "123 Main St" --output /path/to/file.pdf
"""

import os, sys, time, re, base64, argparse, functools
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Unbuffered output
print = functools.partial(print, flush=True)

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.mls'))
MLS_USERNAME = os.getenv('MLS_USERNAME')
MLS_PASSWORD = os.getenv('MLS_PASSWORD')
OUTPUT_DIR = os.path.expanduser("~/Desktop")


def dismiss_popups(page):
    """Kill colorbox overlays, notification dialogs, etc."""
    page.evaluate("""() => {
        const ids = ['cboxOverlay', 'colorbox'];
        ids.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = 'none'; });
        if (typeof jQuery !== 'undefined' && jQuery.colorbox) jQuery.colorbox.close();
        document.querySelectorAll('.ui-dialog').forEach(d => d.style.display = 'none');
        document.querySelectorAll('.ui-dialog-titlebar-close, [title="Close"], button.close')
            .forEach(b => { try { b.click(); } catch(e) {} });
    }""")


def login_to_paragon(page):
    """SSO login at CCAR → click Paragon link → arrive at MLS."""
    print("🔑 Step 1: Loading CCAR portal…")
    page.goto("https://ccar.mysolidearth.com/portal", wait_until="networkidle", timeout=30_000)
    page.wait_for_timeout(3000)

    # Click the Email radio (second .v-radio)
    print("   Clicking Email radio…")
    radios = page.locator(".v-radio")
    if radios.count() >= 2:
        radios.nth(1).click()
    else:
        # Fallback: JS click
        page.evaluate("""() => {
            const rs = document.querySelectorAll('.v-radio');
            if (rs.length >= 2) rs[1].click();
        }""")
    page.wait_for_timeout(2000)

    # Fill credentials — after radio switch the field is input[type='email'][name='email']
    print("   Entering credentials…")
    try:
        page.fill("input[type='email'][name='email']", MLS_USERNAME, timeout=5000)
    except PWTimeout:
        page.fill("input[name='member_login_id']", MLS_USERNAME, timeout=5000)
    page.fill("input[type='password']", MLS_PASSWORD)
    page.click("button[type='submit']")

    # Wait for redirect to resources/panels (login success)
    print("   Waiting for login redirect…")
    for _ in range(20):
        page.wait_for_timeout(1000)
        if "resources" in page.url or "panels" in page.url or "dashboard" in page.url:
            break
    print(f"   ✅ Logged in → {page.url[:60]}")

    # Click the Paragon link on the resources page
    print("🏠 Step 2: Opening Paragon MLS…")
    paragon_link = page.locator("a[href*='paragon' i]").first
    if paragon_link.count():
        with page.context.expect_page() as new_page_info:
            paragon_link.click()
        paragon_page = new_page_info.value
        paragon_page.wait_for_load_state("domcontentloaded")
        print("   Paragon opened in new tab")
    else:
        # Fallback: navigate directly
        paragon_page = page
        paragon_page.goto("http://ccar.paragonrels.com/", wait_until="domcontentloaded", timeout=30_000)

    # Wait for Paragon to fully load (it's slow)
    print("   Waiting for Paragon to load…")
    paragon_page.wait_for_timeout(15000)
    dismiss_popups(paragon_page)
    paragon_page.wait_for_timeout(2000)
    dismiss_popups(paragon_page)

    if "paragonrels.com" not in paragon_page.url:
        print(f"   ❌ Not on Paragon. URL: {paragon_page.url}")
        paragon_page.screenshot(path="/tmp/mls_pw_not_paragon.png")
        return None

    print(f"   ✅ On Paragon: {paragon_page.url[:60]}")
    return paragon_page


def search_listing(page, address):
    """Use Power Search (select2) to find a listing by address."""
    print(f"🔍 Step 3: Searching for '{address}'…")

    # The Power Search is a select2 dropdown — click to open, then type
    search_input = page.locator("input.select2-search__field").first
    if not search_input.count():
        # Fallback selectors
        for sel in ["input[placeholder*='Power Search']", "input[placeholder*='search']", "#powerSearchInput"]:
            search_input = page.locator(sel).first
            if search_input.count():
                break

    if not search_input.count():
        print("   ❌ Power Search input not found")
        page.screenshot(path="/tmp/mls_pw_no_search.png")
        return False

    search_input.click()
    page.wait_for_timeout(500)
    search_input.fill(address)
    page.wait_for_timeout(2000)
    search_input.press("Enter")
    print("   ✅ Search submitted")
    page.wait_for_timeout(8000)
    return True


def find_listing_iframe(page):
    """Locate the search results iframe (tab1_1) containing the listing."""
    for f in page.frames:
        url = f.url or ""
        name = f.name or ""
        if "listingIds" in url or ("tab1" in name and "Search" in url):
            print(f"   ✅ Found listing iframe: name={name} url={url[:80]}")
            return f
    # Second pass: any iframe with Search in URL
    for f in page.frames:
        if "Search" in (f.url or ""):
            print(f"   ✅ Found Search iframe: name={f.name}")
            return f
    print("   ❌ No listing iframe found")
    for f in page.frames:
        print(f"      Frame: name={f.name} url={(f.url or '')[:80]}")
    return None


def find_report_url(search_frame, page):
    """Get the direct URL of the ifView report iframe."""
    # Check child frames
    for cf in search_frame.child_frames:
        if "ifView" in (cf.name or "") or "Report" in (cf.url or ""):
            return cf.url

    # Try JS extraction
    url = search_frame.evaluate("""() => {
        const f = document.getElementById('ifView');
        return f && f.src ? f.src : '';
    }""")
    return url or None


def click_toggle_pdf(search_frame, page):
    """Click 'Toggle PDF' in the toolbar and find the resulting PDF URL."""
    print("📄 Step 5: Clicking Toggle PDF…")

    # Toggle PDF is an <a> with title="Toggle PDF" inside the search iframe
    toggled = search_frame.evaluate("""() => {
        const links = document.querySelectorAll('a');
        for (const a of links) {
            if ((a.getAttribute('title') || '').includes('Toggle PDF')) {
                a.click();
                return true;
            }
        }
        return false;
    }""")

    if not toggled:
        print("   ❌ Toggle PDF button not found in iframe")
        # Try from all frames
        for f in page.frames:
            try:
                result = f.evaluate("""() => {
                    const links = document.querySelectorAll('a');
                    for (const a of links) {
                        if ((a.getAttribute('title') || '').includes('Toggle PDF')) {
                            a.click();
                            return true;
                        }
                    }
                    return false;
                }""")
                if result:
                    print(f"   ✅ Found Toggle PDF in frame: {f.name}")
                    toggled = True
                    break
            except Exception:
                continue

    if not toggled:
        print("   ❌ Toggle PDF not found anywhere")
        return None

    print("   ✅ Clicked Toggle PDF, waiting for PDF to render…")
    page.wait_for_timeout(10000)

    # After toggle, look for PDF content in sub-iframes
    for f in page.frames:
        url = f.url or ""
        if '.pdf' in url.lower() or 'application/pdf' in url.lower():
            return url

    # Look for embed/object/iframe with PDF
    for f in page.frames:
        try:
            pdf_url = f.evaluate("""() => {
                const els = document.querySelectorAll('embed[type="application/pdf"], object[type="application/pdf"], embed[src*=".pdf"], iframe[src*=".pdf"], iframe[src*="Report"]');
                for (const el of els) {
                    const u = el.src || el.data || '';
                    if (u) return u;
                }
                return null;
            }""")
            if pdf_url:
                return pdf_url
        except Exception:
            continue

    # Check ifPrintView or ifDivView
    for name in ['ifPrintView', 'ifDivView']:
        try:
            url = search_frame.evaluate(f"""() => {{
                const f = document.getElementById('{name}');
                return f && f.src ? f.src : '';
            }}""")
            if url and 'about:blank' not in url:
                return url
        except Exception:
            continue

    return None


def get_listing_sheet(address, output_path=None):
    """Full pipeline: login → search → get PDF."""
    if not MLS_USERNAME or not MLS_PASSWORD:
        print("❌ MLS_USERNAME / MLS_PASSWORD not set in .env.mls")
        return None

    if not output_path:
        safe_name = address.replace('/', '-').replace('\\', '-').strip()
        output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.pdf")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=['--window-size=1920,1200', '--disable-blink-features=AutomationControlled'],
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1200},
            accept_downloads=True,
        )
        # Stealth: hide webdriver flag
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page = context.new_page()
        page.set_default_timeout(30_000)

        try:
            # ── Login ──────────────────────────────────────
            paragon_page = login_to_paragon(page)
            if not paragon_page:
                return None

            # ── Search ─────────────────────────────────────
            if not search_listing(paragon_page, address):
                return None

            # ── Find listing iframe ────────────────────────
            print("📋 Step 4: Locating listing…")
            search_frame = find_listing_iframe(paragon_page)
            if not search_frame:
                paragon_page.screenshot(path="/tmp/mls_pw_no_iframe.png")
                return None

            # Wait for listing detail to render
            for attempt in range(15):
                try:
                    text = search_frame.evaluate("document.body ? document.body.innerText.substring(0, 1000) : ''")
                    if any(kw in text for kw in ['Asking Price', 'MLS #', 'Bedrooms', 'List Price', 'Sq Ft', 'ALL FIELDS']):
                        print("   ✅ Listing detail loaded")
                        break
                except Exception:
                    pass
                paragon_page.wait_for_timeout(2000)
            else:
                print("   ⚠️ Listing detail may not have fully loaded")

            paragon_page.wait_for_timeout(3000)

            # ── Get report URL ─────────────────────────────
            report_url = find_report_url(search_frame, paragon_page)
            if report_url:
                print(f"   Report URL: {report_url[:100]}")

            # ── Try Toggle PDF first ───────────────────────
            pdf_url = click_toggle_pdf(search_frame, paragon_page)

            if pdf_url:
                print(f"   PDF URL found: {pdf_url[:120]}")
                # Download the PDF using the authenticated session
                pdf_page = context.new_page()
                response = pdf_page.goto(pdf_url, wait_until="networkidle", timeout=60_000)
                if response and 'pdf' in (response.headers.get('content-type', '') or '').lower():
                    # Direct PDF download
                    body = response.body()
                    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(body)
                    size_kb = len(body) / 1024
                    print(f"✅ PDF downloaded: {output_path} ({size_kb:.0f} KB)")
                    pdf_page.close()
                    return output_path
                else:
                    # It's an HTML page, use CDP printToPDF
                    print("   PDF URL returned HTML, using CDP printToPDF…")
                    pdf_page.wait_for_timeout(5000)
                    pdf_data = generate_cdp_pdf(pdf_page)
                    pdf_page.close()
                    if pdf_data:
                        save_pdf_bytes(pdf_data, output_path)
                        return output_path

            # ── Fallback: CDP printToPDF on report iframe ──
            if report_url:
                print("📄 Fallback: CDP printToPDF on report page…")
                report_page = context.new_page()
                report_page.goto(report_url, wait_until="networkidle", timeout=60_000)
                report_page.wait_for_timeout(8000)

                # Let images load
                report_page.evaluate("""() => {
                    return Promise.all(
                        Array.from(document.images)
                            .filter(img => !img.complete)
                            .map(img => new Promise(resolve => {
                                img.onload = img.onerror = resolve;
                            }))
                    );
                }""")
                report_page.wait_for_timeout(3000)

                # Hide UI chrome
                report_page.evaluate("""() => {
                    document.querySelectorAll('.hideWhenPrinted, .listingCheckBox, #f-head, .f-panel-menu, #header, #nav, .navbar')
                        .forEach(el => el.style.display = 'none');
                }""")
                report_page.wait_for_timeout(500)

                pdf_data = generate_cdp_pdf(report_page)
                report_page.close()
                if pdf_data:
                    save_pdf_bytes(pdf_data, output_path)
                    return output_path

            # ── Last resort: print current page ────────────
            print("📄 Last resort: printing current Paragon view…")
            pdf_data = generate_cdp_pdf(paragon_page)
            if pdf_data:
                save_pdf_bytes(pdf_data, output_path)
                return output_path

            print("❌ All PDF generation methods failed")
            return None

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            try:
                (paragon_page or page).screenshot(path="/tmp/mls_pw_error.png")
                print("📸 Debug screenshot: /tmp/mls_pw_error.png")
            except Exception:
                pass
            return None
        finally:
            browser.close()


def generate_cdp_pdf(page):
    """Use Chrome DevTools Protocol to print page to PDF bytes."""
    try:
        cdp = page.context.new_cdp_session(page)
        result = cdp.send("Page.printToPDF", {
            "landscape": False,
            "displayHeaderFooter": False,
            "printBackground": True,
            "preferCSSPageSize": True,
            "paperWidth": 8.5,
            "paperHeight": 11,
            "marginTop": 0.3,
            "marginBottom": 0.3,
            "marginLeft": 0.3,
            "marginRight": 0.3,
            "scale": 1,
        })
        return base64.b64decode(result["data"])
    except Exception as e:
        print(f"   CDP printToPDF error: {e}")
        return None


def save_pdf_bytes(data, path):
    """Save raw PDF bytes to disk with size/quality report."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)
    size_kb = len(data) / 1024
    print(f"✅ PDF saved: {path} ({size_kb:.0f} KB)")

    # Quick page count
    page_markers = data.count(b'/Type /Page') - data.count(b'/Type /Pages')
    if page_markers > 0:
        print(f"   ~{page_markers} pages")


def main():
    parser = argparse.ArgumentParser(description="Generate MLS listing sheet PDF via Playwright")
    parser.add_argument("address", nargs="+", help="Property address to search")
    parser.add_argument("--output", "-o", default=None, help="Output PDF path")
    args = parser.parse_args()

    address = " ".join(args.address)
    result = get_listing_sheet(address, args.output)
    if not result:
        sys.exit(1)
    print(f"\n🎉 Done: {result}")


if __name__ == "__main__":
    main()
