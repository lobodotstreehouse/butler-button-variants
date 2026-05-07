"""
Get full page info, understand structure, then:
1. Try to toggle the Draft/Published status via the Edit page info dialog
2. Try PUT /pages/{id} with correct body from GET response
"""
import json, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'

DRAFT_PAGES = [
    ('concierge', '413198000000002013'),
    ('home', '413198000000004653'),
    ('trip-planning', '413198000000047002'),
    ('travel-advisor', '413198000000047014'),
]


def build_cookies(raw):
    seen, out = set(), []
    for name, value in raw.items():
        if not value or not isinstance(value, str): continue
        if (name, value) in seen: continue
        seen.add((name, value))
        out.append({'name': name, 'value': value,
                    'domain': '.sitebuilder-60059075182.zohositescontent.in',
                    'path': '/', 'httpOnly': False, 'secure': True})
    return out


def main():
    raw = json.loads(Path(COOKIES_JSON).read_text())
    cookies = build_cookies(raw)

    all_responses = {}
    def capture_response(resp):
        if 'zs-site/api' in resp.url:
            try:
                all_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        pg = context.new_page()
        pg.on('response', capture_response)

        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        # Step 1: Get the full page info for Concierge
        pg.evaluate("""() => {
            window.__pgInfo = 'pending';
            window.$X.get({
                url: '/zs-site/api/v1/pages/413198000000002013',
                headers: window.app.getHeaders(),
                success: function(r) { window.__pgInfo = r; },
                error: function(e) { window.__pgInfo = {error: String(e)}; },
            });
        }""")
        pg.wait_for_timeout(8000)
        pg_info = pg.evaluate("window.__pgInfo")
        if pg_info and pg_info != 'pending':
            print("=== Concierge page info ===")
            print(json.dumps(pg_info, indent=2)[:3000])
        else:
            url_key = f"{BASE}/zs-site/api/v1/pages/413198000000002013"
            if url_key in all_responses:
                print("=== Concierge page info (from network) ===")
                try:
                    data = json.loads(all_responses[url_key]['body'])
                    print(json.dumps(data, indent=2)[:3000])
                    pg_info = data
                except Exception as e:
                    print(f"Parse error: {e}: {all_responses[url_key]['body'][:500]}")

        if not pg_info or pg_info == 'pending':
            print("Could not get page info")
            browser.close()
            return

        # Extract the page_details structure and try PUT with same structure
        page_details = pg_info.get('page_info', {}).get('page_details', {})
        print(f"\nKey page_details fields:")
        for k, v in page_details.items():
            print(f"  {k}: {v!r}")

        # Try PUT /pages/413198000000002013 with body based on GET response
        # Change content_state to 3 (published + draft)
        body = dict(page_details)
        body['content_state'] = 3
        print(f"\nTrying PUT with content_state=3 body based on GET structure...")
        pg.evaluate(f"""() => {{
            window.__putResult = 'pending';
            window.$X.put({{
                url: '/zs-site/api/v1/pages/413198000000002013',
                headers: window.app.getHeaders(),
                bodyJSON: {json.dumps(body)},
                success: function(r) {{ window.__putResult = r; }},
                error: function(e) {{ window.__putResult = {{error: String(e)}}; }},
            }});
        }}""")
        pg.wait_for_timeout(8000)
        put_result = pg.evaluate("window.__putResult")
        put_url = f"{BASE}/zs-site/api/v1/pages/413198000000002013"
        if put_url in all_responses:
            net = all_responses[put_url]
            print(f"PUT result: HTTP {net['status']} {net['body'][:400]}")
            del all_responses[put_url]
        elif put_result and put_result != 'pending':
            print(f"PUT result: {json.dumps(put_result)[:400]}")

        # Step 2: Open Edit page info dialog and look for toggles
        print("\n=== Edit page info dialog ===")
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        pg.evaluate("""() => {
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                if (walker.currentNode.textContent.trim() === 'Concierge') {
                    var p = walker.currentNode.parentElement;
                    for (var i = 0; i < 10; i++) {
                        if (!p) break;
                        var links = p.querySelectorAll('a');
                        for (var l of links) {
                            if (l.textContent.trim() === 'Edit page info' && l.offsetParent !== null) {
                                l.click();
                                return;
                            }
                        }
                        p = p.parentElement;
                    }
                }
            }
        }""")
        pg.wait_for_timeout(5000)
        pg.screenshot(path='/tmp/zoho-56-page-info.png')

        # Get full dialog HTML
        dialog_html = pg.evaluate("""() => {
            var d = document.querySelector('[class*="dialog"], [class*="modal"]');
            if (d && d.offsetParent !== null) return d.outerHTML.substring(0, 5000);
            // Get the visible overlay
            var overlays = document.querySelectorAll('[class*="overlay"], [class*="Dialog"]');
            for (var o of overlays) {
                if (o.offsetParent !== null) return o.outerHTML.substring(0, 5000);
            }
            return null;
        }""")
        if dialog_html:
            print(f"Dialog HTML:\n{dialog_html[:3000]}")
        else:
            print("No dialog found, checking page text:")
            body_text = pg.locator('body').inner_text()
            print(body_text[:1000])

        # Look for any status/publish related elements
        status_toggle = pg.evaluate("""() => {
            // Look for elements near "Publish" or "Status" text
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            var results = [];
            while (walker.nextNode()) {
                var t = walker.currentNode.textContent.trim().toLowerCase();
                if (t === 'publish' || t === 'status' || t === 'draft' || t === 'published') {
                    var el = walker.currentNode.parentElement;
                    if (el.offsetParent !== null) {
                        results.push({
                            text: walker.currentNode.textContent.trim(),
                            tag: el.tagName,
                            class: el.className.substring(0, 60),
                            id: el.id,
                            parent: el.parentElement?.className?.substring(0, 60),
                        });
                    }
                }
            }
            return results.slice(0, 20);
        }""")
        print(f"\nStatus/Publish elements: {json.dumps(status_toggle, indent=2)}")

        # Try clicking any "Publish" toggle in the dialog
        toggle_click = pg.evaluate("""() => {
            // Look for toggle-like elements
            var toggles = document.querySelectorAll('[class*="toggle"], [class*="switch"], [class*="slide"]');
            for (var t of toggles) {
                if (t.offsetParent !== null) {
                    t.click();
                    return 'clicked toggle: ' + t.className;
                }
            }
            // Try clicking "Draft" text to toggle it
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                if (walker.currentNode.textContent.trim() === 'Draft') {
                    var el = walker.currentNode.parentElement;
                    if (el.offsetParent !== null) {
                        el.click();
                        return 'clicked Draft element: ' + el.className;
                    }
                }
            }
            return 'no toggle found';
        }""")
        print(f"\nToggle click: {toggle_click}")
        pg.wait_for_timeout(2000)
        pg.screenshot(path='/tmp/zoho-56-after-toggle.png')

        # Look for the "save" button in the dialog
        save_result = pg.evaluate("""() => {
            var btns = document.querySelectorAll('button');
            for (var btn of btns) {
                var txt = btn.textContent.trim();
                if (btn.offsetParent !== null && (txt === 'Save' || txt === 'Update' || txt === 'Done')) {
                    btn.click();
                    return 'clicked: ' + txt;
                }
            }
            return 'no save button';
        }""")
        print(f"Save result: {save_result}")
        pg.wait_for_timeout(5000)

        # Check API calls for page update
        update_url = f"{BASE}/zs-site/api/v1/pages/413198000000002013"
        if update_url in all_responses:
            net = all_responses[update_url]
            print(f"\nPage update API: HTTP {net['status']} {net['body'][:400]}")

        # Check new content state
        pg.evaluate("""() => {
            window.__pgInfo2 = 'pending';
            window.$X.get({
                url: '/zs-site/api/v1/pages/413198000000002013',
                headers: window.app.getHeaders(),
                success: function(r) { window.__pgInfo2 = r; },
                error: function(e) { window.__pgInfo2 = {error: String(e)}; },
            });
        }""")
        pg.wait_for_timeout(8000)
        pg_info2 = pg.evaluate("window.__pgInfo2")
        if pg_info2 and pg_info2 != 'pending':
            pd = pg_info2.get('page_info', {}).get('page_details', {})
            print(f"\nConcierge content_state after toggle: {pd.get('content_state')}")
        else:
            url_key2 = f"{BASE}/zs-site/api/v1/pages/413198000000002013"
            if url_key2 in all_responses:
                try:
                    data = json.loads(all_responses[url_key2]['body'])
                    pd = data.get('page_info', {}).get('page_details', {})
                    print(f"\nConcierge content_state after toggle: {pd.get('content_state')}")
                except:
                    pass

        browser.close()


if __name__ == '__main__':
    main()
