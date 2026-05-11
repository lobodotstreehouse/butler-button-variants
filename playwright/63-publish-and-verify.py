"""Publish the butlerbutton.co Zoho Site and verify the per-page header_footer_code
blocks landed on the live HTML. Run after 62-install-per-page-injects.py.
"""
import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE         = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID      = '413198000000002010'

EXPECTED_LOADERS = {
    'home':           'inject-home-v3.js?v=7',
    'trip-planning':  'inject-trip-planning-v3.js?v=7',
    'concierge':      'inject-concierge-v3.js?v=7',
    'travel-advisor': 'inject-advisor-v3.js?v=7',
    'supplier-code':  'inject-supplier-code-v3.js?v=7',
}


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
        spa_hdr = p.evaluate("() => app.getHeaders()")
        hdr = {
            'X-ZCSRF-TOKEN': f"csrfp={raw.get('csrfc','')}",
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': BASE,
            'Referer': f"{BASE}/zcms/{SITE_ID}/pages",
            'X-Requested-With': 'XMLHttpRequest',
        }
        if isinstance(spa_hdr, dict): hdr.update(spa_hdr)

        pub_url = f"{BASE}/zs-site/api/v1/publish"
        print(f"Publishing via POST {pub_url}")
        r = ctx.request.post(pub_url, headers=hdr, data='{}')
        print(f"  status={r.status} body={r.text()[:300]}")
        if r.status not in (200, 202):
            print('FATAL: publish failed')
            b.close()
            sys.exit(20)

        # Wait for CDN to propagate (typically <30s)
        time.sleep(15)

        # Probe each route via unauth context.request
        anon = b.new_context()  # no cookies
        anon_p = anon.new_page()
        results = []
        for slug, expected_loader in EXPECTED_LOADERS.items():
            url = 'https://www.butlerbutton.co/' if slug == 'home' else f'https://www.butlerbutton.co/{slug}'
            for attempt in range(3):
                resp = anon.request.get(url)
                html = resp.text()
                has_loader = expected_loader in html
                # Also check whether the site-wide header IIFE is still loading inject-{slug}-v3.js?v=6
                has_old_iife = f"inject-{slug.replace('home','home').replace('travel-advisor','advisor')}-v3.js?v=6" in html
                if has_loader:
                    break
                time.sleep(8)
            results.append({'slug': slug, 'url': url, 'status': resp.status,
                            'has_loader': has_loader, 'has_old_iife': has_old_iife,
                            'attempts': attempt + 1})
            print(f"  {slug:<16} status={resp.status} loader_present={has_loader} old_iife_still={has_old_iife} attempts={attempt+1}")

        b.close()

    Path('/tmp/publish-verify.json').write_text(json.dumps(results, indent=2))
    fail = any(not r['has_loader'] for r in results)
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
