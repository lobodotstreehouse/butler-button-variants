"""
Sets native Zoho SEO title + description for all 4 pages via the
"Edit page info" UI dialog. Injects decrypted Chrome cookies so no
manual login is needed.

  python3 playwright/03-intercept-seo-save.py
"""

import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_JSON = '/tmp/zoho_cookies_clean.json'
BASE = 'https://sitebuilder-60059075182.zohositescontent.in'
SITE_ID = '413198000000002010'
SCRIPT_DIR = Path(__file__).parent

PAGES = [
    {
        'name': 'Home',
        'id': '413198000000004653',
        'seo_title': 'Butler Button | Personal Travel Expert - 100% Human, 150+ Countries',
        'seo_desc': '100% human travel experts. 150+ countries. AI plans it, a human handles it, you enjoy it. On-demand concierge from $25. No membership required.',
    },
    {
        'name': 'Trip Planning',
        'id': '413198000000047002',
        'seo_title': 'AI Trip Planning with Human Expert Review | Butler Button',
        'seo_desc': 'AI screens 200,000+ options. A human travel expert reviews it. Delivered in 24 hours. $25/country. 150+ countries. No membership required.',
    },
    {
        'name': 'Concierge',
        'id': '413198000000002013',
        'seo_title': 'On-Demand Human Travel Concierge - Not a Chatbot | Butler Button',
        'seo_desc': 'A real human concierge who pre-reads your itinerary before you depart. 24/7 coverage. 97% of disruptions resolved under 60 min. Starting $25/day.',
    },
    {
        'name': 'Travel Advisor',
        'id': '413198000000047014',
        'seo_title': 'Private Travel Advisor Under Your Brand | Butler Button by VELTM',
        'seo_desc': 'White-label travel advisor service for professionals. Butler Button delivers 5-star concierge under your brand. Your clients get a personal travel expert.',
    },
]


def build_cookies(raw: dict) -> list:
    seen = set()
    cookies = []
    for name, value in raw.items():
        if not value or not isinstance(value, str):
            continue
        key = (name, value)
        if key in seen:
            continue
        seen.add(key)
        cookies.append({
            'name': name,
            'value': value,
            'domain': '.sitebuilder-60059075182.zohositescontent.in',
            'path': '/',
            'httpOnly': False,
            'secure': True,
        })
    return cookies


def screenshot(page, label):
    try:
        page.screenshot(path=str(SCRIPT_DIR / f"{label}.png"), timeout=10000)
    except Exception as e:
        print(f"  [screenshot failed: {e}]")


