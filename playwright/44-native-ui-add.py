"""
Use Playwright's native UI automation (fill, click) to add www.butlerbutton.co.
Navigate to domain settings, click Add Domain, fill the mapDomainForm input,
click Continue, and capture what API is called.
"""
import json, time, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'


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

    all_requests = []
    all_responses = {}
    def capture_request(req):
        if 'zs-site/api' in req.url:
            try:
                all_requests.append({'url': req.url, 'method': req.method,
                                      'body': req.post_data or ''})
            except Exception:
                pass
    def capture_response(resp):
        if 'zs-site/api' in resp.url:
            try:
                all_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=400)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('request', capture_request)
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(3000)

        # Click Add Domain button (use .nth(0) to avoid strict mode)
        print("Clicking Add Domain button...")
        page.locator('#zp_adddomainbtn').nth(0).click()
        page.wait_for_timeout(4000)
        page.screenshot(path='/tmp/zoho-44-dialog-1.png')

        # Check if dialog is open
        dialog_visible = page.locator('.hb-dialog-overlay').nth(0).is_visible()
        print(f"Dialog visible: {dialog_visible}")

        if not dialog_visible:
            print("Dialog not open, trying showAddDomain...")
            page.evaluate("""() => { require(['domains'], function(d) { d.showAddDomain(); }); }""")
            page.wait_for_timeout(4000)
            page.screenshot(path='/tmp/zoho-44-dialog-2.png')

        # Try to fill the map domain input (native fill)
        map_input = page.locator('#zp_mapDomainName').first
        if map_input.is_visible():
            print("Filling mapDomainName with www.butlerbutton.co...")
            map_input.fill('www.butlerbutton.co')
            page.wait_for_timeout(2000)

            # Get the continue button for mapDomainForm
            map_continue = page.locator('#mapDomainForm button').first
            if map_continue.is_visible():
                print("Clicking Continue in mapDomainForm...")
                map_continue.click()
                page.wait_for_timeout(5000)
                page.screenshot(path='/tmp/zoho-44-after-continue.png')
        else:
            # Try the older form
            custom_input = page.locator('#zp_exsdomainame').first
            if custom_input.is_visible():
                print("Filling zp_exsdomainame...")
                custom_input.fill('www.butlerbutton.co')
                page.wait_for_timeout(2000)
                page.locator('#zp_existingdombtn').nth(0).click()
                page.wait_for_timeout(5000)
                page.screenshot(path='/tmp/zoho-44-after-submit.png')
            else:
                print("No domain input found!")
                all_inputs = page.locator('input').all()
                for inp in all_inputs:
                    if inp.is_visible():
                        pid = inp.get_attribute('id') or ''
                        pp = inp.get_attribute('placeholder') or ''
                        print(f"  Visible input: id={pid} placeholder={pp}")

        # Wait and check what happened
        page.wait_for_timeout(5000)
        page.screenshot(path='/tmp/zoho-44-final.png')

        # Get page text
        page_text = page.locator('body').inner_text()
        print(f"\nPage text:\n{page_text[:2000]}")

        # Check domain list
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
        print(f"\nDomain list:")
        new_www_id = None
        if doms and 'domain_list' in doms:
            for d in doms['domain_list']:
                print(f"  {d['domain_name']} id={d['domain_id']} primary={d['primary_domain']}")
                if d['domain_name'] == 'www.butlerbutton.co':
                    new_www_id = d['domain_id']

        browser.close()

    print(f"\nNew www ID: {new_www_id}")
    print("\nAll captured API requests:")
    for req in all_requests:
        print(f"  {req['method']} {req['url']}: {req['body'][:200]}")

    print("\nAll captured API responses:")
    for url, r in sorted(all_responses.items()):
        print(f"\n  HTTP {r['status']}  {url}")
        print(f"  {r['body'][:400]}")


if __name__ == '__main__':
    main()
