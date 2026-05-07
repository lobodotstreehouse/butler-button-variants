"""
The CDN has old cached content (title=go.VELTMtours.com).
Concierge/trip-planning/home pages not serving.
1. Get full page list with skip_publish, content_state, etc.
2. Check if concierge/trip-planning have skip_publish=True
3. Try to "touch" pages to mark them dirty for republish
4. Do a full publish
5. Also try to publish from the visual editor
"""
import json, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'
HOME_PAGE_ID = '413198000000004653'


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
        page = context.new_page()
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                  wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # 1. Get full page list
        page.evaluate(f"""() => {{
            window.__pages = 'pending';
            window.$X.get({{
                url: '/zs-site/api/v1/pages?subsite_id={SITE_ID}&include_all=true',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__pages = r; }},
                error: function(e) {{ window.__pages = {{error: String(e)}}; }},
            }});
        }}""")
        for _ in range(4):
            page.wait_for_timeout(5000)
            result = page.evaluate("window.__pages")
            if result and result != 'pending':
                break

        print("=== Page states ===")
        pages_by_url = {}
        if result and result != 'pending' and 'pages_details' in result:
            pages = result['pages_details'].get('pages', [])
            for p in pages:
                url = p.get('resource_url', '')
                pages_by_url[url] = p
                print(f"  url={url!r} id={p.get('resource_id')} skip_pub={p.get('skip_publish')} "
                      f"content_state={p.get('content_state')} trash={p.get('trash')} "
                      f"published_url={p.get('published_resource_url')}")
        else:
            print(f"  Failed: {result}")

        # 2. Check if skip_publish can be cleared for concierge/trip-planning
        # Try setting skip_publish=False explicitly via PUT on those pages
        target_pages = ['concierge', 'trip-planning', 'travel-advisor', 'home']
        for url in target_pages:
            p = pages_by_url.get(url)
            if p:
                pid = p.get('resource_id')
                print(f"\n=== Force-enabling {url} (ID: {pid}) for publish ===")

                # Try PUT to update page metadata
                page.evaluate(f"""() => {{
                    window.__pageUpdate = 'pending';
                    window.$X.put({{
                        url: '/zs-site/api/v1/pages/{pid}',
                        headers: window.app.getHeaders(),
                        bodyJSON: {{resource_id: '{pid}', skip_publish: false}},
                        success: function(r) {{ window.__pageUpdate = r; }},
                        error: function(e) {{ window.__pageUpdate = {{error: String(e)}}; }},
                    }});
                }}""")
                page.wait_for_timeout(6000)
                upd = page.evaluate("window.__pageUpdate")
                if upd and upd != 'pending':
                    print(f"  PUT result: {json.dumps(upd)[:200]}")
                put_url = f"{BASE}/zs-site/api/v1/pages/{pid}"
                if put_url in all_responses:
                    print(f"  Network: HTTP {all_responses[put_url]['status']} {all_responses[put_url]['body'][:200]}")
            else:
                print(f"\n  Page not found: {url}")

        # 3. Try to publish specific pages via /pages/{id}/publish
        print("\n=== Publishing individual pages ===")
        for url in target_pages:
            p = pages_by_url.get(url)
            if p:
                pid = p.get('resource_id')
                page.evaluate(f"""() => {{
                    window.__pagePub = 'pending';
                    window.$X.post({{
                        url: '/zs-site/api/v1/pages/{pid}/publish',
                        headers: window.app.getHeaders(),
                        bodyJSON: {{}},
                        success: function(r) {{ window.__pagePub = r; }},
                        error: function(e) {{ window.__pagePub = {{error: String(e)}}; }},
                    }});
                }}""")
                page.wait_for_timeout(6000)
                pub = page.evaluate("window.__pagePub")
                if pub and pub != 'pending':
                    print(f"  {url}: {json.dumps(pub)[:200]}")
                pub_url = f"{BASE}/zs-site/api/v1/pages/{pid}/publish"
                if pub_url in all_responses:
                    print(f"  {url} network: HTTP {all_responses[pub_url]['status']} {all_responses[pub_url]['body'][:200]}")
                    del all_responses[pub_url]

        # 4. Now try a full site publish
        print("\n=== Full site publish ===")
        page.evaluate("""() => {
            window.__pub = 'pending';
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__pub = r; },
                error: function(e) { window.__pub = {error: String(e)}; },
            });
        }""")
        for _ in range(4):
            page.wait_for_timeout(5000)
            pub = page.evaluate("window.__pub")
            if pub and pub != 'pending':
                break
        pub_url = f"{BASE}/zs-site/api/v1/publish"
        if pub and pub != 'pending':
            print(f"  Result: {json.dumps(pub)[:400]}")
        elif pub_url in all_responses:
            print(f"  Network: {all_responses[pub_url]['body'][:400]}")

        # 5. Check what the visual editor's publish button does
        # Navigate to the home page editor and click publish there
        print("\n=== Checking home page in editor ===")
        page.goto(f"{BASE}/zcms/{SITE_ID}/page/{HOME_PAGE_ID}",
                  wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)

        # Check if the page loads
        page_title = page.title()
        print(f"  Editor page title: {page_title}")
        page.screenshot(path='/tmp/zoho-49-editor.png')

        # Get editor state
        editor_state = page.evaluate("""() => {
            var d = window.app && window.app.data;
            return d ? {
                resourceUrl: d.resource_url,
                contentState: d.content_state,
                publishStatus: d.publish_status,
            } : null;
        }""")
        print(f"  Editor state: {json.dumps(editor_state)}")

        # Click the editor's Publish button
        print("  Clicking editor Publish button...")
        pub_btn = page.evaluate("""() => {
            var btns = document.querySelectorAll('button, a');
            for (var btn of btns) {
                if (btn.textContent.trim() === 'Publish' && btn.offsetParent !== null) {
                    btn.click();
                    return 'clicked: ' + btn.className;
                }
            }
            return 'not found';
        }""")
        print(f"  Publish button click: {pub_btn}")
        page.wait_for_timeout(8000)
        page.screenshot(path='/tmp/zoho-49-after-pub.png')

        browser.close()

    print("\n=== Live site check (after 15s) ===")
    import time; time.sleep(15)
    for url in ['https://www.butlerbutton.co/', 'https://www.butlerbutton.co/concierge',
                'https://www.butlerbutton.co/trip-planning', 'https://www.butlerbutton.co/categories']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', url], capture_output=True, text=True, timeout=20)
        print(f"  GET {url}: {r.stdout}")


if __name__ == '__main__':
    main()
