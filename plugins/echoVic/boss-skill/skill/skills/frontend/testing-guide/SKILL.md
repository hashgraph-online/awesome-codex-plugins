---
name: frontend/testing-guide
description: 前端测试编写指南，包括单元测试、集成测试和E2E测试的编写方法和最佳实践
type: methodology
agent: boss-frontend
---

# 前端测试编写指南

## 测试要求（强制）

> **职责边界**：Frontend Agent 是测试的**编写者**，QA Agent 是测试的**验证者**。

### 测试金字塔

| 测试类型 | 占比 | 要求 |
|----------|------|------|
| **单元测试** | ~70% | 每个组件/Hook 必须有测试 |
| **集成测试** | ~20% | 组件交互、状态管理测试 |
| **E2E 测试** | ~10% | **必须编写**，覆盖用户流程 |

## 单元测试编写

### 组件渲染测试

```typescript
// Button.test.tsx
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    screen.getByText('Click').click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click</Button>);
    expect(screen.getByText('Click')).toBeDisabled();
  });
});
```

### Hook 测试

```typescript
// useCounter.test.ts
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('initializes with default value', () => {
    const { result } = renderHook(() => useCounter());
    expect(result.current.count).toBe(0);
  });

  it('increments count', () => {
    const { result } = renderHook(() => useCounter());
    act(() => {
      result.current.increment();
    });
    expect(result.current.count).toBe(1);
  });
});
```

### 表单验证测试

```typescript
// LoginForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('shows validation error for invalid email', async () => {
    render(<LoginForm />);
    const emailInput = screen.getByLabelText('Email');
    
    await userEvent.type(emailInput, 'invalid-email');
    await userEvent.tab(); // Trigger blur
    
    await waitFor(() => {
      expect(screen.getByText('Invalid email format')).toBeInTheDocument();
    });
  });

  it('submits form with valid data', async () => {
    const onSubmit = jest.fn();
    render(<LoginForm onSubmit={onSubmit} />);
    
    await userEvent.type(screen.getByLabelText('Email'), 'user@example.com');
    await userEvent.type(screen.getByLabelText('Password'), 'password123');
    await userEvent.click(screen.getByRole('button', { name: 'Login' }));
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: 'password123',
      });
    });
  });
});
```

## 集成测试编写

### 组件交互测试

```typescript
// UserList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserList } from './UserList';
import { UserProvider } from './UserContext';

describe('UserList integration', () => {
  it('adds new user to list', async () => {
    render(
      <UserProvider>
        <UserList />
      </UserProvider>
    );
    
    // 打开添加用户表单
    await userEvent.click(screen.getByText('Add User'));
    
    // 填写表单
    await userEvent.type(screen.getByLabelText('Name'), 'John Doe');
    await userEvent.type(screen.getByLabelText('Email'), 'john@example.com');
    
    // 提交
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }));
    
    // 验证用户出现在列表中
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
    });
  });
});
```

### 状态管理测试

```typescript
// store.test.ts
import { renderHook, act } from '@testing-library/react';
import { useStore } from './store';

describe('Store integration', () => {
  it('updates user state across components', () => {
    const { result } = renderHook(() => useStore());
    
    act(() => {
      result.current.setUser({ id: '1', name: 'Alice' });
    });
    
    expect(result.current.user).toEqual({ id: '1', name: 'Alice' });
    
    act(() => {
      result.current.updateUserName('Bob');
    });
    
    expect(result.current.user?.name).toBe('Bob');
  });
});
```

## E2E 测试编写（必须）

> **完整 Playwright 方法论**：详见 `Skill(skill: "qa/e2e-playwright")`，包含项目初始化、Page Object Model、认证复用、API Mock、视觉回归、多浏览器测试、CI 集成和调试技巧。

### E2E 测试必须覆盖

- ✅ 创建流程（如：添加数据）
- ✅ 编辑流程（如：修改数据）
- ✅ 删除流程（如：删除数据）
- ✅ 列表展示（如：查看列表）
- ✅ 核心业务流程

### Playwright 示例（Page Object Model）

