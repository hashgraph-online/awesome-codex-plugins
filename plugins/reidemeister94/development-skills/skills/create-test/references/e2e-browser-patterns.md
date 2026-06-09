# E2E Browser Patterns Reference — Playwright / TypeScript

## Project Architecture

```
tests/
  e2e/
    pages/                  # Page Object classes (one per page/feature)
      BasePage.ts
      LoginPage.ts
      CheckoutPage.ts
    components/             # Reusable UI element wrappers
      Modal.ts
      Header.ts
      DataTable.ts
    fixtures/               # Playwright fixture extensions
      index.ts              # Re-exports all custom fixtures
      auth.ts               # Authenticated state fixtures
    specs/                  # Test files organized by feature domain
      auth/
        login.spec.ts
        registration.spec.ts
      checkout/
        cart.spec.ts
        payment.spec.ts
    visual/                 # Visual regression tests (separate tag)
      screenshots.spec.ts
  playwright.config.ts
```

---

## Page Object Model

### Base Page

```typescript
import { type Page, type Locator } from '@playwright/test';

export abstract class BasePage {
  constructor(protected readonly page: Page) {}

  abstract get url(): string;

  async goto(): Promise<void> {
    await this.page.goto(this.url);
  }

  async waitForLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }
}
```

### Concrete Page — Lazy Getter Locators (Critical Pattern)

```typescript
import { type Page, type Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class CheckoutPage extends BasePage {
  get url() { return '/checkout'; }

  // LAZY GETTERS — resolved when accessed, never in constructor
  // This prevents stale element references
  get cartItems(): Locator {
    return this.page.getByRole('listitem');
  }

  get totalPrice(): Locator {
    return this.page.getByTestId('total-price');
  }

  get submitButton(): Locator {
    return this.page.getByRole('button', { name: 'Confirm Order' });
  }

  get emptyCartMessage(): Locator {
    return this.page.getByText('Your cart is empty');
  }

  // ACTIONS — encapsulate multi-step interactions
  async addItem(name: string): Promise<void> {
    await this.page.getByRole('button', { name: `Add ${name}` }).click();
  }

  async submitOrder(): Promise<void> {
    await this.submitButton.click();
    await expect(this.page).toHaveURL(/\/confirmation/);
  }

  async getTotal(): Promise<string> {
    return await this.totalPrice.textContent() ?? '';
  }
}
```

### Component Composition

```typescript
export class Modal {
  private readonly container: Locator;

  constructor(private readonly page: Page) {
    this.container = page.getByRole('dialog');
  }

  get title(): Locator {
    return this.container.getByRole('heading');
  }

  get closeButton(): Locator {
    return this.container.getByRole('button', { name: 'Close' });
  }

  async close(): Promise<void> {
    await this.closeButton.click();
    await expect(this.container).not.toBeVisible();
  }

  async isOpen(): Promise<boolean> {
    return await this.container.isVisible();
  }
}

// Use in page objects:
export class SettingsPage extends BasePage {
  get url() { return '/settings'; }

  get confirmModal(): Modal {
    return new Modal(this.page);
  }

  async deleteAccount(): Promise<void> {
    await this.page.getByRole('button', { name: 'Delete Account' }).click();
    // Modal appears — delegate to component
    await expect(this.confirmModal.title).toHaveText('Are you sure?');
  }
}
```

### Custom Fixtures for Page Objects

```typescript
// fixtures/index.ts
import { test as base } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { CheckoutPage } from '../pages/CheckoutPage';

type PageFixtures = {
  loginPage: LoginPage;
  checkoutPage: CheckoutPage;
};

export const test = base.extend<PageFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  checkoutPage: async ({ page }, use) => {
    await use(new CheckoutPage(page));
  },
});

export { expect } from '@playwright/test';

// In tests:
import { test, expect } from '../fixtures';

test('completes checkout flow', async ({ checkoutPage }) => {
  await checkoutPage.goto();
  await checkoutPage.addItem('Widget');
  await expect(checkoutPage.totalPrice).toContainText('$9.99');
  await checkoutPage.submitOrder();
});
```

