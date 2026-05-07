"""
Complete flow after www.butlerbutton.co was deleted:
1. Re-add www.butlerbutton.co via POST /domains API
2. Make it primary (via UI click)
3. Re-install SSL
4. Publish
5. Check live site
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
        if 'zs-site/api' in resp.url or 'letsencrypt' in resp.url.lower():
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

        # Step 1: Re-add www.butlerbutton.co via API
        print("=== Step 1: Re-add www.butlerbutton.co ===")
        page.evaluate("""() => {
            window.__addDom = null;
            window.$X.post({
                url: '/zs-site/api/v1/domains',
                headers: window.app.getHeaders(),
                bodyJSON: {domain_name: 'www.butlerbutton.co', domain_type: 1},
                success: function(r) { window.__addDom = r; },
                error: function(e) { window.__addDom = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(8000)
        add_result = page.evaluate("window.__addDom || null")
        print(f"Add domain result: {json.dumps(add_result)[:500] if add_result else '(null - check network)'}")

        # Check network capture
        add_url = f"{BASE}/zs-site/api/v1/domains"
        if add_url in all_responses:
            body = all_responses[add_url]['body']
            print(f"Network add: HTTP {all_responses[add_url]['status']} {body[:500]}")
            try:
                add_data = json.loads(body)
                for d in add_data.get('domain_list', []):
                    if d.get('domain_name') == 'www.butlerbutton.co':
                        new_domain_id = d['domain_id']
                        print(f"New domain ID: {new_domain_id}")
            except Exception:
                pass

        # Get new domain ID from domains list
        page.evaluate("""() => {
            window.__domsCheck = null;
            window.$X.get({
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) { window.__domsCheck = r; },
                error: function(e) { window.__domsCheck = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(6000)
        doms_check = page.evaluate("window.__domsCheck || null")
        print(f"\nDomains after add:")
        new_www_id = None
        if doms_check and 'domain_list' in doms_check:
            for d in doms_check['domain_list']:
                print(f"  {d['domain_name']} id={d['domain_id']} primary={d['primary_domain']} "
                      f"verified={d['verified']} vs={d.get('verification_status')} ssl={d.get('ssl_status')}")
                if d['domain_name'] == 'www.butlerbutton.co':
                    new_www_id = d['domain_id']
        print(f"New www.butlerbutton.co ID: {new_www_id}")

        if not new_www_id:
            print("ERROR: Domain was not added successfully")
            browser.close()
            return

        # Step 2: Make www.butlerbutton.co primary (via UI - reload page first)
        print(f"\n=== Step 2: Making www.butlerbutton.co primary ===")
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(3000)

        # Find Make primary button for www.butlerbutton.co (the new domain ID)
        primary_el = page.locator(f'[id="{new_www_id}-primary"]')
        if primary_el.is_visible():
            print(f"Clicking Make primary for id={new_www_id}...")
            primary_el.click()
            page.wait_for_timeout(8000)
        else:
            # Try text-based
            make_primary = page.locator('li:has-text("Make primary")').all()
            for mp in make_primary:
                if mp.is_visible():
                    mp_id = mp.get_attribute('id') or ''
                    if new_www_id in mp_id:
                        print(f"Clicking Make primary (id={mp_id})...")
                        mp.click()
                        page.wait_for_timeout(8000)
                        break
            else:
                # Call via API
                print(f"Clicking via API: GET /domains/{new_www_id}/markPrimary")
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
                print(f"markPrimary: {json.dumps(mp_result)[:300] if mp_result else '(null)'}")

        # Check domains after make-primary
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
        print(f"\nDomains after make-primary:")
        www_is_primary = False
        if doms2 and 'domain_list' in doms2:
            for d in doms2['domain_list']:
                print(f"  {d['domain_name']} primary={d['primary_domain']} ssl={d.get('ssl_status')}")
                if d['domain_name'] == 'www.butlerbutton.co' and d['primary_domain'] == 1:
                    www_is_primary = True
        print(f"www.butlerbutton.co is primary: {www_is_primary}")

        # Step 3: Install free SSL
        print(f"\n=== Step 3: Installing SSL ===")
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/ssl",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        ssl_result = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    try {
                        domains.installFreeSSLClick();
                        resolve({called: true});
                    } catch(e) {
                        resolve({error: String(e)});
                    }
                });
            });
        }""")
        print(f"installFreeSSL result: {ssl_result}")
        page.wait_for_timeout(5000)

        page.screenshot(path='/tmp/zoho-ssl-install.png')
        print("Screenshot: /tmp/zoho-ssl-install.png")

        # Wait for SSL
        print("Waiting 90 seconds for SSL to install...")
        page.wait_for_timeout(90000)

        # Check SSL status
        page.evaluate("""() => {
            window.__ssl = null;
            window.$X.get({
                url: '/zs-site/api/v1/ssl',
                headers: window.app.getHeaders(),
                success: function(r) { window.__ssl = r; },
                error: function(e) { window.__ssl = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(6000)
        ssl_status = page.evaluate("window.__ssl || null")
        print(f"SSL status: {json.dumps(ssl_status)[:500] if ssl_status else '(null)'}")

        # Step 4: Publish
        print(f"\n=== Step 4: Publishing ===")
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

    # Step 5: Wait and check live site
    print("\nWaiting 30 seconds...")
    time.sleep(30)

    print("\n=== Live site check ===")
    for url in ['https://www.butlerbutton.co/', 'https://www.butlerbutton.co/home',
                'https://www.butlerbutton.co/concierge']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', url], capture_output=True, text=True, timeout=20)
        print(f"  GET {url}: {r.stdout}")

    print("\n\nAll API responses:")
    for url, r in sorted(all_responses.items()):
        if any(k in url.lower() for k in ['domain', 'ssl', 'publish', 'mark']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:600]}")


if __name__ == '__main__':
    main()
