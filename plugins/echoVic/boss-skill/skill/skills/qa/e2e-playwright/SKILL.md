---
name: qa/e2e-playwright
description: Playwright E2E 测试完整方法论，涵盖项目初始化、Page Object Model、认证复用、API Mock、视觉回归、多浏览器测试、CI 集成和调试技巧
version: 1.0.0
agent: qa
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
  - shared/tech-stack-detection
triggers:
  - 需要编写或执行 E2E 测试时
  - 需要配置 Playwright 测试环境时
  - 门禁要求 E2E 测试通过时
  - 需要视觉回归测试时
---

# Playwright E2E 测试方法论

## 适用场景

- Web 项目需要编写端到端测试
- 门禁（Gate 1）要求 E2E 测试通过
- 需要覆盖关键用户流程的自动化验证
- 需要多浏览器/多视口兼容性验证
- 需要视觉回归测试

---

## 1. 项目初始化

### 1.1 安装

```bash
# 新项目初始化（推荐）
npm init playwright@latest

# 已有项目添加
npm install -D @playwright/test
npx playwright install
```

### 1.2 配置文件（`playwright.config.ts`）

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  // 测试产物目录
  outputDir: './e2e/test-results',

  // 全局超时
  timeout: 30_000,
  expect: { timeout: 5_000 },

  // 并行执行
  fullyParallel: true,
  workers: process.env.CI ? 1 : undefined,

  // 失败重试（CI 中重试一次减少 flaky）
  retries: process.env.CI ? 1 : 0,

  // 报告
  reporter: [
    ['html', { outputFolder: './e2e/playwright-report' }],
    ['json', { outputFile: './e2e/test-results/results.json' }],
    // CI 中额外输出到 stdout
    ...(process.env.CI ? [['github'] as const] : []),
  ],

  // 全局配置
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    // 失败时自动截图
    screenshot: 'only-on-failure',
    // 失败时录制 trace
    trace: 'on-first-retry',
    // 失败时录制视频
    video: 'on-first-retry',
  },

  // 多浏览器 + 移动端视口
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
    { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },
  ],

  // 开发服务器自动启动
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

**关键配置说明**：

| 配置项 | 作用 | 建议值 |
|--------|------|--------|
| `fullyParallel` | 测试文件间并行执行 | `true` |
| `workers` | 并行 worker 数 | CI 为 1，本地默认 |
| `retries` | 失败重试次数 | CI 为 1，本地为 0 |
| `trace` | 失败时生成可视化时间线 | `on-first-retry` |
| `webServer` | 自动启动开发服务器 | 必须配置 |

### 1.3 目录结构

```
e2e/
├── playwright.config.ts        # 配置文件（或放在项目根目录）
├── fixtures/                   # 自定义 fixtures
│   ├── base.ts                 # 扩展 base test
│   └── auth.ts                 # 认证 fixture
├── pages/                      # Page Object Models
│   ├── login.page.ts
│   ├── dashboard.page.ts
│   └── components/             # 可复用组件 POM
│       ├── navbar.component.ts
│       └── modal.component.ts
├── specs/                      # 测试用例
│   ├── auth/
│   │   ├── login.spec.ts
│   │   └── register.spec.ts
│   ├── dashboard/
│   │   └── dashboard.spec.ts
│   └── crud/
│       └── user-management.spec.ts
├── helpers/                    # 测试工具
│   ├── seed.ts                 # 数据种子
│   └── cleanup.ts              # 数据清理
├── test-results/               # 测试产物（gitignore）
└── playwright-report/          # HTML 报告（gitignore）
```

---

## 2. Page Object Model（POM）

### 2.1 核心原则

- **每个页面一个 POM 类**：封装定位器和操作方法
- **不暴露 Locator**：外部只调用语义化方法
- **组件级复用**：导航栏、弹窗等提取为独立组件 POM

### 2.2 基础 POM

```typescript
// e2e/pages/login.page.ts
import { type Page, type Locator } from '@playwright/test';

export class LoginPage {
  private readonly emailInput: Locator;
  private readonly passwordInput: Locator;
  private readonly submitButton: Locator;
  private readonly errorMessage: Locator;

  constructor(private readonly page: Page) {
    this.emailInput = page.getByLabel('邮箱');
    this.passwordInput = page.getByLabel('密码');
    this.submitButton = page.getByRole('button', { name: '登录' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async getErrorMessage() {
    return this.errorMessage.textContent();
  }
}
```

