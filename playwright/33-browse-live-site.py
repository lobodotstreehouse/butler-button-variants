"""
Visit www.butlerbutton.co in a real browser (no auth cookies) and see what loads.
Also try publishing again now that the .zohosites.in domain is added.
Check the home page resource ID and why / returns 500.
"""
import json, subprocess
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

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)

        # 1. First browse live site WITHOUT auth cookies (public context)
        public_context = browser.new_context(viewport={'width': 1440, 'height': 900})
        pub_page = public_context.new_page()
        pub_responses = {}
        def cap_pub(r):
            pub_responses[r.url] = r.status
        pub_page.on('response', cap_pub)

        print("Visiting www.butlerbutton.co (public)...")
        try:
            pub_page.goto('https://www.butlerbutton.co/', wait_until='domcontentloaded', timeout=20000)
        except Exception as e:
            print(f"  Root / error: {e}")

        pub_page.wait_for_timeout(3000)
        pub_page.screenshot(path='/tmp/zoho-live-home.png')
        print("Screenshot: /tmp/zoho-live-home.png")
        print(f"Root / URL now: {pub_page.url}")
        print(f"Root / title: {pub_page.title()}")
        body = pub_page.locator('body').inner_text()
        print(f"Root / body text:\n{body[:500]}")

        try:
            pub_page.goto('https://www.butlerbutton.co/concierge', wait_until='domcontentloaded', timeout=20000)
        except Exception as e:
            print(f"  /concierge error: {e}")
        pub_page.wait_for_timeout(3000)
        pub_page.screenshot(path='/tmp/zoho-live-concierge.png')
        print("\nScreenshot: /tmp/zoho-live-concierge.png")
        print(f"/concierge URL now: {pub_page.url}")
        print(f"/concierge title: {pub_page.title()}")
        body2 = pub_page.locator('body').inner_text()
        print(f"/concierge body text:\n{body2[:500]}")
        public_context.close()

        # 2. Auth context - publish again now that .zohosites.in is added
        auth_context = browser.new_context(viewport={'width': 1440, 'height': 900})
        auth_context.add_cookies(cookies)
        page = auth_context.new_page()
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(2000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Get full pages list from network capture
        # Already triggered by navigation to /pages
        pages_url = f"{BASE}/zs-site/api/v1/pages?is_first=true&subsite_id={SITE_ID}"
        if pages_url in all_responses:
            pages_data = json.loads(all_responses[pages_url]['body'])
            pages = pages_data.get('pages_details', {}).get('pages', [])
            print(f"\nAll pages ({len(pages)}):")
            for p in pages:
                print(f"  url='{p.get('resource_url')}' name='{p.get('resource_name')}' "
                      f"id={p.get('resource_id')} type={p.get('resource_type')} "
                      f"home={p.get('home_resource_id')}")
        else:
            # Get manually
            page.evaluate(f"""() => {{
                window.$X.get({{
                    url: '/zs-site/api/v1/pages?subsite_id={SITE_ID}&include_all=true',
                    headers: window.app.getHeaders(),
                    success: function(r) {{ window.__allPages = r; }},
                    error: function(e) {{ window.__allPages = {{error: String(e)}}; }},
                }});
            }}""")
            page.wait_for_timeout(6000)
            ap = page.evaluate("window.__allPages || null")
            print(f"\nAll pages: {json.dumps(ap)[:1000] if ap else '(null)'}")

        # Get home page resource
        home_resource_id = '413198000000004653'
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/pages/{home_resource_id}',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__homePage = r; }},
                error: function(e) {{ window.__homePage = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(6000)
        home = page.evaluate("window.__homePage || null")
        print(f"\nHome page resource: {json.dumps(home)[:800] if home else '(null)'}")

        # Publish again with .zohosites.in in the mix
        print("\nPublishing again (now with .zohosites.in domain)...")
        page.evaluate("""() => {
            window.__pub2 = null;
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__pub2 = r; },
                error: function(e) { window.__pub2 = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(15000)
        pub2 = page.evaluate("window.__pub2 || null")
        print(f"Publish result: {json.dumps(pub2)[:500] if pub2 else '(null)'}")

        auth_context.close()
        browser.close()

    print("\n\nWaiting 15 seconds...")
    import time
    time.sleep(15)

    print("\n=== Live site check after publish ===")
    for url in ['https://www.butlerbutton.co/', 'https://www.butlerbutton.co/concierge',
                'https://butlerbutton.zohosites.in/']:
        result = subprocess.run(
            ['curl', '-sv', '--max-time', '15', url],
            capture_output=True, text=True, timeout=20
        )
        status = next((l for l in result.stderr.split('\n') if '< HTTP/' in l), 'unknown')
        body_snip = result.stdout[:200] if result.stdout else '(empty)'
        print(f"\n  {url}: {status.strip()}")
        print(f"  Body: {body_snip}")


if __name__ == '__main__':
    main()
