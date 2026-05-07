"""
Get sub_site_url, domains from app.data, check full pages list, try preview URL,
and attempt to add a native Zoho subdomain to unlock domain swap.
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
        if 'zs-site/api' in resp.url or 'zohosites' in resp.url:
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

        # 1. Get the fields we need from app.data
        specific = page.evaluate("""() => {
            var d = window.app && window.app.data || {};
            return {
                sub_site_url: d.sub_site_url,
                sub_site_tree: d.sub_site_tree,
                sub_site_title: d.sub_site_title,
                has_sub_site: d.has_sub_site,
                domains: d.domains,
                resources: JSON.stringify(d.resources || {}).substring(0, 500),
                siteName: d.siteName,
                site_name: d.site_name,
            };
        }""")
        print(f"app.data specific fields: {json.dumps(specific, indent=2)[:2000]}")

        # 2. Get full pages list
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/pages?subsite_id={SITE_ID}',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__fullPages = r; }},
                error: function(e) {{ window.__fullPages = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(6000)
        full_pages = page.evaluate("window.__fullPages || null")
        if full_pages and 'pages_details' in full_pages:
            pages = full_pages['pages_details'].get('pages', [])
            print(f"\nAll pages ({len(pages)} total):")
            for p in pages:
                print(f"  id={p.get('resource_id')} url='{p.get('resource_url')}' "
                      f"name='{p.get('resource_name')}' type={p.get('resource_type')} "
                      f"home={p.get('home_resource_id')}")
        else:
            print(f"\nPages: {json.dumps(full_pages)[:400] if full_pages else '(null)'}")

        # 3. Try to access the site via preview URL
        # The Zoho Sites preview might be at the builder domain
        preview_urls = [
            f"{BASE}/zcms/{SITE_ID}/preview",
            f"https://sites.zoho.in/portal/veltm-tours",
            f"https://sites.zoho.in/portal/butler",
        ]
        for purl in preview_urls:
            page.goto(purl, wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(2000)
            title = page.title()
            url_now = page.url
            print(f"\nPreview URL {purl}: redirected to {url_now}, title='{title}'")

        # 4. Navigate back and check addDomain source for subdomain format
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(2000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        add_domain_fn = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    resolve({
                        addDomainKeys: Object.keys(domains).filter(k =>
                            k.toLowerCase().includes('add') || k.toLowerCase().includes('zoho') ||
                            k.toLowerCase().includes('sub') || k.toLowerCase().includes('native')
                        ),
                        addDomain: String(domains.addDomain || '').substring(0, 800),
                        addZohoDomain: String(domains.addZohoDomain || '').substring(0, 800),
                        getZohoSubdomain: String(domains.getZohoSubdomain || '').substring(0, 800),
                    });
                });
            });
        }""")
        print(f"\nDomain module add-related: {json.dumps(add_domain_fn, indent=2)[:2000]}")

        # 5. Check what the domains module knows about zohosites subdomains
        zoho_domain_info = page.evaluate("""() => {
            return new Promise(function(resolve) {
                require(['domains'], function(domains) {
                    // Get all function names
                    var allKeys = Object.keys(domains);
                    resolve({
                        allKeys: allKeys,
                        zohoDomainFn: String(domains.checkZohoDomain || domains.validateZohoDomain ||
                                             domains.addZohoSubdomain || '').substring(0, 600),
                    });
                });
            });
        }""")
        print(f"\nAll domain module keys: {zoho_domain_info.get('allKeys', [])}")

        # 6. Try accessing site via zohosites subdomain guesses
        # The site account ID is 60059075182
        # Try common patterns
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)

        # Extract the full domains page HTML to see what subdomain options exist
        domains_html = page.evaluate("""() => {
            var domainSection = document.querySelector('#zoho-sub-domain, .zoho-subdomain, [class*="zohosub"], [class*="native"]');
            if (domainSection) return domainSection.outerHTML.substring(0, 1000);
            // Get the full page text
            return document.body.innerText.substring(0, 2000);
        }""")
        print(f"\nDomains settings page text:\n{domains_html[:2000]}")

        browser.close()

    print("\n\nCaptured API responses:")
    for url, r in sorted(all_responses.items()):
        print(f"\n  HTTP {r['status']}  {url}")
        print(f"  {r['body'][:400]}")


if __name__ == '__main__':
    main()
