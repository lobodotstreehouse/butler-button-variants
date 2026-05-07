"""
Open visual editor for concierge page, capture ALL network requests to find CDN path structure.
Also check the second Zoho account for comparison of CDN paths on a working site.
"""
import json, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'
CONCIERGE_ID = '413198000000002013'


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

    all_urls = set()
    stratus_urls = []
    def capture_response(resp):
        url = resp.url
        all_urls.add(url)
        if 'stratus' in url or 'cdn' in url.lower() or 'sites-stratus' in url:
            try:
                stratus_urls.append({'url': url, 'status': resp.status, 'body_len': len(resp.text())})
            except Exception:
                stratus_urls.append({'url': url, 'status': resp.status, 'body_len': -1})

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        # 1. Open pages list and capture URLs
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)

        # 2. Try the page preview link from the pages list - look for a "View/Preview" link for concierge
        # Click on the concierge page row
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Find preview URL from the pages directory
        preview_info = page.evaluate("""() => {
            // Check if there are any page rows with view/preview links
            var rows = document.querySelectorAll('[class*="page"], [class*="resource"]');
            var info = [];
            for (var row of rows) {
                var links = row.querySelectorAll('a');
                for (var l of links) {
                    if (l.href && (l.href.includes('concierge') || l.href.includes('preview') ||
                                   l.href.includes('butlerbutton'))) {
                        info.push({href: l.href, text: l.textContent.trim()});
                    }
                }
            }
            return info;
        }""")
        print(f"Preview links from pages list: {json.dumps(preview_info, indent=2)}")

        # 3. Open visual editor for concierge page
        print("\nOpening visual editor for concierge...")
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages/{CONCIERGE_ID}/edit",
                  wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)

        # 4. Capture all network requests
        print(f"\nStratus/CDN URLs captured: {len(stratus_urls)}")
        for item in stratus_urls[:20]:
            print(f"  HTTP {item['status']}  {item['url']}  ({item['body_len']} bytes)")

        # Find all unique domains used
        domains = set()
        for url in all_urls:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domains.add(parsed.netloc)
            except:
                pass
        print(f"\nAll domains accessed: {sorted(domains)}")

        # 5. Get the iframe src if visual editor uses an iframe
        iframe_srcs = page.evaluate("""() => {
            var iframes = document.querySelectorAll('iframe');
            return Array.from(iframes).map(f => f.src).filter(s => s && s.length > 0);
        }""")
        print(f"\nIframe sources: {iframe_srcs}")

        # 6. Look for any content-serving URL in the page source
        page_source_urls = page.evaluate("""() => {
            var text = document.documentElement.innerHTML;
            var matches = text.match(/https?:\/\/[^"'\s]+stratus[^"'\s]+/g) || [];
            return [...new Set(matches)].slice(0, 10);
        }""")
        print(f"\nStratus URLs in page source: {page_source_urls}")

        # 7. Get publish history from page - look at the page HTML for any live URL references
        live_urls = page.evaluate("""() => {
            var text = document.documentElement.innerHTML;
            var matches = text.match(/https?:\/\/www\.butlerbutton\.co[^"'\s]*/g) || [];
            var zoho_matches = text.match(/https?:\/\/[^"'\s]*zohosites[^"'\s]*/g) || [];
            return {
                butlerbutton: [...new Set(matches)].slice(0, 10),
                zohosites: [...new Set(zoho_matches)].slice(0, 10),
            };
        }""")
        print(f"\nLive URL refs in editor page: {json.dumps(live_urls, indent=2)}")

        browser.close()

    # Also check CDN paths via curl
    print("\n\n=== CDN path tests ===")
    cdn_paths = [
        '/60059075182/concierge',
        '/60059075182/413198000000002010/concierge',
        '/60059075182/413198000000002013',
        '/60059075182/413198000000002013/index.html',
        '/60059075182/413198000000002013/concierge.html',
        '/sites/60059075182/concierge',
        '/www.butlerbutton.co/concierge',
        '/413198000000002010/concierge',
    ]
    for path in cdn_paths:
        url = f"https://sites-stratus.zohostratus.in{path}"
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                            '--max-time', '5', url], capture_output=True, text=True, timeout=10)
        if r.stdout != '404':
            print(f"  {path}: HTTP {r.stdout}")


if __name__ == '__main__':
    main()
