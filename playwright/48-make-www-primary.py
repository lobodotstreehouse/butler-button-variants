"""
www.butlerbutton.co is back in domain list (ID ~625000009337250).
1. Find the "Make primary" button for www.butlerbutton.co
2. Click it
3. Publish
4. Install SSL for www if needed
5. Verify content serving
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
        browser = pw.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(3000)

        # Find the domain ID for www.butlerbutton.co
        www_domain_id = page.evaluate("""() => {
            var els = document.querySelectorAll('[id$="-primary"]');
            for (var el of els) {
                // Check if this "make primary" is for www.butlerbutton.co
                var row = el.closest('[class*="row"], [class*="grid"], li, tr');
                if (row && row.textContent.includes('www.butlerbutton.co')) {
                    return el.id.replace(/-primary$/, '');
                }
            }
            // Try data-domain-name
            var el2 = document.querySelector('[data-domain-name="www.butlerbutton.co"]');
            if (el2) {
                return el2.id.replace(/-primary$|-trash$/, '');
            }
            return null;
        }""")
        print(f"www.butlerbutton.co domain ID: {www_domain_id}")

        if not www_domain_id:
            # Try to find all domain rows
            all_rows = page.evaluate("""() => {
                var results = [];
                var rows = document.querySelectorAll('[id$="-primary"]');
                for (var el of rows) {
                    var row = el.closest('[class*="row"], [class*="grid"], li, tr, div');
                    results.push({
                        id: el.id,
                        rowText: row?.textContent?.trim()?.substring(0, 100),
                        dataName: el.getAttribute('data-domain-name'),
                    });
                }
                return results;
            }""")
            print(f"All Make Primary buttons: {json.dumps(all_rows, indent=2)}")

            # Look for www.butlerbutton.co in these
            for row in all_rows:
                if row.get('rowText') and 'www.butlerbutton.co' in row.get('rowText', ''):
                    www_domain_id = row['id'].replace('-primary', '')
                    print(f"Found www ID from row text: {www_domain_id}")
                    break
                if row.get('dataName') == 'www.butlerbutton.co':
                    www_domain_id = row['id'].replace('-primary', '')
                    print(f"Found www ID from data-domain-name: {www_domain_id}")
                    break

        if not www_domain_id:
            # Try a different approach - find all elements with www.butlerbutton.co text
            www_elements = page.evaluate("""() => {
                var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                var results = [];
                while (walker.nextNode()) {
                    if (walker.currentNode.textContent.trim() === 'www.butlerbutton.co') {
                        var parent = walker.currentNode.parentElement;
                        var container = parent;
                        // Walk up to find domain ID
                        for (var i = 0; i < 5; i++) {
                            container = container.parentElement;
                            if (!container) break;
                            var primaryBtn = container.querySelector('[id$="-primary"]');
                            if (primaryBtn) {
                                results.push({
                                    id: primaryBtn.id,
                                    domainId: primaryBtn.id.replace(/-primary$/, ''),
                                    dataDomainName: primaryBtn.getAttribute('data-domain-name'),
                                });
                                break;
                            }
                        }
                    }
                }
                return results;
            }""")
            print(f"www elements: {json.dumps(www_elements)}")
            if www_elements:
                www_domain_id = www_elements[0]['domainId']
                print(f"Using domain ID: {www_domain_id}")

        if not www_domain_id:
            print("Could not find www.butlerbutton.co domain ID - checking all domain IDs")
            # Last resort: try known IDs
            # From script 47: new IDs are 625000009337250 and 625000009337251
            # butlerbutton.zohosites.in is likely 625000009337250 (primary)
            # www.butlerbutton.co is likely 625000009337251 (secondary)
            # butlerbutton.co might be 625000009337252 or similar
            page.evaluate("""() => {
                window.__domsCheck = 'pending';
                window.$X.get({
                    url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                    headers: window.app.getHeaders(),
                    success: function(r) { window.__domsCheck = r; },
                    error: function(e) { window.__domsCheck = {error: String(e)}; },
                });
            }""")
            for _ in range(4):
                page.wait_for_timeout(5000)
                r = page.evaluate("window.__domsCheck")
                if r and r != 'pending':
                    break
            if r and r != 'pending' and 'domain_list' in r:
                print("Domain list:")
                for d in r['domain_list']:
                    print(f"  {d.get('domain_name')} id={d.get('domain_id')} primary={d.get('primary_domain')}")
                    if d.get('domain_name') == 'www.butlerbutton.co':
                        www_domain_id = d['domain_id']
                        print(f"  ^ WWW ID: {www_domain_id}")

        if www_domain_id:
            print(f"\n=== Making www.butlerbutton.co (ID: {www_domain_id}) primary ===")

            # Method 1: Click the UI button (use attribute selector - ID starts with digit)
            btn_visible = page.evaluate(f"""() => {{
                var btn = document.getElementById('{www_domain_id}-primary');
                return btn ? btn.offsetParent !== null : false;
            }}""")
            if btn_visible:
                print("Clicking Make Primary button in UI...")
                page.evaluate(f"document.getElementById('{www_domain_id}-primary').click()")
                page.wait_for_timeout(8000)
                page.screenshot(path='/tmp/zoho-48-after-primary.png')
            else:
                # Method 2: Call markPrimary API directly
                print("UI button not found/visible, calling markPrimary API...")
                page.evaluate(f"""() => {{
                    window.__mp = 'pending';
                    window.$X.get({{
                        url: '/zs-site/api/v1/domains/{www_domain_id}/markPrimary',
                        headers: window.app.getHeaders(),
                        success: function(r) {{ window.__mp = r; }},
                        error: function(e) {{ window.__mp = {{error: String(e)}}; }},
                    }});
                }}""")
                page.wait_for_timeout(10000)
                mp = page.evaluate("window.__mp")
                print(f"markPrimary result: {json.dumps(mp)[:300] if mp and mp != 'pending' else mp}")

            # Check domain list after making primary
            page.evaluate("""() => {
                window.__domsAfter = 'pending';
                window.$X.get({
                    url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                    headers: window.app.getHeaders(),
                    success: function(r) { window.__domsAfter = r; },
                    error: function(e) { window.__domsAfter = {error: String(e)}; },
                });
            }""")
            for _ in range(4):
                page.wait_for_timeout(5000)
                da = page.evaluate("window.__domsAfter")
                if da and da != 'pending':
                    break
            if da and da != 'pending' and 'domain_list' in da:
                print("\nDomain list after making primary:")
                for d in da['domain_list']:
                    print(f"  {d.get('domain_name')} id={d.get('domain_id')} primary={d.get('primary_domain')}")

            # Publish with www.butlerbutton.co as primary
            print("\n=== Publishing ===")
            page.evaluate("""() => {
                window.__pub = 'pending';
                window.$X.post({
                    url: '/zs-site/api/v1/publish',
                    headers: window.app.getHeaders(),
                    bodyJSON: {},
                    success: function(r) { window.__pub = r; },
                    error: function(e) { window.__pub = {error: String(e)}; },
                });
            }""")
            for _ in range(4):
                page.wait_for_timeout(5000)
                pub = page.evaluate("window.__pub")
                if pub and pub != 'pending':
                    break
            pub_url = f"{BASE}/zs-site/api/v1/publish"
            if pub and pub != 'pending':
                print(f"  Publish result: {json.dumps(pub)[:500]}")
            elif pub_url in all_responses:
                print(f"  Network: {all_responses[pub_url]['body'][:500]}")
            else:
                print(f"  Result still pending")

            # Wait then check live
            print("\nWaiting 30 seconds for CDN propagation...")
            page.wait_for_timeout(30000)

        browser.close()

    print("\n=== Live site check ===")
    for url in ['https://www.butlerbutton.co/', 'https://www.butlerbutton.co/home',
                'https://butlerbutton.zohosites.in/', 'https://butlerbutton.zohosites.in/home']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', url], capture_output=True, text=True, timeout=20)
        print(f"  GET {url}: {r.stdout}")


if __name__ == '__main__':
    main()
