"""Rollback: site-wide header IIFE back to ?v=6 to restore the prior working
state (stale Fastly CDN nodes were serving the pre-Friday Payment-Link form).
Triggered because the ?v=7 cutover surfaced a template-literal regex escape
bug in Friday's parseCountries that crashes applyBody, leaving the modal
unrenderable.
"""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE         = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID      = '413198000000002010'
SNAP_DIR     = Path('/Users/openclaw/butler-button-variants/live-snapshots/butlerbutton-co-2026-05-11')

# Read the original header IIFE we snapshotted before cutover
ROLLBACK_HEADER = (SNAP_DIR / 'header-iife.html').read_text()


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
    print(f"Rollback header ({len(ROLLBACK_HEADER)} chars):\n  {ROLLBACK_HEADER[:200]}...")
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
        r = ctx.request.get(hfc_url, headers=hdr)
        snippet = r.json().get('snippet') or r.json()
        old_footer = (snippet or {}).get('footercode') or ''
        save_resp = ctx.request.post(
            hfc_url, headers=hdr,
            data=json.dumps({'snippet': {'headercode': ROLLBACK_HEADER, 'footercode': old_footer}}),
        )
        print(f"save: {save_resp.status}")
        if save_resp.status != 200:
            print(f"  body: {save_resp.text()[:300]}")
            b.close(); sys.exit(16)

        pub = ctx.request.post(f"{BASE}/zs-site/api/v1/publish", headers=hdr, data='{}')
        print(f"publish: {pub.status}")
        if pub.status not in (200, 202):
            print(f"  body: {pub.text()[:300]}")
            b.close(); sys.exit(17)

        time.sleep(15)
        anon = b.new_context()
        for slug in ('home','trip-planning','concierge','travel-advisor','supplier-code'):
            url = 'https://www.butlerbutton.co/' if slug == 'home' else f'https://www.butlerbutton.co/{slug}'
            for attempt in range(3):
                t = anon.request.get(url).text()
                v6 = t.count('?v=6')
                v7 = t.count('?v=7')
                if v6 > 0 and v7 == 0: break
                time.sleep(8)
            print(f"  {slug:<16} v6={v6} v7={v7} attempts={attempt+1}")
        b.close()
    print('DONE: rolled back to ?v=6 header IIFE')


if __name__ == '__main__':
    main()
