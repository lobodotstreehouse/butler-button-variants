/**
 * Bumps `?v=N` cache-bust on ALL v3 inject scripts in the Zoho header
 * code, then publishes. Use after any change to zoho-inject/*v3*.js
 * (incl. the Supabase booking-API rewrite).
 *
 * Usage:
 *   node playwright/60-bump-all-v3-inject-versions.js
 *
 * Flow (mirrors 04-bump-home-inject-version.js):
 *   1. Launch visible Chromium (reuses zoho-auth.json if present)
 *   2. Navigate to header code editor for SITE_ID
 *   3. Read header code via $X SPA context
 *   4. Bump ?v=N for every inject-*-v3.js reference (each independently)
 *   5. Save via $X.post /zs-site/api/v1/sites/<id>/headerfootercode
 *   6. Publish via $X.post /zs-site/api/v1/publish
 *   7. Persist updated auth state back to zoho-auth.json
 *
 * Targets (all five v3 injects):
 *   inject-home-v3.js
 *   inject-advisor-v3.js
 *   inject-concierge-v3.js
 *   inject-trip-planning-v3.js
 *   inject-supplier-code-v3.js
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

const TARGETS = [
  'inject-home-v3.js',
  'inject-advisor-v3.js',
  'inject-concierge-v3.js',
  'inject-trip-planning-v3.js',
  'inject-supplier-code-v3.js',
];

function log(...a) { console.log('[bump-v3]', ...a); }

function bumpOne(headercode, filename) {
  const re = new RegExp(filename.replace(/\./g, '\\.') + '\\?v=(\\d+)', '');
  const m = headercode.match(re);
  if (!m) return { ok: false, reason: 'not-found', filename };
  const oldV = parseInt(m[1], 10);
  const newV = oldV + 1;
  const reAll = new RegExp(filename.replace(/\./g, '\\.') + '\\?v=\\d+', 'g');
  const next = headercode.replace(reAll, `${filename}?v=${newV}`);
  return { ok: true, filename, oldV, newV, headercode: next };
}

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

  await page.waitForURL(url => {
    const s = url.toString();
    return s.includes('zohositescontent.in') && s.includes('/pages');
  }, { timeout: LOGIN_WAIT_MS });
  log('Pages list loaded');
  await page.waitForTimeout(3000);

  log('Navigating to header code editor');
  await page.goto(HEADER_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(5000);

  await page.waitForFunction(
    () => typeof window.$X === 'object' && typeof window.app === 'object',
    { timeout: 30000 }
  );
  log('$X SPA context ready');

  const current = await page.evaluate(async (siteId) => {
    return await new Promise((resolve, reject) => {
      window.$X.get({
        url: `/zs-site/api/v1/sites/${siteId}/headerfootercode`,
        headers: window.app.getHeaders(),
        success: resolve,
        error: reject,
      });
    });
  }, SITE_ID);
  log('Fetched current header code payload');

  const snippet = (current && current.snippet) || current;
  let headercode = snippet.headercode || '';
  const footercode = snippet.footercode || '';

  const results = [];
  for (const filename of TARGETS) {
    const r = bumpOne(headercode, filename);
    results.push(r);
    if (r.ok) {
      headercode = r.headercode;
      log(`  ${filename}: ${r.oldV} -> ${r.newV}`);
    } else {
      log(`  ${filename}: SKIPPED (${r.reason})`);
    }
  }

  const anyBumped = results.some(r => r.ok);
  if (!anyBumped) {
    console.error('[bump-v3] ERROR: no v3 inject references found in header code');
    console.error(headercode);
    process.exit(2);
  }

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
  }, { siteId: SITE_ID, headercode, footercode });
  log('Save response:', JSON.stringify(saveResult).slice(0, 200));

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

  await context.storageState({ path: STATE_PATH });
  log(`Auth saved -> ${STATE_PATH}`);

  await browser.close();

  log('DONE. Bumped versions:');
  for (const r of results) {
    if (r.ok) log(`  ${r.filename}: ?v=${r.newV}`);
    else log(`  ${r.filename}: skipped (${r.reason})`);
  }
}

main().catch(err => {
  console.error('[bump-v3] FAILED:', err);
  process.exit(1);
});
