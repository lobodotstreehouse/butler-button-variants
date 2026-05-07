/**
 * Step 2: Set native Zoho page SEO title + meta description for all 4 pages.
 * Requires zoho-auth.json from 01-capture-auth.js first.
 *
 *   node playwright/02-set-seo-fields.js
 *
 * Strategy: navigate to each page's settings dialog via the Zoho Sites UI,
 * intercept the save network request to confirm the correct endpoint, then
 * fill and submit the SEO fields.
 */

const { chromium } = require('playwright');
const path = require('path');

const STATE_PATH = path.join(__dirname, 'zoho-auth.json');
const SITE_ID = '413198000000002010';
const EDITOR_BASE = `https://sitebuilder-60059075182.zohositescontent.in`;
const PAGES_URL = `${EDITOR_BASE}/zcms/${SITE_ID}/pages`;

const PAGES = [
  {
    name: 'Home',
    resource_id: '413198000000004653',
    seo_title: 'Butler Button | Personal Travel Expert - 100% Human, 150+ Countries',
    seo_desc: '100% human travel experts. 150+ countries. AI plans it, a human handles it, you enjoy it. On-demand concierge from $25. No membership required.',
  },
  {
    name: 'Trip Planning',
    resource_id: '413198000000047002',
    seo_title: 'AI Trip Planning with Human Expert Review | Butler Button',
    seo_desc: 'AI screens 200,000+ options. A human travel expert reviews it. Delivered in 24 hours. $25/country. 150+ countries. No membership required.',
  },
  {
    name: 'Concierge',
    resource_id: '413198000000002013',
    seo_title: 'On-Demand Human Travel Concierge - Not a Chatbot | Butler Button',
    seo_desc: 'A real human concierge who pre-reads your itinerary before you depart. 24/7 coverage. 97% of disruptions resolved under 60 min. Starting $25/day.',
  },
  {
    name: 'Travel Advisor',
    resource_id: '413198000000047014',
    seo_title: 'Private Travel Advisor Under Your Brand | Butler Button by VELTM',
    seo_desc: 'White-label travel advisor service for professionals. Butler Button delivers 5-star concierge under your brand. Your clients get a personal travel expert.',
  },
];

// Known-bad fields from direct PUT attempts:
// seo_title and seo_desc cause EXTRA_KEY_FOUND_IN_JSON from /zs-site/api/v1/pages/{id}
// So we must use the UI dialog. Track what the save request looks like.

async function waitForSelector(page, selector, timeout = 10000) {
  try {
    await page.waitForSelector(selector, { timeout });
    return true;
  } catch {
    return false;
  }
}

