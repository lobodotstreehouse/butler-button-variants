"""
Get full publish response, check CDN URL patterns, try page preview links,
look for content-serving layer endpoints.
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

    all_requests = {}
    all_responses = {}
    def capture_request(req):
        if 'zs-site/api' in req.url and 'publish' in req.url.lower():
            try:
                all_requests[req.url] = {'method': req.method, 'body': req.post_data}
            except Exception:
                pass
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
        page.on('request', capture_request)
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(2000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # 1. Get full publish response
        page.evaluate("""() => {
            window.__pubFull = null;
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__pubFull = r; },
                error: function(e) { window.__pubFull = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(15000)
        pub_full = page.evaluate("window.__pubFull || null")
        print(f"Full publish response: {json.dumps(pub_full, indent=2)[:2000] if pub_full else '(null)'}")

        # Check network capture of publish response
        pub_url = f"{BASE}/zs-site/api/v1/publish"
        if pub_url in all_responses:
            print(f"\nNetwork-captured publish: {all_responses[pub_url]['body'][:1000]}")

        # 2. Get CDN URL from app.data and check content URL patterns
        cdn_info = page.evaluate("""() => {
            var d = window.app && window.app.data || {};
            return {
                siteCdnUrl: d.siteCdnUrl,
                static_servers: d.static_servers,
                content_domain: d.content_domain,
                content_domain_prefix: d.content_domain_prefix,
                server_name: d.server_name,
                cdnUrl: d.cdnUrl,
                versionCdnUrl: d.versionCdnUrl,
                sigma_content_domain_suffix: d.sigma_content_domain_suffix,
            };
        }""")
        print(f"\nCDN info: {json.dumps(cdn_info, indent=2)}")

        # 3. Get page preview URL by navigating to pages list and extracting preview links
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)

        # Get all links that might be preview links
        links = page.evaluate("""() => {
            var links = document.querySelectorAll('a');
            var results = [];
            for (var l of links) {
                var href = l.href;
                if (href && (href.includes('preview') || href.includes('butlerbutton.co') ||
                             href.includes('zohosites') || href.includes('stratus'))) {
                    results.push({href: href, text: l.textContent.trim().substring(0, 50)});
                }
            }
            return results.slice(0, 20);
        }""")
        print(f"\nPreview-related links on pages view: {json.dumps(links, indent=2)}")

        # 4. Get page edit links to find preview URLs
        page_items = page.evaluate("""() => {
            // Find all page list items and their action buttons
            var items = document.querySelectorAll('[data-resource-url], [data-page-url], [class*="page-item"]');
            var results = [];
            for (var item of items) {
                var url = item.getAttribute('data-resource-url') || item.getAttribute('data-page-url') || '';
                var links = Array.from(item.querySelectorAll('a')).map(l => ({href: l.href, text: l.textContent.trim()}));
                if (url || links.length) results.push({url, links});
            }
            return results.slice(0, 5);
        }""")
        print(f"\nPage items with links: {json.dumps(page_items, indent=2)[:1000]}")

        # 5. Look for the visual preview button in page list and click it for the concierge page
        # Find any button/link that opens a preview
        preview_btn = page.locator('[class*="preview"], [title*="Preview"], [title*="preview"]').first
        if preview_btn.is_visible():
            preview_href = preview_btn.get_attribute('href') or 'no href'
            print(f"\nPreview button href: {preview_href}")

        # 6. Check publish log or status endpoint
        for ep in ['/zs-site/api/v1/publishlog', '/zs-site/api/v1/publish/status',
                   '/zs-site/api/v1/publish/log', '/zs-site/api/v1/sites/publish']:
            page.evaluate(f"""() => {{
                window.__eptest = null;
                window.$X.get({{
                    url: '{ep}',
                    headers: window.app.getHeaders(),
                    success: function(r) {{ window.__eptest = r; }},
                    error: function(e) {{ window.__eptest = {{err: String(e)}}; }},
                }});
            }}""")
            page.wait_for_timeout(3000)
            res = page.evaluate("window.__eptest || null")
            print(f"\n  GET {ep}: {json.dumps(res)[:200] if res else '(null)'}")

        # 7. Try accessing the live page via the SPA's "view live" functionality
        # Find the publish button and click it to see the full publish dialog
        pub_btn = page.locator('.h-publish, [class*="publish"]').first
        print(f"\nPublish button: visible={pub_btn.is_visible()}")

        browser.close()

    # 8. Check if the CDN serves content
    cdn_urls_to_try = [
        'https://sites-stratus.zohostratus.in/60059075182/413198000000002010/index.html',
        'https://sites-stratus.zohostratus.in/60059075182/index.html',
        'https://www.butlerbutton.co/home',
        'https://www.butlerbutton.co/concierge',
    ]
    print("\n\n=== CDN/live checks ===")
    for url in cdn_urls_to_try:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '10', url], capture_output=True, text=True, timeout=15)
        print(f"  GET {url}: {r.stdout}")

    print("\n\nAll publish-related API responses:")
    for url, r in sorted(all_responses.items()):
        if 'publish' in url.lower():
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:800]}")


if __name__ == '__main__':
    main()
