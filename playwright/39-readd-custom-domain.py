"""
Re-add www.butlerbutton.co through the proper UI flow.
Navigate the Add Domain dialog carefully, click 'Map a domain' Continue,
fill in the domain, submit.
"""
import json, time, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'
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
        browser = pw.chromium.launch(headless=False, slow_mo=200)
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

        # Confirm www.butlerbutton.co is gone
        text = page.locator('body').inner_text()
        print("Current domain state:")
        for line in text.split('\n'):
            if 'domain' in line.lower() or 'primary' in line.lower() or 'butler' in line.lower():
                print(f"  {line.strip()}")

        # Step 1: Click Add Domain
        print("\n=== Opening Add Domain dialog ===")
        add_btn = page.locator('a:has-text("Add Domain")').first
        print(f"Add Domain button visible: {add_btn.is_visible()}")
        add_btn.click()
        page.wait_for_timeout(3000)
        page.screenshot(path='/tmp/zoho-add-1.png')
        print("Screenshot 1: /tmp/zoho-add-1.png")

        # Print dialog state
        dialog_text = page.locator('#domainDialogDiv').inner_text() if page.locator('#domainDialogDiv').is_visible() else 'not found'
        print(f"Dialog text: {dialog_text[:500]}")

        # Step 2: Find and click the "Continue" button under "Map a domain" section
        # The dialog has: Zoho subdomain section, "Map a domain" section with Continue, "Buy a domain"
        # We need to click the Continue button in the "Map a domain" section
        all_buttons = page.locator('button').all()
        print(f"\nAll visible buttons:")
        for btn in all_buttons:
            if btn.is_visible():
                txt = btn.inner_text().strip()
                cls = btn.get_attribute('class') or ''
                parent_id = btn.evaluate('el => el.parentElement?.id || el.parentElement?.className || ""')
                print(f"  '{txt}' class='{cls}' parent='{parent_id}'")

        # Click the Continue button (for Map a domain section)
        continue_btn = page.locator('button:has-text("Continue")').last
        if continue_btn.is_visible():
            print(f"\nClicking Continue (Map a domain)...")
            continue_btn.click()
            page.wait_for_timeout(3000)
            page.screenshot(path='/tmp/zoho-add-2.png')
            print("Screenshot 2: /tmp/zoho-add-2.png")

        # Step 3: Find the custom domain input
        # It should now be visible in customDomainDiv
        print("\nLooking for custom domain input...")
        page.evaluate("document.getElementById('customDomainDiv') && (document.getElementById('customDomainDiv').style.display = 'block')")

        # Get all inputs visible
        inputs = page.locator('input').all()
        for inp in inputs:
            if inp.is_visible():
                itype = inp.get_attribute('type') or 'text'
                iid = inp.get_attribute('id') or ''
                iplaceholder = inp.get_attribute('placeholder') or ''
                iclass = inp.get_attribute('class') or ''
                print(f"  Input: type={itype} id='{iid}' placeholder='{iplaceholder}' class='{iclass[:50]}'")

        # Get the full dialog HTML to understand structure
        dialog_html = page.evaluate("""() => {
            var d = document.getElementById('domainDialogDiv');
            return d ? d.outerHTML.substring(0, 5000) : 'not found';
        }""")
        print(f"\nDialog HTML (5000 chars):\n{dialog_html[:5000]}")

        # Try to find the domain input in customDomainDiv
        custom_domain_input = page.locator('#customDomainDiv input, [placeholder*="domain"], [id*="customdomain"]').first
        if custom_domain_input.is_visible():
            print(f"\nFilling domain input...")
            custom_domain_input.fill('www.butlerbutton.co')
        else:
            # Try to show the custom domain section and find the input
            # The "Continue" click might navigate to a different view
            # Let's search more broadly
            all_inputs = page.locator('input').all()
            for inp in all_inputs:
                iid = inp.get_attribute('id') or ''
                if 'zp_subdomainname' not in iid:
                    print(f"  Trying input id='{iid}'...")
                    inp.fill('www.butlerbutton.co')
                    page.wait_for_timeout(1000)
                    break

        page.wait_for_timeout(2000)
        page.screenshot(path='/tmp/zoho-add-3.png')
        print("Screenshot 3: /tmp/zoho-add-3.png")

        # Get page state
        text_now = page.locator('body').inner_text()
        print(f"\nPage text now:\n{text_now[:1000]}")

        # Click save/submit
        btns = page.locator('button').all()
        for btn in btns:
            if btn.is_visible():
                txt = btn.inner_text().strip()
                print(f"  Visible button: '{txt}'")
                if txt.lower() in ['save', 'add', 'continue', 'next', 'map', 'submit', 'done']:
                    disabled = btn.get_attribute('disabled')
                    if not disabled:
                        print(f"  Clicking: '{txt}'")
                        btn.click()
                        page.wait_for_timeout(8000)
                        break

        page.screenshot(path='/tmp/zoho-add-4.png')

        # Wait for DNS instructions or success
        page.wait_for_timeout(5000)
        final_text = page.locator('body').inner_text()
        print(f"\nFinal dialog text:\n{final_text[:2000]}")

        # Check domain list
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)

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
        print(f"\n=== Final domain state ===")
        new_www_id = None
        if doms and 'domain_list' in doms:
            for d in doms['domain_list']:
                print(f"  {d['domain_name']} id={d.get('domain_id')} primary={d.get('primary_domain')} "
                      f"verified={d.get('verified')} vs={d.get('verification_status')} "
                      f"ssl={d.get('ssl_status')}")
                if d['domain_name'] == 'www.butlerbutton.co':
                    new_www_id = d['domain_id']

        browser.close()

    print(f"\nNew www.butlerbutton.co ID: {new_www_id}")

    print("\n\nAll significant API responses:")
    for url, r in sorted(all_responses.items()):
        if any(k in url.lower() for k in ['domain', 'mark', 'trash', 'add']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:600]}")


if __name__ == '__main__':
    main()
