"""
Bump inject version to force a real content change, save, then publish.
Uses fire-and-store pattern (no async/await) to avoid context-destroyed errors.
"""
import json, sys, re, subprocess, time
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

    api_responses = {}
    def capture_response(resp):
        if 'zs-site/api' in resp.url:
            try:
                api_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
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

        # Fetch current header code via fire-and-store (no async/await)
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/sites/{SITE_ID}/headerfootercode',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__hfc = r; window.__hfc_done = true; }},
                error: function(e) {{ window.__hfc = {{error: String(e)}}; window.__hfc_done = true; }},
            }});
        }}""")
        page.wait_for_timeout(8000)
        hfc = page.evaluate("window.__hfc || null")

        if not hfc:
            # Check network capture
            hfc_url = f"{BASE}/zs-site/api/v1/sites/{SITE_ID}/headerfootercode"
            if hfc_url in api_responses:
                hfc = json.loads(api_responses[hfc_url]['body'])
            else:
                print("ERROR: Could not fetch header code")
                browser.close()
                sys.exit(1)

        snippet = hfc.get('snippet') if isinstance(hfc, dict) else None
        snippet = snippet or hfc
        headercode = (snippet or {}).get('headercode') or ''
        footercode = (snippet or {}).get('footercode') or ''
        print(f"Header code: {len(headercode)} chars")

        # Find current version and bump
        # Match any ?v=N in the inject scripts
        m = re.search(r'(inject-home-v2\.js\?v=)(\d+)', headercode)
        if not m:
            m = re.search(r'(inject-[^"]+\.js\?v=)(\d+)', headercode)
        if not m:
            print("ERROR: No ?v=N version found in header code")
            print(f"Header preview: {headercode[:300]}")
            browser.close()
            sys.exit(2)

        old_v = int(m.group(2))
        new_v = old_v + 1
        print(f"Bumping inject version: ?v={old_v} -> ?v={new_v}")

        # Replace ALL version numbers in all inject scripts
        new_header = re.sub(r'(inject-[^"]+\.js\?v=)(\d+)', lambda m2: f"{m2.group(1)}{new_v}", headercode)
        if new_header == headercode:
            print("ERROR: Substitution made no changes")
            browser.close()
            sys.exit(3)

        changed = re.findall(r'inject-[^"]+\.js\?v=\d+', new_header)
        print(f"Updated inject refs: {changed}")

        # Save via fire-and-store
        new_header_escaped = json.dumps(new_header)
        footercode_escaped = json.dumps(footercode)

        page.evaluate(f"""() => {{
            var h = {new_header_escaped};
            var f = {footercode_escaped};
            window.$X.post({{
                url: '/zs-site/api/v1/sites/{SITE_ID}/headerfootercode',
                headers: window.app.getHeaders(),
                bodyJSON: {{ snippet: {{ headercode: h, footercode: f }} }},
                success: function(r) {{ window.__save = r; window.__save_done = true; }},
                error: function(e) {{ window.__save = {{error: String(e)}}; window.__save_done = true; }},
            }});
        }}""")
        page.wait_for_timeout(8000)
        save = page.evaluate("window.__save || null")
        print(f"Save result: {json.dumps(save)[:300] if save else '(null - check network)'}")

        # Publish via fire-and-store
        page.evaluate("""() => {
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__pub = r; window.__pub_done = true; },
                error: function(e) { window.__pub = {error: String(e)}; window.__pub_done = true; },
            });
        }""")
        page.wait_for_timeout(10000)
        pub = page.evaluate("window.__pub || null")
        print(f"Publish result: {json.dumps(pub)[:500] if pub else '(null - check network)'}")

        browser.close()

    print("\nNetwork-captured responses:")
    for url, r in api_responses.items():
        if 'header' in url or 'publish' in url:
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:400]}")

    print("\nWaiting 30 seconds for propagation...")
    time.sleep(30)

    print("\n=== Live site check ===")
    for url in ['https://www.butlerbutton.co', 'https://www.butlerbutton.co/concierge']:
        result = subprocess.run(
            ['curl', '-sL', '--max-time', '20', url,
             '-w', '\n---HTTP: %{http_code} SIZE: %{size_download}---'],
            capture_output=True, text=True, timeout=25
        )
        print(f"\n  {url}:")
        print(f"  {result.stdout.strip()[-200:]}")


if __name__ == '__main__':
    main()
