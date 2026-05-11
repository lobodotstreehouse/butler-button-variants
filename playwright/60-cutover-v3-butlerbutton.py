"""
Replaces the live butlerbutton.co header IIFE so all five page slugs route
to their inject-{name}-v3.js cousin, then publishes the site.

Before:
  ""  or "/index"      -> inject-home-v2.js?v=18
  "/trip-planning"     -> inject-trip-planning-v2.js?v=18
  "/concierge"         -> inject-concierge-v2.js?v=18
  "/travel-advisor"    -> inject-advisor-v2.js?v=18
  "/supplier-code"     -> inject-supplier-code.js?v=16

After:
  ""  or "/index"      -> inject-home-v3.js?v=3
  "/trip-planning"     -> inject-trip-planning-v3.js?v=3
  "/concierge"         -> inject-concierge-v3.js?v=3
  "/travel-advisor"    -> inject-advisor-v3.js?v=3
  "/supplier-code"     -> inject-supplier-code-v3.js?v=3

Auth: reuses /tmp/zoho_cookies_clean.json (refreshed via /zoho-auth-playwright
when stale). Memory rule: use literal `</script>` in the header string,
NOT `<\\/script>` — Python doesn't interpret `\\/` as `/` and the stray
backslash will break the HTML parser.
"""

import json, sys, re
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE         = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID      = '413198000000002010'

NEW_HEADER = (
    '<script>(function(){'
    'var x=location.pathname.replace(/\\/+$/,"");'
    'var s=document.createElement("script");'
    'var b="https://lobodotstreehouse.github.io/butler-button-variants/zoho-inject/";'
    'if(x===""||x==="/index"){s.src=b+"inject-home-v3.js?v=6";}'
    'else if(x==="/trip-planning"){s.src=b+"inject-trip-planning-v3.js?v=6";}'
    'else if(x==="/concierge"){s.src=b+"inject-concierge-v3.js?v=6";}'
    'else if(x==="/travel-advisor"){s.src=b+"inject-advisor-v3.js?v=6";}'
    'else if(x==="/supplier-code"){s.src=b+"inject-supplier-code-v3.js?v=6";}'
    'else{return;}'
    'document.head.appendChild(s);'
    '})();</script>'
)


def build_cookies(raw: dict) -> list:
    seen, cookies = set(), []
    for name, value in raw.items():
        if not value or not isinstance(value, str):
            continue
        key = (name, value)
        if key in seen:
            continue
        seen.add(key)
        cookies.append({
            'name': name, 'value': value,
            'domain': '.sitebuilder-60059075182.zohositescontent.in',
            'path': '/', 'httpOnly': False, 'secure': True,
        })
    return cookies


def main():
    raw = json.loads(Path(COOKIES_JSON).read_text())
    cookies = build_cookies(raw)
    print(f"Loaded {len(cookies)} cookies")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=40)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)

        page = context.new_page()

        pages_url = f"{BASE}/zcms/{SITE_ID}/pages"
        print(f"Loading {pages_url}")
        page.goto(pages_url, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(2000)

        if 'accounts.zoho' in page.url or '/login' in page.url:
            print(f"PRECHECK FAIL: session expired (url={page.url})")
            print("Run /zoho-auth-playwright or refresh /tmp/zoho_cookies_clean.json then retry.")
            browser.close()
            sys.exit(10)

        # Try to grab the SPA's own header object via a fast eval before the SPA
        # navs again. If that fails, fall back to synthesized headers.
        page.wait_for_function(
            "typeof window.$X === 'object' && typeof window.app === 'object'",
            timeout=30000,
        )
        spa_headers = None
        for attempt in range(5):
            try:
                spa_headers = page.evaluate("() => window.app.getHeaders()")
                break
            except Exception as e:
                print(f"getHeaders eval attempt {attempt+1} failed: {e}; retrying")
                page.wait_for_timeout(1500)
        print(f"SPA app.getHeaders() = {json.dumps(spa_headers)[:500] if spa_headers else 'NONE'}")

        csrfc = raw.get('csrfc') or ''
        api_headers = {
            'X-ZCSRF-TOKEN': f'csrfp={csrfc}',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': BASE,
            'Referer': f'{BASE}/zcms/{SITE_ID}/pages',
            'X-Requested-With': 'XMLHttpRequest',
        }
        if isinstance(spa_headers, dict):
            api_headers.update(spa_headers)
        api_url = f"{BASE}/zs-site/api/v1/sites/{SITE_ID}/headerfootercode"
        publish_url = f"{BASE}/zs-site/api/v1/publish"

        # Fetch + log current header so the deploy log carries a rollback copy too.
        resp = context.request.get(api_url, headers=api_headers)
        print(f"GET status={resp.status}")
        if resp.status != 200:
            body = resp.text()[:500]
            print(f"FATAL: GET failed status={resp.status} body={body}")
            browser.close()
            sys.exit(15)
        print(f"GET raw body (first 800 chars): {resp.text()[:800]}")
        current = resp.json()
        snippet = current.get('snippet') if isinstance(current, dict) else None
        snippet = snippet or current
        old_header = snippet.get('headercode') or ''
        old_footer = snippet.get('footercode') or ''
        print(f"OLD header: {len(old_header)} chars; first 240:\n  {old_header[:240]}")
        Path('/tmp/bb-old-header.txt').write_text(old_header)
        print('OLD header written to /tmp/bb-old-header.txt')

        if 'inject-home-v3.js' in old_header:
            print('NOTE: header already references v3. Re-saving anyway to ensure parity.')

        save_resp = context.request.post(
            api_url,
            headers=api_headers,
            data=json.dumps({'snippet': {'headercode': NEW_HEADER, 'footercode': old_footer}}),
        )
        print(f"Save: status={save_resp.status} body={save_resp.text()[:300]}")
        if save_resp.status != 200:
            print('FATAL: save failed')
            browser.close()
            sys.exit(16)

        pub_resp = context.request.post(publish_url, headers=api_headers, data='{}')
        print(f"Publish: status={pub_resp.status} body={pub_resp.text()[:300]}")
        if pub_resp.status not in (200, 202):
            print('FATAL: publish failed')
            browser.close()
            sys.exit(17)

        verify_resp = context.request.get(api_url, headers=api_headers)
        print(f"VERIFY raw body (first 800 chars): {verify_resp.text()[:800]}")
        verify = verify_resp.json()
        v_snip = verify.get('snippet') if isinstance(verify, dict) else verify
        v_snip = v_snip or verify
        v_header = (v_snip or {}).get('headercode') or ''
        Path('/tmp/bb-new-header.txt').write_text(v_header)
        print('NEW header written to /tmp/bb-new-header.txt')

        v3_count = len(re.findall(r'inject-[a-z-]+-v3\.js', v_header))
        v2_count = len(re.findall(r'inject-[a-z-]+-v2\.js', v_header))
        print(f"VERIFY: v3 refs={v3_count}, v2 refs={v2_count}")
        if v3_count != 5 or v2_count != 0:
            print('VERIFY FAIL: header does not match expected v3 routing')
            browser.close()
            sys.exit(20)

        browser.close()
        print('DONE. butlerbutton.co header now routes all 5 pages to inject-*-v3.js?v=3.')


if __name__ == '__main__':
    main()
