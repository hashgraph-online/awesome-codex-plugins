import { defineConfig } from '@playwright/test'

const baseURL = process.env.THOTH_DASHBOARD_URL ?? 'http://127.0.0.1:8501'
const outputDir = process.env.THOTH_PLAYWRIGHT_OUTPUT_DIR ?? 'playwright-report'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: {
    timeout: 15_000,
  },
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['list'], ['html', { outputFolder: outputDir, open: 'never' }]],
  use: {
    baseURL,
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
})