async function setPageSEO(page, pageData) {
  console.log(`\n--- Processing: ${pageData.name} (${pageData.resource_id}) ---`);

  // Navigate to pages list
  await page.goto(PAGES_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);

  // Intercept the save request so we can confirm endpoint + body
  const saveRequests = [];
  page.on('request', req => {
    const url = req.url();
    if (url.includes('/pages/') || url.includes('seo') || url.includes('page')) {
      const method = req.method();
      if (method === 'PUT' || method === 'POST') {
        saveRequests.push({ url, method, body: req.postData() });
      }
    }
  });

  // Zoho Sites page list: each page row has a settings/gear icon or three-dot menu.
  // Try to find the row containing this page's resource ID in a data attribute,
  // or locate it by name text, then click its settings trigger.

  // Approach 1: look for data-page-id or similar attribute
  const rowSelector = `[data-page-id="${pageData.resource_id}"], [data-id="${pageData.resource_id}"], [data-resource-id="${pageData.resource_id}"]`;
  let foundRow = await waitForSelector(page, rowSelector, 5000);

  let settingsTrigger = null;

  if (foundRow) {
    const row = page.locator(rowSelector).first();
    // Look for a gear/settings icon within the row
    settingsTrigger = row.locator('button, [class*="setting"], [class*="gear"], [class*="more"], [title*="setting" i], [title*="properties" i]').first();
  } else {
    // Approach 2: find by page name text in the list, then sibling/parent action button
    console.log(`  Row by ID not found, trying by page name: "${pageData.name}"`);
    const nameLocator = page.locator(`text="${pageData.name}"`).first();
    const nameVisible = await nameLocator.isVisible().catch(() => false);
    if (nameVisible) {
      const parentRow = nameLocator.locator('xpath=ancestor::*[contains(@class,"page") or contains(@class,"row") or contains(@class,"item")][1]');
      settingsTrigger = parentRow.locator('button, [class*="setting"], [class*="more"], [class*="options"]').first();
    }
  }

  if (!settingsTrigger) {
    console.error(`  Could not locate settings trigger for ${pageData.name}. Taking screenshot for debug.`);
    await page.screenshot({ path: path.join(__dirname, `debug-${pageData.resource_id}.png`) });
    return false;
  }

  // Click settings trigger
  await settingsTrigger.click({ timeout: 8000 }).catch(async () => {
    console.log('  Direct click failed, trying JS click...');
    await settingsTrigger.evaluate(el => el.click());
  });
  await page.waitForTimeout(1000);

  // Look for Page Properties or SEO option in the resulting menu/dialog
  const menuOptions = [
    'text="Page Properties"',
    'text="Properties"',
    'text="SEO"',
    'text="Settings"',
    '[class*="properties"]',
    '[class*="page-setting"]',
  ];

  let menuClicked = false;
  for (const opt of menuOptions) {
    const el = page.locator(opt).first();
    const visible = await el.isVisible().catch(() => false);
    if (visible) {
      console.log(`  Found menu option: ${opt}`);
      await el.click();
      menuClicked = true;
      await page.waitForTimeout(1500);
      break;
    }
  }

  if (!menuClicked) {
    console.error(`  No properties/SEO menu found for ${pageData.name}. Screenshot saved.`);
    await page.screenshot({ path: path.join(__dirname, `debug-menu-${pageData.resource_id}.png`) });
    // Dump visible text to help diagnose
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 2000));
    console.log('  Page text sample:', bodyText);
    return false;
  }

  // Now look for SEO title and description fields in the dialog
  // Zoho uses labels like "SEO Title", "Meta Description", "Page Title", "Description"
  const seoTitleSelectors = [
    'input[name*="seo_title" i]',
    'input[placeholder*="SEO title" i]',
    'input[placeholder*="title" i]',
    '[label*="SEO Title"] input',
    'input[id*="seo" i]',
    '.seo-title input',
    // fallback: first text input in dialog
  ];

  const seoDescSelectors = [
    'textarea[name*="description" i]',
    'textarea[placeholder*="description" i]',
    'textarea[placeholder*="meta" i]',
    'input[name*="description" i]',
    '[label*="description"] textarea',
    '.meta-desc textarea',
    '.seo-desc textarea',
  ];

  let titleField = null;
  for (const sel of seoTitleSelectors) {
    const el = page.locator(sel).first();
    const visible = await el.isVisible().catch(() => false);
    if (visible) { titleField = el; console.log(`  SEO title field: ${sel}`); break; }
  }

  let descField = null;
  for (const sel of seoDescSelectors) {
    const el = page.locator(sel).first();
    const visible = await el.isVisible().catch(() => false);
    if (visible) { descField = el; console.log(`  SEO desc field: ${sel}`); break; }
  }

  // If we haven't found specific fields, dump dialog HTML for inspection
  if (!titleField || !descField) {
    console.warn('  Could not locate SEO fields by selector. Dumping dialog HTML...');
    const dialogHTML = await page.evaluate(() => {
      const dialogs = document.querySelectorAll('[class*="dialog"], [class*="modal"], [class*="panel"], [role="dialog"]');
      return Array.from(dialogs).map(d => d.outerHTML.substring(0, 3000)).join('\n---\n');
    });
    console.log(dialogHTML || '  (no dialogs found)');
    await page.screenshot({ path: path.join(__dirname, `debug-dialog-${pageData.resource_id}.png`) });
    return false;
  }

  // Fill SEO title
  await titleField.click();
  await titleField.selectText().catch(() => {});
  await page.keyboard.press('Control+a');
  await titleField.fill(pageData.seo_title);
  console.log(`  Set title: ${pageData.seo_title}`);

  // Fill SEO description
  await descField.click();
  await page.keyboard.press('Control+a');
  await descField.fill(pageData.seo_desc);
  console.log(`  Set desc: ${pageData.seo_desc}`);

  // Find and click Save button
  const saveSelectors = [
    'button:has-text("Save")',
    'button:has-text("Update")',
    'button:has-text("Done")',
    'button:has-text("Apply")',
    '[class*="save-btn"]',
    '[class*="saveBtn"]',
  ];

  let saved = false;
  for (const sel of saveSelectors) {
    const btn = page.locator(sel).first();
    const visible = await btn.isVisible().catch(() => false);
    if (visible) {
      console.log(`  Clicking save: ${sel}`);

      // Wait for the network response after clicking
      const [response] = await Promise.all([
        page.waitForResponse(resp => {
          const url = resp.url();
          return (url.includes('/pages') || url.includes('/page/') || url.includes('seo')) &&
                 (resp.status() === 200 || resp.status() === 201);
        }, { timeout: 10000 }).catch(() => null),
        btn.click(),
      ]);

      if (response) {
        console.log(`  Save response: ${response.status()} ${response.url()}`);
        const body = await response.json().catch(() => ({}));
        console.log('  Response body:', JSON.stringify(body).substring(0, 500));
        // Log the request that triggered this
        console.log('  Intercepted save requests:', JSON.stringify(saveRequests, null, 2));
      }

      saved = true;
      await page.waitForTimeout(2000);
      break;
    }
  }

  if (!saved) {
    console.error(`  No save button found for ${pageData.name}`);
    await page.screenshot({ path: path.join(__dirname, `debug-save-${pageData.resource_id}.png`) });
    return false;
  }

  console.log(`  Done: ${pageData.name}`);
  return true;
}

async function main() {
  const fs = require('fs');
  if (!fs.existsSync(STATE_PATH)) {
    console.error(`Auth state not found at ${STATE_PATH}. Run 01-capture-auth.js first.`);
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const context = await browser.newContext({
    storageState: STATE_PATH,
    viewport: { width: 1400, height: 900 },
  });
  const page = await context.newPage();

  // Verify auth is still valid
  await page.goto(PAGES_URL, { waitUntil: 'networkidle', timeout: 30000 });
  const currentUrl = page.url();
  if (currentUrl.includes('accounts.zoho') || currentUrl.includes('login')) {
    console.error('Session expired. Re-run 01-capture-auth.js to refresh auth.');
    await browser.close();
    process.exit(1);
  }
  console.log(`Auth OK. Current URL: ${currentUrl}`);

  const results = [];
  for (const pageData of PAGES) {
    const ok = await setPageSEO(page, pageData);
    results.push({ name: pageData.name, ok });
  }

  console.log('\n=== Results ===');
  results.forEach(r => console.log(`  ${r.ok ? 'OK' : 'FAIL'} ${r.name}`));

  await browser.close();
}

main().catch(err => { console.error(err); process.exit(1); });
