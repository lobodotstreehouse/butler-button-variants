"""
Open Add Domain dialog, explore Zoho subdomain flow, get searchZdomain source,
try to add a .zohosites.in native subdomain.
Also try POST /domains/verify with proper params and capture full response.
"""
import json
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
        browser = pw.chromium.launch(headless=False, slow_mo=150)
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

        # Get domain module function sources
        fn_sources = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    resolve({
                        searchZdomain: String(domains.searchZdomain || '').substring(0, 1200),
                        connectAndVerifyZDomain: String(domains.connectAndVerifyZDomain || '').substring(0, 1200),
                        showAddDomain: String(domains.showAddDomain || '').substring(0, 1200),
                        getDomainsStore: String(domains.getDomainsStore || '').substring(0, 800),
                        allKeys: Object.keys(domains),
                    });
                });
            });
        }""")
        print(f"searchZdomain:\n{fn_sources.get('searchZdomain', '')}\n")
        print(f"connectAndVerifyZDomain:\n{fn_sources.get('connectAndVerifyZDomain', '')}\n")
        print(f"showAddDomain:\n{fn_sources.get('showAddDomain', '')}\n")
        print(f"getDomainsStore:\n{fn_sources.get('getDomainsStore', '')}\n")

        # Try POST /domains/verify with proper params - capture full response
        page.evaluate("""() => {
            window.__verifyResp = null;
            window.$X.post({
                url: '/zs-site/api/v1/domains/verify',
                headers: window.app.getHeaders(),
                params: {domain_name: 'www.butlerbutton.co', domain_type: '1'},
                success: function(r) { window.__verifyResp = r; },
                error: function(e) { window.__verifyResp = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(8000)
        verify_resp = page.evaluate("window.__verifyResp || null")
        print(f"\nPOST /domains/verify (proper params): {json.dumps(verify_resp)[:1000] if verify_resp else '(null)'}")

        # Click the "Add Domain" button and screenshot
        add_btn = page.locator('a:has-text("Add Domain"), button:has-text("Add Domain"), '
                               '.h-addDomain, [class*="addDomain"], .add-domain').first
        if add_btn.is_visible():
            print("\nClicking Add Domain button...")
            add_btn.click()
            page.wait_for_timeout(3000)
            page.screenshot(path='/tmp/zoho-add-domain-dialog.png')
            print("Screenshot: /tmp/zoho-add-domain-dialog.png")

            # Get dialog content
            dialog_text = page.locator('[class*="dialog"], [class*="modal"], .sites-formoverlay').all()
            for d in dialog_text:
                if d.is_visible():
                    txt = d.inner_text()
                    html = d.evaluate('el => el.outerHTML').replace('\\n', '\n')
                    print(f"\nDialog text:\n{txt[:1500]}")
                    print(f"\nDialog HTML:\n{html[:2000]}")
        else:
            # Try via JavaScript
            print("\nAdd Domain button not found via CSS, trying JS click...")
            page.evaluate("""() => {
                var btns = document.querySelectorAll('a, button');
                for (var i=0; i<btns.length; i++) {
                    if (btns[i].textContent.includes('Add Domain') || btns[i].textContent.includes('Add domain')) {
                        btns[i].click();
                        return btns[i].textContent;
                    }
                }
                return 'not found';
            }""")
            page.wait_for_timeout(3000)
            page.screenshot(path='/tmp/zoho-add-domain-dialog.png')

            dialog_text = page.locator('body').inner_text()
            print(f"\nPage after Add Domain click:\n{dialog_text[:2000]}")

        # Try calling showAddDomain directly
        page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    try {
                        domains.showAddDomain();
                        resolve({called: true});
                    } catch(e) {
                        resolve({error: String(e)});
                    }
                });
            });
        }""")
        page.wait_for_timeout(3000)
        page.screenshot(path='/tmp/zoho-add-domain-2.png')
        print("Screenshot 2: /tmp/zoho-add-domain-2.png")

        # Get the current dialog HTML
        dialog_html = page.evaluate("""() => {
            var panels = document.querySelectorAll('[class*="overlay"], [class*="dialog"], [class*="modal"], .sites-formoverlay');
            var results = [];
            panels.forEach(function(p) {
                if (p.offsetParent !== null) {
                    results.push(p.outerHTML.substring(0, 2000));
                }
            });
            return results;
        }""")
        print(f"\nVisible dialogs: {len(dialog_html)}")
        for i, h in enumerate(dialog_html):
            print(f"\nDialog {i}:\n{h[:1500]}")

        browser.close()

    print("\n\nAll captured API responses:")
    for url, r in sorted(all_responses.items()):
        if any(k in url for k in ['domain', 'verify', 'zdomain']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:800]}")


if __name__ == '__main__':
    main()
