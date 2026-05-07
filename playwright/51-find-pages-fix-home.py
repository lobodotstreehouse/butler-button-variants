"""
1. Navigate to pages list - find IDs for concierge/trip-planning/travel-advisor by DOM inspection
2. Check Site Options for home page setting
3. Try changing home page or adding URL redirect for /
4. Get page IDs from the pages list UI
"""
import json, subprocess, time
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
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        pg = context.new_page()
        pg.on('response', capture_response)

        # Navigate to pages list
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.screenshot(path='/tmp/zoho-51-pages-list.png')

        # Get all page links from the DOM
        page_links = pg.evaluate("""() => {
            var results = {};
            // Find all links that look like page editor links
            var links = document.querySelectorAll('a[href*="/page/"]');
            for (var l of links) {
                var m = l.href.match(/\/page\/(\d+)/);
                if (m) {
                    var text = l.textContent.trim() || l.closest('[data-page-name]')?.getAttribute('data-page-name');
                    // Look for the page name nearby
                    var container = l.closest('li, tr, [class*="row"], [class*="item"], div');
                    var nameEl = container?.querySelector('[class*="name"], [class*="title"], h3, h4, span, p');
                    var name = nameEl?.textContent?.trim() || l.textContent.trim();
                    if (name && m[1]) results[name.toLowerCase()] = m[1];
                }
            }
            return results;
        }""")
        print(f"Page links from DOM: {json.dumps(page_links, indent=2)}")

        # Also look for data attributes
        page_data_attrs = pg.evaluate("""() => {
            var results = [];
            var els = document.querySelectorAll('[data-page-id], [data-resource-id], [data-id]');
            for (var el of els) {
                var id = el.getAttribute('data-page-id') || el.getAttribute('data-resource-id') || el.getAttribute('data-id');
                var name = el.getAttribute('data-page-name') || el.getAttribute('data-name') || el.textContent.trim().substring(0, 50);
                if (id && !id.match(/^zs-|^fa-|^icon-/)) {
                    results.push({id: id, name: name});
                }
            }
            return results.slice(0, 30);
        }""")
        print(f"\nData attribute IDs: {json.dumps(page_data_attrs[:20], indent=2)}")

        # Try to find by searching page text in the DOM
        page_text_map = pg.evaluate("""() => {
            var results = {};
            var textNodes = document.querySelectorAll('[class*="page"], [class*="item"], li');
            for (var el of textNodes) {
                var text = el.textContent.trim().toLowerCase();
                if (text.includes('concierge') || text.includes('trip-planning') ||
                    text.includes('trip planning') || text.includes('travel-advisor') ||
                    text.includes('travel advisor')) {
                    // Look for links inside
                    var link = el.querySelector('a[href*="/page/"]');
                    if (link) {
                        var m = link.href.match(/\/page\/(\d+)/);
                        if (m) results[text.substring(0, 30)] = m[1];
                    }
                }
            }
            return results;
        }""")
        print(f"\nPage text map: {json.dumps(page_text_map, indent=2)}")

        # Look at the full page text to see what's listed
        body_text = pg.locator('body').inner_text()
        print(f"\nPages page text (first 2000 chars):")
        for line in body_text.split('\n'):
            l = line.strip()
            if l and len(l) > 2:
                print(f"  {l}")

        # Wait for JS to load and check app state
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        # Try to get page list from window.app
        app_pages = pg.evaluate("""() => {
            // Try various paths to get pages
            var d = window.app;
            var paths = [
                d?.data?.pages,
                d?.data?.sub_site_tree?.pages,
                d?.pages,
                d?.model?.pages,
            ];
            for (var p of paths) {
                if (p && Array.isArray(p)) return p.slice(0, 20).map(function(pg) {
                    return {id: pg.resource_id || pg.id, url: pg.resource_url || pg.url, title: pg.title};
                });
                if (p && typeof p === 'object') {
                    var keys = Object.keys(p);
                    if (keys.length > 0) return {type: 'object', keys: keys.slice(0, 10)};
                }
            }
            // Look in window for page-related data
            for (var k of Object.keys(window)) {
                if (k.toLowerCase().includes('page') || k.toLowerCase().includes('resource')) {
                    var v = window[k];
                    if (Array.isArray(v) && v.length > 0 && v.length < 50) {
                        return {found_in: k, data: JSON.stringify(v).substring(0, 500)};
                    }
                }
            }
            return {app_keys: Object.keys(d||{}).slice(0, 20)};
        }""")
        print(f"\nApp pages state: {json.dumps(app_pages)[:500]}")

        # Navigate to home page and check what happens
        print("\n=== Checking home page ===")
        pg.goto(f"{BASE}/zcms/{SITE_ID}/page/413198000000004653",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.screenshot(path='/tmp/zoho-51-home-editor.png')

        # Get ALL network responses for the home page load
        print("Home page responses:")
        for url, r in sorted(all_responses.items()):
            if any(k in url for k in ['page', 'resource', 'content']):
                print(f"  HTTP {r['status']} {url}")
                if r['status'] >= 400:
                    print(f"    Body: {r['body'][:200]}")

        # Try to see if there's an error visible in the editor
        page_error = pg.evaluate("""() => {
            // Look for error messages
            var errors = document.querySelectorAll('[class*="error"], [class*="Error"]');
            var msgs = [];
            for (var e of errors) {
                if (e.offsetParent !== null && e.textContent.trim()) {
                    msgs.push(e.textContent.trim().substring(0, 100));
                }
            }
            return msgs;
        }""")
        print(f"\nVisible errors: {page_error}")

        body_text_editor = pg.locator('body').inner_text()
        print(f"\nEditor body text (first 500):")
        print(body_text_editor[:500])

        # Navigate back and check Site Options for home page setting
        print("\n=== Site Options ===")
        pg.goto(f"{BASE}/zcms/{SITE_ID}/settings/options",
                wait_until='networkidle', timeout=45000)
        pg.wait_for_timeout(4000)
        options_text = pg.locator('body').inner_text()
        print("Options page text:")
        for line in options_text.split('\n'):
            l = line.strip()
            if l and len(l) > 2 and len(l) < 200:
                print(f"  {l}")

        pg.screenshot(path='/tmp/zoho-51-site-options.png')

        browser.close()

    print("\n=== Live site check ===")
    for path in ['/', '/concierge', '/trip-planning', '/categories', '/company']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '12', f'https://www.butlerbutton.co{path}'],
                           capture_output=True, text=True, timeout=20)
        print(f"  GET {path}: {r.stdout}")


if __name__ == '__main__':
    main()
