"""
Find the native Zoho subdomain for this site, try accessing site via native URL,
inspect the 404 body from live site, and get full site record.
"""
import json, subprocess
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

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(2000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # 1. Get full site/app data
        app_data = page.evaluate("JSON.stringify(window.app && window.app.data || {})")
        data = json.loads(app_data)
        print("app.data keys:", list(data.keys()))
        for k in ['site_url', 'publishedDomain', 'zohosite_url', 'subDomain', 'sub_domain',
                  'site_subdomain', 'native_domain', 'hosting_domain', 'hosting_cName',
                  'domainName', 'siteName', 'site_name', 'zoho_domain']:
            if k in data:
                print(f"  {k}: {data[k]}")

        # 2. GET /sites to list all sites
        page.evaluate("""() => {
            window.$X.get({
                url: '/zs-site/api/v1/sites',
                headers: window.app.getHeaders(),
                success: function(r) { window.__sites = r; },
                error: function(e) { window.__sites = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(6000)
        sites = page.evaluate("window.__sites || null")
        print(f"\nGET /sites: {json.dumps(sites)[:800] if sites else '(null)'}")

        # 3. GET /sites/{SITE_ID} for full site record
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/sites/{SITE_ID}',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__siteRec = r; }},
                error: function(e) {{ window.__siteRec = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(6000)
        site_rec = page.evaluate("window.__siteRec || null")
        print(f"\nGET /sites/{SITE_ID}: {json.dumps(site_rec)[:1000] if site_rec else '(null)'}")

        # 4. GET domains list to check all domain entries
        page.evaluate("""() => {
            window.$X.get({
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) { window.__domains = r; },
                error: function(e) { window.__domains = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(6000)
        domains = page.evaluate("window.__domains || null")
        print(f"\nDomain list:")
        if domains and 'domain_list' in domains:
            for d in domains['domain_list']:
                print(f"  id={d.get('domain_id')} name={d.get('domain_name')} primary={d.get('primary_domain')} "
                      f"verified={d.get('verified')} zoho_verified={d.get('is_zoho_verified')} "
                      f"type={d.get('domain_type')} status={d.get('verification_status')}")
        else:
            print(f"  {json.dumps(domains)[:400] if domains else '(null)'}")

        # 5. Check app.data for zohosite subdomain info
        zoho_sub = page.evaluate("""() => {
            var appD = window.app && window.app.data || {};
            // Search for anything with 'zoho' or 'sub' in the key
            var result = {};
            Object.keys(appD).forEach(function(k) {
                if (k.toLowerCase().includes('zoho') || k.toLowerCase().includes('sub') ||
                    k.toLowerCase().includes('domain') || k.toLowerCase().includes('url') ||
                    k.toLowerCase().includes('host') || k.toLowerCase().includes('site')) {
                    result[k] = appD[k];
                }
            });
            return result;
        }""")
        print(f"\napp.data URL/domain/site fields: {json.dumps(zoho_sub, indent=2)[:1500]}")

        browser.close()

    # 6. Inspect live 404 response body
    print("\n\n=== Live site curl checks ===")
    for url in ['https://www.butlerbutton.co/', 'https://www.butlerbutton.co/concierge',
                'https://www.butlerbutton.co/index']:
        result = subprocess.run(
            ['curl', '-sv', '--max-time', '15', '-L', url],
            capture_output=True, text=True, timeout=20
        )
        status_line = next((l for l in result.stderr.split('\n') if '< HTTP/' in l), 'unknown')
        body_preview = result.stdout[:400] if result.stdout else '(empty)'
        print(f"\n  {url}")
        print(f"  Status: {status_line.strip()}")
        print(f"  Body: {body_preview}")

    # Network responses
    print("\n\nAll captured API responses:")
    for url, r in sorted(all_responses.items()):
        if any(k in url for k in ['sites/', 'domain', 'subsite']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:600]}")


if __name__ == '__main__':
    main()
