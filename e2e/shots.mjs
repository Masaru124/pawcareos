// Captures the surfaces I am designing at 1440 and 390 for visual review.
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from '@playwright/test';

const creds = JSON.parse(fs.readFileSync('.creds.json', 'utf8'));
const out = path.resolve('..', 'design');
fs.mkdirSync(out, { recursive: true });
const base = 'http://localhost:3000';

const browser = await chromium.launch({ channel: 'chrome' });

async function shot(page, name, url, fullPage = false) {
  await page.goto(base + url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(700);
  await page.screenshot({ path: path.join(out, `${name}.png`), fullPage });
  console.log('shot', name);
}

async function signIn(context, who) {
  const page = await context.newPage();
  await page.goto(base + '/login', { waitUntil: 'networkidle' });
  await page.getByLabel('Work email').fill(creds[who].email);
  await page.getByLabel('Password').fill(creds[who].password);
  await page.locator('form button[type="submit"]').click();
  await page.waitForTimeout(2500);
  return page;
}

const desktop = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const landing = await desktop.newPage();
await shot(landing, 'landing-1440', '/');
// Scroll once so the lazy chapter photographs are fetched before the full capture.
await landing.evaluate(async () => {
  for (let y = 0; y < document.body.scrollHeight; y += 600) {
    window.scrollTo(0, y);
    await new Promise((r) => setTimeout(r, 120));
  }
  window.scrollTo(0, 0);
});
await landing.waitForTimeout(800);
await shot(landing, 'landing-full-1440', '/', true);

const phone = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
const mobile = await phone.newPage();
await shot(mobile, 'landing-390', '/');

const ownerPage = await signIn(desktop, 'owner');
await shot(ownerPage, 'admin-1440', '/admin');
await shot(ownerPage, 'frontdesk-1440', '/frontdesk');

const doctorCtx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const doctorPage = await signIn(doctorCtx, 'doctor');
await shot(doctorPage, 'doctor-1440', '/doctor');

const parentCtx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const parentPage = await signIn(parentCtx, 'parent');
await shot(parentPage, 'portal-1440', '/portal');
await shot(parentPage, 'find-a-vet-1440', '/find-a-vet');

await browser.close();
