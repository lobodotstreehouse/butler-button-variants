"""
Find and call the API to mark draft pages as "ready to publish".
The /resources/{id}/publish endpoint returns "Resource is not set to ready to publish".
Try various endpoints to change page status from Draft to Ready-to-Publish.
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

    all_responses = {}
    all_requests = []
    def capture_response(resp):
        if 'zs-site/api' in resp.url:
            try:
                body = resp.text()
                all_responses[resp.url] = {'status': resp.status, 'body': body}
                # Keep track of sequence
                all_requests.append({'url': resp.url, 'status': resp.status, 'body': body[:300]})
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
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        # Try multiple approaches to mark pages as ready to publish
        for page_url, page_id in DRAFT_PAGES:
            print(f"\n=== {page_url} (ID: {page_id}) ===")

            # Approach 1: POST /resources/{id}/readyToPublish
            pg.evaluate(f"""() => {{
                window.__rtp = 'pending';
                window.$X.post({{
                    url: '/zs-site/api/v1/resources/{page_id}/readyToPublish',
                    headers: window.app.getHeaders(),
                    bodyJSON: {{}},
                    success: function(r) {{ window.__rtp = r; }},
                    error: function(e) {{ window.__rtp = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(5000)
            r1 = pg.evaluate("window.__rtp")
            url1 = f"{BASE}/zs-site/api/v1/resources/{page_id}/readyToPublish"
            if url1 in all_responses:
                net = all_responses[url1]
                print(f"  readyToPublish: HTTP {net['status']} {net['body'][:200]}")
                del all_responses[url1]
            elif r1 and r1 != 'pending':
                print(f"  readyToPublish result: {json.dumps(r1)[:200]}")
            else:
                print(f"  readyToPublish: timeout")

            # Approach 2: POST /resources/{id}/markPublish
            pg.evaluate(f"""() => {{
                window.__mp = 'pending';
                window.$X.post({{
                    url: '/zs-site/api/v1/resources/{page_id}/markPublish',
                    headers: window.app.getHeaders(),
                    bodyJSON: {{}},
                    success: function(r) {{ window.__mp = r; }},
                    error: function(e) {{ window.__mp = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(5000)
            r2 = pg.evaluate("window.__mp")
            url2 = f"{BASE}/zs-site/api/v1/resources/{page_id}/markPublish"
            if url2 in all_responses:
                net = all_responses[url2]
                print(f"  markPublish: HTTP {net['status']} {net['body'][:200]}")
                del all_responses[url2]

            # Approach 3: PUT /zs-site/api/v1/resources/{id} with status update
            pg.evaluate(f"""() => {{
                window.__pup = 'pending';
                window.$X.put({{
                    url: '/zs-site/api/v1/resources/{page_id}',
                    headers: window.app.getHeaders(),
                    bodyJSON: {{content_state: 2}},
                    success: function(r) {{ window.__pup = r; }},
                    error: function(e) {{ window.__pup = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(5000)
            r3 = pg.evaluate("window.__pup")
            url3 = f"{BASE}/zs-site/api/v1/resources/{page_id}"
            if url3 in all_responses:
                net = all_responses[url3]
                print(f"  PUT resources: HTTP {net['status']} {net['body'][:200]}")
                del all_responses[url3]

            # Approach 4: PUT /pages/{id} with correct body
            body_variants = [
                {"skip_publish": False},
                {"content_state": 3},
                {"resource_id": page_id, "content_state": 3},
                {"page": {"resource_id": page_id, "content_state": 3}},
            ]
            for bv in body_variants:
                bv_str = json.dumps(bv)
                pg.evaluate(f"""() => {{
                    window.__pv = 'pending';
                    window.$X.put({{
                        url: '/zs-site/api/v1/pages/{page_id}',
                        headers: window.app.getHeaders(),
                        bodyJSON: {bv_str},
                        success: function(r) {{ window.__pv = r; }},
                        error: function(e) {{ window.__pv = {{error: String(e)}}; }},
                    }});
                }}""")
                pg.wait_for_timeout(4000)
                r4 = pg.evaluate("window.__pv")
                url4 = f"{BASE}/zs-site/api/v1/pages/{page_id}"
                if url4 in all_responses:
                    net = all_responses[url4]
                    print(f"  PUT pages {bv}: HTTP {net['status']} {net['body'][:200]}")
                    del all_responses[url4]
                    if net['status'] == 200 and '"0"' in net['body']:
                        print(f"  SUCCESS with body: {bv}")
                        break

        # Also try clicking "Edit page info" to see what dialog appears
        print("\n=== Checking Edit page info dialog ===")
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(5000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        # Click "Edit page info" for Concierge
        all_requests.clear()
        pg.evaluate("""() => {
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                if (walker.currentNode.textContent.trim() === 'Concierge') {
                    var p = walker.currentNode.parentElement;
                    for (var i = 0; i < 10; i++) {
                        if (!p) break;
                        var links = p.querySelectorAll('a');
                        for (var l of links) {
                            if (l.textContent.trim() === 'Edit page info' && l.offsetParent !== null) {
                                l.click();
                                return 'clicked Edit page info for Concierge';
                            }
                        }
                        p = p.parentElement;
                    }
                }
            }
            return 'not found';
        }""")
        pg.wait_for_timeout(5000)
        pg.screenshot(path='/tmp/zoho-55-page-info.png')

        # Check what dialog appeared
        dialog_text = pg.evaluate("""() => {
            var d = document.querySelector('[class*="dialog"], [class*="modal"], [class*="popup"]');
            if (d && d.offsetParent !== null) return d.textContent.trim().substring(0, 500);
            return null;
        }""")
        print(f"Page info dialog: {dialog_text}")

        # Check for status field in the dialog
        status_els = pg.evaluate("""() => {
            var inputs = document.querySelectorAll('input, select, [class*="toggle"], [class*="status"]');
            var results = [];
            for (var el of inputs) {
                if (el.offsetParent !== null) {
                    results.push({
                        tag: el.tagName,
                        id: el.id,
                        name: el.name,
                        type: el.type,
                        value: el.value,
                        class: el.className.substring(0, 50),
                    });
                }
            }
            return results.slice(0, 20);
        }""")
        print(f"Status elements: {json.dumps(status_els, indent=2)}")

        # Look at all API responses captured during page info dialog
        print("\nAPI calls during Edit page info:")
        for req in all_requests:
            print(f"  HTTP {req['status']} {req['url']}")
            print(f"  {req['body'][:200]}")

        browser.close()


if __name__ == '__main__':
    main()