### 2.3 组件 POM

```typescript
// e2e/pages/components/navbar.component.ts
import { type Page, type Locator } from '@playwright/test';

export class NavbarComponent {
  private readonly userMenu: Locator;
  private readonly logoutButton: Locator;

  constructor(private readonly page: Page) {
    this.userMenu = page.getByTestId('user-menu');
    this.logoutButton = page.getByRole('menuitem', { name: '退出登录' });
  }

  async logout() {
    await this.userMenu.click();
    await this.logoutButton.click();
  }

  async getUserDisplayName() {
    return this.userMenu.textContent();
  }
}
```

### 2.4 定位器优先级

选择定位器时遵循以下优先级（可靠性从高到低）：

| 优先级 | 方法 | 示例 | 说明 |
|--------|------|------|------|
| 1 | `getByRole` | `getByRole('button', { name: '提交' })` | 无障碍语义，最稳定 |
| 2 | `getByLabel` | `getByLabel('邮箱')` | 表单元素首选 |
| 3 | `getByPlaceholder` | `getByPlaceholder('请输入邮箱')` | 备选 |
| 4 | `getByText` | `getByText('欢迎回来')` | 静态文本 |
| 5 | `getByTestId` | `getByTestId('submit-btn')` | 无语义标记时的兜底 |
| 6 | CSS/XPath | `page.locator('.btn-primary')` | **尽量避免** |

---

## 3. 认证状态复用

### 3.1 Global Setup 方式

```typescript
// e2e/global-setup.ts
import { chromium, type FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // 执行登录
  await page.goto('http://localhost:3000/login');
  await page.getByLabel('邮箱').fill('admin@example.com');
  await page.getByLabel('密码').fill('password');
  await page.getByRole('button', { name: '登录' }).click();
  await page.waitForURL('/dashboard');

  // 保存认证状态
  await page.context().storageState({ path: './e2e/.auth/admin.json' });
  await browser.close();
}

export default globalSetup;
```

**配置引用**：

```typescript
// playwright.config.ts
export default defineConfig({
  globalSetup: './e2e/global-setup.ts',
  projects: [
    // 不带认证的测试
    { name: 'public', testMatch: /public\.spec\.ts/ },
    // 带认证的测试
    {
      name: 'authenticated',
      use: { storageState: './e2e/.auth/admin.json' },
      testIgnore: /public\.spec\.ts/,
    },
  ],
});
```

### 3.2 多角色认证

```typescript
// e2e/fixtures/auth.ts
import { test as base } from '@playwright/test';

type AuthFixtures = {
  adminPage: Page;
  userPage: Page;
};

export const test = base.extend<AuthFixtures>({
  adminPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: './e2e/.auth/admin.json',
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
  userPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: './e2e/.auth/user.json',
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});
```

---

## 4. API Mocking

### 4.1 使用 `page.route` 拦截请求

```typescript
test('显示用户列表（API Mock）', async ({ page }) => {
  // 拦截 API 请求
  await page.route('/api/users', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: '张三', email: 'zhang@example.com' },
        { id: 2, name: '李四', email: 'li@example.com' },
      ]),
    });
  });

  await page.goto('/users');
  await expect(page.getByText('张三')).toBeVisible();
  await expect(page.getByText('李四')).toBeVisible();
});
```

### 4.2 模拟错误响应

```typescript
test('API 失败时显示错误提示', async ({ page }) => {
  await page.route('/api/users', async (route) => {
    await route.fulfill({ status: 500, body: 'Internal Server Error' });
  });

  await page.goto('/users');
  await expect(page.getByText('加载失败')).toBeVisible();
  await expect(page.getByRole('button', { name: '重试' })).toBeVisible();
});
```

### 4.3 Mock 与真实请求混合

```typescript
test('部分 API Mock', async ({ page }) => {
  // 只 Mock 第三方支付接口，其余走真实请求
  await page.route('**/api/payment/**', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ success: true, transactionId: 'mock-tx-001' }),
    });
  });

  await page.goto('/checkout');
  // ... 执行支付流程
});
```

