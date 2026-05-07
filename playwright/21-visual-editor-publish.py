"""
Open the visual editor for the home page, force-publish from within it.
Also captures what URLs the visual editor uses.
"""
import json, sys, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'
# Home page resource_id from pages API: 413198000000002008 (head_resource_id)
# or check pages for the homepage
PAGE_RESOURCE_ID = '413198000000002008'


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
        if 'zs-site' in resp.url or 'zohositescontent' in resp.url:
            try:
                body = resp.text() if resp.headers.get('content-type','').startswith('text') or 'json' in resp.headers.get('content-type','') else ''
                all_responses[resp.url] = {'status': resp.status, 'body': body[:200]}
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        # Try to open the visual page editor directly
        editor_url = f"{BASE}/zcms/{SITE_ID}/pages/{PAGE_RESOURCE_ID}/edit"
        print(f"Opening visual editor: {editor_url}")
        page.goto(editor_url, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        print(f"Current URL: {page.url}")
        print(f"Title: {page.title()}")
        page.screenshot(path='/tmp/zoho-visual-editor.png')
        print("Screenshot: /tmp/zoho-visual-editor.png")

        # Wait for editor to fully load
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(3000)

        # Check app data in the editor context
        editor_data = page.evaluate("""() => {
            return {
                publishedDomain: window.app.data.publishedDomain,
                isSitePublished: window.app.data.isSitePublished,
                currentPageId: window.app.data.currentPageId || window.app.data.sub_site_id,
                pageUrl: window.location.href,
            };
        }""")
        print(f"\nEditor app data: {json.dumps(editor_data)}")

        # Publish from within the editor context
        print("\nPublishing from editor context...")
        page.evaluate("""() => {
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__editorPub = r; },
                error: function(e) { window.__editorPub = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(10000)
        pub = page.evaluate("window.__editorPub || null")
        print(f"Editor publish: {json.dumps(pub)[:500] if pub else '(null)'}")

        # Check if there's a Publish button in the editor
        pub_btn = page.locator('text=Publish').all()
        print(f"\nPublish buttons: {len(pub_btn)}")
        for btn in pub_btn[:5]:
            try:
                print(f"  visible={btn.is_visible()}, class={btn.get_attribute('class')}")
            except Exception:
                pass

        browser.close()

    print("\nChecking key API calls made during editor load:")
    for url, r in sorted(all_responses.items()):
        if 'publish' in url.lower() or 'page' in url.lower() or 'content' in url.lower():
            print(f"  HTTP {r['status']}  {url[-80:]}")

    # Live check
    print("\n=== Live site check ===")
    import time
    time.sleep(10)
    for url in ['https://www.butlerbutton.co']:
        result = subprocess.run(
            ['curl', '-sv', '--max-time', '10', url],
            capture_output=True, text=True, timeout=15
        )
        lines = [l for l in result.stderr.split('\n') if 'HTTP/' in l or 'content-length' in l.lower()]
        print(f"  {url}: {lines}")


if __name__ == '__main__':
    main()
