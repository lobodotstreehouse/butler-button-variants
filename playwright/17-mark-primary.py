"""
POST /zs-site/api/v1/domains/{DOMAIN_ID}/markPrimary to trigger ZGS routing update.
Then republish.
"""
import json, sys, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'
DOMAIN_ID = '625000009337247'


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

        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Call markPrimary endpoint directly
        print(f"Calling POST /domains/{DOMAIN_ID}/markPrimary ...")
        page.evaluate(f"""() => {{
            window.$X.post({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID}/markPrimary',
                headers: window.app.getHeaders(),
                bodyJSON: {{
                    domain_name: 'www.butlerbutton.co',
                    domain_type: 1
                }},
                success: function(r) {{ window.__markPrimary = r; window.__markPrimary_done = true; }},
                error: function(e) {{ window.__markPrimary = {{error: String(e)}}; window.__markPrimary_done = true; }},
            }});
        }}""")
        page.wait_for_timeout(8000)
        mark_result = page.evaluate("window.__markPrimary || null")
        print(f"markPrimary result: {json.dumps(mark_result)[:500] if mark_result else '(null - check network)'}")

        # Also try markPrimary with no body
        print(f"\nCalling POST /domains/{DOMAIN_ID}/markPrimary (empty body)...")
        page.evaluate(f"""() => {{
            window.$X.post({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID}/markPrimary',
                headers: window.app.getHeaders(),
                bodyJSON: {{}},
                success: function(r) {{ window.__markPrimary2 = r; }},
                error: function(e) {{ window.__markPrimary2 = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        mark_result2 = page.evaluate("window.__markPrimary2 || null")
        print(f"markPrimary2 result: {json.dumps(mark_result2)[:500] if mark_result2 else '(null)'}")

        # Now publish
        print("\nPublishing...")
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(2000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        page.evaluate("""() => {
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__pub = r; },
                error: function(e) { window.__pub = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(10000)
        pub_result = page.evaluate("window.__pub || null")
        print(f"Publish result: {json.dumps(pub_result)[:500] if pub_result else '(null - check network)'}")

        browser.close()

    print("\n\nAll API responses:")
    for url, r in all_responses.items():
        if any(k in url for k in ['domain', 'publish', 'verify', 'primary']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:500]}")

    # Check live site
    print("\n=== Live site check ===")
    for url in ['https://www.butlerbutton.co', 'https://www.butlerbutton.co/concierge']:
        result = subprocess.run(
            ['curl', '-sI', '--max-time', '10', url],
            capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.split('\n')
        status = next((l for l in lines if l.startswith('HTTP/')), 'unknown')
        print(f"  {url}: {status}")


if __name__ == '__main__':
    main()
