/**
 * Injects decrypted Chrome cookies into Playwright, opens page properties dialog
 * for the Home page, intercepts the save request to find the exact API format,
 * then sets SEO fields for all 4 pages.
 *
 *   node playwright/03-intercept-seo-save.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const COOKIES_JSON = '/tmp/zoho_cookies_clean.json';
const BASE = 'https://sitebuilder-60059075182.zohositescontent.in';
const SITE_ID = '413198000000002010';

const PAGES = [
  {
    name: 'Home',
    id: '413198000000004653',
    url_slug: 'home',
    seo_title: 'Butler Button | Personal Travel Expert - 100% Human, 150+ Countries',
    seo_desc: '100% human travel experts. 150+ countries. AI plans it, a human handles it, you enjoy it. On-demand concierge from $25. No membership required.',
  },
  {
    name: 'Trip Planning',
    id: '413198000000047002',
    url_slug: 'trip-planning',
    seo_title: 'AI Trip Planning with Human Expert Review | Butler Button',
    seo_desc: 'AI screens 200,000+ options. A human travel expert reviews it. Delivered in 24 hours. $25/country. 150+ countries. No membership required.',
  },
  {
    name: 'Concierge',
    id: '413198000000002013',
    url_slug: 'concierge',
    seo_title: 'On-Demand Human Travel Concierge - Not a Chatbot | Butler Button',
    seo_desc: 'A real human concierge who pre-reads your itinerary before you depart. 24/7 coverage. 97% of disruptions resolved under 60 min. Starting $25/day.',
  },
  {
    name: 'Travel Advisor',
    id: '413198000000047014',
    url_slug: 'travel-advisor',
    seo_title: 'Private Travel Advisor Under Your Brand | Butler Button by VELTM',
    seo_desc: 'White-label travel advisor service for professionals. Butler Button delivers 5-star concierge under your brand. Your clients get a personal travel expert.',
  },
];

function buildCookies(rawCookies) {
  const cookies = [];
  for (const [name, value] of Object.entries(rawCookies)) {
    if (!value || typeof value !== 'string') continue;
    // Deduplicate _zxor (same name twice in source)
    if (cookies.find(c => c.name === name && c.value === value)) continue;
    cookies.push({
      name,
      value,
      domain: '.sitebuilder-60059075182.zohositescontent.in',
      path: '/',
      httpOnly: false,
      secure: true,
    });
  }
  return cookies;
}

async function interceptSaveRequest(page) {
  return new Promise(resolve => {
    let captured = null;
    page.on('request', req => {
      const url = req.url();
      const method = req.method();
      if ((method === 'PUT' || method === 'POST') && url.includes('/pages')) {
        const body = req.postData();
        captured = { url, method, body, headers: req.headers() };
        console.log(`\n  INTERCEPTED: ${method} ${url}`);
        console.log(`  Body: ${body ? body.substring(0, 500) : '(empty)'}`);
        console.log(`  CSRF header: ${req.headers()['x-zcsrf-token'] || 'MISSING'}`);
        resolve(captured);
      }
    });
    // Also resolve after 15s if no request fires
    setTimeout(() => resolve(captured), 15000);
  });
}

async function setPageSEO(context, pageData, knownSaveFormat) {
  const page = await context.newPage();

  // Enable request interception
  const savePromise = interceptSaveRequest(page);

  const pagesUrl = `${BASE}/zcms/${SITE_ID}/pages`;
  await page.goto(pagesUrl, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);

  console.log(`  Current URL: ${page.url()}`);

  // Take screenshot for debug
  await page.screenshot({ path: path.join(__dirname, `debug-pages-${pageData.id}.png`) });

  // Dump page structure to find the page row
  const pageContent = await page.evaluate(() => {
    // Look for any element containing the page name or resource_id
    const rows = document.querySelectorAll('[data-resource-id], [data-page-id], [data-id], .sites-pageitem, .sites-listitem');
    return Array.from(rows).slice(0, 20).map(r => ({
      tag: r.tagName,
      classes: r.className,
      dataResourceId: r.getAttribute('data-resource-id'),
      dataPageId: r.getAttribute('data-page-id'),
      dataId: r.getAttribute('data-id'),
      text: r.innerText ? r.innerText.substring(0, 50) : '',
    }));
  });
  console.log('  Page items found:', JSON.stringify(pageContent.slice(0, 5)));

  // Try to find and click the settings for this page
  // Zoho Sites typically has a gear/settings icon per page row
  const settingsTriggers = await page.evaluate((pageId) => {
    // Look for elements with data attributes matching page id
    const byId = document.querySelectorAll(`[data-resource-id="${pageId}"], [data-page-id="${pageId}"], [data-id="${pageId}"]`);
    return Array.from(byId).map(el => ({
      tag: el.tagName,
      classes: el.className,
      text: el.innerText ? el.innerText.substring(0, 50) : '',
    }));
  }, pageData.id);
  console.log(`  Triggers for ${pageData.id}:`, settingsTriggers);

  // Try clicking settings icon - look for various patterns
  const clicked = await page.evaluate((pageId, pageName) => {
    // Pattern 1: find parent container with resource-id then find action button
    const containers = document.querySelectorAll(`[data-resource-id="${pageId}"]`);
    if (containers.length > 0) {
      const cont = containers[0].closest('[class*="item"], [class*="row"], li') || containers[0].parentElement;
      const btn = cont && cont.querySelector('[class*="setting"], [class*="gear"], [class*="more"], button');
      if (btn) { btn.click(); return `clicked btn in container: ${btn.className}`; }
    }
    // Pattern 2: find by page name text
    const allText = document.querySelectorAll('*');
    for (const el of allText) {
      if (el.children.length === 0 && el.innerText && el.innerText.trim() === pageName) {
        const row = el.closest('[class*="item"], [class*="row"], li') || el.parentElement;
        if (row) {
          const btn = row.querySelector('[class*="setting"], [class*="gear"], [class*="more"], [class*="opt"], button');
          if (btn) { btn.click(); return `clicked via name: ${btn.className}`; }
          // Try right-clicking the row
          row.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true }));
          return `context menu on row: ${row.className}`;
        }
      }
    }
    return 'nothing clicked';
  }, pageData.id, pageData.name);
  console.log(`  Click result: ${clicked}`);

  await page.waitForTimeout(2000);

  // Screenshot after click
  await page.screenshot({ path: path.join(__dirname, `debug-afterclick-${pageData.id}.png`) });

  // Look for any dialog/panel that opened with SEO fields
  const dialogs = await page.evaluate(() => {
    const elements = document.querySelectorAll('[class*="dialog"], [class*="modal"], [class*="panel"], [class*="popup"], [class*="overlay"], [role="dialog"]');
    return Array.from(elements)
      .filter(el => el.offsetParent !== null) // visible only
      .map(el => ({
        tag: el.tagName,
        classes: el.className,
        id: el.id,
        html: el.innerHTML.substring(0, 500),
      }));
  });
  console.log(`  Visible dialogs: ${dialogs.length}`);
  dialogs.forEach(d => console.log(`    ${d.tag}.${d.classes.substring(0,50)} id=${d.id}`));

  // If no dialog, dump full page body
  if (dialogs.length === 0) {
    const bodyHTML = await page.evaluate(() => document.body.innerHTML.substring(0, 3000));
    fs.writeFileSync(path.join(__dirname, `debug-body-${pageData.id}.html`), bodyHTML);
    console.log(`  No dialogs -- body HTML saved`);
  }

  const captured = await savePromise;
  await page.close();
  return captured;
}

async function main() {
  const rawCookies = JSON.parse(fs.readFileSync(COOKIES_JSON, 'utf-8'));
  const cookies = buildCookies(rawCookies);
  console.log(`Loaded ${cookies.length} cookies`);

  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  });
  await context.addCookies(cookies);

  // First: navigate to the editor and check auth
  const page = await context.newPage();
  await page.goto(`${BASE}/zcms/${SITE_ID}/pages`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);
  const url = page.url();
  console.log(`Auth check URL: ${url}`);

  if (url.includes('accounts.zoho') || url.includes('login')) {
    console.error('Session expired! Cannot proceed without re-auth.');
    await browser.close();
    process.exit(1);
  }
  await page.screenshot({ path: path.join(__dirname, 'debug-auth-check.png') });
  console.log('Auth OK. Starting page properties interception...');
  await page.close();

  // Process Home page first to capture the save format
  console.log(`\n--- Processing Home page for format discovery ---`);
  const captured = await setPageSEO(context, PAGES[0], null);
  if (captured) {
    console.log('\n=== CAPTURED SAVE REQUEST ===');
    console.log(JSON.stringify(captured, null, 2));
    fs.writeFileSync(path.join(__dirname, 'debug-save-request.json'), JSON.stringify(captured, null, 2));
  }

  await browser.close();
}

main().catch(err => { console.error(err); process.exit(1); });
