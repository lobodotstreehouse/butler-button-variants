"""
Open missing pages in the visual editor, check content, and force republish.
Target pages: home (413198000000004653), concierge, trip-planning, travel-advisor
"""
import json, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'


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

    page_ids = {}  # will be populated from pages list

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        pg = context.new_page()
        pg.on('response', capture_response)

        # Load pages list
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        # Get pages from JS state
        pages_data = pg.evaluate("""() => {
            // Try to get page data from app state
            var d = window.app && window.app.data;
            if (d && d.pages) return d.pages;
            if (d && d.sub_site_tree && d.sub_site_tree.pages) return d.sub_site_tree.pages;
            return null;
        }""")
        print(f"Pages from app.data: {json.dumps(pages_data)[:500] if pages_data else '(null)'}")

        # Also get from API with longer wait
        pg.evaluate(f"""() => {{
            window.__pgs = 'pending';
            window.$X.get({{
                url: '/zs-site/api/v1/pages?subsite_id={SITE_ID}&include_all=true',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__pgs = r; }},
                error: function(e) {{ window.__pgs = {{error: String(e)}}; }},
            }});
        }}""")
        for _ in range(8):
            pg.wait_for_timeout(5000)
            r = pg.evaluate("window.__pgs")
            if r and r != 'pending':
                break
            print(f"  Waiting for pages API... ({(_+1)*5}s)")

        if r and r != 'pending' and 'pages_details' in r:
            pages = r['pages_details'].get('pages', [])
            print(f"\nGot {len(pages)} pages:")
            for p in pages:
                url = p.get('resource_url', '')
                pid = p.get('resource_id', '')
                page_ids[url] = pid
                print(f"  url={url!r} id={pid} skip_pub={p.get('skip_publish')} content_state={p.get('content_state')}")
        else:
            print(f"\nPages API still pending or error: {r}")
            # Fall back to known IDs from earlier scripts
            page_ids = {
                'home': '413198000000004653',
            }
            # Get other IDs from the pages list HTML
            page_links = pg.evaluate("""() => {
                var links = document.querySelectorAll('a[href*="/page/"]');
                var result = {};
                for (var l of links) {
                    var match = l.href.match(/\/page\/(\d+)/);
                    if (match) {
                        result[l.textContent.trim().toLowerCase()] = match[1];
                    }
                }
                return result;
            }""")
            print(f"Page links from DOM: {json.dumps(page_links)}")
            if page_links:
                page_ids.update(page_links)

        print(f"\nPage IDs: {json.dumps(page_ids)}")

        # For each missing page, open in editor and publish
        target_pages = ['home', 'concierge', 'trip-planning', 'travel-advisor']
        for target in target_pages:
            pid = page_ids.get(target)
            if not pid:
                # Try to find by checking links in pages list
                pid = pg.evaluate(f"""() => {{
                    var links = document.querySelectorAll('a');
                    for (var l of links) {{
                        if (l.textContent.trim().toLowerCase() === '{target}' ||
                            l.href && l.href.includes('/page/')) {{
                            // check nearby text
                            var nearby = l.closest('[class*="row"], [class*="item"], li, tr');
                            if (nearby && nearby.textContent.toLowerCase().includes('{target}')) {{
                                var m = l.href.match(/\/page\/(\d+)/);
                                if (m) return m[1];
                            }}
                        }}
                    }}
                    return null;
                }}""")
                if pid:
                    print(f"Found {target} ID from DOM: {pid}")
                    page_ids[target] = pid

            if not pid:
                print(f"\nSkipping {target} - no page ID found")
                continue

            print(f"\n=== Processing page: {target} (ID: {pid}) ===")

            # Navigate to page editor
            pg.goto(f"{BASE}/zcms/{SITE_ID}/page/{pid}",
                    wait_until='networkidle', timeout=60000)
            pg.wait_for_timeout(5000)
            pg.screenshot(path=f'/tmp/zoho-50-{target}.png')

            # Check if editor loaded
            editor_loaded = pg.evaluate("""() => {
                return typeof window.app === 'object' && window.app !== null;
            }""")
            print(f"  Editor loaded: {editor_loaded}")

            if not editor_loaded:
                print(f"  Editor not loaded for {target}, trying pages list approach")
                continue

            # Try to get the page info
            page_info = pg.evaluate("""() => {
                var d = window.app && window.app.data;
                return d ? {
                    resourceUrl: d.resource_url,
                    contentState: d.content_state,
                    resourceId: d.resource_id,
                    title: document.title,
                } : null;
            }""")
            print(f"  Page info: {json.dumps(page_info)}")

            # Navigate to page in pages list and find the publish button
            pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                    wait_until='networkidle', timeout=60000)
            pg.wait_for_timeout(4000)
            pg.wait_for_function(
                "typeof window.$X==='object' && typeof window.app==='object'",
                timeout=30000)
            pg.wait_for_timeout(2000)

            # Try to publish this specific page via API
            pg.evaluate(f"""() => {{
                window.__pp = 'pending';
                window.$X.post({{
                    url: '/zs-site/api/v1/pages/{pid}/publish',
                    headers: window.app.getHeaders(),
                    bodyJSON: {{}},
                    success: function(r) {{ window.__pp = r; }},
                    error: function(e) {{ window.__pp = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(8000)
            pp = pg.evaluate("window.__pp")
            pp_url = f"{BASE}/zs-site/api/v1/pages/{pid}/publish"
            if pp and pp != 'pending':
                print(f"  Page publish result: {json.dumps(pp)[:300]}")
            elif pp_url in all_responses:
                print(f"  Network: HTTP {all_responses[pp_url]['status']} {all_responses[pp_url]['body'][:300]}")
                del all_responses[pp_url]
            else:
                print(f"  Page publish: still pending/no response")

            # Also try GET publish for this page
            pg.evaluate(f"""() => {{
                window.__ppg = 'pending';
                window.$X.get({{
                    url: '/zs-site/api/v1/pages/{pid}/publish',
                    headers: window.app.getHeaders(),
                    success: function(r) {{ window.__ppg = r; }},
                    error: function(e) {{ window.__ppg = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(6000)
            ppg = pg.evaluate("window.__ppg")
            if ppg and ppg != 'pending':
                print(f"  GET page publish: {json.dumps(ppg)[:300]}")

        # Final full site publish
        print("\n=== Final full site publish ===")
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(4000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(2000)

        pg.evaluate("""() => {
            window.__fpub = 'pending';
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__fpub = r; },
                error: function(e) { window.__fpub = {error: String(e)}; },
            });
        }""")
        for _ in range(4):
            pg.wait_for_timeout(5000)
            fpub = pg.evaluate("window.__fpub")
            if fpub and fpub != 'pending':
                break
        pub_url = f"{BASE}/zs-site/api/v1/publish"
        if fpub and fpub != 'pending':
            print(f"  Result: {json.dumps(fpub)[:400]}")
        elif pub_url in all_responses:
            print(f"  Network: {all_responses[pub_url]['body'][:400]}")

        # Click the UI Publish button
        print("\nClicking UI Publish button...")
        pg.evaluate("""() => {
            var btns = document.querySelectorAll('button, a');
            for (var btn of btns) {
                if ((btn.textContent.trim() === 'Publish' || btn.classList.contains('h-publish'))
                    && btn.offsetParent !== null) {
                    btn.click();
                    return 'clicked';
                }
            }
            return 'not found';
        }""")
        pg.wait_for_timeout(6000)
        # Accept any dialog
        pg.evaluate("""() => {
            var btns = document.querySelectorAll('button');
            for (var btn of btns) {
                if ((btn.textContent.trim().toLowerCase().includes('publish') ||
                     btn.textContent.trim().toLowerCase() === 'continue')
                    && btn.offsetParent !== null) {
                    btn.click();
                    return 'clicked dialog btn: ' + btn.textContent.trim();
                }
            }
            return 'no dialog btn';
        }""")
        pg.wait_for_timeout(10000)
        pg.screenshot(path='/tmp/zoho-50-final-publish.png')

        browser.close()

    print("\nWaiting 30 seconds for propagation...")
    time.sleep(30)

    print("\n=== Final live site check ===")
    for url in ['https://www.butlerbutton.co/', 'https://www.butlerbutton.co/concierge',
                'https://www.butlerbutton.co/trip-planning', 'https://www.butlerbutton.co/travel-advisor',
                'https://www.butlerbutton.co/categories']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', url], capture_output=True, text=True, timeout=20)
        print(f"  GET {url}: {r.stdout}")


if __name__ == '__main__':
    main()
