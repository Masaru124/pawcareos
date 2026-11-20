import fs from 'node:fs';
import path from 'node:path';

import { expect, test, type Page } from '@playwright/test';

/**
 * The recorded demo. One test, one page, one video: every surface in the order a
 * person would meet it. Steps are paced so the recording is watchable.
 */
test.use({ video: { mode: 'on', size: { width: 1280, height: 720 } } });
test.describe.configure({ mode: 'serial' });
test.setTimeout(300_000);

const creds = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', '.creds.json'), 'utf8'),
) as {
  owner: { email: string; password: string };
  doctor: { email: string; password: string };
  parent: { email: string; password: string };
};

const DEMO_DIR = path.join(__dirname, '..', '..', 'demo');
const TMP = path.join(__dirname, '..', 'test-results');
const STAMP = Date.now();

const pause = (page: Page, ms = 450) => page.waitForTimeout(ms);
const step = (name: string) => console.log(`:: ${name}`);

async function signIn(page: Page, email: string, password: string, landing: RegExp) {
  // networkidle waits for hydration, so the click runs the React handler rather
  // than a native form submit.
  await page.goto('/login', { waitUntil: 'networkidle' });
  await page.getByLabel('Work email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.locator('form button[type="submit"]').click();
  await page.waitForURL(landing, { timeout: 45_000 });
  await pause(page, 600);
}

async function signOut(page: Page) {
  await page.getByRole('link', { name: 'Sign out' }).first().click();
  await page.waitForURL(/\/login/, { timeout: 30_000 });
  await pause(page, 400);
}

/** A one-page PDF standing in for a photographed paper vaccine card. */
function writeSamplePdf(): string {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, 'vaccine-card-2019.pdf');
  fs.writeFileSync(
    file,
    [
      '%PDF-1.4',
      '1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj',
      '2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj',
      '3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] >> endobj',
      'trailer << /Root 1 0 R >>',
      '%%EOF',
    ].join('\n'),
  );
  return file;
}

// The video is finalised when the context closes, so the runner collects the
// webm from test-results afterwards (see the ffmpeg step in the demo notes).

test('PawCare OS walkthrough', async ({ page }) => {
  fs.mkdirSync(DEMO_DIR, { recursive: true });

  step('1 landing');
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('main h1').first()).toBeVisible();
  await pause(page, 1000);

  step('2 directory');
  await page.goto('/find-a-vet', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('main h1')).toHaveText('Book the next free slot.');
  await pause(page, 1000);

  step('3 owner');
  await signIn(page, creds.owner.email, creds.owner.password, /\/(admin)\/?$/);
  await pause(page, 1200);
  await signOut(page);

  step('4 doctor');
  await signIn(page, creds.doctor.email, creds.doctor.password, /\/(doctor)\/?$/);
  await pause(page, 1200);
  await signOut(page);

  step('5 parent portal');
  await signIn(page, creds.parent.email, creds.parent.password, /\/(portal)\/?$/);
  await page.getByRole('link', { name: 'Records' }).first().click();
  await page.waitForURL(/\/portal\/pets\/[0-9a-f-]+$/);
  await expect(page.getByText(/Digital health record/)).toBeVisible();
  await pause(page, 900);

  step('6 legacy upload');
  const note = `Paper rabies card ${STAMP}`;
  await page.locator('#record_file').setInputFiles(writeSamplePdf());
  await page.getByLabel('Note (optional)').fill(note);
  await page.getByRole('button', { name: 'Add to the file' }).click();
  await expect(page.getByText(note)).toBeVisible({ timeout: 25_000 });
  await pause(page, 1200);

  step('7 legacy delete');
  await page
    .locator('li', { hasText: note })
    .getByRole('button', { name: 'Delete this uploaded record' })
    .click();
  await expect(page.getByText(note)).toHaveCount(0, { timeout: 25_000 });
  await pause(page, 800);

  step('8 passport');
  const passportHref = await page
    .locator('main')
    .getByRole('link', { name: 'Passport', exact: true })
    .first()
    .getAttribute('href');
  expect(passportHref).toMatch(/^\/p\//);
  await page.goto(passportHref ?? '/portal', { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(/\/p\/[a-z0-9-]+$/i);
  await pause(page, 1200);
  await signOut(page);

  step('9 self-serve signup');
  const newEmail = `demo.${STAMP}@pawcare.test`;
  const newPhone = `+9199000${String(STAMP).slice(-5)}`;
  await page.goto('/login?as=parent', { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'Create account' }).click();
  await page.getByLabel('Full name').fill('Demo Parent');
  await page.getByLabel('Email', { exact: true }).fill(newEmail);
  await page.getByLabel('WhatsApp number').fill(newPhone);
  await page.getByLabel('Password').fill('PawCare!Demo2026');
  await page.locator('form button[type="submit"]').click();
  await page.waitForURL(/\/portal\/?$/, { timeout: 60_000 });
  await expect(page.getByText('No pets yet')).toBeVisible();
  await pause(page, 1800);

  step('done');
});
