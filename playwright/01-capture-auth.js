/**
 * Captures Zoho auth session. Launches a visible browser, waits up to 5 minutes
 * for you to complete login and reach the pages list, then saves state automatically.
 * No readline/Enter needed -- just log in and the script detects it.
 *
 *   node playwright/01-capture-auth.js
 *
 * Writes: playwright/zoho-auth.json
 */

const { chromium } = require('playwright');
const path = require('path');

const EDITOR_URL = 'https://sitebuilder-60059075182.zohositescontent.in/zcms/413198000000002010/pages';
const STATE_PATH = path.join(__dirname, 'zoho-auth.json');
const TIMEOUT_MS = 5 * 60 * 1000;

async function main() {
  const browser = await chromium.launch({ headless: false, slowMo: 0 });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();

  console.log('Navigating to Zoho Sites editor...');
  await page.goto(EDITOR_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });

  console.log('Waiting for pages list to load (log in if prompted)...');
  // Wait until the URL is the pages list (not an accounts/login page)
  await page.waitForURL(url => {
    const s = url.toString();
    return s.includes('zohositescontent.in') && s.includes('/pages');
  }, { timeout: TIMEOUT_MS });

  // Extra settle time for SPA to fully load
  await page.waitForTimeout(3000);

  await context.storageState({ path: STATE_PATH });
  console.log(`Auth state saved to: ${STATE_PATH}`);
  await browser.close();
}

main().catch(err => { console.error(err); process.exit(1); });
