"""
Full domain cycle:
1. Make butlerbutton.zohosites.in primary
2. Delete www.butlerbutton.co
3. Re-add www.butlerbutton.co via UI
4. Make www.butlerbutton.co primary again
5. Re-install SSL
6. Publish
7. Check live site
"""
import json, time, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'
DOMAIN_ID_WWW = '625000009337247'   # www.butlerbutton.co
DOMAIN_ID_ZIN = '625000009337249'   # butlerbutton.zohosites.in


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


def check_domains(page):
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
    if doms and 'domain_list' in doms:
        for d in doms['domain_list']:
            print(f"    {d['domain_name']} id={d['domain_id']} primary={d['primary_domain']} "
                  f"verified={d['verified']} ssl={d.get('ssl_status')} "
                  f"verification_status={d.get('verification_status')}")
    return doms


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

        print("=== Step 1: Current domain state ===")
        check_domains(page)

        # Step 2: Make butlerbutton.zohosites.in primary
        print(f"\n=== Step 2: markPrimary for butlerbutton.zohosites.in ===")
        page.evaluate(f"""() => {{
            window.__mp = null;
            window.$X.get({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID_ZIN}/markPrimary',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__mp = r; }},
                error: function(e) {{ window.__mp = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(8000)
        mp = page.evaluate("window.__mp || null")
        print(f"markPrimary result: {json.dumps(mp)[:400] if mp else '(null - check network)'}")

        # Check domains after
        print("\nDomains after markPrimary:")
        check_domains(page)

        # Step 3: Delete www.butlerbutton.co
        print(f"\n=== Step 3: Delete www.butlerbutton.co ===")
        # Use trashDomain via the UI element
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Try direct DELETE API
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
        print(f"DELETE result: {json.dumps(del_result)[:300] if del_result else '(null - check network)'}")

        if not del_result or 'error' in str(del_result):
            # Try trashDomain via UI
            print("Trying trashDomain via UI...")
            page.evaluate(f"""() => {{
                require(['domains'], function(domains) {{
                    var el = document.createElement('div');
                    el.id = '{DOMAIN_ID_WWW}';
                    el.setAttribute('data-domain-name', 'www.butlerbutton.co');
                    el.setAttribute('data-domain-type', '1');
                    el.setAttribute('data-primary-domain', '0');
                    domains.trashDomain.call(el);
                }});
            }}""")
            page.wait_for_timeout(3000)

            # Handle confirmation dialog
            page.screenshot(path='/tmp/zoho-delete-dialog.png')
            delete_btn = page.locator('button:has-text("Delete"), button:has-text("Remove"), '
                                      'button:has-text("Yes"), button:has-text("Confirm")').first
            if delete_btn.is_visible():
                print(f"Clicking delete confirm: '{delete_btn.inner_text()}'")
                delete_btn.click()
                page.wait_for_timeout(5000)
            else:
                print("No delete dialog found")
                # Check current dialog text
                dialog_text = page.locator('body').inner_text()
                print(f"Page text snippet: {dialog_text[:500]}")

        # Check domains after delete
        print("\nDomains after delete attempt:")
        check_domains(page)

        # Reload domain settings
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        print("\nDomains after page reload:")
        doms_data = check_domains(page)

        # Check if www.butlerbutton.co was deleted
        www_deleted = True
        if doms_data and 'domain_list' in doms_data:
            for d in doms_data['domain_list']:
                if d['domain_name'] == 'www.butlerbutton.co':
                    www_deleted = False
                    break

        if not www_deleted:
            print("\nERROR: www.butlerbutton.co was NOT deleted. Cannot proceed with re-add.")
            browser.close()
            return

        print("\n=== Step 4: Re-add www.butlerbutton.co ===")
        # Click Add Domain button
        add_btn = page.locator('a:has-text("Add Domain")').first
        if add_btn.is_visible():
            add_btn.click()
        else:
            page.evaluate("""() => {
                var btns = document.querySelectorAll('a, button, span');
                for (var b of btns) {
                    if (b.textContent.trim().includes('Add Domain')) { b.click(); return; }
                }
            }""")
        page.wait_for_timeout(3000)

        # Click "Map a domain" tab (for custom domain, not Zoho subdomain)
        map_btn = page.locator(':has-text("Map a domain"), :has-text("Map Domain"), '
                               ':has-text("own a domain"), :has-text("Continue")').filter(
                                   has_text='Continue').last
        if map_btn.is_visible():
            print("Clicking Continue to get to Map a domain...")
            map_btn.click()
            page.wait_for_timeout(2000)

        page.screenshot(path='/tmp/zoho-readd-domain-1.png')
        dialog_text = page.locator('body').inner_text()
        print(f"Add domain dialog:\n{dialog_text[:1500]}")

        # Look for custom domain input
        custom_input = page.locator('input[type="text"]:not(#zp_subdomainname), '
                                    '[placeholder*="domain"], [placeholder*="www"]').first
        if custom_input.is_visible():
            print("Found custom domain input, typing www.butlerbutton.co...")
            custom_input.fill('www.butlerbutton.co')
            page.wait_for_timeout(2000)
            page.screenshot(path='/tmp/zoho-readd-domain-2.png')

            # Click Save/Add/Continue
            save_btn = page.locator('button:has-text("Save"), button:has-text("Add"), '
                                    'button:has-text("Continue"), button:has-text("Map")').first
            if save_btn.is_visible():
                print(f"Clicking: '{save_btn.inner_text()}'")
                save_btn.click()
                page.wait_for_timeout(5000)
        else:
            print("Custom domain input not found")
            # Check what's in the dialog
            print(dialog_text[:2000])

        page.screenshot(path='/tmp/zoho-readd-domain-3.png')

        # Check domains after re-add
        page.wait_for_timeout(3000)
        print("\nDomains after re-add attempt:")
        check_domains(page)

        browser.close()

    print("\n\nAll significant API responses:")
    for url, r in sorted(all_responses.items()):
        if any(k in url for k in ['domain', 'markPrimary', 'trash']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:500]}")


if __name__ == '__main__':
    main()
