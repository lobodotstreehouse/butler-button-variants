"""
Try POST /domains/{id}/markPrimary with skip_check: true (the non-default code path).
Also try deleting + re-adding the domain.
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
        browser = pw.chromium.launch(headless=False, slow_mo=50)
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

        # POST markPrimary with skip_check: true
        print(f"POST /domains/{DOMAIN_ID}/markPrimary skip_check=true...")
        page.evaluate(f"""() => {{
            window.$X.post({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID}/markPrimary',
                headers: window.app.getHeaders(),
                bodyJSON: {{skip_check: true}},
                success: function(r) {{ window.__mps = r; }},
                error: function(e) {{ window.__mps = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(8000)
        mps = page.evaluate("window.__mps || null")
        print(f"POST markPrimary skip_check: {json.dumps(mps)[:500] if mps else '(null)'}")

        # Try DELETE + re-add domain
        print(f"\nDELETING domain {DOMAIN_ID}...")
        page.evaluate(f"""() => {{
            window.$X.delete({{
                url: '/zs-site/api/v1/domains/{DOMAIN_ID}',
                headers: window.app.getHeaders(),
                bodyJSON: {{}},
                success: function(r) {{ window.__del = r; }},
                error: function(e) {{ window.__del = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        del_result = page.evaluate("window.__del || null")
        print(f"DELETE result: {json.dumps(del_result)[:500] if del_result else '(null - check network)'}")

        # Re-add domain
        print(f"\nRe-adding domain www.butlerbutton.co...")
        page.evaluate("""() => {
            window.$X.post({
                url: '/zs-site/api/v1/domains',
                headers: window.app.getHeaders(),
                bodyJSON: {domain_name: 'www.butlerbutton.co'},
                success: function(r) { window.__add = r; },
                error: function(e) { window.__add = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(8000)
        add_result = page.evaluate("window.__add || null")
        print(f"ADD result: {json.dumps(add_result)[:800] if add_result else '(null - check network)'}")

        # Check domain list
        print("\nChecking domain list after re-add...")
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
        if doms and 'domain_list' in doms:
            for d in doms['domain_list']:
                print(f"  domain: {d['domain_name']} id={d['domain_id']} "
                      f"primary={d['primary_domain']} verified={d['verified']} "
                      f"dns={d['dns_status']} ssl={d.get('ssl_status')}")

        browser.close()

    print("\n\nAll API responses:")
    for url, r in all_responses.items():
        if any(k in url.lower() for k in ['domain', 'publish', 'primary', 'delete']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:600]}")


if __name__ == '__main__':
    main()
