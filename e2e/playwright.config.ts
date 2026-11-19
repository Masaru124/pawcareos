import { defineConfig } from '@playwright/test';

/**
 * Runs against the dev servers that are already up: Next on 3000, FastAPI on 8000.
 * Uses the installed Chrome so no browser download is needed.
 */
export default defineConfig({
  testDir: './tests',
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['json', { outputFile: 'report.json' }]],
  use: {
    baseURL: 'http://localhost:3000',
    channel: 'chrome',
    viewport: { width: 1440, height: 900 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
});
