"""
Delete www.butlerbutton.co domain and re-add it to force fresh ZGS routing.
Uses domains.trashDomain (from the domains module).
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
        page.wait_for_timeout(2000)

        # Check $X methods
        xmethods = page.evaluate("Object.keys(window.$X || {}).filter(k => typeof window.$X[k] === 'function')")
        print(f"$X methods: {xmethods}")

        # Check what trashDomain does
        trash_fn = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    resolve(String(domains.trashDomain).substring(0, 800));
                });
            });
        }""")
        print(f"\ntrashDomain function:\n{trash_fn}")

        # Try trashDomain with a mock element
        print(f"\n\nCalling trashDomain with domain_id {DOMAIN_ID}...")
        page.evaluate(f"""() => {{
            require(['domains'], function(domains) {{
                try {{
                    // Create element with correct attributes
                    var el = document.createElement('div');
                    el.id = '{DOMAIN_ID}';
                    el.setAttribute('data-domain-name', 'www.butlerbutton.co');
                    el.setAttribute('data-domain-type', '1');
                    el.setAttribute('data-primary-domain', '1');
                    domains.trashDomain.call(el);
                    window.__trashCalled = true;
                }} catch(e) {{
                    window.__trashCalled = 'error: ' + String(e);
                }}
            }});
        }}""")
        page.wait_for_timeout(3000)
        trash_called = page.evaluate("window.__trashCalled || 'not set'")
        print(f"trashDomain called: {trash_called}")

        # Look for confirmation dialog and handle it
        page.wait_for_timeout(2000)
        page.screenshot(path='/tmp/zoho-trash-dialog.png')

        # Check for confirmation dialog
        dialogs = page.locator('[class*="dialog"], [class*="modal"], [class*="alert"]').all()
        confirm_btn = None
        for d in dialogs:
            if d.is_visible():
                print(f"\nDialog found: {d.inner_text()[:200]}")
                btns = d.locator('button').all()
                for btn in btns:
                    txt = btn.inner_text().strip()
                    if txt.lower() in ['delete', 'remove', 'yes', 'continue', 'ok', 'confirm']:
                        confirm_btn = btn
                        break

        if confirm_btn:
            print(f"Clicking confirm: '{confirm_btn.inner_text()}'")
            confirm_btn.click()
            page.wait_for_timeout(5000)
        else:
            # Try finding buttons with delete-related text
            delete_btn = page.locator('button:has-text("Delete"), button:has-text("Remove"), button:has-text("Yes")').first
            if delete_btn.is_visible():
                print(f"Clicking: {delete_btn.inner_text()}")
                delete_btn.click()
                page.wait_for_timeout(5000)
            else:
                print("No confirmation dialog found - trashDomain might have used a different flow")
                # Try direct API delete methods
                for method in ['put', 'post']:
                    print(f"\nTrying {method.upper()} /domains/{DOMAIN_ID}/trash...")
                    page.evaluate(f"""() => {{
                        window.$X.{method}({{
                            url: '/zs-site/api/v1/domains/{DOMAIN_ID}/trash',
                            headers: window.app.getHeaders(),
                            bodyJSON: {{}},
                            success: function(r) {{ window.__trash = r; }},
                            error: function(e) {{ window.__trash = {{err: String(e)}}; }},
                        }});
                    }}""")
                    page.wait_for_timeout(5000)
                    trash = page.evaluate("window.__trash || null")
                    print(f"  {method.upper()} /trash: {json.dumps(trash)[:300] if trash else '(null)'}")

        # Check domain list after delete
        page.wait_for_timeout(3000)
        page.evaluate("""() => {
            window.$X.get({
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) { window.__doms = r; },
                error: function(e) { window.__doms = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(5000)
        doms = page.evaluate("window.__doms || null")
        print(f"\nDomain list after delete attempt:")
        if doms and 'domain_list' in doms:
            for d in doms['domain_list']:
                print(f"  {d['domain_name']} id={d['domain_id']} primary={d['primary_domain']}")
        else:
            print(f"  {json.dumps(doms)[:300] if doms else '(null)'}")

        browser.close()

    print("\n\nAll API responses:")
    for url, r in all_responses.items():
        if any(k in url.lower() for k in ['domain', 'trash', 'delete']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:500]}")


if __name__ == '__main__':
    main()
