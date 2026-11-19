import fs from 'node:fs';
import path from 'node:path';

import { expect, test, type Page } from '@playwright/test';

type Creds = {
  baseURL: string;
  clinic: string;
  inviteEmail: string;
  owner: { email: string; password: string; role: string };
  doctor: { email: string; password: string; role: string };
  parent: { email: string; password: string; role: string };
};

const creds: Creds = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', '.creds.json'), 'utf8'),
) as Creds;

const SHOTS = path.join(__dirname, '..', 'shots');
const problems: { test: string; url: string; kind: string; detail: string }[] = [];

/** Screens, console errors and 5xx responses are recorded, then asserted at the end. */
function watch(page: Page, testName: string): void {
  page.on('pageerror', (error) =>
    problems.push({ test: testName, url: page.url(), kind: 'pageerror', detail: error.message }),
  );
  page.on('console', (message) => {
    if (message.type() === 'error') {
      problems.push({ test: testName, url: page.url(), kind: 'console', detail: message.text() });
    }
  });
  page.on('response', (response) => {
    if (response.status() >= 500) {
      problems.push({
        test: testName,
        url: response.url(),
        kind: `http ${response.status()}`,
        detail: '',
      });
    }
  });
}

async function shot(page: Page, name: string): Promise<void> {
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: true });
}

async function signIn(page: Page, email: string, password: string): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Work email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.locator('form button[type="submit"]').click();
  await page.waitForURL(/\/(admin|queue|portal)\/?$/, { timeout: 40_000 });
}

test.beforeAll(() => {
  fs.mkdirSync(SHOTS, { recursive: true });
});

test.afterAll(() => {
  fs.writeFileSync(path.join(__dirname, '..', 'issues.json'), JSON.stringify(problems, null, 2));
  const serverErrors = problems.filter((item) => item.kind.startsWith('http 5'));
  expect(serverErrors, `server errors: ${JSON.stringify(serverErrors, null, 2)}`).toHaveLength(0);
});

// ---------------------------------------------------------------------------
// 1. Owner / admin
// ---------------------------------------------------------------------------
test.describe('owner', () => {
  test('dashboard, team, invitations, audit trail and clinic navigation', async ({ page }) => {
    watch(page, 'owner');
    const inviteEmail = `reception+${Date.now()}@pawcare.test`;

    await test.step('signs in and is routed to /admin', async () => {
      await signIn(page, creds.owner.email, creds.owner.password);
      await expect(page).toHaveURL(/\/admin$/);
      await expect(page.locator('main h1')).toHaveText(creds.clinic);
      await expect(page.getByText('Admin panel · owner')).toBeVisible();
      await shot(page, 'owner-01-dashboard');
    });

    await test.step('KPI cards render', async () => {
      for (const label of [
        'Active patients',
        'Appointments today',
        'Next 7 days',
        'Overdue boosters',
        'Doctors',
        'Staff',
      ]) {
        await expect(page.getByText(label, { exact: true })).toBeVisible();
      }
    });

    await test.step('team list shows roles and claim state', async () => {
      await expect(page.getByText(creds.owner.email)).toBeVisible();
      await expect(page.getByText(creds.doctor.email)).toBeVisible();
      await expect(page.getByText('signed in').first()).toBeVisible();
    });

    await test.step('audit feed records claims', async () => {
      await expect(page.getByText('Recent activity')).toBeVisible();
      await expect(page.getByText('user.claimed').first()).toBeVisible();
    });

    await test.step('invites a receptionist and sees them appear', async () => {
      await page.getByLabel('Full name').fill('E2E Receptionist');
      await page.getByLabel('Work email').fill(inviteEmail);
      await page.getByLabel('Role').selectOption('receptionist');
      await page.getByRole('button', { name: 'Invite colleague' }).click();
      await expect(page.getByRole('status')).toContainText('can now sign in as');
      await expect(page.getByLabel('Full name')).toHaveValue('');
      await page.reload();
      await expect(page.getByText(inviteEmail)).toBeVisible();
      await expect(page.getByText('invited').first()).toBeVisible();
      await shot(page, 'owner-02-team-after-invite');
    });

    await test.step('clinic board opens in owner view', async () => {
      await page.getByRole('link', { name: 'Clinic board' }).click();
      await expect(page).toHaveURL(/\/queue$/);
      await expect(page.getByText(/Owner view/)).toBeVisible();
      await expect(page.getByRole('link', { name: 'Admin' })).toBeVisible();
      await shot(page, 'owner-03-queue');
    });

    await test.step('patient directory lists and searches', async () => {
      await page.getByRole('link', { name: 'Patients' }).first().click();
      await expect(page.locator('main h1')).toHaveText('Every passport.');
      await page.getByLabel('Search patients').fill('Bruno');
      await page.getByRole('button', { name: 'Search' }).click();
      await expect(page.getByText(/match(es)? for/)).toBeVisible();
      await shot(page, 'owner-04-patient-search');
    });
  });
});