---

## Locator Strategy — Priority Order

```typescript
// 1. ROLE (most resilient, semantic — always try first)
page.getByRole('button', { name: 'Submit' });
page.getByRole('heading', { level: 1 });
page.getByRole('textbox', { name: 'Email' });
page.getByRole('link', { name: 'Sign up' });

// 2. TEXT (visible content)
page.getByText('Welcome back');
page.getByLabel('Password');  // associated <label>
page.getByPlaceholder('Enter email');

// 3. TEST ID (explicit test hooks — when semantic options fail)
page.getByTestId('cart-total');

// 4. CHAINING + FILTERING (narrow scope for ambiguous locators)
page.getByRole('listitem')
  .filter({ hasText: 'Product 2' })
  .getByRole('button', { name: 'Add to cart' });

// NEVER — breaks when designers change CSS/DOM
// page.locator('button.btn-primary');
// page.locator('#submit-btn');
// page.locator('div > span:nth-child(2)');
// page.locator('//button[@class="submit"]');
```

---

## Assertion Patterns

### Web-First Assertions (Always Use These)

```typescript
// Auto-retry with configurable timeout — handles async rendering
await expect(page.getByText('Success')).toBeVisible();
await expect(page.getByRole('alert')).toContainText('Saved');
await expect(page).toHaveURL(/\/dashboard/);
await expect(page).toHaveTitle('Dashboard');
await expect(page.getByTestId('count')).toHaveText('42');
```

### Soft Assertions (Gather All Failures)

```typescript
test('dashboard displays all widgets', async ({ page }) => {
  await page.goto('/dashboard');
  // Continue checking even if one fails — report all failures at end
  await expect.soft(page.getByTestId('revenue')).toBeVisible();
  await expect.soft(page.getByTestId('users')).toBeVisible();
  await expect.soft(page.getByTestId('orders')).toBeVisible();
});
```

### NEVER Use Synchronous Checks

```typescript
// WRONG — races with rendering, flaky
const visible = await page.getByText('welcome').isVisible();
expect(visible).toBe(true);

// WRONG — no auto-retry
const text = await page.getByTestId('status').textContent();
expect(text).toBe('Active');

// CORRECT — auto-retry
await expect(page.getByText('welcome')).toBeVisible();
await expect(page.getByTestId('status')).toHaveText('Active');
```

---

## API Mocking (Route Interception)

```typescript
test('handles API error gracefully', async ({ page }) => {
  // Mock the API response before navigation
  await page.route('**/api/products', (route) =>
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Internal Server Error' }),
    })
  );

  await page.goto('/products');
  await expect(page.getByRole('alert')).toContainText('Failed to load');
});

test('displays product list', async ({ page }) => {
  await page.route('**/api/products', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Widget', price: 9.99 },
        { id: 2, name: 'Gadget', price: 19.99 },
      ]),
    })
  );

  await page.goto('/products');
  await expect(page.getByRole('listitem')).toHaveCount(2);
});
```

---

## Visual Regression Testing

### Configuration

```typescript
// playwright.config.ts
export default defineConfig({
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.01,  // 1% tolerance for full pages
      threshold: 0.2,           // per-pixel color sensitivity
      animations: 'disabled',   // #1 source of flakiness
    },
  },
  // Use Docker for CI to match baseline rendering exactly
  // npx playwright test --update-snapshots  (to regenerate baselines)
});
```

### Component-Level Screenshots (Preferred)

```typescript
test('button renders correctly in all states', async ({ page }) => {
  await page.goto('/components/button');

  const button = page.getByRole('button', { name: 'Submit' });

  // Default state
  await expect(button).toHaveScreenshot('button-default.png');

  // Hover state
  await button.hover();
  await expect(button).toHaveScreenshot('button-hover.png');

  // Disabled state
  await page.getByRole('checkbox', { name: 'Disable' }).check();
  await expect(button).toHaveScreenshot('button-disabled.png');
});
```

