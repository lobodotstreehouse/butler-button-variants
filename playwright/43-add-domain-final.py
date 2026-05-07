"""
Fix strict mode error, open Add Domain dialog properly, navigate to custom domain
section, submit, capture API call. Also check why POST /domains fails.
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
        if 'zs-site/api' in req.url and 'domain' in req.url.lower():
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
        browser = pw.chromium.launch(headless=False, slow_mo=300)
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

        # First: check why POST /domains fails
        # Get the actual request headers being sent
        headers_info = page.evaluate("""() => {
            var h = window.app.getHeaders();
            return JSON.stringify(h);
        }""")
        print(f"Request headers: {headers_info[:500]}")

        # Try POST /domains with detailed error info
        page.evaluate("""() => {
            window.__addErr = null;
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/zs-site/api/v1/domains', true);
            var headers = window.app.getHeaders();
            for (var k in headers) { xhr.setRequestHeader(k, headers[k]); }
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onload = function() {
                window.__addErr = {status: xhr.status, body: xhr.responseText};
            };
            xhr.onerror = function(e) { window.__addErr = {error: 'xhr error'}; };
            xhr.send(JSON.stringify({domain_name: 'www.butlerbutton.co', domain_type: 1}));
        }""")
        page.wait_for_timeout(6000)
        err = page.evaluate("window.__addErr || null")
        print(f"\nDirect XHR result: {json.dumps(err)[:500] if err else '(null)'}")

        # Click Add Domain button using JS to avoid strict mode
        print("\n=== Opening Add Domain dialog ===")
        page.evaluate("""() => {
            var btn = document.getElementById('zp_adddomainbtn');
            if (btn) btn.click();
        }""")
        page.wait_for_timeout(3000)
        page.screenshot(path='/tmp/zoho-add-dialog-v2.png')
        print("Screenshot: /tmp/zoho-add-dialog-v2.png")

        # Check if dialog opened
        dialog_visible = page.evaluate("""() => {
            var d = document.querySelector('.hb-dialog-overlay, .domain-dialog-cntr, [id="domainDialogDiv"]');
            return d ? d.style.display !== 'none' && d.offsetParent !== null : false;
        }""")
        print(f"Dialog visible: {dialog_visible}")

        if not dialog_visible:
            # Try showAddDomain directly with proper args
            page.evaluate("""() => {
                require(['domains'], function(d) {
                    d.showAddDomain(false, false, false);
                });
            }""")
            page.wait_for_timeout(3000)
            dialog_visible = page.evaluate("""() => {
                var d = document.querySelector('.hb-dialog-overlay');
                return d ? d.offsetParent !== null : false;
            }""")
            print(f"Dialog visible (after JS call): {dialog_visible}")

        # Get dialog content
        page.wait_for_timeout(2000)
        page.screenshot(path='/tmp/zoho-add-dialog-v2-2.png')

        dialog_html = page.evaluate("""() => {
            var d = document.querySelector('.domain-dialog-cntr, #domainDialogDiv');
            return d ? d.outerHTML.substring(0, 5000) : 'not found';
        }""")
        print(f"\nDialog HTML:\n{dialog_html[:3000]}")

        # Try clicking Continue to show custom domain section
        page.evaluate("""() => {
            // Try finding the Continue button in the custom domain section
            var btns = document.querySelectorAll('button');
            for (var btn of btns) {
                if (btn.textContent.trim() === 'Continue' && btn.offsetParent !== null) {
                    btn.click();
                    return 'clicked continue: ' + btn.className;
                }
            }
            return 'continue not found';
        }""")
        page.wait_for_timeout(2000)

        # Show customDomainDiv
        page.evaluate("""() => {
            var d = document.getElementById('customDomainDiv');
            if (d) { d.style.display = 'block'; d.style.visibility = 'visible'; }
            var sub = document.getElementById('subDomainDiv');
            if (sub) sub.style.display = 'none';
        }""")
        page.wait_for_timeout(1000)

        # Get full HTML of customDomainDiv
        custom_html = page.evaluate("""() => {
            var d = document.getElementById('customDomainDiv');
            return d ? d.outerHTML : 'not found';
        }""")
        print(f"\ncustomDomainDiv HTML:\n{custom_html[:4000]}")

        # Find the input and fill it
        # Based on the HTML, the custom domain input should have id like 'zp_customdomain' or similar
        input_ids = page.evaluate("""() => {
            var d = document.getElementById('customDomainDiv');
            if (!d) return [];
            return Array.from(d.querySelectorAll('input')).map(i => ({
                id: i.id, type: i.type, placeholder: i.placeholder, class: i.className
            }));
        }""")
        print(f"\nInputs in customDomainDiv: {input_ids}")

        if input_ids:
            first_input = input_ids[0]
            input_id = first_input.get('id')
            if input_id:
                print(f"\nFilling #{input_id}...")
                page.evaluate(f"""() => {{
                    var inp = document.getElementById('{input_id}');
                    if (inp) {{
                        inp.value = 'www.butlerbutton.co';
                        inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                        inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                        inp.dispatchEvent(new Event('keyup', {{bubbles: true}}));
                    }}
                }}""")
                page.wait_for_timeout(3000)

        # Find submit button in customDomainDiv
        btns_info = page.evaluate("""() => {
            var d = document.getElementById('customDomainDiv');
            if (!d) return [];
            return Array.from(d.querySelectorAll('button')).map(b => ({
                id: b.id, type: b.type, text: b.textContent.trim(), disabled: b.disabled, class: b.className
            }));
        }""")
        print(f"\nButtons in customDomainDiv: {btns_info}")

        # Enable and click submit
        if btns_info:
            page.evaluate("""() => {
                var d = document.getElementById('customDomainDiv');
                if (d) {
                    d.querySelectorAll('button').forEach(b => { b.disabled = false; b.removeAttribute('disabled'); });
                }
            }""")

            for btn in btns_info:
                if btn.get('type') == 'submit' or btn.get('text') in ['Save', 'Add', 'Continue', 'Next', 'Map']:
                    btn_id = btn.get('id', '')
                    if btn_id:
                        print(f"Clicking button #{btn_id}: '{btn.get('text')}'")
                        page.evaluate(f"document.getElementById('{btn_id}')?.click()")
                    else:
                        print(f"Clicking button by text: '{btn.get('text')}'")
                        page.evaluate(f"""() => {{
                            var d = document.getElementById('customDomainDiv');
                            var btns = d.querySelectorAll('button');
                            for (var b of btns) {{
                                if (b.textContent.trim() === '{btn.get('text')}') {{
                                    b.click();
                                    return;
                                }}
                            }}
                        }}""")
                    page.wait_for_timeout(8000)
                    break

        page.screenshot(path='/tmp/zoho-after-domain-add.png')

        # Check result
        page.wait_for_timeout(3000)
        page.evaluate("""() => {
            window.__domsF = null;
            window.$X.get({
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) { window.__domsF = r; },
                error: function(e) { window.__domsF = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(6000)
        doms_f = page.evaluate("window.__domsF || null")
        print(f"\nFinal domains:")
        new_www_id = None
        if doms_f and 'domain_list' in doms_f:
            for d in doms_f['domain_list']:
                print(f"  {d['domain_name']} id={d['domain_id']} primary={d['primary_domain']} "
                      f"verified={d['verified']} vs={d.get('verification_status')}")
                if d['domain_name'] == 'www.butlerbutton.co':
                    new_www_id = d['domain_id']

        browser.close()

    print(f"\nNew www ID: {new_www_id}")
    print(f"\nCaptured requests to /domains:")
    for req in all_requests:
        print(f"  {req['method']} {req['url']}: {req['body'][:200]}")

    print("\nAll captured domain API responses:")
    for url, r in sorted(all_responses.items()):
        if 'domain' in url.lower():
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:600]}")


if __name__ == '__main__':
    main()
