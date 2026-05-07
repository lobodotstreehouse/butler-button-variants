"""
Fetch and search v2settingsbundle.js for publish_status handling, domain verification,
and the customDomainDNS=false branch. Also check if domain needs re-adding or verify.
"""
import json, sys, re
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

    settings_bundle = {}

    def capture_response(resp):
        if 'v2settingsbundle' in resp.url:
            try:
                settings_bundle[resp.url] = resp.text()
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', capture_response)

        page.goto(f"{BASE}/zcms/{SITE_ID}/pages", wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(3000)

        # Load publish dialog to trigger loading settings JS
        page.goto(f"{BASE}/zcms/{SITE_ID}/settings/domains",
                  wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(4000)

        browser.close()

    print(f"Loaded {len(settings_bundle)} settings bundle files")

    for url, body in settings_bundle.items():
        print(f"\nBundle: {url[-80:]}")
        print(f"Size: {len(body)} chars")

        # Find all occurrences of publish_status
        for pattern in [r'publish_status', r'customDomainDNS', r'CUSTOM_DOMAIN', r'dns_not',
                        r'verified', r'domain.*verify', r'verify.*domain']:
            matches = [(m.start(), body[max(0,m.start()-100):m.start()+200])
                       for m in re.finditer(pattern, body, re.IGNORECASE)]
            if matches:
                print(f"\n  -- Pattern: '{pattern}' ({len(matches)} hits) --")
                for start, snippet in matches[:3]:
                    print(f"    ...{snippet.strip()}...")

        # Find the block containing publish_status == 103
        idx = body.find('publish_status == 103')
        if idx >= 0:
            print(f"\n  === publish_status == 103 block ===")
            print(f"  {body[max(0,idx-300):idx+500]}")

        # Find the CUSTOM_DOMAIN_DNS_NOT_UPDATED comment
        idx2 = body.find('CUSTOM_DOMAIN_DNS_NOT_UPDATED')
        if idx2 >= 0:
            print(f"\n  === CUSTOM_DOMAIN_DNS_NOT_UPDATED block ===")
            print(f"  {body[max(0,idx2-300):idx2+500]}")

        # Find domain verification
        idx3 = body.find('verifyDomain')
        if idx3 >= 0:
            print(f"\n  === verifyDomain block ===")
            print(f"  {body[max(0,idx3-100):idx3+400]}")

        idx4 = body.find('domain/verify')
        if idx4 >= 0:
            print(f"\n  === domain/verify endpoint ===")
            print(f"  {body[max(0,idx4-100):idx4+400]}")

        # Find what sets customDomainDNS
        for match in re.finditer(r'customDomainDNS', body):
            idx = match.start()
            print(f"\n  customDomainDNS at {idx}:")
            print(f"  {body[max(0,idx-200):idx+200]}")


if __name__ == '__main__':
    main()
