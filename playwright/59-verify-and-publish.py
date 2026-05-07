"""
Verify current content_state of draft pages, then try to publish them.
The status li click in script 58 may have changed them to state 2 (Ready to publish).
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
        browser = pw.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        pg = context.new_page()
        pg.on('response', capture_response)

        # Fresh load to capture current page states
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        # Step 1: Read page states from the initial API call
        pgs_url = f"{BASE}/zs-site/api/v1/pages?is_first=true&subsite_id={SITE_ID}"
        if pgs_url in all_responses:
            try:
                data = json.loads(all_responses[pgs_url]['body'])
                pages = data.get('pages_details', {}).get('pages', [])
                print("=== Current page states ===")
                for p in pages:
                    url_val = p.get('resource_url', '')
                    print(f"  {url_val}: content_state={p.get('content_state')} skip={p.get('skip_publish')}")
            except Exception as e:
                print(f"Parse error: {e}")
        else:
            print("Pages list not captured in initial load")

        # Step 2: Get individual page states for each draft page
        print("\n=== Individual page states ===")
        for page_url, page_id in DRAFT_PAGES:
            pg.evaluate(f"""() => {{
                window.__ps_{page_id.replace('-','')} = 'pending';
                window.$X.get({{
                    url: '/zs-site/api/v1/pages/{page_id}',
                    headers: window.app.getHeaders(),
                    success: function(r) {{ window.__ps_{page_id.replace('-','')} = r; }},
                    error: function(e) {{ window.__ps_{page_id.replace('-','')} = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(6000)
            result = pg.evaluate(f"window.__ps_{page_id.replace('-','')}")
            pg_url_key = f"{BASE}/zs-site/api/v1/pages/{page_id}"
            if result and result != 'pending':
                # Try page_details directly or via page_info
                pd = result.get('page_details') or result.get('page_info', {}).get('page_details', {})
                cs = pd.get('content_state', '?')
                print(f"  {page_url}: content_state={cs}")
            elif pg_url_key in all_responses:
                try:
                    d = json.loads(all_responses[pg_url_key]['body'])
                    pd = d.get('page_details') or d.get('page_info', {}).get('page_details', {})
                    cs = pd.get('content_state', '?')
                    print(f"  {page_url}: content_state={cs} (from network)")
                except Exception as e:
                    print(f"  {page_url}: parse error {e}: {all_responses[pg_url_key]['body'][:200]}")
            else:
                print(f"  {page_url}: no response")

        # Step 3: Check what the badge shows in the UI - are any showing "Ready to publish" instead of "Draft"?
        badge_states = pg.evaluate("""() => {
            var results = [];
            // Look for all draft/ready badges
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                var t = walker.currentNode.textContent.trim();
                var el = walker.currentNode.parentElement;
                if (el.offsetParent !== null && (t === 'Draft' || t === 'Ready to publish')) {
                    // Find which page this belongs to - look for page name in parent
                    var row = el;
                    var pageName = '';
                    for (var i = 0; i < 10; i++) {
                        if (!row.parentElement) break;
                        row = row.parentElement;
                        // Find page name in row
                        var links = row.querySelectorAll('a.jsnav, a[data-event*="editContent"]');
                        for (var l of links) {
                            var lt = l.textContent.trim();
                            if (lt && !lt.includes('Edit') && lt.length < 60) {
                                pageName = lt;
                                break;
                            }
                        }
                        if (pageName) break;
                    }
                    results.push({
                        status: t,
                        pageName: pageName,
                        badgeClass: el.className,
                        badgeId: el.id,
                    });
                }
            }
            return results;
        }""")
        print(f"\n=== UI badge states ===")
        for b in badge_states:
            print(f"  {b.get('pageName', '?')}: {b['status']} (class: {b['badgeClass']})")

        # Step 4: Check the status li elements - are they showing "Ready to publish" or "Mark as draft"?
        status_li_states = pg.evaluate("""() => {
            var ids = [
                'status_413198000000002013',
                'status_413198000000004653',
                'status_413198000000047002',
                'status_413198000000047014',
            ];
            var results = {};
            for (var id of ids) {
                var el = document.getElementById(id);
                if (el) {
                    results[id] = {
                        text: el.textContent.trim(),
                        dataContentState: el.getAttribute('data-content-state'),
                        dataCurrContentState: el.getAttribute('data-currcontent-state'),
                    };
                } else {
                    results[id] = 'NOT FOUND';
                }
            }
            return results;
        }""")
        print(f"\n=== Status li element states ===")
        print(json.dumps(status_li_states, indent=2))

        # Step 5: If pages are still draft (state 1), try the updatePageStatusPartial
        # by finding and clicking the "Ready to publish" option for each
        print("\n=== Checking if pages need to be marked ready ===")
        pages_to_fix = []
        for page_url, page_id in DRAFT_PAGES:
            li_id = f"status_{page_id}"
            li_state = status_li_states.get(li_id, {})
            if isinstance(li_state, dict):
                curr_state = li_state.get('dataCurrContentState', '?')
                next_state = li_state.get('dataContentState', '?')
                text = li_state.get('text', '?')
                print(f"  {page_url}: current_state={curr_state}, option='{text}'")
                if curr_state == '1':  # Still draft
                    pages_to_fix.append((page_url, page_id))
            else:
                print(f"  {page_url}: li not found")
                pages_to_fix.append((page_url, page_id))

        if pages_to_fix:
            print(f"\nNeed to mark {len(pages_to_fix)} pages ready to publish")
            for page_url, page_id in pages_to_fix:
                click_r = pg.evaluate(f"""() => {{
                    var li = document.getElementById('status_{page_id}');
                    if (!li) return 'not found';
                    // Make sure the li text says Ready to publish before clicking
                    var txt = li.textContent.trim();
                    if (txt !== 'Ready to publish') return 'wrong state: ' + txt;
                    li.click();
                    return 'clicked: ' + txt;
                }}""")
                print(f"  {page_url}: {click_r}")
                pg.wait_for_timeout(3000)

                # Check update response
                upd_url = f"{BASE}/zs-site/api/v1/pages/{page_id}"
                if upd_url in all_responses:
                    body = all_responses[upd_url]['body']
                    try:
                        d = json.loads(body)
                        pd = d.get('page_details') or d.get('page_info', {}).get('page_details', {})
                        print(f"    Updated: content_state={pd.get('content_state')}")
                    except:
                        print(f"    Response: {body[:200]}")

        # Step 6: Try publishing each page now
        pg.wait_for_timeout(2000)
        print("\n=== Publishing pages via POST /resources/{id}/publish ===")
        for page_url, page_id in DRAFT_PAGES:
            pg.evaluate(f"""() => {{
                window.__rp = 'pending';
                window.$X.post({{
                    url: '/zs-site/api/v1/resources/{page_id}/publish',
                    headers: window.app.getHeaders(),
                    bodyJSON: {{}},
                    success: function(r) {{ window.__rp = r; }},
                    error: function(e) {{ window.__rp = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(6000)
            r = pg.evaluate("window.__rp")
            pub_url = f"{BASE}/zs-site/api/v1/resources/{page_id}/publish"
            if pub_url in all_responses:
                net = all_responses[pub_url]
                print(f"  {page_url}: HTTP {net['status']} {net['body'][:200]}")
                del all_responses[pub_url]
            elif r and r != 'pending':
                print(f"  {page_url}: {json.dumps(r)[:200]}")
            else:
                print(f"  {page_url}: timeout")

        # Step 7: Final site publish
        print("\n=== Final site publish ===")
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
        for _ in range(5):
            pg.wait_for_timeout(5000)
            fp = pg.evaluate("window.__fp")
            if fp and fp != 'pending':
                break
        pub_url_s = f"{BASE}/zs-site/api/v1/publish"
        if fp and fp != 'pending':
            print(f"  Result: {json.dumps(fp)[:400]}")
        elif pub_url_s in all_responses:
            print(f"  Network: {all_responses[pub_url_s]['body'][:400]}")

        # Check final page states
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pgs_url2 = f"{BASE}/zs-site/api/v1/pages?is_first=true&subsite_id={SITE_ID}"
        if pgs_url2 in all_responses:
            try:
                data = json.loads(all_responses[pgs_url2]['body'])
                pages = data.get('pages_details', {}).get('pages', [])
                print("\n=== FINAL page states ===")
                for p in pages:
                    url_val = p.get('resource_url', '')
                    if url_val in ['home', 'concierge', 'trip-planning', 'travel-advisor']:
                        print(f"  {url_val}: content_state={p.get('content_state')}")
            except Exception as e:
                print(f"Parse error: {e}")

        browser.close()

    print("\nWaiting 60 seconds for CDN propagation...")
    time.sleep(60)

    print("\n=== Final live check ===")
    for path in ['/', '/concierge', '/trip-planning', '/travel-advisor', '/categories']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', f'https://www.butlerbutton.co{path}'],
                           capture_output=True, text=True, timeout=20)
        print(f"  GET {path}: {r.stdout}")


if __name__ == '__main__':
    main()
