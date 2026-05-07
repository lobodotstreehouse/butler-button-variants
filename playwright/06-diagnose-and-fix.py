"""
Diagnose butlerbutton.co 500/404 and force a clean republish.
Fetches site info, page list, publish status, then triggers publish.
"""

import json, sys, time
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
        if (name, value) in seen:
            continue
        seen.add((name, value))
        cookies.append({
            'name': name, 'value': value,
            'domain': '.sitebuilder-60059075182.zohositescontent.in',
            'path': '/', 'httpOnly': False, 'secure': True,
        })
    return cookies


def xget(page, url):
    return page.evaluate(f"""async () => {{
        return await new Promise((resolve, reject) => {{
            window.$X.get({{
                url: '{url}',
                headers: window.app.getHeaders(),
                success: resolve,
                error: reject,
            }});
        }});
    }}""")


def xpost(page, url, body=None):
    body_json = json.dumps(body or {})
    return page.evaluate(f"""async () => {{
        return await new Promise((resolve, reject) => {{
            window.$X.post({{
                url: '{url}',
                headers: window.app.getHeaders(),
                bodyJSON: {body_json},
                success: resolve,
                error: reject,
            }});
        }});
    }}""")


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
        print(f"Auth OK")

        target = f"{BASE}/zcms/{SITE_ID}/settings/code/header"
        page.goto(target, wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)
        page.wait_for_function(
            "typeof window.$X === 'object' && typeof window.app === 'object'",
            timeout=30000,
        )
        page.wait_for_timeout(4000)
        page.wait_for_load_state('networkidle', timeout=15000)
        print(f"SPA ready — {page.url}")

        # 1. Site info
        print("\n--- Site info ---")
        try:
            info = xget(page, f'/zs-site/api/v1/sites/{SITE_ID}')
            print(json.dumps(info)[:800])
        except Exception as e:
            print(f"Site info error: {e}")

        # 2. Pages list
        print("\n--- Pages ---")
        try:
            pages_data = xget(page, f'/zs-site/api/v1/sites/{SITE_ID}/pages')
            print(json.dumps(pages_data)[:800])
        except Exception as e:
            print(f"Pages error: {e}")

        # 3. Domain info
        print("\n--- Domain ---")
        try:
            domain = xget(page, f'/zs-site/api/v1/sites/{SITE_ID}/domain')
            print(json.dumps(domain)[:800])
        except Exception as e:
            print(f"Domain error: {e}")

        # 4. Intercept and fire publish
        print("\n--- Publishing ---")
        pub_responses = []

        def handle_response(response):
            if 'publish' in response.url and 'api' in response.url:
                try:
                    pub_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'body': response.text()[:500],
                    })
                except Exception as e:
                    pub_responses.append({'url': response.url, 'error': str(e)})

        page.on('response', handle_response)

        page.evaluate("""() => {
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__pubOk = r; },
                error: function(e) { window.__pubErr = e; },
            });
        }""")
        print("Publish fired — waiting 10s...")
        page.wait_for_timeout(10000)

        for r in pub_responses:
            print(f"  {r.get('url','')} HTTP {r.get('status','')} — {r.get('body','')[:300]}")

        browser.close()


if __name__ == '__main__':
    main()
