"""
Publish each draft page through the visual editor.
Draft pages: concierge (2013), home (4653), trip-planning (47002), travel-advisor (47014)
Editor URL pattern: /zcms/editor/{page_url}
"""
import json, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'

DRAFT_PAGES = [
    ('concierge', '413198000000002013'),
    ('home', '413198000000004653'),
    ('trip-planning', '413198000000047002'),
    ('travel-advisor', '413198000000047014'),
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

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        pg = context.new_page()

        all_responses = {}
        def capture_response(resp):
            if 'zs-site/api' in resp.url:
                try:
                    all_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
                except Exception:
                    pass
        pg.on('response', capture_response)

        # Load site context first
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        for page_url, page_id in DRAFT_PAGES:
            print(f"\n{'='*50}")
            print(f"=== Publishing draft page: {page_url} (ID: {page_id}) ===")
            print(f"{'='*50}")

            # Navigate to editor - try the /zcms/editor/ URL pattern
            editor_url = f"{BASE}/zcms/editor/{page_url}"
            print(f"Navigating to: {editor_url}")
            pg.goto(editor_url, wait_until='networkidle', timeout=60000)
            pg.wait_for_timeout(8000)
            pg.screenshot(path=f'/tmp/zoho-53-{page_url}-editor.png')

            current_url = pg.url
            print(f"Current URL: {current_url}")

            # Check if editor is loaded
            editor_state = pg.evaluate("""() => {
                var d = window.app && window.app.data;
                return {
                    hasApp: typeof window.app === 'object',
                    resourceId: d?.resource_id,
                    resourceUrl: d?.resource_url,
                    contentState: d?.content_state,
                    pageTitle: document.title,
                };
            }""")
            print(f"Editor state: {json.dumps(editor_state)}")

            if not editor_state.get('hasApp') or not editor_state.get('resourceId'):
                print(f"  Editor not loaded properly, trying from pages list...")

                # Navigate to pages list and click Edit content for this page
                pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                        wait_until='networkidle', timeout=60000)
                pg.wait_for_timeout(5000)
                pg.wait_for_function(
                    "typeof window.$X==='object' && typeof window.app==='object'",
                    timeout=30000)
                pg.wait_for_timeout(3000)

                # Find and click Edit content for the specific page
                click_result = pg.evaluate(f"""() => {{
                    // Find text nodes containing the page name
                    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                    while (walker.nextNode()) {{
                        var text = walker.currentNode.textContent.trim().toLowerCase();
                        if (text === '{page_url.replace('-', ' ')}' || text === '{page_url}') {{
                            var parent = walker.currentNode.parentElement;
                            // Look for Edit content in the same row
                            for (var i = 0; i < 8; i++) {{
                                if (!parent) break;
                                var links = parent.querySelectorAll('a, span, button');
                                for (var l of links) {{
                                    if (l.textContent.trim() === 'Edit content' && l.offsetParent !== null) {{
                                        l.click();
                                        return 'clicked Edit content for {page_url}';
                                    }}
                                }}
                                parent = parent.parentElement;
                            }}
                        }}
                    }}
                    return 'not found';
                }}""")
                print(f"  Click result: {click_result}")
                pg.wait_for_timeout(8000)
                pg.screenshot(path=f'/tmp/zoho-53-{page_url}-from-list.png')

                editor_state = pg.evaluate("""() => {
                    var d = window.app && window.app.data;
                    return {
                        resourceId: d?.resource_id,
                        resourceUrl: d?.resource_url,
                        contentState: d?.content_state,
                    };
                }""")
                print(f"  Editor state after click: {json.dumps(editor_state)}")

            # Now try to find and click the Publish button
            # In Zoho Sites visual editor, the publish button is in the header
            print(f"Looking for Publish button...")

            pub_buttons = pg.evaluate("""() => {
                var results = [];
                var btns = document.querySelectorAll('button, a, span, div');
                for (var btn of btns) {
                    if (btn.offsetParent !== null) {
                        var txt = btn.textContent.trim();
                        if (txt === 'Publish' || txt === 'Publish Page' || txt === 'Publish page'
                            || txt.startsWith('Publish')) {
                            results.push({
                                tag: btn.tagName,
                                text: txt,
                                class: btn.className.substring(0, 80),
                                id: btn.id,
                                dataEvent: btn.getAttribute('data-event'),
                            });
                        }
                    }
                }
                return results;
            }""")
            print(f"Visible Publish buttons: {json.dumps(pub_buttons)}")

            if pub_buttons:
                print("Clicking Publish button...")
                pg.evaluate("""() => {
                    var btns = document.querySelectorAll('button, a, span, div');
                    for (var btn of btns) {
                        if (btn.offsetParent !== null) {
                            var txt = btn.textContent.trim();
                            if (txt === 'Publish' || txt === 'Publish Page') {
                                btn.click();
                                return 'clicked: ' + txt;
                            }
                        }
                    }
                    return 'not found';
                }""")
                pg.wait_for_timeout(5000)

                # Handle any publish dialog
                dialog_result = pg.evaluate("""() => {
                    var btns = document.querySelectorAll('button');
                    for (var btn of btns) {
                        if (btn.offsetParent !== null) {
                            var txt = btn.textContent.trim().toLowerCase();
                            if (txt === 'publish' || txt === 'continue' || txt === 'ok') {
                                btn.click();
                                return 'clicked dialog: ' + btn.textContent.trim();
                            }
                        }
                    }
                    return 'no dialog button';
                }""")
                print(f"Dialog result: {dialog_result}")
                pg.wait_for_timeout(10000)
                pg.screenshot(path=f'/tmp/zoho-53-{page_url}-after-pub.png')

            # Try API approach if UI doesn't work
            print("Trying API publish approach...")
            pg.evaluate(f"""() => {{
                window.__pagePub = 'pending';
                var headers = window.app?.getHeaders() || {{}};
                window.$X.post({{
                    url: '/zs-site/api/v1/pages/{page_id}/publish',
                    headers: headers,
                    bodyJSON: {{}},
                    success: function(r) {{ window.__pagePub = r; }},
                    error: function(e) {{ window.__pagePub = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(8000)
            pub_result = pg.evaluate("window.__pagePub")
            if pub_result and pub_result != 'pending':
                print(f"  API result: {json.dumps(pub_result)[:300]}")
            else:
                pub_url = f"{BASE}/zs-site/api/v1/pages/{page_id}/publish"
                if pub_url in all_responses:
                    print(f"  Network: HTTP {all_responses[pub_url]['status']} {all_responses[pub_url]['body'][:300]}")

            # Check pages list again for current status
            pages_url = f"{BASE}/zs-site/api/v1/pages?is_first=true&subsite_id={SITE_ID}"
            if pages_url in all_responses:
                try:
                    pages_data = json.loads(all_responses[pages_url]['body'])
                    pages = pages_data.get('pages_details', {}).get('pages', [])
                    for p in pages:
                        if p.get('resource_url') == page_url:
                            print(f"  Page state: content_state={p.get('content_state')}")
                except:
                    pass

        # Final site-wide publish
        print("\n=== Final site publish ===")
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        pg.evaluate("""() => {
            window.__finalPub = 'pending';
            window.$X.post({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                bodyJSON: {},
                success: function(r) { window.__finalPub = r; },
                error: function(e) { window.__finalPub = {error: String(e)}; },
            });
        }""")
        for _ in range(5):
            pg.wait_for_timeout(5000)
            r = pg.evaluate("window.__finalPub")
            if r and r != 'pending':
                break
        pub_url = f"{BASE}/zs-site/api/v1/publish"
        if r and r != 'pending':
            print(f"  Result: {json.dumps(r)[:400]}")
        elif pub_url in all_responses:
            print(f"  Network: {all_responses[pub_url]['body'][:400]}")

        # Click UI Publish button
        print("\nClicking UI Publish button...")
        pg.evaluate("""() => {
            var btns = document.querySelectorAll('button, a');
            for (var btn of btns) {
                if (btn.offsetParent !== null && btn.textContent.trim() === 'Publish') {
                    btn.click(); return 'clicked';
                }
            }
            // Try h-publish class
            var hpub = document.querySelector('.h-publish');
            if (hpub && hpub.offsetParent !== null) { hpub.click(); return 'h-publish clicked'; }
            return 'not found';
        }""")
        pg.wait_for_timeout(5000)
        pg.evaluate("""() => {
            var btns = document.querySelectorAll('button');
            for (var btn of btns) {
                var txt = btn.textContent.trim();
                if ((txt === 'Continue' || txt === 'Publish') && btn.offsetParent !== null) {
                    btn.click(); return 'dialog: ' + txt;
                }
            }
        }""")
        pg.wait_for_timeout(15000)

        browser.close()

    print("\nWaiting 60 seconds for CDN propagation...")
    time.sleep(60)

    print("\n=== Final live check ===")
    for path in ['/', '/concierge', '/trip-planning', '/travel-advisor', '/categories', '/company']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', f'https://www.butlerbutton.co{path}'],
                           capture_output=True, text=True, timeout=20)
        print(f"  GET {path}: {r.stdout}")


if __name__ == '__main__':
    main()