def process_page(context, page_data, all_requests):
    print(f"\n--- {page_data['name']} ({page_data['id']}) ---")
    page = context.new_page()

    def capture(req):
        if req.method in ('PUT', 'POST') and '/pages' in req.url and 'api' in req.url:
            body = req.post_data or ''
            hdrs = dict(req.headers)
            entry = {
                'page': page_data['name'],
                'method': req.method,
                'url': req.url,
                'body': body,
                'csrf': hdrs.get('x-zcsrf-token', ''),
            }
            all_requests.append(entry)
            print(f"  *** CAPTURED {req.method} {req.url}")
            print(f"      body: {body[:400]}")
            print(f"      csrf: {hdrs.get('x-zcsrf-token','')[:80]}")

    page.on('request', capture)

    pages_url = f"{BASE}/zcms/{SITE_ID}/pages"
    page.goto(pages_url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(2000)
    screenshot(page, f"s01-{page_data['id']}-list")

    # Click "Edit page info" for this specific page row.
    # The link text is exactly "Edit page info" and it's in the same row as the page name.
    clicked = page.evaluate("""(pageName) => {
        // Find the row containing this page name
        for (const el of document.querySelectorAll('a, span, td, div')) {
            if (el.children.length === 0 && (el.innerText || '').trim() === pageName) {
                // Walk up to the row
                let row = el.closest('tr, li, [class*="item"], [class*="row"]') || el.parentElement;
                if (!row) continue;
                // Find "Edit page info" link in this row
                for (const a of row.querySelectorAll('a, button, span')) {
                    if ((a.innerText || '').trim() === 'Edit page info') {
                        a.click();
                        return 'clicked Edit page info in row: ' + row.tagName + '.' + row.className.substring(0,40);
                    }
                }
            }
        }
        // Fallback: click any "Edit page info" link (first visible one matching the page)
        for (const a of document.querySelectorAll('a[href*="' + pageName.toLowerCase().replace(/ /g,'-') + '"], a')) {
            if ((a.innerText || '').trim() === 'Edit page info' && a.offsetParent) {
                a.click();
                return 'fallback Edit page info: ' + a.href;
            }
        }
        return 'not found';
    }""", page_data['name'])
    print(f"  Edit page info click: {clicked}")
    page.wait_for_timeout(3000)
    screenshot(page, f"s02-{page_data['id']}-dialog")

    # The dialog has tabs: General, SEO, Options. Click SEO tab.
    seo_tab = page.evaluate("""() => {
        // data-tab="seo" or li with text "SEO"
        for (const el of document.querySelectorAll('[data-tab="seo"], li, a, button')) {
            const t = (el.innerText || '').trim();
            if (t === 'SEO' && el.offsetParent) {
                el.click();
                return 'clicked SEO tab: ' + el.tagName + '.' + el.className.substring(0,40);
            }
        }
        return 'SEO tab not found';
    }""")
    print(f"  SEO tab: {seo_tab}")
    page.wait_for_timeout(1000)
    screenshot(page, f"s03-{page_data['id']}-seo-tab")

    # Dump dialog HTML for debug
    dialog_info = page.evaluate("""() => {
        const visible = [];
        for (const el of document.querySelectorAll('[class*="dialog"], [class*="modal"], [class*="panel"], [class*="popup"], [role="dialog"], [class*="pagedetails"], [class*="page-prop"]')) {
            if (el.offsetParent !== null) {
                visible.push({
                    tag: el.tagName,
                    classes: el.className.substring(0, 60),
                    id: el.id,
                    html: el.innerHTML.substring(0, 2000),
                });
            }
        }
        return visible;
    }""")
    if dialog_info:
        print(f"  Visible dialogs: {len(dialog_info)}")
        for d in dialog_info:
            print(f"    {d['tag']}#{d['id']}.{d['classes'][:40]}")
        # Save first dialog HTML for inspection
        (SCRIPT_DIR / f"dbg-dialog-{page_data['id']}.html").write_text(
            dialog_info[0]['html'] if dialog_info else ''
        )
    else:
        # No standard dialog -- dump all visible forms/inputs
        forms_info = page.evaluate("""() => {
            const inputs = document.querySelectorAll('input[type="text"], textarea');
            return Array.from(inputs).filter(el => el.offsetParent !== null).map(el => ({
                tag: el.tagName,
                name: el.name,
                id: el.id,
                dataBind: el.getAttribute('data-bind'),
                placeholder: el.placeholder,
                value: el.value.substring(0, 50),
            }));
        }""")
        print(f"  No dialogs. Visible inputs: {len(forms_info)}")
        for inp in forms_info[:10]:
            print(f"    {inp}")

    # Fill SEO title field
    filled = page.evaluate("""([title, desc]) => {
        const log = [];
        const titleSels = [
            '[data-bind="page_info.seo.title"]',
            '[data-bind*="seo.title"]',
            '#seo-c input[type="text"]',
            'input.form-control[type="text"]',
            'input.sites-inputtext',
        ];
        const descSels = [
            '[data-bind="page_info.seo.description"]',
            '[data-bind*="seo.description"]',
            '#seo-c textarea',
            'textarea.form-control',
            'textarea.sites-textarea',
        ];

        function setField(el, val) {
            // Use native input value setter to trigger React/Angular bindings
            const nativeSetter = Object.getOwnPropertyDescriptor(el.__proto__ || Object.getPrototypeOf(el), 'value');
            if (nativeSetter && nativeSetter.set) {
                nativeSetter.set.call(el, val);
            } else {
                el.value = val;
            }
            ['input', 'change', 'keyup', 'blur'].forEach(evt =>
                el.dispatchEvent(new Event(evt, {bubbles: true}))
            );
        }

        let titleEl = null;
        for (const sel of titleSels) {
            const el = document.querySelector(sel);
            if (el && el.offsetParent !== null) { titleEl = el; log.push('title:' + sel); break; }
        }
        let descEl = null;
        for (const sel of descSels) {
            const el = document.querySelector(sel);
            if (el && el.offsetParent !== null) { descEl = el; log.push('desc:' + sel); break; }
        }

        if (titleEl) setField(titleEl, title);
        else log.push('NO_TITLE');
        if (descEl) setField(descEl, desc);
        else log.push('NO_DESC');

        return {log, titleFound: !!titleEl, descFound: !!descEl,
                titleVal: titleEl ? titleEl.value : null,
                descVal: descEl ? descEl.value.substring(0, 80) : null};
    }""", [page_data['seo_title'], page_data['seo_desc']])
    print(f"  Fill: {filled}")
    page.wait_for_timeout(500)

    if not filled.get('titleFound') and not filled.get('descFound'):
        print(f"  WARN: no SEO fields found. Check dbg-dialog-{page_data['id']}.html")
        page.close()
        return False

    # Click Save button
    saved = page.evaluate("""() => {
        // Look for Save button by text in visible area
        for (const btn of document.querySelectorAll('button, [class*="btn"]')) {
            const t = (btn.innerText || '').trim();
            if ((t === 'Save' || t === 'Update' || t === 'Done') && btn.offsetParent) {
                btn.click();
                return 'Save clicked: ' + t + ' class=' + btn.className.substring(0,40);
            }
        }
        return 'no save button';
    }""")
    print(f"  Save: {saved}")
    page.wait_for_timeout(3000)
    screenshot(page, f"s04-{page_data['id']}-after-save")

    page.close()
    return True


def main():
    raw = json.loads(Path(COOKIES_JSON).read_text())
    cookies = build_cookies(raw)
    print(f"Loaded {len(cookies)} cookies")

    all_requests = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=80)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)

        # Auth check
        page = context.new_page()
        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(2000)
        url = page.url
        print(f"Auth: {url}")
        if 'accounts.zoho' in url or 'login' in url:
            print("Session expired.")
            browser.close()
            sys.exit(1)
        print("Auth OK")
        page.close()

        results = []
        for p in PAGES:
            ok = process_page(context, p, all_requests)
            results.append({'name': p['name'], 'ok': ok})

        browser.close()

    print("\n=== RESULTS ===")
    for r in results:
        print(f"  {'OK' if r['ok'] else 'FAIL'} {r['name']}")

    if all_requests:
        out = SCRIPT_DIR / 'debug-save-requests.json'
        out.write_text(json.dumps(all_requests, indent=2))
        print(f"\nCaptured {len(all_requests)} save request(s) -> {out}")
        print(json.dumps(all_requests[0], indent=2))


if __name__ == '__main__':
    main()
