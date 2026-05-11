"""Snapshot the live butlerbutton.co Zoho state before cutover:
  1) Header/footer code
  2) Each of 5 page resources (home, trip-planning, concierge, travel-advisor, supplier-code)
  3) Each live page's rendered HTML (unauth curl)

Writes to /Users/openclaw/butler-button-variants/live-snapshots/butlerbutton-co-2026-05-11/.
"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE         = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID      = '413198000000002010'
SNAP_DIR     = Path('/Users/openclaw/butler-button-variants/live-snapshots/butlerbutton-co-2026-05-11')

PAGES = {
    'home':           '413198000000004653',
    'trip-planning':  '413198000000047002',
    'concierge':      '413198000000002013',
    'travel-advisor': '413198000000047014',
    'supplier-code':  '413198000000054082',
}


def build_cookies(raw, domain):
    seen, cookies = set(), []
    for name, value in raw.items():
        if not value or not isinstance(value, str):
            continue
        if (name, value) in seen:
            continue
        seen.add((name, value))
        cookies.append({
            'name': name, 'value': value, 'domain': domain,
            'path': '/', 'httpOnly': False, 'secure': True,
        })
    return cookies


def main():
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    raw = json.loads(Path(COOKIES_JSON).read_text())
    cookies = build_cookies(raw, '.sitebuilder-60059075182.zohositescontent.in')
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
            browser.close()
            sys.exit(10)

        page.wait_for_function(
            "typeof window.$X === 'object' && typeof window.app === 'object'",
            timeout=30000,
        )
        spa_headers = None
        for attempt in range(5):
            try:
                spa_headers = page.evaluate("() => window.app.getHeaders()")
                break
            except Exception:
                page.wait_for_timeout(1500)

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

        # 1. Header / footer code
        hfc_url = f"{BASE}/zs-site/api/v1/sites/{SITE_ID}/headerfootercode"
        resp = context.request.get(hfc_url, headers=api_headers)
        print(f"headerfootercode GET status={resp.status}")
        if resp.status != 200:
            print(f"FATAL: headerfootercode GET failed body={resp.text()[:500]}")
            browser.close()
            sys.exit(15)
        hfc = resp.json()
        (SNAP_DIR / 'header-footer-code.json').write_text(json.dumps(hfc, indent=2))
        snippet = hfc.get('snippet') if isinstance(hfc, dict) else None
        snippet = snippet or hfc
        header = (snippet or {}).get('headercode') or ''
        footer = (snippet or {}).get('footercode') or ''
        (SNAP_DIR / 'header-iife.html').write_text(header)
        (SNAP_DIR / 'footer-code.html').write_text(footer)
        print(f"  header: {len(header)} chars -> header-iife.html")
        print(f"  footer: {len(footer)} chars -> footer-code.html")

        # 2. Per-page resource JSON
        for slug, rid in PAGES.items():
            page_url = f"{BASE}/zs-site/api/v1/pages/{rid}"
            r = context.request.get(page_url, headers=api_headers)
            print(f"page {slug} (rid={rid}) status={r.status}")
            if r.status != 200:
                print(f"  WARN body={r.text()[:300]}")
                continue
            body = r.json()
            (SNAP_DIR / f'page-{slug}.json').write_text(json.dumps(body, indent=2))
            # extract custom code block if present
            for key in ('snippet', 'page', 'data'):
                if isinstance(body, dict) and key in body and isinstance(body[key], dict):
                    body = body[key]
                    break
            # save any custom html/code field we find
            for cand in ('content', 'html', 'body', 'pagecontent', 'rawcontent', 'sections'):
                if cand in body and body[cand]:
                    (SNAP_DIR / f'page-{slug}-{cand}.txt').write_text(
                        json.dumps(body[cand], indent=2) if not isinstance(body[cand], str) else body[cand]
                    )
                    print(f"  -> page-{slug}-{cand}.txt")

        # 3. Live rendered HTML (unauth)
        unauth = context.new_page()
        for slug in PAGES:
            target = 'https://www.butlerbutton.co/' if slug == 'home' else f'https://www.butlerbutton.co/{slug}'
            try:
                resp = context.request.get(target)
                (SNAP_DIR / f'rendered-{slug}.html').write_text(resp.text())
                print(f"rendered {target} -> {resp.status} ({len(resp.text())} chars)")
            except Exception as e:
                print(f"rendered {target} FAILED: {e}")

        browser.close()
        print(f"\nDONE. Snapshots in {SNAP_DIR}")


if __name__ == '__main__':
    main()
