"""Bump the site-wide header IIFE from ?v=6 (current rollback state) to ?v=9
to force a global CDN pull of commit 12745cc (parseCountries regex fix on top
of Friday's butler-booking-api purchase model). Then publish.
"""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID = '413198000000002010'

NEW_HEADER = (
    '<script>(function(){'
    'var x=location.pathname.replace(/\\/+$/,"");'
    'var s=document.createElement("script");'
    'var b="https://lobodotstreehouse.github.io/butler-button-variants/zoho-inject/";'
    'if(x===""||x==="/index"){s.src=b+"inject-home-v3.js?v=9";}'
    'else if(x==="/trip-planning"){s.src=b+"inject-trip-planning-v3.js?v=9";}'
    'else if(x==="/concierge"){s.src=b+"inject-concierge-v3.js?v=9";}'
    'else if(x==="/travel-advisor"){s.src=b+"inject-advisor-v3.js?v=9";}'
    'else if(x==="/supplier-code"){s.src=b+"inject-supplier-code-v3.js?v=9";}'
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
    # Wait briefly for GH Pages to propagate the new commit
    time.sleep(30)

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

        hfc_url = f"{BASE}/zs-site/api/v1/sites/{SITE_ID}/headerfootercode"
        cur = ctx.request.get(hfc_url, headers=hdr).json()
        snippet = cur.get('snippet') or cur
        old_footer = (snippet or {}).get('footercode') or ''
        r = ctx.request.post(hfc_url, headers=hdr,
            data=json.dumps({'snippet': {'headercode': NEW_HEADER, 'footercode': old_footer}}))
        print(f"save: {r.status}")
        if r.status != 200:
            print(f"  body: {r.text()[:300]}")
            b.close(); sys.exit(16)

        pub = ctx.request.post(f"{BASE}/zs-site/api/v1/publish", headers=hdr, data='{}')
        print(f"publish: {pub.status}")
        if pub.status not in (200, 202):
            print(f"  body: {pub.text()[:300]}")
            b.close(); sys.exit(17)

        # Verify CDN propagation + that the fix is in the served bytes
        time.sleep(15)
        anon = b.new_context()
        ok_count = 0
        for slug, fname in [
            ('home','inject-home-v3.js'),
            ('trip-planning','inject-trip-planning-v3.js'),
            ('concierge','inject-concierge-v3.js'),
            ('travel-advisor','inject-advisor-v3.js'),
            ('supplier-code','inject-supplier-code-v3.js'),
        ]:
            url = f"https://lobodotstreehouse.github.io/butler-button-variants/zoho-inject/{fname}?v=9"
            for attempt in range(4):
                t = anon.request.get(url).text()
                has_fix = '\\\\s*(?:,|\\\\/' in t  # python string for the doubled regex
                if has_fix: break
                time.sleep(8)
            page_url = 'https://www.butlerbutton.co/' if slug == 'home' else f'https://www.butlerbutton.co/{slug}'
            live = anon.request.get(page_url).text()
            v8 = live.count('?v=9')
            v6 = live.count('?v=6')
            print(f"  {slug:<16} fix_in_cdn={has_fix} live_v8={v8} live_v6={v6}")
            if has_fix and v8 > 0 and v6 == 0:
                ok_count += 1

        b.close()
    print(f"\nDONE. {ok_count}/5 routes confirmed.")


if __name__ == '__main__':
    main()
