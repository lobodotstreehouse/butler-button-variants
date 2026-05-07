"""
Find domain verification token and try to complete domain verification.
Extract verifyDomain function source. Screenshot domain settings page.
Try to find/click verify button in the UI.
"""
import json, subprocess
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
        browser = pw.chromium.launch(headless=False, slow_mo=100)
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
        page.wait_for_timeout(3000)

        # Screenshot the domain settings page
        page.screenshot(path='/tmp/zoho-domain-settings-full.png')
        print("Screenshot: /tmp/zoho-domain-settings-full.png")

        # Get all visible text
        body_text = page.locator('body').inner_text()
        print(f"\nDomain settings page text:\n{body_text[:3000]}")

        # Get the full HTML of domain list section
        domain_html = page.evaluate("""() => {
            var el = document.querySelector('.domain-list, #domain-list, [class*="domain"], .sites-contentpanel');
            return el ? el.outerHTML.substring(0, 3000) : 'not found';
        }""")
        print(f"\nDomain section HTML:\n{domain_html[:3000]}")

        # Get verifyDomain and validateDomain function sources
        fn_sources = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    resolve({
                        verifyDomain: String(domains.verifyDomain || '').substring(0, 1000),
                        validateDomain: String(domains.validateDomain || '').substring(0, 1000),
                        verifyClick: String(domains.verifyClick || domains.verifyDomainClick || '').substring(0, 800),
                        allKeys: Object.keys(domains),
                    });
                });
            });
        }""")
        print(f"\nverifyDomain fn:\n{fn_sources.get('verifyDomain', '')}")
        print(f"\nvalidateDomain fn:\n{fn_sources.get('validateDomain', '')}")
        print(f"\nAll domain keys: {fn_sources.get('allKeys', [])}")

        # Try finding any verify button for the domain
        verify_btns = page.locator('button:has-text("Verify"), a:has-text("Verify"), '
                                   '[class*="verify"], button:has-text("verify")').all()
        print(f"\nVerify buttons found: {len(verify_btns)}")
        for btn in verify_btns:
            if btn.is_visible():
                txt = btn.inner_text()
                cls = btn.get_attribute('class') or ''
                print(f"  Button: '{txt}' class='{cls}'")

        # Try calling verifyDomain with a mock element
        print("\nCalling domains.verifyDomain with domain element...")
        result = page.evaluate(f"""() => {{
            return new Promise(function(resolve) {{
                require(['domains'], function(domains) {{
                    if (!domains.verifyDomain) {{ resolve({{error: 'verifyDomain not found'}}); return; }}
                    var el = document.getElementById('{DOMAIN_ID}');
                    if (!el) {{
                        el = document.createElement('a');
                        el.id = '{DOMAIN_ID}';
                        el.setAttribute('data-domain-name', 'www.butlerbutton.co');
                        el.setAttribute('data-domain-type', '1');
                    }}
                    try {{
                        domains.verifyDomain.call(el);
                        resolve({{called: true}});
                    }} catch(e) {{
                        resolve({{error: String(e)}});
                    }}
                }});
            }});
        }}""")
        print(f"verifyDomain result: {json.dumps(result)}")
        page.wait_for_timeout(5000)
        page.screenshot(path='/tmp/zoho-after-verify.png')

        # Try different verify API endpoints
        endpoints_to_try = [
            ('get', f'/zs-site/api/v1/domains/{DOMAIN_ID}/verify'),
            ('post', f'/zs-site/api/v1/domains/{DOMAIN_ID}/verify'),
            ('get', f'/zs-site/api/v1/domains/{DOMAIN_ID}/validate'),
            ('get', f'/zs-site/api/v1/domains/{DOMAIN_ID}/checkdns'),
            ('get', f'/zs-site/api/v1/domains/{DOMAIN_ID}/dns'),
            ('post', f'/zs-site/api/v1/domains/{DOMAIN_ID}/updatestatus'),
        ]

        for method, url in endpoints_to_try:
            window_var = f'__test_{method}_{url.split("/")[-1]}'
            js = f"""() => {{
                window['__testresult'] = null;
                window.$X.{method}({{
                    url: '{url}',
                    headers: window.app.getHeaders(),
                    bodyJSON: {{}},
                    success: function(r) {{ window['__testresult'] = {{ok: r}}; }},
                    error: function(e) {{ window['__testresult'] = {{err: String(e)}}; }},
                }});
            }}"""
            page.evaluate(js)
            page.wait_for_timeout(4000)
            res = page.evaluate("window.__testresult || null")
            print(f"\n  {method.upper()} {url}: {json.dumps(res)[:200] if res else '(null)'}")

        # Get full domain data from network captures
        browser.close()

    print("\n\nAll captured API responses (domain/verify related):")
    for url, r in sorted(all_responses.items()):
        print(f"\n  HTTP {r['status']}  {url}")
        print(f"  {r['body'][:600]}")


if __name__ == '__main__':
    main()
