"""
Check SSL hosting tab and trigger UI-level publish (click the green Publish button).
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
    cookies = build_cookies(raw)

    api_responses = {}

    def capture_response(resp):
        if 'zs-site/api' in resp.url:
            try:
                api_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)

        # Click SSL hosting tab
        print("Clicking SSL hosting tab...")
        page.locator('text=SSL hosting').click()
        page.wait_for_timeout(3000)

        page.screenshot(path='/tmp/zoho-ssl-tab.png')
        print("Screenshot saved: /tmp/zoho-ssl-tab.png")

        ssl_text = page.locator('body').inner_text()[:2000]
        print(f"\nSSL tab text:\n{ssl_text[:800]}")

        # Check for any buttons/actions available
        buttons = page.locator('button').all()
        print(f"\nButtons visible: {[b.inner_text() for b in buttons[:20] if b.is_visible()]}")

        # Now navigate to pages and trigger UI publish
        print("\n\nNavigating to pages view for UI publish...")
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Find and click the Publish button
        print("Looking for Publish button...")
        publish_btn = None

        # Try the green Publish button in the header
        candidates = page.locator('button, .sites-button, [class*="publish"]').all()
        for el in candidates:
            try:
                txt = el.inner_text().strip()
                if txt.lower() == 'publish' and el.is_visible():
                    print(f"Found: '{txt}' class={el.get_attribute('class')}")
                    publish_btn = el
                    break
            except Exception:
                pass

        if publish_btn:
            print("Clicking Publish button...")
            publish_btn.click()
            page.wait_for_timeout(5000)

            # Handle any confirmation dialog
            try:
                confirm = page.locator('button:has-text("Publish"), button:has-text("Continue"), button:has-text("OK")')
                if confirm.count() > 0:
                    print(f"Confirmation dialog found, clicking...")
                    confirm.first.click()
                    page.wait_for_timeout(5000)
            except Exception as e:
                print(f"No confirmation dialog: {e}")

            page.screenshot(path='/tmp/zoho-after-publish.png')
            print("Post-publish screenshot: /tmp/zoho-after-publish.png")
        else:
            print("Publish button not found, using API...")
            page.evaluate("""() => {
                window.$X.post({
                    url: '/zs-site/api/v1/publish',
                    headers: window.app.getHeaders(),
                    bodyJSON: {},
                    success: function(r) { window.__pubOk = r; },
                    error: function(e) { window.__pubErr = e; },
                });
            }""")
            page.wait_for_timeout(8000)

        page.wait_for_timeout(5000)

        browser.close()

    print("\n=== API responses ===")
    for url, r in api_responses.items():
        if 'publish' in url or 'ssl' in url.lower() or 'domain' in url:
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:600]}")


if __name__ == '__main__':
    main()
