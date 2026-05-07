"""
Check Zoho editor preview, find native site URL, and attempt domain re-mapping fix.
"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE    = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID = '413198000000002010'


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

    api_responses = {}
    preview_urls = set()

    def capture_response(resp):
        if 'zs-site/api' in resp.url:
            try:
                api_responses[resp.url] = {'status': resp.status, 'body': resp.text()}
            except Exception:
                pass
        # Watch for preview/live URLs
        if 'zohosites.in' in resp.url or 'butlerbutton' in resp.url:
            preview_urls.add(resp.url)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        # Navigate to pages list
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)
        page.wait_for_function(
            "typeof window.$X==='object' && typeof window.app==='object'",
            timeout=30000)
        page.wait_for_timeout(2000)

        # Find the native/preview URL from app.data
        site_info = page.evaluate("""() => {
            var data = {};
            if (window.app && window.app.data) {
                data.builder_base_url = window.app.data.builder_base_url;
                data.site_url = window.app.data.site_url;
                data.preview_url = window.app.data.preview_url;
                data.publish_url = window.app.data.publish_url;
                data.site_name = window.app.data.site_name;
                data.zsite_id = window.app.data.zsite_id;
                data.subSiteId = window.app.data.subSiteId;
                data.api_url = window.app.data.api_url;
                data.allKeys = Object.keys(window.app.data).slice(0, 50);
            }
            return data;
        }""")
        print(f"\nApp data keys: {json.dumps(site_info, indent=2)[:2000]}")

        # Get all app.data fields that include URLs
        url_fields = page.evaluate("""() => {
            var result = {};
            if (!window.app || !window.app.data) return result;
            Object.keys(window.app.data).forEach(function(k) {
                var v = window.app.data[k];
                if (typeof v === 'string' && (v.includes('http') || v.includes('zohosites') || v.includes('butlerbutton'))) {
                    result[k] = v;
                }
            });
            return result;
        }""")
        print(f"\nURL fields in app.data: {json.dumps(url_fields, indent=2)}")

        # Try to get the site info via the correct GET endpoint
        page.evaluate(f"""() => {{
            window.$X.get({{
                url: '/zs-site/api/v1/sites/{SITE_ID}',
                headers: window.app.getHeaders(),
                success: function(r) {{ window.__siteInfo = r; }},
                error: function(e) {{ window.__siteInfo = {{err: String(e)}}; }},
            }});
        }}""")
        page.wait_for_timeout(5000)
        site_info_2 = page.evaluate("window.__siteInfo || null")
        print(f"\nSite info API: {json.dumps(site_info_2, indent=2)[:1000] if site_info_2 else '(null)'}")

        # Try preview URL
        print("\nTrying preview URLs...")
        for preview_path in [
            f'/zcms/{SITE_ID}/preview',
            f'/zcms/{SITE_ID}/preview/413198000000002013',  # concierge resource_id
        ]:
            preview_url = f"{BASE}{preview_path}"
            print(f"\nGET {preview_url}")
            try:
                page.goto(preview_url, wait_until='commit', timeout=15000)
                page.wait_for_timeout(2000)
                code = api_responses.get(preview_url, {}).get('status', 'unknown')
                title = page.title()
                print(f"  Title: {title}, URL: {page.url}")
                page.screenshot(path=f'/tmp/zoho-preview-{preview_path.replace("/", "_")}.png')
            except Exception as e:
                print(f"  Error: {e}")

        browser.close()

    print("\n\nCaptured API responses:")
    for url, r in api_responses.items():
        if 'sites/{SITE_ID}'.format(SITE_ID=SITE_ID) in url or 'preview' in url:
            print(f"\n  HTTP {r['status']}  {url}")
            print(f"  {r['body'][:300]}")


if __name__ == '__main__':
    main()