### 4.4 何时用 Mock vs 真实 API

| 场景 | 建议 |
|------|------|
| 核心用户路径 | **真实 API**（关键路径证据规则） |
| 第三方服务（支付、邮件） | Mock |
| 错误/边界状态 | Mock |
| 加载状态、空数据 | Mock |
| 数据量大的列表/分页 | Mock + 至少一条真实路径 |

⚠️ **Boss 门禁规则**：核心用户路径只由 Mock 证明的，必须标记为**未验证**，不能作为发布证据。

---

## 5. 关键用户流程测试（必须覆盖）

### 5.1 CRUD 完整流程

```typescript
// e2e/specs/crud/user-management.spec.ts
import { test, expect } from '@playwright/test';
import { UserListPage } from '../../pages/user-list.page';
import { UserFormPage } from '../../pages/user-form.page';

test.describe('用户管理 CRUD', () => {
  let userList: UserListPage;
  let userForm: UserFormPage;

  test.beforeEach(async ({ page }) => {
    userList = new UserListPage(page);
    userForm = new UserFormPage(page);
    await userList.goto();
  });

  test('创建 → 编辑 → 删除完整流程', async ({ page }) => {
    // 创建
    await userList.clickAddUser();
    await userForm.fillName('测试用户');
    await userForm.fillEmail('test@example.com');
    await userForm.submit();
    await expect(page.getByText('测试用户')).toBeVisible();

    // 编辑
    await userList.editUser('测试用户');
    await userForm.fillName('修改后的用户');
    await userForm.submit();
    await expect(page.getByText('修改后的用户')).toBeVisible();
    await expect(page.getByText('测试用户')).not.toBeVisible();

    // 删除
    await userList.deleteUser('修改后的用户');
    await userList.confirmDelete();
    await expect(page.getByText('修改后的用户')).not.toBeVisible();
  });

  test('列表分页展示', async ({ page }) => {
    await expect(userList.getTable()).toBeVisible();
    await userList.goToNextPage();
    await expect(page).toHaveURL(/page=2/);
  });

  test('空列表提示', async ({ page }) => {
    // 使用 route mock 空数据场景
    await page.route('/api/users*', (route) =>
      route.fulfill({ status: 200, body: JSON.stringify({ data: [], total: 0 }) })
    );
    await page.reload();
    await expect(page.getByText('暂无数据')).toBeVisible();
  });
});
```

### 5.2 认证流程

```typescript
// e2e/specs/auth/login.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/login.page';

test.describe('登录', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('正确凭据成功登录', async ({ page }) => {
    await loginPage.login('admin@example.com', 'password');
    await expect(page).toHaveURL('/dashboard');
  });

  test('错误凭据显示提示', async ({ page }) => {
    await loginPage.login('admin@example.com', 'wrong-password');
    await expect(page.getByRole('alert')).toContainText('密码错误');
    await expect(page).toHaveURL('/login');
  });

  test('未登录重定向到登录页', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });
});
```

### 5.3 表单验证

```typescript
test.describe('表单验证', () => {
  test('必填字段为空时显示错误', async ({ page }) => {
    await page.goto('/users/new');
    await page.getByRole('button', { name: '提交' }).click();

    await expect(page.getByText('姓名不能为空')).toBeVisible();
    await expect(page.getByText('邮箱不能为空')).toBeVisible();
  });

  test('邮箱格式错误时显示提示', async ({ page }) => {
    await page.goto('/users/new');
    await page.getByLabel('邮箱').fill('invalid-email');
    await page.getByLabel('邮箱').blur();

    await expect(page.getByText('邮箱格式不正确')).toBeVisible();
  });
});
```

---

## 6. 视觉回归测试

### 6.1 截图对比

```typescript
test('首页视觉回归', async ({ page }) => {
  await page.goto('/');
  // 等待动态内容稳定
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveScreenshot('homepage.png', {
    maxDiffPixelRatio: 0.01,
  });
});

test('组件视觉回归', async ({ page }) => {
  await page.goto('/components/button');
  const button = page.getByTestId('primary-button');
  await expect(button).toHaveScreenshot('primary-button.png');
});
```

