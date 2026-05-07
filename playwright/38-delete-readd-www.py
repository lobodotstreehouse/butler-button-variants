"""
Now that www.butlerbutton.co is non-primary:
1. Click Edit to see the domain edit dialog (check for TXT record)
2. Delete www.butlerbutton.co
3. Re-add it through the proper UI flow
4. Make it primary again
5. Publish and check
"""
import json, time, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'
DOMAIN_ID_WWW = '625000009337247'
DOMAIN_ID_ZIN = '625000009337249'


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

        page.screenshot(path='/tmp/zoho-before-delete.png')
        print("Screenshot before: /tmp/zoho-before-delete.png")

        # Step 1: Click Edit on www.butlerbutton.co to see edit dialog
        edit_el = page.locator(f'[id="{DOMAIN_ID_WWW}-edit"], li:has-text("Edit")').first
        print(f"\nEdit element visible: {edit_el.is_visible()}")

        # Get all action list items
        action_items = page.evaluate(f"""() => {{
            var items = document.querySelectorAll('li, a');
            var results = [];
            for (var item of items) {{
                if (item.id && item.id.includes('{DOMAIN_ID_WWW}')) {{
                    results.push({{
                        id: item.id,
                        text: item.textContent.trim(),
                        class: item.className,
                        dataEvent: item.getAttribute('data-event'),
                    }});
                }}
            }}
            return results;
        }}""")
        print(f"Action items for www.butlerbutton.co: {json.dumps(action_items, indent=2)}")

        # Step 2: Delete www.butlerbutton.co
        print("\n=== Deleting www.butlerbutton.co ===")
        # Try direct API delete first
        page.evaluate(f"""() => {{
            window.__del = null;
            window.$X.del({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID_WWW}',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__del = r; }},
                error: function(e) {{ window.__del = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(6000)
        del_result = page.evaluate("window.__del || null")
        print(f"DELETE API result: {json.dumps(del_result)[:300] if del_result else '(null)'}")

        # Check network capture
        del_url = f"{BASE}/zs-site/api/v1/domains/{DOMAIN_ID_WWW}"
        if del_url in all_responses:
            print(f"Network DELETE: HTTP {all_responses[del_url]['status']} {all_responses[del_url]['body'][:300]}")

        # If API delete failed, try through UI
        if not del_result or 'error' in str(del_result):
            print("API delete failed, trying UI delete...")
            delete_btn = page.locator(f'[id="{DOMAIN_ID_WWW}-delete"], '
                                      'li:has-text("Delete")').first
            if delete_btn.is_visible():
                delete_btn.click()
                page.wait_for_timeout(3000)

                # Handle confirmation dialog
                page.screenshot(path='/tmp/zoho-delete-confirm.png')
                confirm = page.locator('button:has-text("Delete"), button:has-text("Confirm"), '
                                       'button:has-text("Yes")').first
                if confirm.is_visible():
                    print(f"Confirming delete: '{confirm.inner_text()}'")
                    confirm.click()
                    page.wait_for_timeout(5000)
            else:
                print("Delete button not found")

        # Check domain list after delete
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        page.evaluate("""() => {
            window.__doms = null;
            window.$X.get({
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) { window.__doms = r; },
                error: function(e) { window.__doms = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(6000)
        doms = page.evaluate("window.__doms || null")
        print(f"\nDomains after delete:")
        www_gone = True
        new_www_id = None
        if doms and 'domain_list' in doms:
            for d in doms['domain_list']:
                print(f"  {d['domain_name']} id={d['domain_id']} primary={d['primary_domain']}")
                if d['domain_name'] == 'www.butlerbutton.co':
                    www_gone = False
        print(f"www.butlerbutton.co deleted: {www_gone}")

        if not www_gone:
            print("ERROR: Domain not deleted. Stopping here.")
            browser.close()
            return

        # Step 3: Re-add www.butlerbutton.co
        print("\n=== Re-adding www.butlerbutton.co ===")
        # Navigate to domain settings and click Add Domain
        add_btn_el = page.locator('a:has-text("Add Domain")').first
        if add_btn_el.is_visible():
            add_btn_el.click()
        else:
            page.evaluate("""() => {
                require(['domains'], function(d) { d.showAddDomain(); });
            }""")
        page.wait_for_timeout(3000)

        # Skip to "Map a domain" by clicking Continue
        continue_btn = page.locator('button:has-text("Continue")').first
        if continue_btn.is_visible():
            print("Clicking Continue (skip Zoho subdomain)...")
            continue_btn.click()
            page.wait_for_timeout(2000)

        page.screenshot(path='/tmp/zoho-readd-1.png')

        # Find the domain input field
        domain_inputs = page.locator('input[type="text"], input:not([type])').all()
        custom_input = None
        for inp in domain_inputs:
            if inp.is_visible():
                placeholder = inp.get_attribute('placeholder') or ''
                if ('domain' in placeholder.lower() or 'www' in placeholder.lower()
                        or not placeholder):
                    custom_input = inp
                    print(f"Found input: placeholder='{placeholder}'")
                    break

        if not custom_input:
            # Try the specific domain input
            custom_input = page.locator('#customdomain, [name="domain"], '
                                        '[id*="domain"], [class*="domain"] input').first

        if custom_input and custom_input.is_visible():
            print("Filling www.butlerbutton.co in domain input...")
            custom_input.fill('www.butlerbutton.co')
            page.wait_for_timeout(2000)
            page.screenshot(path='/tmp/zoho-readd-2.png')

            # Find and click the Save/Add button
            save_btn = page.locator('button:has-text("Save"), button:has-text("Add"), '
                                    'button:has-text("Next"), button:has-text("Continue"), '
                                    'button[type="submit"]').first
            if save_btn.is_visible() and not save_btn.get_attribute('disabled'):
                print(f"Clicking save: '{save_btn.inner_text()}'")
                save_btn.click()
                page.wait_for_timeout(8000)
                page.screenshot(path='/tmp/zoho-readd-3.png')
            else:
                print(f"Save button state: visible={save_btn.is_visible()}, "
                      f"disabled={save_btn.get_attribute('disabled')}")
                # Get all visible buttons
                btns = page.locator('button').all()
                for btn in btns:
                    if btn.is_visible():
                        print(f"  Button: '{btn.inner_text()}' disabled={btn.get_attribute('disabled')}")
        else:
            print("Domain input not found, checking dialog state...")
            text = page.locator('body').inner_text()
            print(f"Page text:\n{text[:2000]}")

        # Step 4: Check domain list after re-add
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        page.evaluate("""() => {
            window.__doms2 = null;
            window.$X.get({
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) { window.__doms2 = r; },
                error: function(e) { window.__doms2 = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(6000)
        doms2 = page.evaluate("window.__doms2 || null")
        print(f"\nDomains after re-add:")
        if doms2 and 'domain_list' in doms2:
            for d in doms2['domain_list']:
                print(f"  {d['domain_name']} id={d.get('domain_id')} primary={d.get('primary_domain')} "
                      f"verified={d.get('verified')} verification_status={d.get('verification_status')}")
                if d['domain_name'] == 'www.butlerbutton.co':
                    new_www_id = d['domain_id']

        browser.close()

    print(f"\nNew www.butlerbutton.co domain ID: {new_www_id}")

    # Quick check if anything changed
    print("\n=== Quick live check ===")
    for url in ['https://butlerbutton.zohosites.in/', 'https://butlerbutton.zohosites.in/concierge',
                'https://www.butlerbutton.co/concierge']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '10', url], capture_output=True, text=True, timeout=15)
        print(f"  GET {url}: {r.stdout}")

    print("\n\nAll significant API responses:")
    for url, r in sorted(all_responses.items()):
        if any(k in url for k in ['domain', 'markPrimary', 'delete']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:600]}")


if __name__ == '__main__':
    main()
