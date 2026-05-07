"""
Complete the full UI publish flow including any post-publish domain activation step.
Captures the full publish dialog and clicks through any 'Make Primary' or activation button.
"""
import json, sys, subprocess, time
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
        browser = pw.chromium.launch(headless=False, slow_mo=150)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Find and click Publish button
        print("Looking for Publish button...")
        pub_btn = page.locator('.h-publish, button.navbtn:has-text("Publish")').first
        if pub_btn.is_visible():
            print("Clicking Publish button...")
            pub_btn.click()
            page.wait_for_timeout(3000)
        else:
            print("Publish button not found via CSS, trying text...")
            pub_btn = page.locator('button:has-text("Publish")').first
            pub_btn.click()
            page.wait_for_timeout(3000)

        # Take screenshot of the dialog
        page.screenshot(path='/tmp/zoho-publish-dialog-1.png')
        print("Screenshot 1: /tmp/zoho-publish-dialog-1.png")

        # Look for the dialog content
        page.wait_for_timeout(2000)
        dialog_text = page.locator('[class*="dialog"], [class*="modal"], .demo-dialog').all()
        for d in dialog_text:
            if d.is_visible():
                print(f"\nDialog: {d.inner_text()[:500]}")
                # Look for buttons in this dialog
                btns = d.locator('button').all()
                for btn in btns:
                    if btn.is_visible():
                        txt = btn.inner_text().strip()
                        cls = btn.get_attribute('class') or ''
                        print(f"  Button: '{txt}' class='{cls}'")

        # Look for any "Make Primary", "Activate", "Set as Primary", "Continue" buttons
        target_texts = ['make primary', 'activate', 'set as primary', 'set primary', 'go live', 'publish now']
        for txt in target_texts:
            btn = page.locator(f'button:has-text("{txt}")').first
            if btn.is_visible():
                print(f"\nFound button: '{txt}', clicking...")
                btn.click()
                page.wait_for_timeout(5000)
                page.screenshot(path='/tmp/zoho-publish-dialog-2.png')
                print("Screenshot 2: /tmp/zoho-publish-dialog-2.png")
                break

        # Also try looking for any hidden domain.showPublishDialog state
        dialog_state = page.evaluate("""() => {
            try {
                var d = require('domain');
                return {hasDialog: typeof d.showPublishDialog === 'function'};
            } catch(e) { return {err: String(e)}; }
        }""")
        print(f"\nDomain dialog module state: {dialog_state}")

        # Check what the publish dialog module says
        pub_dialog = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domain'], function(domain) {
                    resolve({
                        keys: Object.keys(domain || {}).slice(0, 20),
                        hasShowPublishDialog: typeof domain.showPublishDialog === 'function',
                    });
                });
            });
        }""")
        print(f"\nPublish domain module: {json.dumps(pub_dialog)}")

        # Get the full publish dialog render function to understand what 'makePrimaryDiv' does
        mpdiv = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domain'], function(domain) {
                    resolve(String(domain.showPublishDialog).substring(0, 1200));
                });
            });
        }""")
        print(f"\nshowPublishDialog:\n{mpdiv}")

        browser.close()

    print("\n\nAll API responses:")
    for url, r in all_responses.items():
        if any(k in url.lower() for k in ['domain', 'publish', 'primary']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:400]}")


if __name__ == '__main__':
    main()
