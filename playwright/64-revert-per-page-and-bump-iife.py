"""Cleanup + cutover:
  1. Revert all 5 pages' header_footer_code to empty (Zoho didn't honor them)
  2. Bump the site-wide header IIFE from ?v=6 to ?v=7 (forces global CDN refresh
     of Friday's butler-booking-api inject scripts)
  3. Publish
  4. Verify v=7 is live on all 5 routes
"""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE         = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID      = '413198000000002010'

PAGES = [
    ('concierge',      '413198000000002013'),
    ('trip-planning',  '413198000000047002'),
    ('travel-advisor', '413198000000047014'),
    ('supplier-code',  '413198000000054082'),
    ('home',           '413198000000004653'),
]

NEW_HEADER_IIFE = (
    '<script>(function(){'
    'var x=location.pathname.replace(/\\/+$/,"");'
    'var s=document.createElement("script");'
    'var b="https://lobodotstreehouse.github.io/butler-button-variants/zoho-inject/";'
    'if(x===""||x==="/index"){s.src=b+"inject-home-v3.js?v=7";}'
    'else if(x==="/trip-planning"){s.src=b+"inject-trip-planning-v3.js?v=7";}'
    'else if(x==="/concierge"){s.src=b+"inject-concierge-v3.js?v=7";}'
    'else if(x==="/travel-advisor"){s.src=b+"inject-advisor-v3.js?v=7";}'
    'else if(x==="/supplier-code"){s.src=b+"inject-supplier-code-v3.js?v=7";}'
    'else{return;}'
    'document.head.appendChild(s);'
    '})();</script>'
)


def build_cookies(raw):
    seen, cookies = set(), []
    for n, v in raw.items():
        if not v or not isinstance(v, str): continue
        if (n, v) in seen: continue
        seen.add((n, v))
        cookies.append({'name': n, 'value': v,
                        'domain': '.sitebuilder-60059075182.zohositescontent.in',
                        'path': '/', 'httpOnly': False, 'secure': True})
    return cookies


def main():
    raw = json.loads(Path(COOKIES_JSON).read_text())
    cookies = build_cookies(raw)
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=False, slow_mo=40)
        ctx = b.new_context(viewport={'width':1440,'height':900})
        ctx.add_cookies(cookies)
        p = ctx.new_page()
        p.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=60000)
        p.wait_for_timeout(2000)
        p.wait_for_function("typeof $X === 'object' && typeof app === 'object'", timeout=30000)
        spa = p.evaluate("() => app.getHeaders()")
        hdr = {
            'X-ZCSRF-TOKEN': f"csrfp={raw.get('csrfc','')}",
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': BASE,
            'Referer': f"{BASE}/zcms/{SITE_ID}/pages",
            'X-Requested-With': 'XMLHttpRequest',
        }
        if isinstance(spa, dict): hdr.update(spa)

        # 1. Revert per-page header_footer_code to empty
        print('=== REVERT per-page header_footer_code ===')
        for slug, rid in PAGES:
            url = f"{BASE}/zs-site/api/v1/pages/{rid}"
            body = {
                'header_flag': 2,  # restore to site-wide default
                'header_footer_code': {'headercode': '', 'footercode': ''},
            }
            r = ctx.request.put(url, headers=hdr, data=json.dumps(body))
            print(f"  {slug:<16} PUT {r.status}")
            if r.status != 200:
                print(f"    body: {r.text()[:200]}")

        # 2. Bump the site-wide header IIFE
        print('\n=== BUMP site-wide header IIFE to v=7 ===')
        hfc_url = f"{BASE}/zs-site/api/v1/sites/{SITE_ID}/headerfootercode"
        r = ctx.request.get(hfc_url, headers=hdr)
        if r.status != 200:
            print(f"FATAL GET: {r.status}")
            b.close(); sys.exit(15)
        cur = r.json()
        snippet = cur.get('snippet') if isinstance(cur, dict) else None
        snippet = snippet or cur
        old_header = (snippet or {}).get('headercode') or ''
        old_footer = (snippet or {}).get('footercode') or ''
        print(f"  current header: {len(old_header)} chars (preview: {old_header[:120]})")
        save_resp = ctx.request.post(
            hfc_url, headers=hdr,
            data=json.dumps({'snippet': {'headercode': NEW_HEADER_IIFE, 'footercode': old_footer}}),
        )
        print(f"  save: {save_resp.status}")
        if save_resp.status != 200:
            print(f"    body: {save_resp.text()[:300]}")
            b.close(); sys.exit(16)

        # 3. Publish
        print('\n=== PUBLISH ===')
        pub_url = f"{BASE}/zs-site/api/v1/publish"
        pub = ctx.request.post(pub_url, headers=hdr, data='{}')
        print(f"  publish: {pub.status}")
        if pub.status not in (200, 202):
            print(f"    body: {pub.text()[:300]}")
            b.close(); sys.exit(17)

        # 4. Verify v=7 is live
        print('\n=== VERIFY live ?v=7 ===')
        time.sleep(15)
        anon = b.new_context()
        verify = []
        for slug, _ in PAGES:
            url = 'https://www.butlerbutton.co/' if slug == 'home' else f'https://www.butlerbutton.co/{slug}'
            for attempt in range(4):
                resp = anon.request.get(url)
                t = resp.text()
                v7 = t.count('?v=7')
                v6 = t.count('?v=6')
                has_route = (slug if slug != 'home' else 'home') in t.lower()
                if v7 > 0 and v6 == 0:
                    break
                time.sleep(8)
            verify.append({'slug': slug, 'status': resp.status, 'v7_count': v7, 'v6_count': v6, 'attempts': attempt+1})
            print(f"  {slug:<16} status={resp.status} v7={v7} v6={v6} attempts={attempt+1}")

        b.close()

    Path('/tmp/cutover-verify.json').write_text(json.dumps(verify, indent=2))
    fail = any(r['v7_count'] == 0 or r['v6_count'] > 0 for r in verify)
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
