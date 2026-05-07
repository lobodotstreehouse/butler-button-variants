"""
Click the 'Make primary' button for butlerbutton.zohosites.in in the UI.
Capture what API call it makes, then delete www.butlerbutton.co, re-add it,
make it primary, re-install SSL, publish.
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

        page.screenshot(path='/tmp/zoho-domains-before.png')
        print("Screenshot: /tmp/zoho-domains-before.png")

        # Get the HTML of the domain list to find the Make primary button
        domain_list_html = page.evaluate("""() => {
            var lists = document.querySelectorAll('.sites-contentpanel, .sites-section, [class*="domain-list"]');
            return Array.from(lists).map(l => l.outerHTML.substring(0, 2000));
        }""")
        print(f"Domain list HTML snippets: {len(domain_list_html)}")
        for h in domain_list_html[:3]:
            print(f"\n{h[:1000]}")

        # Find all clickable elements with "primary" text
        primary_els = page.evaluate("""() => {
            var all = document.querySelectorAll('a, button, span, li');
            var results = [];
            for (var el of all) {
                if (el.textContent.trim().toLowerCase().includes('make primary') ||
                    el.textContent.trim().toLowerCase() === 'make primary') {
                    results.push({
                        tag: el.tagName,
                        id: el.id,
                        class: el.className,
                        text: el.textContent.trim(),
                        dataAttrs: {
                            domainName: el.getAttribute('data-domain-name'),
                            domainType: el.getAttribute('data-domain-type'),
                            primaryDomain: el.getAttribute('data-primary-domain'),
                        },
                        parent: el.parentElement ? el.parentElement.outerHTML.substring(0, 300) : ''
                    });
                }
            }
            return results;
        }""")
        print(f"\nMake primary elements: {json.dumps(primary_els, indent=2)}")

        # Click the Make primary button for butlerbutton.zohosites.in
        # It should be the anchor with id = DOMAIN_ID_ZIN or nearby
        make_primary_btn = None
        for el in primary_els:
            if el.get('tag') in ['A', 'SPAN', 'BUTTON', 'LI']:
                make_primary_btn = page.locator(f"[id='{el.get('id', '')}']") if el.get('id') else None
                break

        if not make_primary_btn or not make_primary_btn.is_visible():
            # Try by text content
            make_primary_btn = page.locator('a:has-text("Make primary"), '
                                            'button:has-text("Make primary"), '
                                            'span:has-text("Make primary")').first

        if make_primary_btn and make_primary_btn.is_visible():
            print(f"\nClicking Make primary button...")
            make_primary_btn.click()
            page.wait_for_timeout(3000)

            # Handle any confirmation dialog
            confirm = page.locator('button:has-text("Yes"), button:has-text("Confirm"), '
                                   'button:has-text("Set Primary"), button:has-text("OK")').first
            if confirm.is_visible():
                print(f"Confirmation: '{confirm.inner_text()}', clicking...")
                confirm.click()
                page.wait_for_timeout(5000)

            page.screenshot(path='/tmp/zoho-after-make-primary.png')
            page.wait_for_timeout(3000)
        else:
            print("Make primary button not visible, trying JS click...")
            # Use changePrimary from domains module on the .zohosites.in element
            result = page.evaluate(f"""() => {{
                return new Promise(function(resolve) {{
                    require(['domains'], function(domains) {{
                        var el = document.getElementById('{DOMAIN_ID_ZIN}');
                        if (!el) {{
                            el = document.createElement('a');
                            el.id = '{DOMAIN_ID_ZIN}';
                        }}
                        el.setAttribute('data-domain-name', 'butlerbutton.zohosites.in');
                        el.setAttribute('data-domain-type', '0');
                        try {{
                            domains.changePrimary.call(el);
                            resolve({{called: true}});
                        }} catch(e) {{
                            resolve({{error: String(e)}});
                        }}
                    }});
                }});
            }}""")
            print(f"JS changePrimary result: {result}")
            page.wait_for_timeout(8000)

        # Check domain state now
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
        print(f"\nDomains after make-primary attempt:")
        new_primary = None
        if doms and 'domain_list' in doms:
            for d in doms['domain_list']:
                print(f"  {d['domain_name']} primary={d['primary_domain']} verified={d['verified']}")
                if d['primary_domain'] == 1:
                    new_primary = d['domain_name']
        print(f"New primary: {new_primary}")

        if new_primary != 'butlerbutton.zohosites.in':
            print("\nFailed to change primary domain. Checking page text...")
            page_text = page.locator('body').inner_text()
            print(f"Page text:\n{page_text[:1000]}")

        browser.close()

    print("\n\nAll captured API responses:")
    for url, r in sorted(all_responses.items()):
        if any(k in url for k in ['domain', 'markPrimary', 'primary']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:500]}")


if __name__ == '__main__':
    main()
