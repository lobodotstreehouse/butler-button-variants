"""
Click on the domain in the UI to see what options appear.
Also try GET/PUT on markPrimary, and look for the verifyFn API call.
"""
import json, sys, subprocess
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

        # Find the domain row and look for hover menu
        print("Hovering over domain to reveal menu...")
        domain_link = page.locator('text=www.butlerbutton.co').first
        domain_link.hover()
        page.wait_for_timeout(1000)
        page.screenshot(path='/tmp/zoho-domain-hover.png')
        print("Screenshot: /tmp/zoho-domain-hover.png")

        # Look for menu items
        buttons = page.locator('button, [class*="action"], [class*="menu"], [class*="edit"]').all()
        visible = [(b.inner_text().strip(), b.get_attribute('class') or '') for b in buttons if b.is_visible()]
        print(f"\nVisible buttons/actions: {visible[:20]}")

        # Try to find action menu for the domain
        action_items = page.locator('[data-domain-id], [id*="domain"]').all()
        print(f"\nDomain-related elements:")
        for el in action_items[:10]:
            try:
                print(f"  tag={el.evaluate('e=>e.tagName')}, id={el.get_attribute('id')}, "
                      f"data-domain-id={el.get_attribute('data-domain-id')}, "
                      f"class={el.get_attribute('class') or ''}")
            except Exception:
                pass

        # Try to find the 3-dot menu or edit icon
        three_dot = page.locator('[class*="ellipsis"], [class*="three-dot"], [class*="more"], [title*="more"], [title*="edit"], [class*="option"]').all()
        print(f"\n3-dot/option menus: {[(el.get_attribute('class'), el.is_visible()) for el in three_dot[:10]]}")

        # Screenshot the domain settings page
        page.screenshot(path='/tmp/zoho-domain-full.png')
        print("Screenshot: /tmp/zoho-domain-full.png")

        # Try right-clicking on domain to see context menu
        try:
            domain_link.click(button='right')
            page.wait_for_timeout(1000)
            page.screenshot(path='/tmp/zoho-domain-rightclick.png')
            print("Right-click screenshot: /tmp/zoho-domain-rightclick.png")
        except Exception as e:
            print(f"Right-click failed: {e}")

        # Try GET on markPrimary
        print(f"\nTrying GET on /domains/{DOMAIN_ID}/markPrimary...")
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID}/markPrimary',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__gmp = r; }},
                error: function(e) {{ window.__gmp = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        gmp = page.evaluate("window.__gmp || null")
        print(f"GET markPrimary: {json.dumps(gmp)[:300] if gmp else '(null)'}")

        # Try PUT on markPrimary
        print(f"\nTrying PUT on /domains/{DOMAIN_ID}/markPrimary...")
        page.evaluate(f"""() => {{
            window.$X.put({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID}/markPrimary',
                headers: window.app.getHeaders(),
                bodyJSON: {{}},
                success: function(r) {{ window.__pmp = r; }},
                error: function(e) {{ window.__pmp = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        pmp = page.evaluate("window.__pmp || null")
        print(f"PUT markPrimary: {json.dumps(pmp)[:300] if pmp else '(null)'}")

        # Look for the verifyFn in the changePrimary implementation
        full_cp = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    resolve(String(domains.changePrimary));
                });
            });
        }""")
        print(f"\n\nFull changePrimary:\n{full_cp[:2000]}")

        browser.close()

    print("\n\nAll API responses:")
    for url, r in all_responses.items():
        if any(k in url for k in ['domain', 'primary', 'verify']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:400]}")


if __name__ == '__main__':
    main()
