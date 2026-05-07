"""
The pages are in DRAFT state (content_state=1).
When in the Zoho Sites editor and you click Publish -> Publish Site,
it should publish ALL pages including drafts.
Try:
1. Open each draft page editor via "Edit content" click
2. Click the dropdown Publish -> Publish Site
3. Wait for publish to complete
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
        browser = pw.chromium.launch(headless=False, slow_mo=400)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        pg = context.new_page()
        pg.on('response', capture_response)

        # Step 1: Navigate to pages list
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        print("Opened pages list")
        pg.screenshot(path='/tmp/zoho-54-pages-list.png')

        # Step 2: Click "Edit content" for Concierge
        print("\nClicking Edit content for Concierge...")
        clicked = pg.evaluate("""() => {
            // Search all text nodes for 'Concierge' then find Edit content nearby
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            var found = [];
            while (walker.nextNode()) {
                var t = walker.currentNode.textContent.trim();
                if (t === 'Concierge') {
                    found.push(walker.currentNode.parentElement);
                }
            }
            for (var el of found) {
                // Walk up to find the row container
                var p = el;
                for (var i = 0; i < 10; i++) {
                    if (!p) break;
                    var editLinks = p.querySelectorAll('a[data-event*="editContent"], a.sites-link');
                    for (var l of editLinks) {
                        if (l.textContent.trim() === 'Edit content' && l.offsetParent !== null) {
                            l.click();
                            return 'clicked for Concierge';
                        }
                    }
                    p = p.parentElement;
                }
            }
            return 'not found';
        }""")
        print(f"  {clicked}")
        pg.wait_for_timeout(15000)  # Wait longer for visual editor to load
        pg.screenshot(path='/tmp/zoho-54-editor-loaded.png')

        current_url = pg.url
        current_title = pg.title()
        print(f"  URL: {current_url}, Title: {current_title}")

        # Check editor state
        editor_state = pg.evaluate("""() => {
            return {
                hasApp: typeof window.app === 'object',
                appDataKeys: window.app?.data ? Object.keys(window.app.data).slice(0, 20) : [],
                resourceId: window.app?.data?.resource_id,
                currentPage: window.app?.data?.resource_url,
                // Try alternate paths
                alt1: window.zs_resource_id || null,
                alt2: window.zs_resource_url || null,
            };
        }""")
        print(f"  Editor state: {json.dumps(editor_state)}")

        # Step 3: Find and click the Publish dropdown, then "Publish Site"
        print("\n=== Clicking Publish Site ===")

        # First click the dropdown trigger
        pg.evaluate("""() => {
            // Click the dropdown arrow button (the chevron next to Publish)
            var btn = document.getElementById('publish_dd_btn');
            if (btn) { btn.click(); return 'clicked publish_dd_btn'; }
            var btns = document.querySelectorAll('[class*="publish"]');
            for (var b of btns) {
                if (b.textContent.trim() === 'Publish' && b.offsetParent !== null) {
                    b.click();
                    return 'clicked: ' + b.className;
                }
            }
            return 'not found';
        }""")
        pg.wait_for_timeout(2000)
        pg.screenshot(path='/tmp/zoho-54-pub-dropdown.png')

        # Now click "Publish Site" from the dropdown
        pub_site_result = pg.evaluate("""() => {
            var items = document.querySelectorAll('*');
            for (var item of items) {
                if (item.children.length === 0 &&
                    item.textContent.trim() === 'Publish Site' &&
                    item.offsetParent !== null) {
                    item.click();
                    return 'clicked Publish Site';
                }
            }
            return 'Publish Site not found';
        }""")
        print(f"  Publish Site click: {pub_site_result}")
        pg.wait_for_timeout(5000)
        pg.screenshot(path='/tmp/zoho-54-pub-dialog.png')

        # Handle the publish dialog
        dialog_buttons = pg.evaluate("""() => {
            var btns = document.querySelectorAll('button');
            var found = [];
            for (var btn of btns) {
                if (btn.offsetParent !== null && btn.textContent.trim()) {
                    found.push({text: btn.textContent.trim(), class: btn.className, id: btn.id});
                }
            }
            return found.slice(0, 20);
        }""")
        print(f"  Dialog buttons: {json.dumps(dialog_buttons)}")

        # Click Continue/Publish in dialog
        pg.evaluate("""() => {
            var btns = document.querySelectorAll('button');
            for (var btn of btns) {
                var txt = btn.textContent.trim();
                if (btn.offsetParent !== null && (txt === 'Continue' || txt === 'Publish')) {
                    btn.click();
                    return 'clicked: ' + txt;
                }
            }
        }""")
        pg.wait_for_timeout(15000)
        pg.screenshot(path='/tmp/zoho-54-after-pub-site.png')

        # Check what API was called
        print("\nAPI responses:")
        for url, r in sorted(all_responses.items()):
            if 'publish' in url.lower():
                print(f"  HTTP {r['status']} {url}")
                print(f"  Body: {r['body'][:400]}")

        # Check publish status from app state
        pub_state = pg.evaluate("""() => {
            return {
                publishedDomain: window.app?.data?.publishedDomain,
                isSitePublished: window.app?.data?.isSitePublished,
                content_state: window.app?.data?.sub_site_tree?.content_state,
            };
        }""")
        print(f"\nPublish state: {json.dumps(pub_state)}")

        # Now try updating page content_state via API
        # For each draft page, try to update its content state
        print("\n=== Trying to update page content_state via API ===")
        for page_url, page_id in DRAFT_PAGES:
            # Try PUT to update the page
            pg.evaluate(f"""() => {{
                window.__pageUp = 'pending';
                window.$X.put({{
                    url: '/zs-site/api/v1/pages/{page_id}',
                    headers: window.app.getHeaders(),
                    bodyJSON: {{
                        resource_id: '{page_id}',
                        subsite_id: '{SITE_ID}',
                        skip_publish: false,
                        content_state: 3,
                    }},
                    success: function(r) {{ window.__pageUp = r; }},
                    error: function(e) {{ window.__pageUp = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(6000)
            r2 = pg.evaluate("window.__pageUp")
            put_url = f"{BASE}/zs-site/api/v1/pages/{page_id}"
            if r2 and r2 != 'pending':
                print(f"  {page_url}: {json.dumps(r2)[:200]}")
            elif put_url in all_responses:
                print(f"  {page_url} network: HTTP {all_responses[put_url]['status']} {all_responses[put_url]['body'][:200]}")

        # Final publish
        print("\n=== Final publish after state updates ===")
        pg.evaluate("""() => {
            window.__fp = 'pending';
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__fp = r; },
                error: function(e) { window.__fp = {error: String(e)}; },
            });
        }""")
        for _ in range(4):
            pg.wait_for_timeout(5000)
            fp = pg.evaluate("window.__fp")
            if fp and fp != 'pending':
                break
        pub_url = f"{BASE}/zs-site/api/v1/publish"
        if fp and fp != 'pending':
            print(f"  Final publish: {json.dumps(fp)[:400]}")
        elif pub_url in all_responses:
            print(f"  Network: {all_responses[pub_url]['body'][:400]}")

        # Get pages list to check content states
        pg.evaluate(f"""() => {{
            window.__pgs2 = 'pending';
            window.$X.get({{
                url: '/zs-site/api/v1/pages?is_first=true&subsite_id={SITE_ID}',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__pgs2 = r; }},
                error: function(e) {{ window.__pgs2 = {{error: String(e)}}; }},
            }});
        }}""")
        for _ in range(4):
            pg.wait_for_timeout(5000)
            pgs2 = pg.evaluate("window.__pgs2")
            if pgs2 and pgs2 != 'pending':
                break
        if pgs2 and pgs2 != 'pending' and 'pages_details' in pgs2:
            print("\nUpdated page states:")
            for p in pgs2['pages_details'].get('pages', []):
                url_val = p.get('resource_url', '')
                if url_val in ['home', 'concierge', 'trip-planning', 'travel-advisor']:
                    print(f"  {url_val}: content_state={p.get('content_state')} skip={p.get('skip_publish')}")
        # Also from network
        pgs_url = f"{BASE}/zs-site/api/v1/pages?is_first=true&subsite_id={SITE_ID}"
        if pgs_url in all_responses:
            try:
                data = json.loads(all_responses[pgs_url]['body'])
                pages = data.get('pages_details', {}).get('pages', [])
                print("\nPage states from network:")
                for p in pages:
                    url_val = p.get('resource_url', '')
                    if url_val in ['home', 'concierge', 'trip-planning', 'travel-advisor']:
                        print(f"  {url_val}: content_state={p.get('content_state')}")
            except:
                pass

        browser.close()

    print("\nWaiting 60 seconds for propagation...")
    time.sleep(60)

    print("\n=== Final live check ===")
    for path in ['/', '/concierge', '/trip-planning', '/travel-advisor', '/categories']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', f'https://www.butlerbutton.co{path}'],
                           capture_output=True, text=True, timeout=20)
        print(f"  GET {path}: {r.stdout}")


if __name__ == '__main__':
    main()
