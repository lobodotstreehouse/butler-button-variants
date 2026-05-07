"""
Inspect Zoho SPA JS to understand publish_status: 103 and domain verification.
"""
import json, sys, re
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

    js_responses = {}
    api_responses = {}

    def capture_response(resp):
        if resp.url.endswith('.js') and 'zoho' in resp.url.lower():
            try:
                body = resp.text()
                if '103' in body and ('publish' in body.lower() or 'domain' in body.lower()):
                    js_responses[resp.url] = body
            except Exception:
                pass
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
        page.wait_for_timeout(3000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Look for publish-related modules in require.js
        print("Looking for publish status codes in SPA JS...")
        result = page.evaluate("""() => {
            var results = [];
            // Check if require is available
            if (typeof require === 'undefined') return 'no require';

            // Try to find the publish module
            var modules = [];
            try {
                var cfg = require.s;
                if (cfg && cfg.contexts && cfg.contexts._) {
                    modules = Object.keys(cfg.contexts._.defined || {});
                }
            } catch(e) {}

            // Search for publish-related module names
            var publishModules = modules.filter(m =>
                m.includes('publish') || m.includes('domain') || m.includes('verify')
            );
            return {publishModules: publishModules.slice(0, 30), totalModules: modules.length};
        }""")
        print(f"SPA modules: {json.dumps(result, indent=2)[:2000]}")

        # Try to get the publish module directly
        print("\n\nChecking publish module for status codes...")
        pub_module = page.evaluate("""() => {
            try {
                var m = require('zs-config/publish');
                return String(m).substring(0, 1000);
            } catch(e1) {
                try {
                    var m2 = require('sites-v2/publish');
                    return String(m2).substring(0, 1000);
                } catch(e2) {
                    return 'not found: ' + e1 + ' / ' + e2;
                }
            }
        }""")
        print(f"Publish module: {pub_module}")

        # Check the full domain list with all fields to understand verification
        print("\n\nFull domain info via fire-and-store...")
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__dom = r; }},
                error: function(e) {{ window.__dom = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        dom = page.evaluate("window.__dom || null")
        if dom:
            print(json.dumps(dom, indent=2)[:2000])

        # Look for verification token
        print("\n\nLooking for domain verify endpoint...")
        verify_result = page.evaluate("""() => {
            try {
                // Look in window objects for any verify-related function
                var keys = Object.keys(window).filter(k =>
                    k.toLowerCase().includes('verify') || k.toLowerCase().includes('domain')
                );
                return {windowKeys: keys.slice(0, 20)};
            } catch(e) {
                return {error: String(e)};
            }
        }""")
        print(f"Window verify keys: {json.dumps(verify_result)}")

        browser.close()

    print("\n\nSearching loaded JS files for publish_status 103...")
    for url, body in js_responses.items():
        idxs = [m.start() for m in re.finditer(r'103', body)]
        for idx in idxs[:5]:
            snippet = body[max(0, idx-80):idx+80]
            print(f"\n  {url[-80:]}")
            print(f"  ...{snippet}...")


if __name__ == '__main__':
    main()