### 6.2 更新基线

```bash
# 更新所有截图基线
npx playwright test --update-snapshots

# 更新指定测试的截图
npx playwright test homepage.spec.ts --update-snapshots
```

### 6.3 注意事项

- 截图基线需提交到 Git
- 不同 OS 渲染有差异，CI 中使用 Docker 保证一致性
- 对动态内容（时间、随机数据）需 Mock 后再截图
- `maxDiffPixelRatio` 容忍微小渲染差异（抗锯齿等）

---

## 7. 多浏览器和移动端测试

### 7.1 配置多 project

```typescript
// playwright.config.ts 中的 projects 已覆盖
// 可根据项目需要选择性启用：

projects: [
  // 桌面浏览器
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },

  // 移动端视口
  { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },

  // 平板
  { name: 'tablet', use: { ...devices['iPad Pro 11'] } },
]
```

### 7.2 按 project 运行

```bash
# 只跑 Chromium
npx playwright test --project=chromium

# 只跑移动端
npx playwright test --project=mobile-chrome --project=mobile-safari
```

### 7.3 响应式断言

```typescript
test('移动端显示汉堡菜单', async ({ page, isMobile }) => {
  await page.goto('/');
  if (isMobile) {
    await expect(page.getByTestId('hamburger-menu')).toBeVisible();
    await expect(page.getByTestId('desktop-nav')).not.toBeVisible();
  } else {
    await expect(page.getByTestId('desktop-nav')).toBeVisible();
    await expect(page.getByTestId('hamburger-menu')).not.toBeVisible();
  }
});
```

---

## 8. 测试数据管理

### 8.1 数据种子（Seed）

```typescript
// e2e/helpers/seed.ts
import { request } from '@playwright/test';

export async function seedTestData(baseURL: string) {
  const api = await request.newContext({ baseURL });
  await api.post('/api/test/seed', {
    data: {
      users: [
        { name: '测试管理员', email: 'admin@test.com', role: 'admin' },
        { name: '测试用户', email: 'user@test.com', role: 'user' },
      ],
    },
  });
  await api.dispose();
}
```

### 8.2 数据清理

```typescript
// e2e/helpers/cleanup.ts
import { request } from '@playwright/test';

export async function cleanupTestData(baseURL: string) {
  const api = await request.newContext({ baseURL });
  await api.post('/api/test/cleanup');
  await api.dispose();
}
```

### 8.3 在 Global Setup/Teardown 中使用

```typescript
// e2e/global-setup.ts
import { seedTestData } from './helpers/seed';

async function globalSetup() {
  await seedTestData('http://localhost:3000');
}
export default globalSetup;

// e2e/global-teardown.ts
import { cleanupTestData } from './helpers/cleanup';

async function globalTeardown() {
  await cleanupTestData('http://localhost:3000');
}
export default globalTeardown;
```

### 8.4 原则

| 原则 | 说明 |
|------|------|
| **测试隔离** | 每个测试独立运行，不依赖其他测试的数据 |
| **可重复** | 多次运行结果一致 |
| **快速清理** | 使用 API 清理而非 UI 操作 |
| **避免硬编码 ID** | 使用动态创建的数据，不依赖数据库自增 ID |

---

## 9. CI/CD 集成

### 9.1 GitHub Actions

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Build application
        run: npm run build

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload test results
        if: ${{ !cancelled() }}
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: e2e/playwright-report/
          retention-days: 30

      - name: Upload trace files
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-traces
          path: e2e/test-results/
          retention-days: 7
```

### 9.2 Docker 一致性

```dockerfile
# e2e/Dockerfile
FROM mcr.microsoft.com/playwright:v1.49.0-noble
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npx", "playwright", "test"]
```

### 9.3 CI 关键配置

| 配置 | CI 值 | 原因 |
|------|-------|------|
| `workers` | 1 | CI 资源有限，避免争抢 |
| `retries` | 1 | 减少 flaky 误报 |
| `reporter` | `github` + `html` | GitHub PR 行内注释 + HTML 归档 |
| `trace` | `on-first-retry` | 只在重试时录制，节省空间 |

---

## 10. 调试技巧

### 10.1 UI 模式（开发首选）

```bash
# 打开可视化调试界面
npx playwright test --ui
```

### 10.2 Trace Viewer

```bash
# 查看失败测试的 trace
npx playwright show-trace e2e/test-results/specs-auth-login-spec-ts/trace.zip
```

Trace Viewer 提供：
- 时间线上的每一步操作
- DOM 快照
- 网络请求日志
- 控制台输出

### 10.3 Debug 模式

```bash
# 逐步执行，自动暂停
npx playwright test --debug

