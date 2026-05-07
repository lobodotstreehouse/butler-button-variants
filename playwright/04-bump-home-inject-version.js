/**
 * Bumps inject-home-v2.js?v=N in go.veltmtours.com header code, then publishes.
 *
 * Usage:
 *   node playwright/04-bump-home-inject-version.js
 *
 * Flow:
 *   1. Launch visible Chromium (reuses zoho-auth.json if present)
 *   2. If not logged in, waits up to 5 minutes for manual login
 *   3. Navigates to header code editor for site 413198000000002010
 *   4. Reads current header code via $X SPA context, regex-bumps ?v=N for inject-home
 *   5. Saves via $X.post /zs-site/api/v1/sites/413198000000002010/headerfootercode
 *   6. Publishes via $X.post /zs-site/api/v1/publish
 *   7. Persists updated auth state back to zoho-auth.json
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SITE_ID       = '413198000000002010';
const EDITOR_DOMAIN = 'sitebuilder-60059075182.zohositescontent.in';
const HEADER_URL    = `https://${EDITOR_DOMAIN}/zcms/${SITE_ID}/settings/code/header`;
const PAGES_URL     = `https://${EDITOR_DOMAIN}/zcms/${SITE_ID}/pages`;
const STATE_PATH    = path.join(__dirname, 'zoho-auth.json');
const LOGIN_WAIT_MS = 5 * 60 * 1000;

function log(...a) { console.log('[bump]', ...a); }

async function main() {
  const hasAuth = fs.existsSync(STATE_PATH);
  log(hasAuth ? 'Reusing saved auth' : 'No saved auth, will wait for manual login');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    storageState: hasAuth ? STATE_PATH : undefined,
  });
  const page = await context.newPage();

  log(`Navigating to ${PAGES_URL}`);
  await page.goto(PAGES_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });

  // Wait for either the pages list OR stay on login. If on login, wait for user.
  await page.waitForURL(url => {
    const s = url.toString();
    return s.includes('zohositescontent.in') && s.includes('/pages');
  }, { timeout: LOGIN_WAIT_MS });
  log('Pages list loaded');
  await page.waitForTimeout(3000);

  // Navigate into the header code editor
  log(`Navigating to header code editor`);
  await page.goto(HEADER_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(5000);

  // Wait until Zoho SPA ($X) is available
  await page.waitForFunction(() => typeof window.$X === 'object' && typeof window.app === 'object', { timeout: 30000 });
  log('$X SPA context ready');

  // Fetch current header code
  const current = await page.evaluate(async (siteId) => {
    const res = await new Promise((resolve, reject) => {
      window.$X.get({
        url: `/zs-site/api/v1/sites/${siteId}/headerfootercode`,
        headers: window.app.getHeaders(),
        success: resolve,
        error: reject,
      });
    });
    return res;
  }, SITE_ID);
  log('Fetched current header code payload');

  // Find and bump inject-home version
  const snippet = (current && current.snippet) || current;
  const headercode = snippet.headercode || '';
  const footercode = snippet.footercode || '';

  const m = headercode.match(/inject-home-v2\.js\?v=(\d+)/);
  if (!m) {
    console.error('[bump] ERROR: could not find inject-home-v2.js?v=N in header code');
    console.error(headercode);
    process.exit(2);
  }
  const oldV = parseInt(m[1], 10);
  const newV = oldV + 1;
  log(`inject-home-v2.js version: ${oldV} -> ${newV}`);

  const newHeader = headercode.replace(
    /inject-home-v2\.js\?v=\d+/g,
    `inject-home-v2.js?v=${newV}`
  );

  if (newHeader === headercode) {
    console.error('[bump] ERROR: replacement produced no change');
    process.exit(3);
  }

  // Save via $X.post
  const saveResult = await page.evaluate(async ({ siteId, headercode, footercode }) => {
    return await new Promise((resolve, reject) => {
      window.$X.post({
        url: `/zs-site/api/v1/sites/${siteId}/headerfootercode`,
        headers: window.app.getHeaders(),
        bodyJSON: { snippet: { headercode, footercode } },
        success: resolve,
        error: reject,
      });
    });
  }, { siteId: SITE_ID, headercode: newHeader, footercode });
  log('Save response:', JSON.stringify(saveResult).slice(0, 200));

  // Publish
  const publishResult = await page.evaluate(async () => {
    return await new Promise((resolve, reject) => {
      window.$X.post({
        url: '/zs-site/api/v1/publish',
        headers: window.app.getHeaders(),
        bodyJSON: {},
        success: resolve,
        error: reject,
      });
    });
  });
  log('Publish response:', JSON.stringify(publishResult).slice(0, 200));

  // Persist updated auth state
  await context.storageState({ path: STATE_PATH });
  log(`Auth saved -> ${STATE_PATH}`);

  await browser.close();
  log(`DONE. inject-home-v2.js bumped to ?v=${newV} and site published.`);
}

main().catch(err => {
  console.error('[bump] FAILED:', err);
  process.exit(1);
});
