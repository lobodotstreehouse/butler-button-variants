"""
Home, Concierge, Trip Planning, Travel Advisor are DRAFT pages.
For each draft page:
1. Click "Edit content" in the pages list
2. Open the page editor
3. Click the Publish button in the editor
4. Confirm and wait
Then do a full site publish.
"""
import json, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE      = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID   = '413198000000002010'
# Known draft pages and their IDs
DRAFT_PAGES = [
    ('Home', '413198000000004653'),
    # IDs for others need to be discovered
]
# Probable IDs for other draft pages (from DOM inspection)
CANDIDATE_IDS = [
    '413198000000047002',
    '413198000000047014',
    '413198000000047037',
    '413198000000018539',
    '413198000000037515',
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


def publish_page_in_editor(page, pid, site_id=SITE_ID):
    """Navigate to page editor and click Publish"""
    all_resp = {}
    def capture(r):
        if 'zs-site/api' in r.url:
            try: all_resp[r.url] = {'status': r.status, 'body': r.text()}
            except: pass
    page.on('response', capture)

    # Navigate to the page via the SPA's pages route
    page.goto(f"{BASE}/zcms/{site_id}/pages",
              wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(4000)
    page.wait_for_function(
        "typeof window.$X==='object' && typeof window.app==='object'",
        timeout=30000)

    # Use app.navigate to go to the page editor
    nav_result = page.evaluate(f"""() => {{
        try {{
            if (window.app && window.app.navigate) {{
                window.app.navigate('/zcms/{site_id}/page/{pid}');
                return 'navigated via app.navigate';
            }}
        }} catch(e) {{}}
        // Try hsNav
        if (window.app && window.app.hsNav) {{
            window.app.hsNav.navigate('/zcms/{site_id}/page/{pid}');
            return 'navigated via hsNav';
        }}
        return 'no navigate method';
    }}""")
    print(f"    Navigation: {nav_result}")
    page.wait_for_timeout(5000)

    # Check URL and state
    current_url = page.url
    print(f"    URL: {current_url}")

    # Check if editor loaded with page data
    page_data = page.evaluate("""() => {
        var d = window.app && window.app.data;
        return d ? {
            resource_id: d.resource_id,
            resource_url: d.resource_url,
            content_state: d.content_state,
            title: document.title,
        } : null;
    }""")
    print(f"    Page data: {json.dumps(page_data)}")

    # Try to click the Publish button
    pub_result = page.evaluate("""() => {
        var btns = document.querySelectorAll('button, a, span');
        var found = [];
        for (var btn of btns) {
            var txt = btn.textContent.trim();
            if ((txt === 'Publish' || txt === 'Publish Page' || txt === 'Publish page')
                && btn.offsetParent !== null) {
                found.push({text: txt, class: btn.className});
                btn.click();
            }
        }
        return found;
    }""")
    print(f"    Publish buttons: {pub_result}")

    page.wait_for_timeout(8000)

    # Check if publish dialog appeared and confirm
    dialog_result = page.evaluate("""() => {
        var btns = document.querySelectorAll('button');
        for (var btn of btns) {
            var txt = btn.textContent.trim().toLowerCase();
            if ((txt.includes('publish') || txt === 'ok' || txt === 'continue')
                && btn.offsetParent !== null) {
                btn.click();
                return 'clicked: ' + btn.textContent.trim();
            }
        }
        return 'no dialog';
    }""")
    print(f"    Dialog: {dialog_result}")
    page.wait_for_timeout(5000)

    # Check response
    for url, r in sorted(all_resp.items()):
        if 'publish' in url.lower() or 'page' in url.lower():
            print(f"    Response: HTTP {r['status']} {url}")
            print(f"    Body: {r['body'][:200]}")

    return all_resp


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
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        # Strategy: Click "Edit content" for each draft page
        # First, find the "Edit content" links that are adjacent to "Draft" status labels

        # Get the page list items with their names and status
        page_items = pg.evaluate("""() => {
            var results = [];
            // Look for rows in the pages list
            var rows = document.querySelectorAll('[class*="row"], [class*="item"], li, tr');
            for (var row of rows) {
                var text = row.textContent;
                if (text.includes('Draft') && text.includes('Edit content')) {
                    // Find the "Edit content" link/button
                    var editBtn = null;
                    var btns = row.querySelectorAll('a, button, span');
                    for (var btn of btns) {
                        if (btn.textContent.trim() === 'Edit content') {
                            editBtn = {
                                tag: btn.tagName,
                                href: btn.href || '',
                                class: btn.className,
                                onclick: btn.getAttribute('onclick') || '',
                                dataEvent: btn.getAttribute('data-event') || '',
                            };
                            break;
                        }
                    }
                    // Find the page name
                    var nameEls = row.querySelectorAll('a, span, h3, h4');
                    var name = '';
                    for (var ne of nameEls) {
                        var t = ne.textContent.trim();
                        if (t && !t.includes('Draft') && !t.includes('Edit') && t.length < 50) {
                            name = t;
                            break;
                        }
                    }
                    results.push({
                        rowText: text.trim().substring(0, 100),
                        name: name,
                        editBtn: editBtn,
                    });
                }
            }
            return results;
        }""")
        print(f"Draft page items: {json.dumps(page_items, indent=2)[:2000]}")

        # Alternative: Click Edit content buttons directly using Playwright
        page_text = pg.locator('body').inner_text()
        draft_sections = []
        lines = page_text.split('\n')
        for i, line in enumerate(lines):
            if 'Draft' in line and i > 0:
                # Look for surrounding context
                context_start = max(0, i-3)
                context_end = min(len(lines), i+3)
                context_lines = lines[context_start:context_end]
                draft_sections.append('\n'.join(context_lines))

        print(f"\nDraft page contexts:")
        for s in draft_sections:
            print(f"  {s!r}")

        # Try a different approach: use Playwright to find and click "Edit content" for draft pages
        # Navigate to pages list and find draft pages
        print("\n=== Clicking Edit content for draft pages ===")

        # Get all "Edit content" buttons visible on the page
        edit_btns = pg.locator('text="Edit content"').all()
        print(f"Found {len(edit_btns)} 'Edit content' buttons")

        # We want to click the ones adjacent to "Draft" labels
        # Let's try a different approach - use the page's navigation
        draft_pages_found = pg.evaluate("""() => {
            // Find all page names that have Draft status
            var results = [];
            var statusEls = document.querySelectorAll('*');
            for (var el of statusEls) {
                if (el.children.length === 0 && el.textContent.trim() === 'Draft') {
                    // Found a Draft status element, find the Edit content button nearby
                    var parent = el.parentElement;
                    for (var i = 0; i < 5; i++) {
                        if (!parent) break;
                        var editContent = parent.querySelector('a[data-event*="editContent"], button[data-event*="editContent"], a[onclick*="editContent"], span[data-event*="editContent"]');
                        if (!editContent) {
                            // Try by text
                            var spans = parent.querySelectorAll('a, button, span');
                            for (var s of spans) {
                                if (s.textContent.trim() === 'Edit content') {
                                    editContent = s;
                                    break;
                                }
                            }
                        }
                        if (editContent) {
                            // Find page name
                            var nameEl = parent.querySelector('[class*="name"], h3, h4');
                            var name = nameEl?.textContent.trim() || parent.textContent.trim().substring(0, 30);
                            results.push({
                                name: name,
                                dataEvent: editContent.getAttribute('data-event'),
                                id: editContent.id,
                                href: editContent.href || '',
                                class: editContent.className,
                            });
                            break;
                        }
                        parent = parent.parentElement;
                    }
                }
            }
            return results;
        }""")
        print(f"\nDraft pages with Edit content: {json.dumps(draft_pages_found, indent=2)}")

        # Try the approach of using the app's navigation to visit each draft page's editor
        # First, try to find the IDs from the response captured during page load
        pages_resp_url = f"{BASE}/zs-site/api/v1/pages?is_first=true&subsite_id={SITE_ID}"
        if pages_resp_url in all_responses:
            resp_data = json.loads(all_responses[pages_resp_url]['body'])
            if 'pages_details' in resp_data:
                print("\nPages from API response captured during load:")
                pages_list = resp_data['pages_details'].get('pages', [])
                for p in pages_list:
                    print(f"  id={p.get('resource_id')} url={p.get('resource_url')!r} "
                          f"status={p.get('content_state')} skip={p.get('skip_publish')}")
        else:
            print("\nPages API response not captured")
            print(f"  Available responses: {list(all_responses.keys())[:10]}")

        # Navigate to each draft page by its ID
        # For Home page, ID is known. For others, try the candidate IDs
        draft_page_ids = ['413198000000004653']  # Home (known)

        # Check candidate IDs to find concierge/trip-planning/travel-advisor
        print("\n=== Checking candidate IDs ===")
        for cid in CANDIDATE_IDS:
            pg.evaluate(f"""() => {{
                window.__pageCheck = 'pending';
                window.$X.get({{
                    url: '/zs-site/api/v1/pages/{cid}?subsite_id={SITE_ID}',
                    headers: window.app.getHeaders(),
                    success: function(r) {{ window.__pageCheck = r; }},
                    error: function(e) {{ window.__pageCheck = {{error: String(e)}}; }},
                }});
            }}""")
            pg.wait_for_timeout(5000)
            result = pg.evaluate("window.__pageCheck")
            if result and result != 'pending':
                url = result.get('resource_url', result.get('page_details', {}).get('resource_url', '?'))
                print(f"  ID {cid}: {json.dumps(result)[:200]}")
            else:
                # Check network
                check_url = f"{BASE}/zs-site/api/v1/pages/{cid}?subsite_id={SITE_ID}"
                if check_url in all_responses:
                    resp = all_responses[check_url]
                    print(f"  ID {cid}: HTTP {resp['status']} {resp['body'][:200]}")
                else:
                    print(f"  ID {cid}: timeout")

        # Use a fresh approach: navigate to pages list and intercept the response
        print("\n=== Navigating to pages list (fresh) with response capture ===")
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(8000)

        # Check all captured responses for page data
        for url, r in sorted(all_responses.items()):
            if 'pages' in url and 'subsite_id' in url and r.get('status') == 200:
                print(f"  Pages response: {url}")
                try:
                    data = json.loads(r['body'])
                    if 'pages_details' in data:
                        pages = data['pages_details'].get('pages', [])
                        for p in pages:
                            url_val = p.get('resource_url', '')
                            pid = p.get('resource_id', '')
                            state = p.get('content_state', '')
                            skip = p.get('skip_publish', '')
                            print(f"    {url_val!r} id={pid} state={state} skip={skip}")
                            if state == 1 or (isinstance(state, str) and '1' in str(state)):
                                draft_page_ids.append(pid)
                except Exception as e:
                    print(f"  Parse error: {e}: {r['body'][:200]}")

        # Now try to publish draft pages - use the "Edit page info" approach
        # which might give access to the publish action
        print("\n=== Publishing draft pages via click ===")
        pg.goto(f"{BASE}/zcms/{SITE_ID}/pages",
                wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(4000)
        pg.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        pg.wait_for_timeout(3000)

        # Click the first "Edit content" button to see what happens
        first_edit = pg.locator('text="Edit content"').first
        if first_edit.is_visible():
            print("Clicking first 'Edit content'...")
            first_edit.click()
            pg.wait_for_timeout(5000)
            new_url = pg.url
            print(f"URL after click: {new_url}")
            pg.screenshot(path='/tmp/zoho-52-after-edit.png')
        else:
            print("'Edit content' not visible")
            pg.screenshot(path='/tmp/zoho-52-no-edit.png')

        # Check what page we're on
        current_data = pg.evaluate("""() => {
            var d = window.app && window.app.data;
            return d ? {
                resource_id: d.resource_id,
                resource_url: d.resource_url,
                content_state: d.content_state,
            } : null;
        }""")
        print(f"Current page data: {json.dumps(current_data)}")

        browser.close()

    print("\n=== Final live check ===")
    for path in ['/', '/concierge', '/trip-planning', '/travel-advisor', '/categories']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '12', f'https://www.butlerbutton.co{path}'],
                           capture_output=True, text=True, timeout=20)
        print(f"  GET {path}: {r.stdout}")


if __name__ == '__main__':
    main()
