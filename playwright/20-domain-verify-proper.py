"""
Call /domains/verify with proper params (no is_domain_connect_verify),
exactly as the Zoho UI does via validateDomain. Then republish.
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
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Call /domains/verify exactly as validateDomain does (params only, no bodyJSON)
        print("Calling POST /domains/verify with domain_name + domain_type (no is_domain_connect_verify)...")
        page.evaluate("""() => {
            window.$X.post({
                url: '/zs-site/api/v1/domains/verify',
                params: {
                    domain_name: 'www.butlerbutton.co',
                    domain_type: '1'
                },
                headers: window.app.getHeaders(),
                handler: function() {
                    window.__verifyResp = this.responseText;
                    window.__verifyDone = true;
                }
            });
        }""")
        page.wait_for_timeout(8000)
        verify_resp = page.evaluate("window.__verifyResp || null")
        print(f"Verify response: {verify_resp[:500] if verify_resp else '(null)'}")

        # Also try marking primary again after verify
        print("\nRe-running GET markPrimary...")
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID}/markPrimary',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__mark = r; }},
                error: function(e) {{ window.__mark = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        mark = page.evaluate("window.__mark || null")
        print(f"markPrimary: {json.dumps(mark)[:300] if mark else '(null)'}")

        # Check domain verified status after verify call
        print("\nChecking domain list after verify...")
        page.evaluate("""() => {
            window.$X.get({
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) { window.__domains = r; },
                error: function(e) { window.__domains = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(5000)
        domains = page.evaluate("window.__domains || null")
        if domains and isinstance(domains, dict) and 'domain_list' in domains:
            for d in domains['domain_list']:
                print(f"Domain: {d.get('domain_name')} verified={d.get('verified')} "
                      f"is_zoho_verified={d.get('is_zoho_verified')} "
                      f"verification_status={d.get('verification_status')} "
                      f"dns_status={d.get('dns_status')}")

        browser.close()

    print("\n\nAll API responses from verify flow:")
    for url, r in all_responses.items():
        if any(k in url for k in ['domain', 'verify', 'publish', 'primary']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:600]}")

    # Publish after verify
    print("\n\nRunning publish after verify...")
    import subprocess
    result = subprocess.run(
        ['python3', 'playwright/05-publish-butlerbutton.py'],
        capture_output=True, text=True, timeout=120, cwd='/Users/openclaw/butler-button-variants'
    )
    print(result.stdout[-500:] if result.stdout else "no output")
    print(result.stderr[-200:] if result.stderr else "")

    # Check live site
    print("\n=== Live site check (GET) ===")
    import time
    time.sleep(15)
    for url in ['https://www.butlerbutton.co', 'https://www.butlerbutton.co/concierge']:
        result = subprocess.run(
            ['curl', '-sL', '--max-time', '15', url, '-w', '\n---HTTP_CODE: %{http_code} SIZE: %{size_download}---'],
            capture_output=True, text=True, timeout=20
        )
        last_lines = result.stdout.strip().split('\n')[-2:]
        print(f"  {url}: {''.join(last_lines)}")


if __name__ == '__main__':
    main()
