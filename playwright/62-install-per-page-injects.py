"""Install per-page header_footer_code blocks on butlerbutton.co, one slug
at a time. Each block is a one-line <script src=...> loader that pulls the
corresponding Friday-aligned inject-<slug>-v3.js from GitHub Pages with a
fresh ?v=7 cache-buster.

After all 5 are installed and individually verified, blank the site-wide
header IIFE (61-blank-site-header.py).

Order: concierge -> trip-planning -> travel-advisor -> supplier-code -> home
(home last because it's the highest-traffic landing).
"""
import json, sys, time, argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE         = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID      = '413198000000002010'
SNAP_DIR     = Path('/Users/openclaw/butler-button-variants/live-snapshots/butlerbutton-co-2026-05-11')
GH_BASE      = 'https://lobodotstreehouse.github.io/butler-button-variants/zoho-inject'

# slug -> (resource_id, inject_filename)
PAGES = [
    ('concierge',      '413198000000002013', 'inject-concierge-v3.js'),
    ('trip-planning',  '413198000000047002', 'inject-trip-planning-v3.js'),
    ('travel-advisor', '413198000000047014', 'inject-advisor-v3.js'),
    ('supplier-code',  '413198000000054082', 'inject-supplier-code-v3.js'),
    ('home',           '413198000000004653', 'inject-home-v3.js'),
]
CACHE_BUST = 'v=7'


def build_cookies(raw, domain):
    seen, cookies = set(), []
    for name, value in raw.items():
        if not value or not isinstance(value, str): continue
        if (name, value) in seen: continue
        seen.add((name, value))
        cookies.append({'name': name, 'value': value, 'domain': domain,
                        'path': '/', 'httpOnly': False, 'secure': True})
    return cookies


def loader_script(inject_filename):
    return ('<script>(function(){var s=document.createElement("script");'
            f's.src="{GH_BASE}/{inject_filename}?{CACHE_BUST}";'
            'document.head.appendChild(s);})();</script>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='Run for a single slug only (debug)')
    ap.add_argument('--dry-run', action='store_true', help='GET only, no PUT')
    args = ap.parse_args()

    raw = json.loads(Path(COOKIES_JSON).read_text())
    cookies = build_cookies(raw, '.sitebuilder-60059075182.zohositescontent.in')
    print(f"Loaded {len(cookies)} cookies | dry_run={args.dry_run} | only={args.only or 'ALL'}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=40)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(2000)

        if 'accounts.zoho' in page.url:
            print(f"PRECHECK FAIL session: {page.url}")
            browser.close()
            sys.exit(10)

        page.wait_for_function(
            "typeof window.$X === 'object' && typeof window.app === 'object'",
            timeout=30000,
        )
        spa_headers = None
        for _ in range(5):
            try:
                spa_headers = page.evaluate("() => window.app.getHeaders()")
                if spa_headers: break
            except Exception:
                page.wait_for_timeout(1500)

        csrfc = raw.get('csrfc') or ''
        hdr = {
            'X-ZCSRF-TOKEN': f'csrfp={csrfc}',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': BASE,
            'Referer': f'{BASE}/zcms/{SITE_ID}/pages',
            'X-Requested-With': 'XMLHttpRequest',
        }
        if isinstance(spa_headers, dict):
            hdr.update(spa_headers)

        results = []
        for slug, rid, inject_fn in PAGES:
            if args.only and slug != args.only:
                continue
            print(f"\n=== {slug} (rid={rid}) ===")
            new_header = loader_script(inject_fn)
            print(f"  New header ({len(new_header)} chars): {new_header}")

            # GET current page resource
            page_url = f"{BASE}/zs-site/api/v1/pages/{rid}"
            r = context.request.get(page_url, headers=hdr)
            if r.status != 200:
                print(f"  GET status={r.status} body={r.text()[:300]}")
                results.append({'slug': slug, 'rid': rid, 'status': 'GET_FAIL'})
                continue
            body = r.json()
            details = body.get('page_info', {}).get('page_details', {})
            current_hfc = details.get('header_footer_code', {}) or {}
            current_header = current_hfc.get('headercode') or ''
            current_footer = current_hfc.get('footercode') or ''
            print(f"  current headercode: {len(current_header)} chars; "
                  f"footercode: {len(current_footer)} chars")

            if args.dry_run:
                results.append({'slug': slug, 'rid': rid, 'status': 'DRY_RUN',
                                'current_len': len(current_header)})
                continue

            # PUT updated header_footer_code (flat shape — confirmed 200 by probe)
            patch = {
                'header_footer_code': {
                    'headercode': new_header,
                    'footercode': current_footer,
                }
            }
            put_resp = context.request.put(
                page_url, headers=hdr, data=json.dumps(patch),
            )
            print(f"  PUT status={put_resp.status}")
            if put_resp.status not in (200, 204):
                print(f"  body: {put_resp.text()[:500]}")
                results.append({'slug': slug, 'rid': rid, 'status': 'PUT_FAIL',
                                'put_status': put_resp.status,
                                'put_body': put_resp.text()[:300]})
                continue

            # Verify
            v = context.request.get(page_url, headers=hdr)
            if v.status != 200:
                results.append({'slug': slug, 'rid': rid, 'status': 'VERIFY_FAIL'})
                continue
            v_details = v.json().get('page_info', {}).get('page_details', {})
            v_header = (v_details.get('header_footer_code') or {}).get('headercode') or ''
            ok = (v_header == new_header)
            print(f"  VERIFY: stored header {len(v_header)} chars | match={ok}")
            results.append({'slug': slug, 'rid': rid,
                            'status': 'OK' if ok else 'MISMATCH',
                            'stored_len': len(v_header)})

        browser.close()

    Path('/tmp/install-results.json').write_text(json.dumps(results, indent=2))
    print('\n=== RESULTS ===')
    for r in results:
        print(f"  {r['slug']:<16} {r['status']}")
    fail = any(r['status'] not in ('OK', 'DRY_RUN') for r in results)
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
