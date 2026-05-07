"""
Retry adding www.butlerbutton.co after a cooldown period.
Try multiple body formats. Then complete the full flow.
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

    all_responses = {}
    def capture_response(resp):
        if 'zs-site/api' in resp.url:
            try:
                all_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
            except Exception:
                pass

    print("Waiting 60 seconds for domain cooldown...")
    time.sleep(60)

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

        # Try using the UI flow to add the domain
        # Find Add Domain button (might be different when only .zohosites.in exists)
        print("Page text (domain section):")
        text = page.locator('body').inner_text()
        for line in text.split('\n'):
            if line.strip() and ('domain' in line.lower() or 'add' in line.lower() or 'butler' in line.lower()):
                print(f"  {line.strip()}")

        # Find the add domain button in different ways
        add_el = page.evaluate("""() => {
            var els = document.querySelectorAll('a, button, span, li, div');
            var found = [];
            for (var el of els) {
                if (el.textContent.trim() === 'Add Domain' ||
                    el.textContent.trim() === 'add domain' ||
                    el.getAttribute('class')?.includes('addDomain') ||
                    el.getAttribute('data-event')?.includes('addDomain')) {
                    found.push({
                        tag: el.tagName,
                        id: el.id,
                        class: el.className,
                        text: el.textContent.trim(),
                        dataEvent: el.getAttribute('data-event'),
                        href: el.href || '',
                    });
                }
            }
            return found;
        }""")
        print(f"\nAdd Domain elements: {json.dumps(add_el, indent=2)}")

        # Try multiple body formats for adding the domain
        bodies_to_try = [
            {'domain_name': 'www.butlerbutton.co'},
            {'domain_name': 'www.butlerbutton.co', 'domain_type': 1},
            {'domain_name': 'www.butlerbutton.co', 'domain_type': '1'},
            {'domain': 'www.butlerbutton.co'},
            {'customDomain': 'www.butlerbutton.co'},
        ]

        new_www_id = None
        for body in bodies_to_try:
            body_str = json.dumps(body)
            window_var = f'__add_{list(body.keys())[0]}'
            page.evaluate(f"""() => {{
                window.__addTry = null;
                window.$X.post({{
                    url: '/zs-site/api/v1/domains',
                    headers: window.app.getHeaders(),
                    bodyJSON: {body_str},
                    success: function(r) {{ window.__addTry = r; }},
                    error: function(e) {{ window.__addTry = {{error: String(e)}}; }},
                }});
            }}""")
            page.wait_for_timeout(6000)
            result = page.evaluate("window.__addTry || null")
            # Get from network
            if f"{BASE}/zs-site/api/v1/domains" in all_responses:
                net_resp = all_responses[f"{BASE}/zs-site/api/v1/domains"]
                print(f"\nBody {body_str}: HTTP {net_resp['status']} → {net_resp['body'][:300]}")
                del all_responses[f"{BASE}/zs-site/api/v1/domains"]
                try:
                    data = json.loads(net_resp['body'])
                    if data.get('status_code') == '0':
                        for d in data.get('domain_list', []):
                            if d.get('domain_name') == 'www.butlerbutton.co':
                                new_www_id = d['domain_id']
                                print(f"SUCCESS! New domain ID: {new_www_id}")
                                break
                        if new_www_id:
                            break
                except Exception:
                    pass
            else:
                print(f"Body {body_str}: no network response captured")

        if not new_www_id:
            # Try via the UI
            print("\n\nTrying UI flow to add domain...")
            page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                      wait_until='networkidle', timeout=45000)
            page.wait_for_timeout(3000)

            # Try clicking whatever "Add Domain" element exists
            page.evaluate("""() => {
                var els = document.querySelectorAll('a, button, span, li, div');
                for (var el of els) {
                    if (el.textContent.trim() === 'Add Domain') {
                        el.click();
                        return 'clicked: ' + el.tagName + ' ' + el.className;
                    }
                }
                return 'not found';
            }""")
            page.wait_for_timeout(3000)
            page.screenshot(path='/tmp/zoho-add-domain-state.png')
            print("Screenshot: /tmp/zoho-add-domain-state.png")

            text = page.locator('body').inner_text()
            print(f"After click:\n{text[:1000]}")

        # If we successfully added the domain, proceed with full flow
        if new_www_id:
            print(f"\n=== Domain added! ID: {new_www_id} ===")

            # Make it primary
            print("Making www.butlerbutton.co primary...")
            page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                      wait_until='networkidle', timeout=45000)
            page.wait_for_timeout(3000)
            page.wait_for_function(
                "typeof window.$X==='object' && typeof window.app==='object'",
                timeout=30000)
            page.wait_for_timeout(3000)

            # Click Make primary for www.butlerbutton.co
            mp_el = page.locator(f'[id="{new_www_id}-primary"]')
            if mp_el.is_visible():
                mp_el.click()
                page.wait_for_timeout(8000)
                print("Clicked Make primary button")
            else:
                # Call API directly
                page.evaluate(f"""() => {{
                    window.__mp = null;
                    window.$X.get({{
                        url: '/zs-site/api/v1/domains/{new_www_id}/markPrimary',
                        headers: window.app.getHeaders(),
                        success: function(r) {{ window.__mp = r; }},
                        error: function(e) {{ window.__mp = {{error: String(e)}}; }},
                    }});
                }}""")
                page.wait_for_timeout(6000)
                mp_result = page.evaluate("window.__mp || null")
                print(f"markPrimary API: {json.dumps(mp_result)[:200] if mp_result else '(null)'}")

            # Install SSL
            print("Installing SSL...")
            page.goto(f"{BASE}/zcms/{SITE_ID}/settings/ssl",
                      wait_until='networkidle', timeout=45000)
            page.wait_for_timeout(3000)
            page.wait_for_function(
                "typeof window.$X==='object' && typeof window.app==='object'",
                timeout=30000)
            page.wait_for_timeout(2000)

            page.evaluate("""() => {
                return new Promise(function(resolve) {
                    require(['domains'], function(d) {
                        try { d.installFreeSSLClick(); resolve({ok: true}); }
                        catch(e) { resolve({error: String(e)}); }
                    });
                });
            }""")
            page.wait_for_timeout(5000)
            print("SSL install triggered. Waiting 2 minutes...")
            page.wait_for_timeout(120000)

            # Publish
            print("Publishing...")
            page.evaluate("""() => {
                window.__pub = null;
                window.$X.post({
                    url: '/zs-site/api/v1/publish',
                    headers: window.app.getHeaders(),
                    bodyJSON: {},
                    success: function(r) { window.__pub = r; },
                    error: function(e) { window.__pub = {error: String(e)}; },
                });
            }""")
            page.wait_for_timeout(15000)
            pub = page.evaluate("window.__pub || null")
            print(f"Publish: {json.dumps(pub)[:400] if pub else '(null)'}")

        browser.close()

    if new_www_id:
        print("\nWaiting 30 seconds...")
        time.sleep(30)

        print("\n=== Live site check ===")
        for url in ['https://www.butlerbutton.co/', 'https://www.butlerbutton.co/home',
                    'https://www.butlerbutton.co/concierge']:
            r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                                '--max-time', '15', url], capture_output=True, text=True, timeout=20)
            print(f"  GET {url}: {r.stdout}")

    print("\n\nAll captured API responses:")
    for url, r in sorted(all_responses.items()):
        if any(k in url.lower() for k in ['domain', 'ssl', 'publish', 'mark']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:400]}")


if __name__ == '__main__':
    main()
