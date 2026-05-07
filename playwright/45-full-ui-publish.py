"""
1. Try accessing the live site content via builder preview
2. Do a FULL UI publish flow (click Publish button, complete dialog)
3. Try different publish body parameters
4. Check if content_state can be confirmed
5. Try POST /publish with force/rebuild params
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
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # 1. Try different publish bodies
        pub_bodies = [
            '{}',
            '{"republish":true}',
            '{"force_publish":true}',
            '{"rebuild":true}',
            '{"publish_type":"full"}',
            '{"subsite_id":"413198000000002010"}',
        ]

        print("=== Testing different publish bodies ===")
        for body_str in pub_bodies:
            page.evaluate(f"""() => {{
                window.__pubTest = null;
                window.$X.post({{
                    url: '/zs-site/api/v1/publish',
                    headers: window.app.getHeaders(),
                    bodyJSON: {body_str},
                    success: function(r) {{ window.__pubTest = r; }},
                    error: function(e) {{ window.__pubTest = {{error: String(e)}}; }},
                }});
            }}""")
            page.wait_for_timeout(8000)
            result = page.evaluate("window.__pubTest || null")

            # Check network capture
            pub_url = f"{BASE}/zs-site/api/v1/publish"
            net = all_responses.get(pub_url, {})
            resp_body = net.get('body', '')
            if pub_url in all_responses:
                del all_responses[pub_url]
            print(f"  body={body_str}: {resp_body[:200] if resp_body else '(null)'}")

        # 2. Full UI publish click
        print("\n=== Full UI Publish ===")
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)

        # Find publish button
        pub_btn = page.locator('.h-publish, [class*="publish"]:not([class*="last"])').first
        print(f"Publish button visible: {pub_btn.is_visible()}")
        if pub_btn.is_visible():
            pub_btn.click()
            page.wait_for_timeout(4000)
            page.screenshot(path='/tmp/zoho-ui-publish-1.png')

            # Look for and click any dialog buttons
            dialog_btns = page.locator('[class*="dialog"] button, [class*="modal"] button').all()
            for btn in dialog_btns:
                if btn.is_visible():
                    txt = btn.inner_text().strip()
                    print(f"Dialog button: '{txt}'")
                    if 'publish' in txt.lower() or 'continue' in txt.lower() or 'save' in txt.lower():
                        btn.click()
                        page.wait_for_timeout(5000)
                        page.screenshot(path='/tmp/zoho-ui-publish-2.png')
                        break

        # 3. Check what the publish modal says
        page.wait_for_timeout(3000)
        dialog_text = page.locator('body').inner_text()
        publish_text = '\n'.join(l for l in dialog_text.split('\n')
                                 if 'publish' in l.lower() or 'domain' in l.lower()
                                 or 'butler' in l.lower())
        print(f"\nPublish-related text:\n{publish_text[:500]}")

        # 4. Try to check what "pages" with publish_status look like
        page.evaluate(f"""() => {{
            window.__pages = null;
            window.$X.get({{
                url: '/zs-site/api/v1/pages?subsite_id={SITE_ID}&include_all=true',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__pages = r; }},
                error: function(e) {{ window.__pages = {{error: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(6000)
        pages_result = page.evaluate("window.__pages || null")
        if pages_result and 'pages_details' in pages_result:
            pages = pages_result['pages_details'].get('pages', [])
            print(f"\nPages ({len(pages)} total):")
            for p in pages:
                print(f"  url='{p.get('resource_url')}' skip_publish={p.get('skip_publish')} "
                      f"trash={p.get('trash')}")

        # 5. Check if there are any "unpublished" flags that need to be fixed
        page.evaluate("""() => {
            window.__siteCheck = null;
            window.$X.get({
                url: '/zs-site/api/v1/publish',
                headers: window.app.getHeaders(),
                success: function(r) { window.__siteCheck = r; },
                error: function(e) { window.__siteCheck = {error: String(e)}; },
            });
        }""")
        page.wait_for_timeout(6000)
        site_check = page.evaluate("window.__siteCheck || null")
        print(f"\nGET /publish: {json.dumps(site_check)[:400] if site_check else '(null)'}")

        # 6. Check the sub_site_tree for any issues
        subsite = page.evaluate("""() => {
            var d = window.app && window.app.data;
            if (!d) return null;
            return {
                content_state: d.sub_site_tree?.content_state,
                last_published_time: d.sub_site_tree?.last_published_time,
                live_search_indexed_time: d.sub_site_tree?.live_search_indexed_time,
                isSitePublished: d.isSitePublished,
                publishedDomain: d.publishedDomain,
            };
        }""")
        print(f"\nSite publish state: {json.dumps(subsite)}")

        # 7. Try accessing site via different domains and look for content
        browser.close()

    print("\n\n=== Live site check ===")
    for url in ['https://butlerbutton.zohosites.in/', 'https://butlerbutton.zohosites.in/home',
                'https://www.butlerbutton.co/', 'https://www.butlerbutton.co/home']:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code} %{size_download}',
                            '--max-time', '15', url], capture_output=True, text=True, timeout=20)
        print(f"  GET {url}: {r.stdout}")


if __name__ == '__main__':
    main()
