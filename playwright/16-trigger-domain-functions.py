"""
Call domains.changePrimary / domains.validateDomain to trigger ZGS routing update.
Intercepts all network requests to see what API is called.
"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE    = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID = '413198000000002010'
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
        if 'zs-site/api' in resp.url or 'domain' in resp.url.lower():
            try:
                all_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        # Load the domains settings page to init the domains module
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(3000)

        # Inspect changePrimary function
        print("Inspecting changePrimary...")
        cp_info = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    resolve({
                        changePrimaryStr: String(domains.changePrimary).substring(0, 500),
                        validateDomainStr: String(domains.validateDomain).substring(0, 500),
                        addDomainRoutedStr: String(domains.addDomainRouted).substring(0, 500),
                    });
                });
            });
        }""")
        print(f"changePrimary: {cp_info.get('changePrimaryStr', '')[:300]}")
        print(f"validateDomain: {cp_info.get('validateDomainStr', '')[:300]}")
        print(f"addDomainRouted: {cp_info.get('addDomainRoutedStr', '')[:300]}")

        # Try to call addDomainRouted with domain info
        print("\n\nCalling addDomainRouted...")
        page.evaluate("""() => {
            require(['domains'], function(domains) {
                try {
                    // addDomainRouted is called after domain is successfully added/verified
                    // Pass domain info similar to what the API returns
                    domains.addDomainRouted({
                        domain_id: '625000009337247',
                        domain_name: 'www.butlerbutton.co',
                        primary_domain: 1,
                        verified: 1,
                        dns_status: true,
                        domain_type: 1
                    });
                    window.__addRouted = 'called';
                } catch(e) {
                    window.__addRouted = 'error: ' + String(e);
                }
            });
        }""")
        page.wait_for_timeout(3000)
        route_result = page.evaluate("window.__addRouted || 'not set'")
        print(f"addDomainRouted result: {route_result}")

        # Try calling changePrimary
        print("\n\nCalling changePrimary with domain element...")
        page.evaluate("""() => {
            require(['domains'], function(domains) {
                try {
                    // Find the domain row element if it exists in the UI
                    var domainEl = document.querySelector('[data-domain-id], [data-id="625000009337247"]');
                    if (!domainEl) {
                        // Create a mock element
                        domainEl = document.createElement('div');
                        domainEl.setAttribute('data-domain-id', '625000009337247');
                        domainEl.setAttribute('data-domain-name', 'www.butlerbutton.co');
                    }
                    domains.changePrimary.call(domainEl);
                    window.__changePrimary = 'called';
                } catch(e) {
                    window.__changePrimary = 'error: ' + String(e);
                }
            });
        }""")
        page.wait_for_timeout(3000)
        cp_result = page.evaluate("window.__changePrimary || 'not set'")
        print(f"changePrimary result: {cp_result}")

        page.wait_for_timeout(5000)

        browser.close()

    print("\n\nAll domain/API responses triggered:")
    for url, r in all_responses.items():
        if 'zs-site/api' in url:
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:400]}")


if __name__ == '__main__':
    main()
