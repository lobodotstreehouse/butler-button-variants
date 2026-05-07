"""
Check Zoho Sites dashboard for errors, page status, and site-level issues.
"""
import json, sys, subprocess
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
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        # Load dashboard
        page.goto(f"{BASE}/zcms/{SITE_ID}/dashboard",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(3000)

        page.screenshot(path='/tmp/zoho-dashboard.png')
        print("Screenshot: /tmp/zoho-dashboard.png")

        # Get all visible text on dashboard
        text = page.locator('body').inner_text()
        print(f"\nDashboard text (first 2000 chars):\n{text[:2000]}")

        # Check any error/warning elements
        warnings = page.locator('[class*="error"], [class*="warning"], [class*="alert"], [class*="danger"]').all()
        for w in warnings:
            if w.is_visible():
                print(f"\nWarning element: {w.inner_text()[:200]}")

        # Load the pages list to check page statuses
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Get page statuses via API
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/pages?is_first=true&subsite_id={SITE_ID}',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__pages = r; }},
                error: function(e) {{ window.__pages = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        pages = page.evaluate("window.__pages || null")

        if pages and 'pages_details' in pages:
            print(f"\nPages status:")
            for p in pages.get('pages_details', {}).get('pages', []):
                print(f"  resource_url={p.get('resource_url')} name={p.get('resource_name')} "
                      f"status={p.get('page_status',p.get('status','unknown'))}")

        # Check site status via GET /sites API
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/subsites/{SITE_ID}',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__siteStatus = r; }},
                error: function(e) {{ window.__siteStatus = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        site_status = page.evaluate("window.__siteStatus || null")
        print(f"\nSubsite status: {json.dumps(site_status)[:500] if site_status else '(null)'}")

        # Check if there's a site-level publish check endpoint
        page.evaluate("""() => {
            window.$X.get({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                success: function(r) { window.__pubStatus = r; },
                error: function(e) { window.__pubStatus = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(5000)
        pub_status = page.evaluate("window.__pubStatus || null")
        print(f"\nPublish status (GET): {json.dumps(pub_status)[:300] if pub_status else '(null)'}")

        browser.close()

    print("\n\nAll API responses from dashboard/pages:")
    for url, r in sorted(all_responses.items()):
        if 'dashboard' in url or 'pages' in url or 'subsite' in url or 'site/' in url:
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:300]}")


if __name__ == '__main__':
    main()
