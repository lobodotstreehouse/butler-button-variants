"""
Find the actual domain verify/activate endpoint by extracting validateDomain,
changePrimaryRequest, and searching the bundle for domain activation patterns.
"""
import json, sys, re
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

    settings_bundle = {}
    def capture_response(resp):
        if 'v2settingsbundle' in resp.url:
            try:
                settings_bundle[resp.url] = resp.text()
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

        # Get the domain row HTML
        domain_html = page.evaluate(f"""() => {{
            var el = document.getElementById('domain_{DOMAIN_ID}');
            return el ? el.outerHTML.substring(0, 1000) : 'not found';
        }}""")
        print(f"Domain row HTML:\n{domain_html}\n")

        # Get full validateDomain and related functions
        fns = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    resolve({
                        validateDomain: String(domains.validateDomain),
                        verifyDomain: String(domains.verifyDomain),
                        changePrimaryFull: String(domains.changePrimary),
                    });
                });
            });
        }""")
        print(f"\nvalidateDomain:\n{fns['validateDomain'][:800]}")
        print(f"\nverifyDomain:\n{fns['verifyDomain'][:800]}")

        browser.close()

    # Search settings bundle for domain endpoints
    for url, body in settings_bundle.items():
        print(f"\n\nSearching bundle {url[-60:]}")

        # Find changePrimaryRequest
        idx = body.find('changePrimaryRequest')
        if idx >= 0:
            # Find function definition
            start = body.rfind('function changePrimaryRequest', 0, idx)
            if start < 0:
                start = body.find('changePrimaryRequest', idx)
            print(f"\n=== changePrimaryRequest ===")
            print(body[start:start+600])

        # Find domain verification URLs
        for pattern in [r"domains/\w+/verify", r"domain.*activate", r"markVerified",
                        r"verifyFn", r"domain.*check", r"dns.*check"]:
            matches = [(m.start(), body[max(0,m.start()-50):m.start()+200])
                       for m in re.finditer(pattern, body, re.IGNORECASE)]
            if matches:
                print(f"\n--- Pattern '{pattern}' ---")
                for _, snippet in matches[:3]:
                    print(f"  {snippet.strip()[:200]}")


if __name__ == '__main__':
    main()
