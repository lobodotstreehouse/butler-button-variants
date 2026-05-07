"""
Click status_{page_id} li elements to mark all 4 draft pages as "Ready to publish",
then publish the site. The dropdown reveals:
  <li id="status_{id}" data-event="click pages.updatePageStatusPartial"
      data-currcontent-state="1" data-content-state="2">
    Ready to publish
  </li>
"""
import json, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'

DRAFT_PAGES = [
    ('concierge',       '413198000000002013'),
    ('home',            '413198000000004653'),
    ('trip-planning',   '413198000000047002'),
    ('travel-advisor',  '413198000000047014'),
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

        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        # Step 1: For each draft page, click its status li to mark Ready to publish
        print("=== Marking pages as Ready to publish ===")
        for page_url, page_id in DRAFT_PAGES:
            print(f"\n--- {page_url} (ID: {page_id}) ---")

            # The li element has id="status_{page_id}" and fires pages.updatePageStatusPartial
            # We need to click it; it may be hidden in the hb-dd-content.
            # We need to first open the dropdown (click hb-dd-btn in that row), then click the li.

            # First: open the dropdown for this page by clicking its badge
            open_result = pg.evaluate(f"""() => {{
                var li = document.getElementById('status_{page_id}');
                if (!li) return 'status_{page_id} not found';
                // Click the parent dropdown btn to open
                var ddBtn = li.closest('[class*="hb-dd"]')?.querySelector('.hb-dd-btn');
                if (ddBtn) {{
                    ddBtn.click();
                    return 'opened dropdown for {page_url}';
                }}
                // If the li is already accessible, click it directly
                li.click();
                return 'clicked li directly';
            }}""")
            print(f"  Open dropdown: {open_result}")
            pg.wait_for_timeout(1000)

            # Now click the "Ready to publish" li
            click_result = pg.evaluate(f"""() => {{
                var li = document.getElementById('status_{page_id}');
                if (!li) return 'not found';
                li.click();
                return 'clicked status_{page_id}: ' + li.textContent.trim();
            }}""")
            print(f"  Click li: {click_result}")
            pg.wait_for_timeout(4000)

            # Check what API call was made
            print("  Recent API calls:")
            for url, r in list(all_responses.items()):
                if page_id in url or 'updatePageStatus' in url or 'pages' in url:
                    print(f"    HTTP {r['status']} {url}")
                    print(f"    {r['body'][:300]}")

        pg.wait_for_timeout(2000)
        pg.screenshot(path='/tmp/zoho-58-after-ready.png')

        # Check all API responses so far
        print("\n=== All API responses so far ===")
        for url, r in sorted(all_responses.items()):
            if 'pages' in url.lower() or 'publish' in url.lower():
                print(f"  HTTP {r['status']} {url}")
                print(f"  {r['body'][:200]}")

        # Step 2: Check content states now
        print("\n=== Checking page states after marking ready ===")
        pg.evaluate(f"""() => {{
            window.__pagesList = 'pending';
            window.$X.get({{
                url: '/zs-site/api/v1/pages?is_first=true&subsite_id={SITE_ID}',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__pagesList = r; }},
                error: function(e) {{ window.__pagesList = {{error: String(e)}}; }},
            }});
        }}""")
        pg.wait_for_timeout(10000)
        pages_list = pg.evaluate("window.__pagesList")
        if pages_list and pages_list != 'pending' and 'pages_details' in pages_list:
            print("Page states:")
            for p in pages_list['pages_details'].get('pages', []):
                url_val = p.get('resource_url', '')
                if url_val in ['home', 'concierge', 'trip-planning', 'travel-advisor']:
                    print(f"  {url_val}: content_state={p.get('content_state')} skip={p.get('skip_publish')}")
        else:
            # Check network capture
            pgs_url = f"{BASE}/zs-site/api/v1/pages?is_first=true&subsite_id={SITE_ID}"
            if pgs_url in all_responses:
                try:
                    data = json.loads(all_responses[pgs_url]['body'])
                    pages = data.get('pages_details', {}).get('pages', [])
                    print("Page states (from network):")
                    for p in pages:
                        url_val = p.get('resource_url', '')
                        if url_val in ['home', 'concierge', 'trip-planning', 'travel-advisor']:
                            print(f"  {url_val}: content_state={p.get('content_state')} skip={p.get('skip_publish')}")
                except Exception as e:
                    print(f"Parse error: {e}")
            else:
                print("Pages list not available in responses")

        # Step 3: Try POST /resources/{id}/publish for each page now they're ready
        print("\n=== Publishing pages via POST /resources/{id}/publish ===")
        for page_url, page_id in DRAFT_PAGES:
            pg.evaluate(f"""() => {{
                window.__pub_{page_id.replace('-','')} = 'pending';
                window.$X.post({{
                    url: '/zs-site/api/v1/resources/{page_id}/publish',
                    headers: window.app.getHeaders(),
                    bodyJSON: {{}},
                    success: function(r) {{ window.__pub_{page_id.replace('-','')} = r; }},
                    error: function(e) {{ window.__pub_{page_id.replace('-','')} = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(6000)
            r = pg.evaluate(f"window.__pub_{page_id.replace('-','')}")
            pub_url = f"{BASE}/zs-site/api/v1/resources/{page_id}/publish"
            if pub_url in all_responses:
                net = all_responses[pub_url]
                print(f"  {page_url}: HTTP {net['status']} {net['body'][:200]}")
                del all_responses[pub_url]
            elif r and r != 'pending':
                print(f"  {page_url}: {json.dumps(r)[:200]}")
            else:
                print(f"  {page_url}: timeout")

        # Step 4: Final site-wide publish
        print("\n=== Final site-wide publish ===")
        pg.evaluate("""() => {
            window.__finalPub = 'pending';
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__finalPub = r; },
                error: function(e) { window.__finalPub = {error: String(e)}; },
            });
        }""")
        for _ in range(5):
            pg.wait_for_timeout(5000)
            fp = pg.evaluate("window.__finalPub")
            if fp and fp != 'pending':
                break
        pub_url = f"{BASE}/zs-site/api/v1/publish"
        if fp and fp != 'pending':
            print(f"  Result: {json.dumps(fp)[:400]}")
        elif pub_url in all_responses:
            print(f"  Network: {all_responses[pub_url]['body'][:400]}")

        browser.close()

    print("\nWaiting 60 seconds for CDN propagation...")
    time.sleep(60)

    print("\n=== Final live check ===")
    for path in ['/', '/concierge', '/trip-planning', '/travel-advisor', '/categories', '/company']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', f'https://www.butlerbutton.co{path}'],
                           capture_output=True, text=True, timeout=20)
        print(f"  GET {path}: {r.stdout}")


if __name__ == '__main__':
    main()
