"""
1. Check full domain list + verification status
2. Try to verify butlerbutton.zohosites.in via POST /domains/verify
3. Retry POST /domains to add www.butlerbutton.co (cooldown may have cleared)
4. Check visual editor preview URL for content
5. Try force-publish via UI editor 'Publish' button path
"""
import json, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'
HOME_PAGE_ID = '413198000000004653'
WWW_DOMAIN = 'www.butlerbutton.co'
ZOHO_DOMAIN_ID = '625000009337249'  # butlerbutton.zohosites.in


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
        if 'zs-site/api' in resp.url or 'sitebuilder' in resp.url:
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
        page.wait_for_timeout(2000)

        # 1. Full domain list with all fields
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
        print("=== Current domain list ===")
        if doms and 'domain_list' in doms:
            for d in doms['domain_list']:
                print(f"  {d.get('domain_name')} id={d.get('domain_id')}")
                print(f"    primary={d.get('primary_domain')} verified={d.get('verified')}")
                print(f"    verification_status={d.get('verification_status')} dns_status={d.get('dns_status')}")
                print(f"    is_zoho_verified={d.get('is_zoho_verified')} ssl={d.get('ssl_status')}")
                print(f"    domain_type={d.get('domain_type')}")
        else:
            print(f"  Error: {json.dumps(doms)[:200]}")

        # 2. Try verify butlerbutton.zohosites.in
        print("\n=== Verify butlerbutton.zohosites.in ===")
        page.evaluate(f"""() => {{
            window.__verify = null;
            window.$X.post({{
                url: '/zs-site/api/v1/domains/verify',
                headers: window.app.getHeaders(),
                bodyJSON: {{subsite_id: '{SITE_ID}', domain_id: '{ZOHO_DOMAIN_ID}'}},
                success: function(r) {{ window.__verify = r; }},
                error: function(e) {{ window.__verify = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(6000)
        verify_result = page.evaluate("window.__verify || null")
        print(f"  Verify result: {json.dumps(verify_result)[:300] if verify_result else '(null)'}")

        # 3. Retry adding www.butlerbutton.co
        print("\n=== Retry add www.butlerbutton.co ===")
        page.evaluate(f"""() => {{
            window.__addWww = null;
            window.$X.post({{
                url: '/zs-site/api/v1/domains',
                headers: window.app.getHeaders(),
                bodyJSON: {{domain_name: 'www.butlerbutton.co', domain_type: 1}},
                success: function(r) {{ window.__addWww = r; }},
                error: function(e) {{ window.__addWww = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(8000)
        add_result = page.evaluate("window.__addWww || null")
        print(f"  Add www result: {json.dumps(add_result)[:400] if add_result else '(null)'}")

        # Check network for the add domain response
        add_url = f"{BASE}/zs-site/api/v1/domains"
        if add_url in all_responses:
            net = all_responses[add_url]
            print(f"  Network: HTTP {net['status']} {net['body'][:400]}")

        new_www_id = None
        if add_result and add_result.get('status_code') == '0':
            for d in add_result.get('domain_list', []):
                if d.get('domain_name') == 'www.butlerbutton.co':
                    new_www_id = d['domain_id']
                    print(f"  SUCCESS! www.butlerbutton.co ID: {new_www_id}")
                    break

        # 4. Try using UI mapDomainForm if API failed
        if not new_www_id:
            print("\n=== Try UI mapDomainForm ===")
            # Click Add Domain via JS
            page.evaluate("""() => {
                var btn = document.querySelector('#zp_adddomainbtn, [id*="adddomainbtn"]');
                if (btn) { btn.click(); return 'clicked ' + btn.id; }
                // Try all buttons
                var btns = document.querySelectorAll('button, a, li');
                for (var b of btns) {
                    if (b.textContent.trim().toLowerCase() === 'add domain' ||
                        b.textContent.trim().toLowerCase() === '+ add domain') {
                        b.click(); return 'clicked text: ' + b.textContent.trim();
                    }
                }
                return 'not found';
            }""")
            page.wait_for_timeout(3000)
            page.screenshot(path='/tmp/zoho-46-add-dialog.png')

            # Check what's visible
            dialog_html = page.evaluate("""() => {
                var d = document.querySelector('#domainDialogDiv, .hb-dialog-overlay, [class*="domain-dialog"]');
                if (!d || d.offsetParent === null) {
                    // Try to find any visible dialog
                    var all = document.querySelectorAll('[class*="dialog"], [class*="modal"]');
                    for (var el of all) {
                        if (el.offsetParent !== null) return el.outerHTML.substring(0, 3000);
                    }
                    return 'no dialog found';
                }
                return d.outerHTML.substring(0, 3000);
            }""")
            print(f"  Dialog: {dialog_html[:500]}")

            # Try the mapDomainForm - show configureDomainDiv
            page.evaluate("""() => {
                var configure = document.getElementById('configureDomainDiv');
                if (configure) {
                    configure.style.display = '';
                    configure.style.visibility = 'visible';
                }
                var mapForm = document.getElementById('mapDomainForm');
                if (mapForm) {
                    mapForm.style.display = '';
                    mapForm.style.visibility = 'visible';
                }
                var inp = document.getElementById('zp_mapDomainName');
                if (inp) {
                    inp.value = 'www.butlerbutton.co';
                    inp.dispatchEvent(new Event('input', {bubbles: true}));
                    inp.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }""")
            page.wait_for_timeout(1000)

            # Check if the input is now filled
            map_input_state = page.evaluate("""() => {
                var inp = document.getElementById('zp_mapDomainName');
                if (!inp) return 'not found';
                return {value: inp.value, visible: inp.offsetParent !== null, disabled: inp.disabled};
            }""")
            print(f"  mapDomainName state: {map_input_state}")

            # Try the old form too
            page.evaluate("""() => {
                var customDiv = document.getElementById('customDomainDiv');
                if (customDiv) {
                    customDiv.style.display = '';
                    customDiv.style.visibility = 'visible';
                }
                var inp = document.getElementById('zp_exsdomainame');
                if (inp) {
                    inp.value = 'www.butlerbutton.co';
                    inp.dispatchEvent(new Event('input', {bubbles: true}));
                    inp.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }""")
            page.wait_for_timeout(1000)

            old_input_state = page.evaluate("""() => {
                var inp = document.getElementById('zp_exsdomainame');
                if (!inp) return 'not found';
                return {value: inp.value, visible: inp.offsetParent !== null, disabled: inp.disabled};
            }""")
            print(f"  zp_exsdomainame state: {old_input_state}")

            # Click any submit button in the domain form
            btn_result = page.evaluate("""() => {
                // Try multiple approaches
                var btn = document.getElementById('zp_existingdombtn');
                if (btn) { btn.removeAttribute('disabled'); btn.click(); return 'clicked zp_existingdombtn'; }
                btn = document.querySelector('#mapDomainForm button[type="submit"], #mapDomainForm button');
                if (btn) { btn.removeAttribute('disabled'); btn.click(); return 'clicked mapDomainForm btn'; }
                return 'no button found';
            }""")
            print(f"  Button click result: {btn_result}")
            page.wait_for_timeout(8000)

            # Check if domain was added
            page.evaluate("""() => {
                window.__domsAfter = null;
                window.$X.get({
                    url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                    headers: window.app.getHeaders(),
                    success: function(r) { window.__domsAfter = r; },
                    error: function(e) { window.__domsAfter = {error: String(e)}; },
                });
            }""")
            page.wait_for_timeout(6000)
            doms_after = page.evaluate("window.__domsAfter || null")
            print("\nDomains after UI attempt:")
            if doms_after and 'domain_list' in doms_after:
                for d in doms_after['domain_list']:
                    print(f"  {d.get('domain_name')} id={d.get('domain_id')} primary={d.get('primary_domain')}")
                    if d.get('domain_name') == 'www.butlerbutton.co':
                        new_www_id = d['domain_id']
                        print(f"  WWW FOUND! ID: {new_www_id}")

        # 5. Check the page visual editor preview
        print("\n=== Check page preview URL ===")
        page.goto(f"{BASE}/zcms/{SITE_ID}/page/{HOME_PAGE_ID}",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)
        page.screenshot(path='/tmp/zoho-46-editor.png')

        # Get any preview/CDN URL from the editor
        preview_url = page.evaluate("""() => {
            if (window.app && window.app.data) {
                return {
                    previewUrl: window.app.data.previewUrl,
                    publishedUrl: window.app.data.publishedUrl,
                    siteCdnUrl: window.app.data.siteCdnUrl,
                    siteBaseUrl: window.app.data.siteBaseUrl,
                    liveUrl: window.app.data.liveUrl,
                };
            }
            return null;
        }""")
        print(f"  Preview/CDN URLs: {json.dumps(preview_url)}")

        # 6. If www was added, do the full flow
        if new_www_id:
            print(f"\n=== www.butlerbutton.co added (ID: {new_www_id}), running full flow ===")
            page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                      wait_until='networkidle', timeout=45000)
            page.wait_for_timeout(3000)
            page.wait_for_function(
                "typeof window.$X==='object' && typeof window.app==='object'",
                timeout=30000)
            page.wait_for_timeout(2000)

            # Verify the domain
            page.evaluate(f"""() => {{
                window.__verify2 = null;
                window.$X.post({{
                    url: '/zs-site/api/v1/domains/verify',
                    headers: window.app.getHeaders(),
                    bodyJSON: {{subsite_id: '{SITE_ID}', domain_id: '{new_www_id}'}},
                    success: function(r) {{ window.__verify2 = r; }},
                    error: function(e) {{ window.__verify2 = {{error: String(e)}}; }},
                }});
            }}""")
            page.wait_for_timeout(6000)
            verify2 = page.evaluate("window.__verify2 || null")
            print(f"  Verify www: {json.dumps(verify2)[:300] if verify2 else '(null)'}")

            # Mark as primary
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
            mp = page.evaluate("window.__mp || null")
            print(f"  markPrimary: {json.dumps(mp)[:200] if mp else '(null)'}")

            # Publish
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
            print(f"  Publish: {json.dumps(pub)[:400] if pub else '(null)'}")

        browser.close()

    print("\n=== Live site check ===")
    for url in ['https://butlerbutton.zohosites.in/', 'https://butlerbutton.zohosites.in/home',
                'https://www.butlerbutton.co/', 'https://www.butlerbutton.co/home']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', url], capture_output=True, text=True, timeout=20)
        print(f"  GET {url}: {r.stdout}")


if __name__ == '__main__':
    main()
