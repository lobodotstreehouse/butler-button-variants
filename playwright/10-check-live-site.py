"""
Navigate to live site in Playwright and capture what's happening.
Also checks domain verify status via the UI.
"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE    = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID = '413198000000002010'


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
    zoho_cookies = build_cookies(raw)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)

        # --- 1. Visit the live site from a clean context ---
        public_context = browser.new_context(viewport={'width': 1440, 'height': 900})
        public_page = public_context.new_page()

        site_responses = {}
        def capture_public(resp):
            site_responses[resp.url] = resp.status

        public_page.on('response', capture_public)

        print("Visiting https://www.butlerbutton.co ...")
        try:
            public_page.goto('https://www.butlerbutton.co',
                             wait_until='commit', timeout=20000)
            public_page.wait_for_timeout(3000)
            url = public_page.url
            title = public_page.title()
            body_text = public_page.locator('body').inner_text()[:300]
            body_html = public_page.content()[:1000]
            print(f"Final URL: {url}")
            print(f"Title: {title}")
            print(f"Body text: {body_text[:200]}")
            print(f"Page HTML (first 1000 chars):\n{body_html}")
        except Exception as e:
            print(f"Error loading site: {e}")

        print("\nResponse statuses:")
        for url, status in list(site_responses.items())[:10]:
            print(f"  {status}  {url}")

        public_context.close()

        # --- 2. Check domain settings page ---
        editor_context = browser.new_context(viewport={'width': 1440, 'height': 900})
        editor_context.add_cookies(zoho_cookies)
        editor_page = editor_context.new_page()

        domain_api_responses = {}
        def capture_domain(resp):
            if 'api' in resp.url:
                try:
                    domain_api_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
                except Exception:
                    pass

        editor_page.on('response', capture_domain)

        print("\n\nLoading domain settings...")
        editor_page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                         wait_until='networkidle', timeout=45000)
        editor_page.wait_for_timeout(4000)

        # Look for verify buttons / status indicators
        page_text = editor_page.locator('body').inner_text()[:2000]
        print(f"\nDomain settings page text:\n{page_text}")

        # Save screenshot
        editor_page.screenshot(path='/tmp/zoho-domain-settings.png')
        print("\nScreenshot saved to /tmp/zoho-domain-settings.png")

        print("\n\nDomain API responses:")
        for url, r in domain_api_responses.items():
            if '/domain' in url or '/ssl' in url or '/publish' in url:
                print(f"\n  HTTP {r['status']}  {url}")
                print(f"  {r['body'][:600]}")

        editor_context.close()
        browser.close()


if __name__ == '__main__':
    main()
