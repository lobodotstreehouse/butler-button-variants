"""
Full diagnostic: site info, domain list, SSL, publish status.
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


def fire(page, var, url, method='get', body=None):
    body_str = json.dumps(body or {})
    page.evaluate(f"""() => {{
        window.$X.{method}({{
            url: '{url}',
            headers: window.app.getHeaders(),
            bodyJSON: {body_str},
            success: function(r) {{ window.__{var} = r; window.__{var}_done = true; }},
            error:   function(e) {{ window.__{var} = {{error: JSON.stringify(e)}}; window.__{var}_done = true; }},
        }});
    }}""")


def main():
    raw = json.loads(Path(COOKIES_JSON).read_text())
    cookies = build_cookies(raw)

    network_responses = {}

    def capture_response(resp):
        if 'zs-site/api' in resp.url:
            try:
                network_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
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
        print("SPA ready")

        # Fire all at once
        fire(page, 'site',    f'/zs-site/api/v1/sites/{SITE_ID}')
        fire(page, 'domain',  f'/zs-site/api/v1/domains?is_ssl_info_needed=true')
        fire(page, 'ssl',     f'/zs-site/api/v1/ssl')
        fire(page, 'pub',     f'/zs-site/api/v1/publish', method='get')

        page.wait_for_timeout(10000)

        for var in ['site', 'domain', 'ssl', 'pub']:
            val = page.evaluate(f"window.__{var} || null")
            print(f"\n=== {var} ===")
            print(json.dumps(val, indent=2)[:2000] if val else "(null)")

        browser.close()

    print("\n=== Network API responses ===")
    for url, r in sorted(network_responses.items()):
        print(f"\n  HTTP {r['status']}  {url}")
        print(f"  {r['body'][:500]}")


if __name__ == '__main__':
    main()
