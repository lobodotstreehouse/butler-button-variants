"""
Try calling domains.validateDomain and check isSitePublished state.
Also look for 'primary domain' re-mapping trigger.
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

    api_responses = {}
    def capture_response(resp):
        if 'zs-site/api' in resp.url:
            try:
                api_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=100)
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

        # Check isSitePublished
        pub_state = page.evaluate("""() => {
            return {
                isSitePublished: window.app.data.isSitePublished,
                publishedDomain: window.app.data.publishedDomain,
                hosting_domain: window.app.data.hosting_domain,
                content_domain_prefix: window.app.data.content_domain_prefix,
                sub_site_id: window.app.data.sub_site_id,
                root_resource_id: window.app.data.root_resource_id,
            };
        }""")
        print(f"\nApp publish state:\n{json.dumps(pub_state, indent=2)}")

        # Navigate to domains settings to load domain module
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Try to call domains.validateDomain via require
        print("\nAttempting to load domains module and call validateDomain...")
        result = page.evaluate("""() => {
            return new Promise(function(resolve) {
                try {
                    require(['domains'], function(domains) {
                        resolve({
                            domainKeys: Object.keys(domains || {}).slice(0, 30),
                            hasValidate: typeof domains.validateDomain === 'function',
                            hasCheckDNS: typeof domains.checkDNS === 'function',
                            hasVerify: typeof domains.verifyDomain === 'function',
                            hasSetPrimary: typeof domains.setDomainPrimary === 'function',
                            hasMakePrimary: typeof domains.makeDomainPrimary === 'function',
                        });
                    });
                } catch(e) {
                    resolve({error: String(e)});
                }
            });
        }""")
        print(f"\nDomains module: {json.dumps(result, indent=2)}")

        # Try to call the domain check DNS endpoint
        print("\nCalling domain checkDNS/verify...")
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID}/checkdns',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__dns = r; }},
                error: function(e) {{ window.__dns = {{err: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(3000)
        dns_result = page.evaluate("window.__dns || null")
        print(f"checkdns: {json.dumps(dns_result)[:300] if dns_result else '(null)'}")

        # Try POST to domains/verify with params (not bodyJSON)
        print("\nCalling POST /domains/verify with params...")
        page.evaluate(f"""() => {{
            window.$X.post({{
                url: '/zs-site/api/v1/domains/verify',
                headers: window.app.getHeaders(),
                params: {{
                    domain_name: 'www.butlerbutton.co',
                    domain_type: 1
                }},
                bodyJSON: {{}},
                success: function(r) {{ window.__verify = r; }},
                error: function(e) {{ window.__verify = {{err: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        verify_result = page.evaluate("window.__verify || null")
        print(f"verify: {json.dumps(verify_result)[:300] if verify_result else '(null)'}")

        # Try making domain primary again via PUT
        print("\nCalling PUT /domains/{DOMAIN_ID} to set as primary...")
        page.evaluate(f"""() => {{
            window.$X.put({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID}',
                headers: window.app.getHeaders(),
                bodyJSON: {{primary_domain: 1, is_primary: true}},
                success: function(r) {{ window.__primary = r; }},
                error: function(e) {{ window.__primary = {{err: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        primary_result = page.evaluate("window.__primary || null")
        print(f"set primary: {json.dumps(primary_result)[:300] if primary_result else '(null)'}")

        browser.close()

    print("\n\nAll API responses:")
    for url, r in api_responses.items():
        if any(k in url for k in ['domain', 'verify', 'publish', 'ssl']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:400]}")


if __name__ == '__main__':
    main()
