"""
1. Screenshot the domains page to see what's actually visible
2. Read domain list HTML fully
3. Try POST /domains with www.butlerbutton.co (longer wait for result)
4. Check if any domain recovery options exist
5. Try markPrimary on www via CDN-level URL (if domain still CDN-active)
"""
import json, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'
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
        if 'zs-site/api' in resp.url:
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
                  wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        page.screenshot(path='/tmp/zoho-47-domains-page.png')
        print("Screenshot saved: /tmp/zoho-47-domains-page.png")

        # Read the page text
        page_text = page.locator('body').inner_text()
        print("\n=== Domain page text ===")
        for line in page_text.split('\n'):
            l = line.strip()
            if l:
                print(f"  {l}")

        # Check if window.$X and window.app are available
        js_ready = page.evaluate("""() => {
            return typeof window.$X === 'object' && typeof window.app === 'object';
        }""")
        print(f"\nJS ready: {js_ready}")

        if not js_ready:
            print("JS not ready, waiting...")
            try:
                page.wait_for_function(
                    "typeof window.$X==='object' && typeof window.app==='object'",
                    timeout=20000)
                print("JS now ready")
            except Exception as e:
                print(f"JS still not ready: {e}")
                browser.close()
                return

        page.wait_for_timeout(2000)

        # Get domain list with extended timeout
        page.evaluate("""() => {
            window.__doms = 'pending';
            window.$X.get({
                url: '/zs-site/api/v1/domains?is_ssl_info_needed=true',
                headers: window.app.getHeaders(),
                success: function(r) { window.__doms = r; },
                error: function(e) { window.__doms = {error: String(e), type: 'error'}; },
            });
        }""")

        # Wait up to 30 seconds for the result
        for i in range(6):
            page.wait_for_timeout(5000)
            result = page.evaluate("window.__doms")
            if result and result != 'pending':
                break
            print(f"  Still waiting for domain list ({(i+1)*5}s)...")

        print("\n=== Domain list from API ===")
        if result and result != 'pending':
            if 'domain_list' in result:
                for d in result['domain_list']:
                    print(f"  {d.get('domain_name')} id={d.get('domain_id')} primary={d.get('primary_domain')}")
                    print(f"    verified={d.get('verified')} vs={d.get('verification_status')} dns={d.get('dns_status')}")
                    print(f"    domain_type={d.get('domain_type')} ssl_status={d.get('ssl_status')}")
                    print(f"    is_zoho_verified={d.get('is_zoho_verified')}")
            else:
                print(f"  Result: {json.dumps(result)[:400]}")
        else:
            print(f"  Timed out - result: {result}")

        # Try reading the full DOM for domain entries
        dom_entries = page.evaluate("""() => {
            // Look for all domain entries in the page
            var entries = [];
            var rows = document.querySelectorAll('[data-domain-id], [id*="-primary"], [id*="-trash"], [id*="-ssl"]');
            var ids = new Set();
            for (var el of rows) {
                var domainId = el.getAttribute('data-domain-id') ||
                               el.id.replace(/-primary|-trash|-ssl.*$/, '');
                if (domainId && !ids.has(domainId)) {
                    ids.add(domainId);
                    var nameEl = el.closest('[class*="row"], [class*="grid"]')?.querySelector('[class*="domain-name"], span, p');
                    entries.push({
                        domainId: domainId,
                        name: nameEl?.textContent?.trim(),
                        classes: el.closest('[class*="row"], [class*="grid"]')?.className,
                    });
                }
            }
            return entries;
        }""")
        print(f"\n=== DOM domain entries ===")
        for e in dom_entries:
            print(f"  {e}")

        # Try POST /domains for www.butlerbutton.co (with 15s wait)
        print("\n=== Try POST /domains (extended wait) ===")
        page.evaluate("""() => {
            window.__addWww2 = 'pending';
            window.$X.post({
                url: '/zs-site/api/v1/domains',
                headers: window.app.getHeaders(),
                bodyJSON: {domain_name: 'www.butlerbutton.co', domain_type: 1},
                success: function(r) { window.__addWww2 = r; },
                error: function(e) { window.__addWww2 = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(15000)
        add2 = page.evaluate("window.__addWww2")
        if add2 and add2 != 'pending':
            print(f"  Result: {json.dumps(add2)[:400]}")

        # Check network capture
        add_url = f"{BASE}/zs-site/api/v1/domains"
        if add_url in all_responses:
            net = all_responses[add_url]
            print(f"  Network: HTTP {net['status']} {net['body'][:400]}")

        # Try POST /domains with domain_name WITHOUT www (butlerbutton.co is apex, probably won't work)
        # but let's try: maybe Zoho treats sub-prefix differently

        # More importantly: find the root cause. What does the publish response say NOW?
        print("\n=== Current publish status ===")
        page.evaluate("""() => {
            window.__pubStatus = 'pending';
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__pubStatus = r; },
                error: function(e) { window.__pubStatus = {error: String(e)}; },
            });
        }""")
        for i in range(4):
            page.wait_for_timeout(5000)
            pub = page.evaluate("window.__pubStatus")
            if pub and pub != 'pending':
                break
        if pub and pub != 'pending':
            print(f"  Publish: {json.dumps(pub)[:400]}")
        else:
            pub_url = f"{BASE}/zs-site/api/v1/publish"
            if pub_url in all_responses:
                print(f"  Network: HTTP {all_responses[pub_url]['status']} {all_responses[pub_url]['body'][:400]}")

        # Check sub_site_tree
        site_data = page.evaluate("""() => {
            var d = window.app && window.app.data;
            if (!d) return null;
            return {
                content_state: d.sub_site_tree?.content_state,
                last_published_time: d.sub_site_tree?.last_published_time,
                isSitePublished: d.isSitePublished,
                publishedDomain: d.publishedDomain,
            };
        }""")
        print(f"\n=== Site state ===")
        print(f"  {json.dumps(site_data)}")

        # Try setting www.butlerbutton.co as primary via markPrimary with old ID
        # (in case the domain is still in CDN and has an ID we can find)
        # From script 38: old www ID was 625000009337247 (deleted)
        # Try anyway - if CDN has it, markPrimary might reactivate it
        print("\n=== Try markPrimary on old www ID (625000009337247) ===")
        page.evaluate("""() => {
            window.__mpOld = 'pending';
            window.$X.get({
                url: '/zs-site/api/v1/domains/625000009337247/markPrimary',
                headers: window.app.getHeaders(),
                success: function(r) { window.__mpOld = r; },
                error: function(e) { window.__mpOld = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(10000)
        mp_old = page.evaluate("window.__mpOld")
        if mp_old and mp_old != 'pending':
            print(f"  markPrimary old ID: {json.dumps(mp_old)[:300]}")
        mp_url = f"{BASE}/zs-site/api/v1/domains/625000009337247/markPrimary"
        if mp_url in all_responses:
            print(f"  Network: HTTP {all_responses[mp_url]['status']} {all_responses[mp_url]['body'][:300]}")

        browser.close()

    print("\n=== Live site check ===")
    for url in ['https://butlerbutton.zohosites.in/', 'https://butlerbutton.zohosites.in/home',
                'https://www.butlerbutton.co/', 'https://www.butlerbutton.co/home']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', url], capture_output=True, text=True, timeout=20)
        print(f"  GET {url}: {r.stdout}")


if __name__ == '__main__':
    main()
