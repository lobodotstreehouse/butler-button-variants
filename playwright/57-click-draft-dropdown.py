"""
Click the Draft badge dropdown button in the pages list for each draft page.
The Draft badge (sites-badge blue) inside hb-dd-btn is a dropdown that may have
"Mark as Ready to Publish" or similar option to change the page status.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'

DRAFT_PAGES = [
    ('Concierge', 'concierge', '413198000000002013'),
    ('Home', 'home', '413198000000004653'),
    ('Trip Planning', 'trip-planning', '413198000000047002'),
    ('Travel Advisor', 'travel-advisor', '413198000000047014'),
]


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
    all_requests = []
    def capture_response(resp):
        if 'zs-site/api' in resp.url:
            try:
                body = resp.text()
                all_responses[resp.url] = {'status': resp.status, 'body': body}
                all_requests.append({'url': resp.url, 'status': resp.status, 'body': body[:300]})
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        pg = context.new_page()
        pg.on('response', capture_response)

        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        # First: inspect the structure of the Draft badge dropdown for Concierge
        print("=== Inspecting Draft badge dropdown for Concierge ===")
        concierge_dropdown_html = pg.evaluate("""() => {
            // Find Concierge text node
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                if (walker.currentNode.textContent.trim() === 'Concierge') {
                    var el = walker.currentNode.parentElement;
                    // Walk up to find the row containing Draft badge
                    for (var i = 0; i < 10; i++) {
                        if (!el) break;
                        var ddBtn = el.querySelector('.hb-dd-btn');
                        if (ddBtn) {
                            return {
                                html: ddBtn.outerHTML.substring(0, 1000),
                                hasDropdown: !!ddBtn.querySelector('[class*="dd"], [class*="dropdown"]'),
                                parentClass: ddBtn.parentElement?.className,
                                ddBtnClass: ddBtn.className,
                                ddBtnId: ddBtn.id,
                            };
                        }
                        el = el.parentElement;
                    }
                    return {error: 'no hb-dd-btn found near Concierge'};
                }
            }
            return {error: 'Concierge text not found'};
        }""")
        print(f"Concierge dropdown: {json.dumps(concierge_dropdown_html, indent=2)}")
        pg.screenshot(path='/tmp/zoho-57-pages.png')

        # Click the hb-dd-btn for Concierge to see the dropdown options
        print("\n=== Clicking Draft dropdown for Concierge ===")
        all_requests.clear()
        click_result = pg.evaluate("""() => {
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                if (walker.currentNode.textContent.trim() === 'Concierge') {
                    var el = walker.currentNode.parentElement;
                    for (var i = 0; i < 10; i++) {
                        if (!el) break;
                        var ddBtn = el.querySelector('.hb-dd-btn');
                        if (ddBtn && ddBtn.offsetParent !== null) {
                            ddBtn.click();
                            return 'clicked hb-dd-btn for Concierge: ' + ddBtn.outerHTML.substring(0, 200);
                        }
                        el = el.parentElement;
                    }
                    return 'hb-dd-btn not visible';
                }
            }
            return 'Concierge not found';
        }""")
        print(f"Click result: {click_result}")
        pg.wait_for_timeout(2000)
        pg.screenshot(path='/tmp/zoho-57-draft-dropdown.png')

        # See what dropdown appeared
        dropdown_options = pg.evaluate("""() => {
            // Look for any newly visible dropdown/menu
            var results = [];
            var els = document.querySelectorAll('[class*="dd-list"], [class*="dropdown-list"], [class*="hb-dd"], [class*="popup"], [class*="menu-list"]');
            for (var el of els) {
                if (el.offsetParent !== null && el.children.length > 0) {
                    results.push({
                        class: el.className,
                        text: el.textContent.trim().substring(0, 200),
                        html: el.outerHTML.substring(0, 500),
                    });
                }
            }
            // Also look for li items that just became visible
            var lis = document.querySelectorAll('li');
            for (var li of lis) {
                if (li.offsetParent !== null && li.parentElement?.offsetParent !== null) {
                    var t = li.textContent.trim();
                    if (t && t.length < 100 && (t.includes('Publish') || t.includes('Ready') || t.includes('Draft') || t.includes('Archive'))) {
                        results.push({
                            tag: 'LI',
                            text: t,
                            class: li.className,
                            parentClass: li.parentElement?.className,
                        });
                    }
                }
            }
            return results;
        }""")
        print(f"\nDropdown options: {json.dumps(dropdown_options, indent=2)}")

        # Get all visible text on page to see if dropdown appeared
        page_text_after = pg.evaluate("""() => {
            // Look for any element that's newly visible with publish-related text
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            var results = [];
            while (walker.nextNode()) {
                var t = walker.currentNode.textContent.trim();
                var el = walker.currentNode.parentElement;
                if (t.length > 2 && t.length < 100 && el.offsetParent !== null) {
                    var lowerT = t.toLowerCase();
                    if (lowerT.includes('publish') || lowerT.includes('ready') || lowerT.includes('archive') || lowerT.includes('mark as')) {
                        results.push({
                            text: t,
                            class: el.className.substring(0, 60),
                            tag: el.tagName,
                        });
                    }
                }
            }
            return results;
        }""")
        print(f"\nPublish-related visible text: {json.dumps(page_text_after, indent=2)}")

        # Try clicking any "Mark as Ready to Publish" or "Publish" option
        option_click = pg.evaluate("""() => {
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                var t = walker.currentNode.textContent.trim();
                var el = walker.currentNode.parentElement;
                if (el.offsetParent !== null) {
                    if (t === 'Mark as ready to publish' || t === 'Ready to Publish' ||
                        t === 'Publish' || t === 'Mark as Publish' || t === 'Publish Page' ||
                        t.toLowerCase() === 'publish' || t.toLowerCase().includes('ready to publish')) {
                        el.click();
                        return 'clicked: ' + t + ' (class: ' + el.className + ')';
                    }
                }
            }
            return 'no publish option found in dropdown';
        }""")
        print(f"\nOption click: {option_click}")
        pg.wait_for_timeout(3000)
        pg.screenshot(path='/tmp/zoho-57-after-option.png')

        # Check API calls
        print("\nAPI calls after dropdown interaction:")
        for req in all_requests:
            print(f"  HTTP {req['status']} {req['url']}")
            print(f"  {req['body'][:200]}")

        # Check content state after
        pg.evaluate("""() => {
            window.__pgState = 'pending';
            window.$X.get({
                url: '/zs-site/api/v1/pages/413198000000002013',
                headers: window.app.getHeaders(),
                success: function(r) { window.__pgState = r; },
                error: function(e) { window.__pgState = {error: String(e)}; },
            });
        }""")
        pg.wait_for_timeout(8000)
        state = pg.evaluate("window.__pgState")
        if state and state != 'pending':
            cs = state.get('page_info', {}).get('page_details', {}).get('content_state')
            print(f"\nConcierge content_state after: {cs}")
        else:
            # Check network
            url_key = f"{BASE}/zs-site/api/v1/pages/413198000000002013"
            if url_key in all_responses:
                try:
                    data = json.loads(all_responses[url_key]['body'])
                    cs = data.get('page_info', {}).get('page_details', {}).get('content_state')
                    print(f"\nConcierge content_state after (network): {cs}")
                except: pass

        # =========================================================
        # Alternative: Look at the hb-dd menu structure for ALL pages
        # =========================================================
        print("\n\n=== Full DOM analysis of hb-dd-btn elements ===")
        all_dd_btns = pg.evaluate("""() => {
            var btns = document.querySelectorAll('.hb-dd-btn');
            var results = [];
            for (var btn of btns) {
                if (btn.offsetParent !== null) {
                    // Find the row this is in
                    var row = btn;
                    for (var i = 0; i < 5; i++) {
                        if (!row.parentElement) break;
                        row = row.parentElement;
                        if (row.className && row.className.includes('sites-listcont')) break;
                    }
                    var pageName = '';
                    var nameEl = row.querySelector('[class*="page-name"], [class*="pagename"], h4, h3');
                    if (!nameEl) {
                        // Try data attributes
                        var as = row.querySelectorAll('a');
                        for (var a of as) {
                            var txt = a.textContent.trim();
                            if (txt && !txt.includes('Edit') && txt.length < 50) {
                                pageName = txt;
                                break;
                            }
                        }
                    } else {
                        pageName = nameEl.textContent.trim();
                    }
                    results.push({
                        btnHTML: btn.outerHTML.substring(0, 300),
                        btnClass: btn.className,
                        btnId: btn.id,
                        rowClass: row.className.substring(0, 60),
                        pageName: pageName,
                    });
                }
            }
            return results;
        }""")
        print(f"All hb-dd-btn elements: {json.dumps(all_dd_btns, indent=2)}")

        browser.close()


if __name__ == '__main__':
    main()
