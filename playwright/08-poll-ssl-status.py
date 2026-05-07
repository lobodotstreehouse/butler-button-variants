"""
Poll SSL cert status and live site health for butlerbutton.co.
"""
import json, sys, subprocess
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
    print(f"Loaded {len(cookies)} cookies")

    ssl_data = {}
    domain_data = {}

    def capture_response(resp):
        if 'sslhosting' in resp.url or 'ssl' in resp.url.lower():
            try:
                ssl_data[resp.url] = {'status': resp.status, 'body': resp.text()[:1000]}
            except Exception:
                pass
        if '/domains' in resp.url and 'api' in resp.url:
            try:
                domain_data[resp.url] = {'status': resp.status, 'body': resp.text()[:800]}
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        # Load SPA
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(2000)
        if 'accounts.zoho' in page.url or '/login' in page.url:
            print("Session expired")
            sys.exit(1)

        # Navigate to SSL settings — Zoho auto-fires the SSL status API
        print("Loading SSL settings page...")
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/sslhosting",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(5000)

        # Also navigate to domains settings
        print("Loading domains settings page...")
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(5000)

        # Also check via $X API directly
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/code/header",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(3000)

        # Fire SSL status check
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/sites/{SITE_ID}/sslhosting',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__ssl = r; window.__ssl_done = true; }},
                error:   function(e) {{ window.__ssl = {{error: JSON.stringify(e)}}; window.__ssl_done = true; }},
            }});
        }}""")
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/sites/{SITE_ID}/domain',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__domain = r; window.__domain_done = true; }},
                error:   function(e) {{ window.__domain = {{error: JSON.stringify(e)}}; window.__domain_done = true; }},
            }});
        }}""")

        page.wait_for_timeout(8000)

        ssl_result = page.evaluate("window.__ssl || null")
        domain_result = page.evaluate("window.__domain || null")

        print("\n=== SSL Status ===")
        print(json.dumps(ssl_result, indent=2)[:1500] if ssl_result else "(null)")

        print("\n=== Domain Info ===")
        print(json.dumps(domain_result, indent=2)[:1500] if domain_result else "(null)")

        browser.close()

    # Check live site HTTP status
    print("\n=== Live site check ===")
    for url in ['https://www.butlerbutton.co', 'http://www.butlerbutton.co',
                'https://butlerbutton.co']:
        try:
            result = subprocess.run(
                ['curl', '-sI', '--max-time', '10', '-L', '--max-redirs', '3', url],
                capture_output=True, text=True, timeout=15
            )
            # Extract first HTTP status line
            lines = result.stdout.split('\n')
            status_lines = [l for l in lines if l.startswith('HTTP/')]
            print(f"  {url}: {status_lines}")
        except Exception as e:
            print(f"  {url}: error — {e}")

    print("\n=== Captured SSL API responses ===")
    for url, r in ssl_data.items():
        print(f"  HTTP {r['status']}  {url}")
        print(f"    {r['body'][:400]}")


if __name__ == '__main__':
    main()
