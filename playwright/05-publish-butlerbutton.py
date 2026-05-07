"""
Re-publishes the site after the go.veltmtours.com -> butlerbutton.co domain change.
The Zoho backend returns HTTP 500 until a fresh publish is triggered.

Usage:
    python3 playwright/05-publish-butlerbutton.py
"""

import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE         = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID      = '413198000000002010'


def build_cookies(raw: dict) -> list:
    seen, cookies = set(), []
    for name, value in raw.items():
        if not value or not isinstance(value, str):
            continue
        key = (name, value)
        if key in seen:
            continue
        seen.add(key)
        cookies.append({
            'name': name, 'value': value,
            'domain': '.sitebuilder-60059075182.zohositescontent.in',
            'path': '/', 'httpOnly': False, 'secure': True,
        })
    return cookies


def main():
    raw = json.loads(Path(COOKIES_JSON).read_text())
    cookies = build_cookies(raw)
    print(f"Loaded {len(cookies)} cookies")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()

        pages_url = f"{BASE}/zcms/{SITE_ID}/pages"
        print(f"Loading {pages_url}")
        page.goto(pages_url, wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(2000)

        if 'accounts.zoho' in page.url or '/login' in page.url:
            print(f"Session expired — {page.url}")
            browser.close()
            sys.exit(1)
        print(f"Auth OK — {page.url}")

        # Navigate to header code editor so the SPA fully initialises $X + app
        target = f"{BASE}/zcms/{SITE_ID}/settings/code/header"
        print(f"Navigating to {target}")
        page.goto(target, wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)

        page.wait_for_function(
            "typeof window.$X === 'object' && typeof window.app === 'object'",
            timeout=30000,
        )
        # Extra settle time — SPA may still fire internal navigations after $X appears
        page.wait_for_timeout(4000)
        page.wait_for_load_state('networkidle', timeout=15000)
        page.wait_for_timeout(1000)
        print(f"$X SPA ready — url: {page.url}")

        # Intercept the publish response before firing so we catch it even if Zoho
        # navigates the SPA immediately after the XHR completes.
        publish_response = {}

        def handle_response(response):
            if '/zs-site/api/v1/publish' in response.url:
                try:
                    publish_response['status'] = response.status
                    publish_response['body'] = response.text()
                except Exception as e:
                    publish_response['error'] = str(e)

        page.on('response', handle_response)

        # Fire publish without awaiting — Zoho may navigate after XHR completes
        page.evaluate("""() => {
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__pubOk = r; },
                error: function(e) { window.__pubErr = e; },
            });
        }""")
        print("Publish fired — waiting for response...")

        # Wait for the network response or SPA to settle
        page.wait_for_timeout(8000)

        if publish_response:
            print(f"Publish response: HTTP {publish_response.get('status')} — {str(publish_response.get('body',''))[:300]}")
        else:
            print("No publish response captured (may have succeeded before intercept registered)")

        browser.close()

    print("Done — check https://www.butlerbutton.co")


if __name__ == '__main__':
    main()
