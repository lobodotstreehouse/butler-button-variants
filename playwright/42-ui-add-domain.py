"""
Use the actual UI button to open Add Domain dialog.
Navigate to custom domain section, fill in www.butlerbutton.co,
capture what API gets called on submit.
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

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=300)
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

        # Click the button with id=zp_adddomainbtn
        print("Clicking zp_adddomainbtn...")
        add_btn = page.locator('#zp_adddomainbtn')
        if add_btn.is_visible():
            add_btn.click()
        else:
            # Try calling showAddDomain directly
            page.evaluate("""() => {
                require(['domains'], function(d) { d.showAddDomain(); });
            }""")
        page.wait_for_timeout(3000)
        page.screenshot(path='/tmp/zoho-add-dialog-open.png')
        print("Screenshot: /tmp/zoho-add-dialog-open.png")

        # Check dialog state
        dialog_open = page.locator('#domainDialogDiv').is_visible()
        print(f"Dialog open: {dialog_open}")

        if not dialog_open:
            print("Dialog not open via button, trying JS...")
            page.evaluate("""() => {
                require(['domains'], function(d) { d.showAddDomain(false, false, false); });
            }""")
            page.wait_for_timeout(3000)
            dialog_open = page.locator('#domainDialogDiv').is_visible()
            print(f"Dialog open (JS): {dialog_open}")

        # Navigate to custom domain section
        # First, check what's visible in the dialog
        if dialog_open:
            dialog_text = page.locator('#domainDialogDiv').inner_text()
            print(f"\nDialog text:\n{dialog_text[:800]}")

            # Click "Continue" under "Map a domain" section
            # This button is in the customDomainDiv section header
            continue_btns = page.locator('button:has-text("Continue"), [id*="continue"], '
                                         '.h-continue').all()
            for btn in continue_btns:
                if btn.is_visible():
                    txt = btn.inner_text()
                    print(f"Found Continue button: '{txt}'")
                    btn.click()
                    page.wait_for_timeout(3000)
                    break

            page.screenshot(path='/tmp/zoho-add-after-continue.png')
            print("Screenshot: /tmp/zoho-add-after-continue.png")

        # Look at the full dialog HTML to find the custom domain section
        custom_div_html = page.evaluate("""() => {
            var d = document.getElementById('customDomainDiv');
            if (d) return {
                style: d.style.display,
                html: d.outerHTML.substring(0, 3000),
            };
            // Search for any input with domain-related placeholder
            var inputs = document.querySelectorAll('input');
            var found = [];
            for (var inp of inputs) {
                if (inp.placeholder?.toLowerCase().includes('domain') ||
                    inp.placeholder?.toLowerCase().includes('www') ||
                    inp.id?.toLowerCase().includes('custom')) {
                    found.push({
                        id: inp.id,
                        placeholder: inp.placeholder,
                        visible: inp.offsetParent !== null,
                        disabled: inp.disabled,
                    });
                }
            }
            return {inputs: found};
        }""")
        print(f"\ncustomDomainDiv: {json.dumps(custom_div_html, indent=2)[:2000]}")

        # Show the custom domain section if it's hidden
        page.evaluate("""() => {
            var d = document.getElementById('customDomainDiv');
            if (d) {
                d.style.display = '';
                d.style.visibility = 'visible';
            }
            var subDiv = document.getElementById('subDomainDiv');
            if (subDiv) subDiv.style.display = 'none';
        }""")
        page.wait_for_timeout(1000)
        page.screenshot(path='/tmp/zoho-custom-domain-section.png')
        print("Screenshot: /tmp/zoho-custom-domain-section.png")

        # Now get all inputs in the customDomainDiv
        custom_inputs = page.evaluate("""() => {
            var d = document.getElementById('customDomainDiv');
            if (!d) return [];
            var inputs = d.querySelectorAll('input, button');
            return Array.from(inputs).map(el => ({
                tag: el.tagName,
                id: el.id,
                type: el.type,
                placeholder: el.placeholder,
                class: el.className,
                disabled: el.disabled,
                value: el.value,
            }));
        }""")
        print(f"\ncustomDomainDiv inputs/buttons: {json.dumps(custom_inputs, indent=2)}")

        # Try to find and fill the custom domain input
        domain_input_id = None
        for el in custom_inputs:
            if el.get('tag') == 'INPUT' and el.get('type') in ['text', None, '']:
                domain_input_id = el.get('id')
                break

        if domain_input_id:
            print(f"\nFilling input #{domain_input_id} with www.butlerbutton.co...")
            page.locator(f'#{domain_input_id}').fill('www.butlerbutton.co')
            page.wait_for_timeout(2000)

            # Enable and click submit button
            page.evaluate(f"""() => {{
                var d = document.getElementById('customDomainDiv');
                if (d) {{
                    var btns = d.querySelectorAll('button');
                    btns.forEach(function(b) {{
                        b.removeAttribute('disabled');
                    }});
                }}
            }}""")

            # Find submit button
            submit_btn = None
            for el in custom_inputs:
                if el.get('tag') == 'BUTTON':
                    submit_btn = page.locator(f'#{el.get("id")}') if el.get('id') else None
                    break

            if submit_btn and submit_btn.is_visible():
                print(f"Clicking submit...")
                submit_btn.click()
                page.wait_for_timeout(8000)
                page.screenshot(path='/tmp/zoho-after-submit.png')

        # Check what happened
        page.wait_for_timeout(3000)
        dialog_text_after = page.locator('body').inner_text()
        print(f"\nPage text after submit:\n{dialog_text_after[:2000]}")

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
        print(f"\nFinal domain list:")
        new_www_id = None
        if doms and 'domain_list' in doms:
            for d in doms['domain_list']:
                print(f"  {d['domain_name']} id={d['domain_id']} primary={d['primary_domain']} "
                      f"verified={d['verified']} vs={d.get('verification_status')}")
                if d['domain_name'] == 'www.butlerbutton.co':
                    new_www_id = d['domain_id']

        browser.close()

    print(f"\nNew www.butlerbutton.co ID: {new_www_id}")

    print("\n\nAll captured API responses:")
    for url, r in sorted(all_responses.items()):
        if any(k in url.lower() for k in ['domain', 'add', 'custom']):
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:600]}")


if __name__ == '__main__':
    main()
