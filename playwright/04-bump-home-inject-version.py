"""
Bumps inject-home-v2.js?v=N in go.veltmtours.com header code, then publishes.

Usage:
    python3 playwright/04-bump-home-inject-version.py

Auth: reuses /tmp/zoho_cookies_clean.json (same as 03-intercept-seo-save.py).
"""

import json, sys, re
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE         = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID      = '413198000000002010'
SCRIPT_DIR   = Path(__file__).parent


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

        # Land on pages list first (Zoho SPA init), then route to header code editor.
        pages_url = f"{BASE}/zcms/{SITE_ID}/pages"
        print(f"Loading {pages_url}")
        page.goto(pages_url, wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(2000)

        if 'accounts.zoho' in page.url or '/login' in page.url:
            print(f"Session expired — url is {page.url}")
            browser.close()
            sys.exit(1)

        target = f"{BASE}/zcms/{SITE_ID}/settings/code/header"
        print(f"Navigating SPA to {target}")
        page.goto(target, wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)

        # Wait for Zoho SPA + settle
        page.wait_for_function("typeof window.$X === 'object' && typeof window.app === 'object'", timeout=30000)
        page.wait_for_timeout(2000)
        print(f"$X SPA ready — current url: {page.url}")

        # Fetch current header code
        current = page.evaluate(f"""async () => {{
            return await new Promise((resolve, reject) => {{
                window.$X.get({{
                    url: '/zs-site/api/v1/sites/{SITE_ID}/headerfootercode',
                    headers: window.app.getHeaders(),
                    success: resolve, error: reject,
                }});
            }});
        }}""")
        snippet = current.get('snippet') if isinstance(current, dict) else None
        snippet = snippet or current
        headercode = snippet.get('headercode') or ''
        footercode = snippet.get('footercode') or ''
        print(f"Header code: {len(headercode)} chars, footer: {len(footercode)} chars")

        m = re.search(r'inject-home-v2\.js\?v=(\d+)', headercode)
        if not m:
            print("ERROR: inject-home-v2.js?v=N not found in header code")
            print(headercode[:800])
            browser.close()
            sys.exit(2)
        old_v = int(m.group(1))
        new_v = old_v + 1
        print(f"Bumping inject-home-v2.js ?v={old_v} -> ?v={new_v}")

        new_header = re.sub(
            r'inject-home-v2\.js\?v=\d+',
            f'inject-home-v2.js?v={new_v}',
            headercode,
        )
        if new_header == headercode:
            print("ERROR: no change after regex replace")
            browser.close()
            sys.exit(3)

        # Save via $X.post
        save_result = page.evaluate(f"""async (args) => {{
            return await new Promise((resolve, reject) => {{
                window.$X.post({{
                    url: '/zs-site/api/v1/sites/{SITE_ID}/headerfootercode',
                    headers: window.app.getHeaders(),
                    bodyJSON: {{ snippet: {{ headercode: args.h, footercode: args.f }} }},
                    success: resolve, error: reject,
                }});
            }});
        }}""", {'h': new_header, 'f': footercode})
        print(f"Save: {json.dumps(save_result)[:300]}")

        # Publish
        pub_result = page.evaluate("""async () => {
            return await new Promise((resolve, reject) => {
                window.$X.post({
                    url: '/zs-site/api/v1/publish',
                    headers: window.app.getHeaders(),
                    bodyJSON: {},
                    success: resolve, error: reject,
                });
            });
        }""")
        print(f"Publish: {json.dumps(pub_result)[:300]}")

        # Verify by re-fetching
        verify = page.evaluate(f"""async () => {{
            return await new Promise((resolve, reject) => {{
                window.$X.get({{
                    url: '/zs-site/api/v1/sites/{SITE_ID}/headerfootercode',
                    headers: window.app.getHeaders(),
                    success: resolve, error: reject,
                }});
            }});
        }}""")
        v_snip = verify.get('snippet') if isinstance(verify, dict) else verify
        v_snip = v_snip or verify
        v_header = (v_snip or {}).get('headercode') or ''
        m2 = re.search(r'inject-home-v2\.js\?v=(\d+)', v_header)
        if m2 and int(m2.group(1)) == new_v:
            print(f"VERIFIED: server now reports ?v={new_v}")
        else:
            print(f"VERIFY WARNING: server reports match={m2.group(0) if m2 else 'none'}")

        browser.close()
        print(f"DONE. inject-home-v2.js?v={new_v} saved and site published.")


if __name__ == '__main__':
    main()
