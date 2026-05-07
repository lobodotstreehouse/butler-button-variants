"""
Check domain verification status and site info via fire-and-store pattern
to avoid the async Promise / SPA navigation context destruction issue.
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


def fire_and_store(page, var, url, method='get'):
    page.evaluate(f"""() => {{
        window.$X.{method}({{
            url: '{url}',
            headers: window.app.getHeaders(),
            bodyJSON: {{}},
            success: function(r) {{ window.__{var} = r; window.__{var}_done = true; }},
            error:   function(e) {{ window.__{var} = {{error: JSON.stringify(e)}}; window.__{var}_done = true; }},
        }});
    }}""")


def read_stored(page, var, wait_ms=6000):
    page.wait_for_timeout(wait_ms)
    try:
        return page.evaluate(f"window.__{var} || null")
    except Exception as e:
        return {'playwright_error': str(e)}


def main():
    raw = json.loads(Path(COOKIES_JSON).read_text())
    cookies = build_cookies(raw)
    print(f"Loaded {len(cookies)} cookies")

    responses = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)

        def capture_response(resp):
            if 'zs-site/api' in resp.url:
                try:
                    responses[resp.url] = {'status': resp.status, 'body': resp.text()[:600]}
                except Exception:
                    pass

        page = context.new_page()
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(2000)

        if 'accounts.zoho' in page.url or '/login' in page.url:
            print("Session expired")
            sys.exit(1)

        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/code/header",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(4000)
        page.wait_for_load_state('networkidle', timeout=15000)
        print(f"SPA ready")

        # Fire all requests simultaneously
        fire_and_store(page, 'site',   f'/zs-site/api/v1/sites/{SITE_ID}')
        fire_and_store(page, 'domain', f'/zs-site/api/v1/sites/{SITE_ID}/domain')
        fire_and_store(page, 'pages',  f'/zs-site/api/v1/sites/{SITE_ID}/pages')
        fire_and_store(page, 'pub',    '/zs-site/api/v1/publish', method='post')

        page.wait_for_timeout(10000)

        for var in ['site', 'domain', 'pages', 'pub']:
            try:
                val = page.evaluate(f"window.__{var} || null")
            except Exception as e:
                val = {'playwright_error': str(e)}
            print(f"\n=== {var} ===")
            print(json.dumps(val)[:600] if val else "(null)")

        browser.close()

    print("\n=== Network responses captured ===")
    for url, r in responses.items():
        print(f"  HTTP {r['status']}  {url}")
        print(f"    {r['body'][:200]}")


if __name__ == '__main__':
    main()