// ---------------------------------------------------------------------------
// 2. Doctor
// ---------------------------------------------------------------------------
test.describe('doctor', () => {
  test('queue, consult workspace, patient search, and RBAC walls', async ({ page }) => {
    watch(page, 'doctor');

    await test.step('signs in and lands on the doctor board', async () => {
      await signIn(page, creds.doctor.email, creds.doctor.password);
      await expect(page).toHaveURL(/\/queue$/);
      await expect(page.getByText(/Doctor.s board/)).toBeVisible();
      await expect(page.getByText(`Signed in as ${creds.doctor.email}`)).toBeVisible();
      await shot(page, 'doctor-01-queue');
    });

    await test.step('opens a consult workspace from the queue', async () => {
      await page.getByRole('link', { name: 'Start consult' }).first().click();
      await expect(page).toHaveURL(/\/consult\/[0-9a-f-]+$/);
      await expect(page.getByText(/Consult ·/)).toBeVisible();
      await expect(page.locator('main h1')).not.toBeEmpty();
      await shot(page, 'doctor-02-consult');
    });

    await test.step('searches the patient directory', async () => {
      await page.goto('/patients');
      await page.getByLabel('Search patients').fill('Coco');
      await page.getByRole('button', { name: 'Search' }).click();
      await expect(page.getByText(/match(es)? for/)).toBeVisible();
      await shot(page, 'doctor-03-patient-search');
    });

    await test.step('is refused the owner-only admin panel', async () => {
      await page.goto('/admin');
      await expect(page.getByText('Admin panel is for the clinic owner')).toBeVisible();
      await shot(page, 'doctor-04-admin-refused');
    });

    await test.step('is refused the pet-parent portal', async () => {
      await page.goto('/portal');
      await expect(page.getByText('No pet records on this account')).toBeVisible();
      await shot(page, 'doctor-05-portal-refused');
    });
  });
});

// ---------------------------------------------------------------------------
// 3. Pet parent
// ---------------------------------------------------------------------------
test.describe('pet parent', () => {
  test('portal, health records, passport, public booking, and RBAC walls', async ({ page }) => {
    watch(page, 'parent');
    let petName = '';

    await test.step('signs in and lands on the portal', async () => {
      await signIn(page, creds.parent.email, creds.parent.password);
      await expect(page).toHaveURL(/\/portal$/);
      await expect(page.locator('main h1')).toHaveText('Priya Sharma');
      await expect(page.getByText(/Number ending …1122/)).toBeVisible();
      petName = (await page.locator('section article h2').first().innerText()).trim();
      expect(petName.length).toBeGreaterThan(0);
      await shot(page, 'parent-01-portal');
    });

    await test.step('opens the digital health record', async () => {
      await page.getByRole('link', { name: 'Records' }).first().click();
      await expect(page).toHaveURL(/\/portal\/pets\/[0-9a-f-]+$/);
      await expect(page.getByText(/Digital health record/)).toBeVisible();
      await expect(page.getByText(/Vaccinations \(\d+\)/)).toBeVisible();
      await expect(page.locator('main h1')).toHaveText(petName);
      await shot(page, 'parent-02-records');
    });

    await test.step('opens the public passport', async () => {
      await page.getByRole('link', { name: 'Passport' }).first().click();
      await expect(page).toHaveURL(/\/p\/[a-z0-9-]+$/i);
      await expect(page.locator('main h1')).toHaveText(petName);
      await shot(page, 'parent-03-passport');
    });

    await test.step('cannot reach the clinic queue', async () => {
      await page.goto('/queue');
      await expect(page.getByText('This account is not linked to a clinic yet')).toBeVisible();
      await shot(page, 'parent-04-queue-refused');
    });

    await test.step('cannot reach the admin panel', async () => {
      await page.goto('/admin');
      await expect(page.getByText('Admin panel · owner')).toHaveCount(0);
      await shot(page, 'parent-05-admin-refused');
    });

    await test.step('books a 24/7 online consult from the public directory', async () => {
      await page.goto('/find-a-vet');
      await expect(page.locator('main h1')).toHaveText('Book the next free slot.');
      await page.getByRole('link', { name: 'Online 24/7' }).first().click();
      await expect(page.getByText(/Online consult · chosen slot/)).toBeVisible();
      await page.locator('a[href*="slot="]').first().click();
      await expect(page.getByRole('button', { name: 'Confirm booking' })).toBeVisible();

      await page.getByLabel('Your name').fill('E2E Parent');
      await page.getByLabel('WhatsApp number').fill('+919900099001');
      await page.locator('#pet_name').fill('TestPup');
      await page.getByLabel('Species').selectOption('Canine');
      await page.getByRole('button', { name: 'Confirm booking' }).click();

      await expect(page.getByText('Booked', { exact: true })).toBeVisible();
      await expect(page.getByText(/reminder(s)? queued/)).toBeVisible();
      await shot(page, 'parent-06-booked');

      await page.getByRole('link', { name: 'Open the passport' }).click();
      await expect(page).toHaveURL(/\/p\/[a-z0-9-]+$/i);
      await expect(page.locator('main h1')).toHaveText('TestPup');
      await shot(page, 'parent-07-new-passport');
    });
  });
});
