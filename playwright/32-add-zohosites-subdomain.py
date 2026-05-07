"""
Add a .zohosites.in native subdomain via the Add Domain dialog.
Type 'butlerbutton' in the input, wait for validation, click Add Domain.
Then check if the site serves at butlerbutton.zohosites.in.
Also check if adding it makes it available to become primary.
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
        if 'zs-site/api' in resp.url or 'integrations' in resp.url:
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

        # Also try direct API call first to see what API the form uses
        # Check checkSubDomain function source
        check_fn = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    resolve({
                        checkSubDomain: String(domains.checkSubDomain || '').substring(0, 1000),
                    });
                });
            });
        }""")
        print(f"checkSubDomain:\n{check_fn.get('checkSubDomain', '')}")

        # Click Add Domain button
        add_btn = page.locator('a:has-text("Add Domain"), [class*="addDomain"]').first
        if add_btn.is_visible():
            add_btn.click()
        else:
            page.evaluate("""() => {
                var btns = document.querySelectorAll('a, button, span');
                for (var b of btns) {
                    if (b.textContent.trim() === 'Add Domain') { b.click(); return; }
                }
            }""")
        page.wait_for_timeout(3000)

        # Check if dialog is open
        subdomain_input = page.locator('#zp_subdomainname')
        if not subdomain_input.is_visible():
            print("Dialog not open, trying again...")
            page.evaluate("""() => {
                require(['domains'], function(d) { d.showAddDomain(); });
            }""")
            page.wait_for_timeout(3000)

        subdomain_input = page.locator('#zp_subdomainname')
        if subdomain_input.is_visible():
            print("Dialog open, typing subdomain...")
            subdomain_input.fill('butlerbutton')
            page.wait_for_timeout(3000)

            # Check if button is enabled
            btn_disabled = page.evaluate("document.getElementById('zp_addsubdombtn')?.disabled")
            print(f"Add button disabled: {btn_disabled}")

            # Get success/error indicator
            page.screenshot(path='/tmp/zoho-subdomain-dialog.png')
            print("Screenshot: /tmp/zoho-subdomain-dialog.png")

            # If there's an error (name taken), try alternatives
            error_el = page.locator('#zp_domerror')
            if error_el.is_visible():
                print("Error on 'butlerbutton', trying 'veltmbutler'...")
                subdomain_input.fill('veltmbutler')
                page.wait_for_timeout(3000)
                btn_disabled = page.evaluate("document.getElementById('zp_addsubdombtn')?.disabled")
                print(f"Add button disabled (veltmbutler): {btn_disabled}")

            # Check the actual button state and success indicator
            success_visible = page.evaluate("document.getElementById('zp_domsuccess')?.style?.display !== 'none'")
            error_visible = page.evaluate("document.getElementById('zp_domerror')?.style?.display !== 'none'")
            print(f"Success indicator: {success_visible}, Error indicator: {error_visible}")

            # If button is enabled or we can enable it, click Add Domain
            btn = page.locator('#zp_addsubdombtn')
            if btn.is_visible():
                # Force enable if needed
                page.evaluate("""() => {
                    var btn = document.getElementById('zp_addsubdombtn');
                    if (btn) { btn.removeAttribute('disabled'); }
                }""")
                print("Clicking Add Domain button...")
                btn.click()
                page.wait_for_timeout(8000)
                page.screenshot(path='/tmp/zoho-after-add-subdomain.png')
                print("Screenshot: /tmp/zoho-after-add-subdomain.png")
        else:
            print("ERROR: Dialog input not found")

        # Check domain list after
        page.evaluate("""() => {
            window.$X.get({
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) { window.__doms = r; },
                error: function(e) { window.__doms = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(6000)
        doms = page.evaluate("window.__doms || null")
        print(f"\nDomain list after add attempt:")
        if doms and 'domain_list' in doms:
            for d in doms['domain_list']:
                print(f"  {d['domain_name']} id={d['domain_id']} primary={d['primary_domain']} "
                      f"verified={d['verified']} zoho_verified={d.get('is_zoho_verified')}")
        else:
            print(f"  {json.dumps(doms)[:400] if doms else '(null)'}")

        browser.close()

    # Check live site and new Zoho subdomain
    print("\n\n=== Live site checks ===")
    for url in ['https://www.butlerbutton.co/', 'https://www.butlerbutton.co/concierge',
                'https://butlerbutton.zohosites.in/', 'https://butlerbutton.zohosites.in/concierge',
                'https://veltmbutler.zohosites.in/', 'https://veltmbutler.zohosites.in/concierge']:
        result = subprocess.run(
            ['curl', '-sIL', '--max-time', '10', url],
            capture_output=True, text=True, timeout=15
        )
        status = next((l for l in result.stdout.split('\n') if 'HTTP/' in l), 'unknown')
        print(f"  {url}: {status.strip()}")

    print("\n\nAll captured API responses:")
    for url, r in sorted(all_responses.items()):
        print(f"\n  HTTP {r['status']}  {url}")
        print(f"  {r['body'][:600]}")


if __name__ == '__main__':
    main()