# 指定测试文件
npx playwright test login.spec.ts --debug
```

### 10.4 代码中暂停

```typescript
test('调试用', async ({ page }) => {
  await page.goto('/login');
  await page.pause(); // 打开 Inspector，手动操作
  // ...
});
```

### 10.5 录制生成测试

```bash
# 打开浏览器录制，自动生成代码
npx playwright codegen http://localhost:3000
```

### 10.6 常见 Flaky 原因及修复

| 原因 | 症状 | 修复 |
|------|------|------|
| 动画未完成 | 元素找到但点击无效 | 等待动画完成或禁用动画 |
| 网络请求延迟 | 元素内容未更新 | 使用 `waitForResponse` |
| 竞态条件 | 间歇性失败 | 使用 `expect().toBeVisible()` 自动等待 |
| 数据未就绪 | 列表为空 | 使用 `waitForLoadState('networkidle')` |
| 时间依赖 | 日期/时间相关断言失败 | Mock 时间或使用范围断言 |

---

## 11. 与 Boss 流水线门禁集成

### 11.1 Gate 1 E2E 检查项

Boss 流水线的 Gate 1 门禁要求 E2E 测试满足：

| 检查项 | 要求 | 说明 |
|--------|------|------|
| E2E 测试存在 | `e2e/` 或 `tests/e2e/` 目录非空 | 不能只有单元测试 |
| 关键路径覆盖 | CRUD + 认证 + 核心业务流程 | 至少 5 个核心用户操作 |
| 全部通过 | 无失败用例 | 失败则门禁不通过 |
| 真实 API 证据 | 核心路径不能只有 Mock | Mock-only 标记为未验证 |

### 11.2 执行命令

```bash
# 门禁检查时执行
npx playwright test --reporter=json --output=e2e/test-results

# 仅核心路径（CI 加速）
npx playwright test --grep @critical

# 完整套件
npx playwright test
```

### 11.3 测试标签

使用标签标记测试优先级，门禁可按标签选择性执行：

```typescript
test('@critical 登录流程', async ({ page }) => { /* ... */ });
test('@critical 核心业务流程', async ({ page }) => { /* ... */ });
test('@smoke 首页加载', async ({ page }) => { /* ... */ });
test('@regression 边界情况', async ({ page }) => { /* ... */ });
```

```bash
# Gate 1 只跑 critical
npx playwright test --grep @critical

# 完整回归
npx playwright test
```

---

## 12. 检查清单

Agent 编写 E2E 测试时，对照以下清单确认完整性：

- [ ] `playwright.config.ts` 已配置（baseURL、webServer、projects）
- [ ] Page Object Model 已建立（每个核心页面一个 POM）
- [ ] 定位器使用语义化方法（`getByRole` > `getByTestId` > CSS）
- [ ] 认证状态已配置复用（`storageState`）
- [ ] 关键用户路径已覆盖（CRUD + 认证 + 核心业务）
- [ ] 错误状态和边界条件已测试（空数据、网络错误、表单验证）
- [ ] 核心路径使用真实 API（非 Mock-only）
- [ ] CI 配置已就绪（GitHub Actions / 其他）
- [ ] 测试产物目录已加入 `.gitignore`（`test-results/`、`playwright-report/`）
- [ ] 截图基线已提交（如使用视觉回归）

## 输出要求

使用本方法论后，Agent 应产出：

1. **`playwright.config.ts`**：完整配置
2. **`e2e/pages/*.page.ts`**：Page Object Model
3. **`e2e/specs/**/*.spec.ts`**：测试用例（覆盖关键路径）
4. **认证 fixture**：`storageState` 或 global-setup
5. **CI 配置**：GitHub Actions 或等价 CI 流程
6. **`.gitignore` 更新**：排除测试产物目录