### Full Page with Dynamic Content Masked

```typescript
test('checkout page visual regression', async ({ page }) => {
  await page.goto('/checkout');
  await expect(page).toHaveScreenshot('checkout.png', {
    fullPage: true,
    animations: 'disabled',
    mask: [
      page.locator('[data-testid="timestamp"]'),
      page.locator('[data-testid="session-id"]'),
      page.locator('[data-testid="user-avatar"]'),
    ],
    maskColor: '#808080',
  });
});
```

### CI/CD Rules

1. **Generate baselines in Docker** — OS font rendering differs. Use the official Playwright image:
   ```bash
   docker run --rm -v $(pwd):/work -w /work \
     mcr.microsoft.com/playwright:v1.50.0-noble \
     npx playwright test --update-snapshots
   ```
2. **Tag visual tests separately**: `test.describe.configure({ tag: '@visual' });`
3. **Run visual tests in a separate CI job** — slower, different failure modes

---

## Playwright Configuration Best Practices

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e/specs',
  outputDir: './tests/e2e/results',

  // Parallel by default — tests in different files run concurrently
  fullyParallel: true,
  workers: process.env.CI ? 2 : undefined,  // limit in CI for stability

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Trace on first retry — far superior to screenshots for debugging
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    // Add more browsers as needed:
    // { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    // { name: 'mobile', use: { ...devices['iPhone 14'] } },
  ],

  // Start dev server before tests (optional)
  // NOTE: substitute the detected package manager — npm/pnpm/yarn/bun.
  // See plugins/development-skills/skills/typescript-dev/references/package-manager.md for translation.
  // e.g. pnpm → 'pnpm dev', yarn → 'yarn dev', bun → 'bun run dev'.
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: true,
  },
});
```

## CI/CD Integration

### Install Only Needed Browsers

```bash
# CI — only Chromium, with system deps
npx playwright install chromium --with-deps
```

### Sharding Across CI Machines

```bash
# Machine 1 of 3
npx playwright test --shard=1/3
# Machine 2 of 3
npx playwright test --shard=2/3
# Machine 3 of 3
npx playwright test --shard=3/3
```

### Critical ESLint Rule

```json
// .eslintrc.json — catches missing await (silent failure cause #1)
{
  "rules": {
    "@typescript-eslint/no-floating-promises": "error"
  }
}
```

---

## Authentication State Reuse

```typescript
// fixtures/auth.ts — login once, reuse state across tests
import { test as setup } from '@playwright/test';

const authFile = 'tests/e2e/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('test@example.com');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('/dashboard');
  await page.context().storageState({ path: authFile });
});

// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'setup', testMatch: /auth\.setup\.ts/ },
    {
      name: 'chromium',
      use: {
        storageState: authFile,
      },
      dependencies: ['setup'],
    },
  ],
});
```

---

## Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|---|---|---|
| CSS selectors / XPath | Break on any designer change | Use `getByRole`, `getByText`, `getByTestId` |
| Synchronous `.isVisible()` checks | Race with rendering, flaky | Use `await expect(loc).toBeVisible()` |
| Assertions in Page Objects | Mixes concerns, hard to debug | Keep assertions in test files only |
| God Page Objects (50+ methods) | Unmaintainable, slow to read | Break into smaller component classes |
| Locators evaluated in constructor | Stale references when DOM updates | Use lazy getters |
| `page.waitForTimeout(1000)` | Flaky, slow, hides real issues | Use web-first assertions or `waitForURL`/`waitForLoadState` |
| Missing `await` on async calls | Silent failures, tests pass incorrectly | Enable `no-floating-promises` ESLint rule |
| Screenshots for CI debugging | Hard to compare, noisy | Use trace viewer (`trace: 'on-first-retry'`) |
| Full-page visual tests for components | Large diffs from unrelated changes | Screenshot specific elements |
| Testing third-party widgets | Not your code, unstable | Mock with `page.route()` |