```typescript
// e2e/pages/user-list.page.ts
import { type Page, type Locator } from '@playwright/test';

export class UserListPage {
  private readonly addButton: Locator;
  private readonly table: Locator;

  constructor(private readonly page: Page) {
    this.addButton = page.getByRole('button', { name: '添加用户' });
    this.table = page.getByRole('table');
  }

  async goto() { await this.page.goto('/users'); }
  async clickAddUser() { await this.addButton.click(); }
  getTable() { return this.table; }

  async editUser(name: string) {
    await this.page.getByRole('row', { name }).getByRole('button', { name: '编辑' }).click();
  }
  async deleteUser(name: string) {
    await this.page.getByRole('row', { name }).getByRole('button', { name: '删除' }).click();
  }
  async confirmDelete() {
    await this.page.getByRole('button', { name: '确认' }).click();
  }
}
```

```typescript
// e2e/specs/crud/user-management.spec.ts
import { test, expect } from '@playwright/test';
import { UserListPage } from '../../pages/user-list.page';

test.describe('用户管理 CRUD', () => {
  let userList: UserListPage;

  test.beforeEach(async ({ page }) => {
    userList = new UserListPage(page);
    await userList.goto();
  });

  test('创建 → 编辑 → 删除完整流程', async ({ page }) => {
    // 创建
    await userList.clickAddUser();
    await page.getByLabel('姓名').fill('测试用户');
    await page.getByLabel('邮箱').fill('test@example.com');
    await page.getByRole('button', { name: '提交' }).click();
    await expect(page.getByText('测试用户')).toBeVisible();

    // 编辑
    await userList.editUser('测试用户');
    await page.getByLabel('姓名').fill('修改后的用户');
    await page.getByRole('button', { name: '提交' }).click();
    await expect(page.getByText('修改后的用户')).toBeVisible();

    // 删除
    await userList.deleteUser('修改后的用户');
    await userList.confirmDelete();
    await expect(page.getByText('修改后的用户')).not.toBeVisible();
  });

  test('列表分页展示', async ({ page }) => {
    await expect(userList.getTable()).toBeVisible();
    await page.getByRole('button', { name: 'Next' }).click();
    await expect(page).toHaveURL(/page=2/);
  });
});
```

### 定位器优先级

| 优先级 | 方法 | 说明 |
|--------|------|------|
| 1 | `getByRole` | 无障碍语义，最稳定 |
| 2 | `getByLabel` | 表单元素首选 |
| 3 | `getByText` | 静态文本 |
| 4 | `getByTestId` | 无语义标记时兜底 |
| 5 | CSS/XPath | **尽量避免** |

## 测试最佳实践

### 测试命名
- 使用描述性的测试名称
- 格式：`it('should [expected behavior] when [condition]')`
- 示例：`it('should show error message when email is invalid')`

### 测试隔离
- 每个测试独立运行，不依赖其他测试
- 使用 beforeEach 设置初始状态
- 使用 afterEach 清理副作用

### Mock 策略
- Mock 外部依赖（API、第三方库）
- 不要 Mock 被测试的代码
- 使用 MSW（Mock Service Worker）Mock API

```typescript
// mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/users', (req, res, ctx) => {
    return res(
      ctx.json([
        { id: '1', name: 'Alice' },
        { id: '2', name: 'Bob' },
      ])
    );
  }),
];
```

### 边界条件测试
- 空数据：列表为空时的展示
- 错误状态：API 失败时的处理
- 加载状态：数据加载中的展示
- 极限值：最大/最小输入值

### 无障碍测试
```typescript
it('is accessible', async () => {
  const { container } = render(<Button>Click</Button>);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## 测试覆盖率要求

- 语句覆盖率：≥ 80%
- 分支覆盖率：≥ 75%
- 函数覆盖率：≥ 80%
- 行覆盖率：≥ 80%

运行覆盖率报告：
```bash
npm test -- --coverage
```

## 测试报告格式

实现完成后，在输出中包含：

**测试添加**：
| 类型 | 文件 | 描述 |
|------|------|------|
| 单元测试 | `src/components/Button.test.tsx` | Button 组件渲染和交互测试 |
| 集成测试 | `src/features/users/UserList.test.tsx` | 用户列表增删改查集成测试 |
| **E2E 测试** | `e2e/user-management.spec.ts` | 用户管理完整流程 E2E 测试 |

**测试结果**：
- 通过：25 / 失败：0
- 覆盖率：85%
- E2E 测试：✅ 已编写并通过
