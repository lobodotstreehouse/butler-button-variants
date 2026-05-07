"""
Inspect changePrimaryRender and showDomain to find what ZGS update happens.
Also try calling the domain module's changePrimary properly via the UI element.
"""
import json, sys, subprocess, time
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

        # Get the domain UI element
        domain_el_info = page.evaluate(f"""() => {{
            var el = document.getElementById('{DOMAIN_ID}');
            if (!el) return 'not found';
            return {{
                id: el.id,
                outerHTML: el.outerHTML.substring(0, 500),
                hasDataDomainName: el.hasAttribute('data-domain-name'),
                getAttribute_class: el.getAttribute('class'),
            }};
        }}""")
        print(f"Domain link element: {json.dumps(domain_el_info, indent=2)}")

        # The domain link has id=625000009337247, so changePrimary should work
        # Let's call changePrimary properly via the link element
        print("\nCalling domains.changePrimary via the actual element...")
        result = page.evaluate(f"""() => {{
            return new Promise(function(resolve) {{
                require(['domains'], function(domains) {{
                    var el = document.getElementById('{DOMAIN_ID}');
                    if (!el) {{ resolve({{error: 'element not found'}}); return; }}
                    // Set up required attributes
                    el.setAttribute('data-domain-name', 'www.butlerbutton.co');
                    el.setAttribute('data-domain-type', '1');
                    try {{
                        domains.changePrimary.call(el);
                        resolve({{called: true}});
                    }} catch(e) {{
                        resolve({{error: String(e)}});
                    }}
                }});
            }});
        }}""")
        print(f"changePrimary result: {json.dumps(result)}")
        page.wait_for_timeout(10000)

        # Check what API was called
        print("\nChecking domain list after changePrimary...")
        dom_after = page.evaluate("""() => {
            window.$X.get({
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) { window.__doms2 = r; },
                error: function(e) { window.__doms2 = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(5000)
        doms = page.evaluate("window.__doms2 || null")
        if doms and 'domain_list' in doms:
            for d in doms['domain_list']:
                print(f"  {d['domain_name']}: primary={d['primary_domain']} verified={d['verified']} "
                      f"modified={d.get('last_modified_time', '')}")

        # Get changePrimaryRender source
        fn_info = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    // We can't get changePrimaryRender directly since it's internal
                    // but we can search window for it
                    var keys = Object.keys(window).filter(k => typeof window[k] === 'function' && k.includes('Primary'));
                    resolve({
                        windowPrimaryFns: keys,
                        domainsKeys: Object.keys(domains).filter(k => k.includes('primary') || k.includes('Primary') || k.includes('render') || k.includes('Render')),
                    });
                });
            });
        }""")
        print(f"\nChangePrimary-related functions: {json.dumps(fn_info)}")

        browser.close()

    print("\n\nAll API responses:")
    for url, r in all_responses.items():
        print(f"\n  HTTP {r['status']}  {url}")
        print(f"  {r['body'][:500]}")

    # Test live site
    print("\n=== Live check ===")
    for url in ['https://www.butlerbutton.co/', 'https://www.butlerbutton.co/concierge']:
        result = subprocess.run(
            ['curl', '-sv', '--max-time', '10', url],
            capture_output=True, text=True, timeout=15
        )
        status = next((l for l in result.stderr.split('\n') if 'HTTP/' in l), 'unknown')
        print(f"  {url}: {status}")


if __name__ == '__main__':
    main()
