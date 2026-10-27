---

name: qa/integration-testing
description: 集成测试方法论，验证模块间协作、数据库交互、服务间调用，参考 Testcontainers、Testing Library、WireMock 等开源实践
version: 1.0.0
agent: qa
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要验证模块间协作时
- 需要测试数据库真实交互时
- 需要测试服务间调用时
- 需要验证前端组件与 API 集成时
  metadata:
  internal: true

---

# 集成测试方法论

> 参考开源实践：Testcontainers、Testing Library、WireMock、Testcontainers-go、Django Test Client

## 集成测试 vs 单元测试

| 维度 | 单元测试       | 集成测试             |
| ---- | -------------- | -------------------- |
| 范围 | 单个函数/组件  | 多个模块协作         |
| 依赖 | Mock 外部依赖  | 真实依赖（DB、HTTP） |
| 速度 | 快（ms）       | 较慢（s）            |
| 目的 | 验证逻辑正确性 | 验证模块间协作       |
| 数据 | Mock 数据      | 测试数据库/真实数据  |

## 1. 后端集成测试

### 1.1 数据库集成测试

使用真实数据库（Testcontainers 或测试数据库），不 mock Repository 层。

#### Node.js + Testcontainers (PostgreSQL)

```typescript
// tests/integration/userRepository.test.ts
import { PostgreSqlContainer } from '@testcontainers/postgresql';
import { PrismaClient } from '@prisma/client';
import { UserRepository } from '../../src/repositories/userRepository';

describe('UserRepository (integration)', () => {
  let container: StartedPostgreSqlContainer;
  let prisma: PrismaClient;
  let repo: UserRepository;

  beforeAll(async () => {
    container = await new PostgreSqlContainer().start();
    prisma = new PrismaClient({ datasources: { db: { url: container.getConnectionUri() } } });
    await prisma.$executeRawUnsafe('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');
    repo = new UserRepository(prisma);
  }, 60000);

  afterAll(async () => {
    await prisma.$disconnect();
    await container.stop();
  }, 60000);

  beforeEach(async () => {
    await prisma.user.deleteMany();
  });

  it('creates and retrieves user', async () => {
    const user = await repo.create({ name: 'Alice', email: 'alice@example.com' });
    const found = await repo.findByEmail('alice@example.com');

    expect(found?.id).toBe(user.id);
    expect(found?.name).toBe('Alice');
  });

  it('returns null for non-existent email', async () => {
    const found = await repo.findByEmail('nonexistent@example.com');
    expect(found).toBeNull();
  });
});
```

#### Python + pytest (PostgreSQL)

```python
# tests/integration/test_user_repository.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.repositories import UserRepository

@pytest.fixture(scope="module")
def db_session():
    engine = create_engine("postgresql://test:test@localhost:5432/test_db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_create_and_get_user(db_session):
    repo = UserRepository(db_session)
    user = repo.create(name="Alice", email="alice@example.com")
    found = repo.find_by_email("alice@example.com")
    assert found.id == user.id
    assert found.name == "Alice"
```

### 1.2 API + DB 端到端集成

```typescript
// tests/integration/user-api.test.ts
import request from 'supertest';
import { app } from '../../src/app';
import { prisma } from '../../src/db';

describe('User API + DB integration', () => {
  beforeAll(async () => {
    await prisma.$connect();
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  beforeEach(async () => {
    await prisma.user.deleteMany();
  });

  it('POST creates user in database', async () => {
    const res = await request(app)
      .post('/api/users')
      .send({ name: 'Alice', email: 'alice@example.com' })
      .expect(201);

    // 验证数据库中确实存在
    const dbUser = await prisma.user.findUnique({ where: { id: res.body.data.id } });
    expect(dbUser).not.toBeNull();
    expect(dbUser?.name).toBe('Alice');
  });

  it('GET returns persisted user', async () => {
    await prisma.user.create({ data: { name: 'Bob', email: 'bob@example.com' } });

    const res = await request(app).get('/api/users').expect(200);
    expect(res.body.data.items).toHaveLength(1);
    expect(res.body.data.items[0].name).toBe('Bob');
  });

  it('DELETE removes user from database', async () => {
    const user = await prisma.user.create({
      data: { name: 'Charlie', email: 'charlie@example.com' },
    });

    await request(app).delete(`/api/users/${user.id}`).expect(200);

    const dbUser = await prisma.user.findUnique({ where: { id: user.id } });
    expect(dbUser).toBeNull();
  });
});
```

### 1.3 服务间调用集成

使用 WireMock 或 Mock Service Worker 模拟外部服务：

```typescript
// tests/integration/order-service.test.ts
import { WireMock } from 'wiremock-captain';

describe('OrderService integration with PaymentService', () => {
  let wiremock: WireMock;

  beforeAll(async () => {
    wiremock = new WireMock('http://localhost:8080');
  });

  it('marks order as paid when payment succeeds', async () => {
    // Mock 支付服务成功响应
    await wiremock.stubFor({
      request: { method: 'POST', url: '/payments' },
      response: { status: 200, jsonBody: { success: true, transactionId: 'tx-123' } },
    });

    const order = await orderService.create({ userId: '1', items: [] });
    const paid = await orderService.pay(order.id, { method: 'credit_card' });

    expect(paid.status).toBe('paid');
  });

  it('keeps order pending when payment fails', async () => {
    await wiremock.stubFor({
      request: { method: 'POST', url: '/payments' },
      response: { status: 402, jsonBody: { error: 'INSUFFICIENT_FUNDS' } },
    });

    const order = await orderService.create({ userId: '1', items: [] });
    await expect(orderService.pay(order.id, { method: 'credit_card' })).rejects.toThrow(
      'Payment failed',
    );

    const refreshed = await orderService.getById(order.id);
    expect(refreshed.status).toBe('pending');
  });
});
```

## 2. 前端集成测试

### 2.1 组件 + 状态管理 + API 集成

使用 Testing Library + MSW (Mock Service Worker)：

```typescript
// tests/integration/UserList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { UserList } from '../../src/components/UserList';

const server = setupServer(
  rest.get('/api/users', (req, res, ctx) =>
    res(ctx.json({ data: { items: [{ id: '1', name: 'Alice', email: 'alice@example.com' }] } }))
  )
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('UserList integration', () => {
  it('fetches and displays users from API', async () => {
    render(<UserList />);

    expect(screen.getByText('加载中...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument();
    });
  });

  it('shows error when API fails', async () => {
    server.use(
      rest.get('/api/users', (req, res, ctx) => res(ctx.status(500)))
    );

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('加载失败')).toBeInTheDocument();
    });
  });
});
```

### 2.2 完整表单提交流程

```typescript
// tests/integration/CreateUserForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { CreateUserForm } from '../../src/components/CreateUserForm';

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('CreateUserForm integration', () => {
  it('submits form and shows success', async () => {
    server.use(
      rest.post('/api/users', (req, res, ctx) =>
        res(ctx.status(201), ctx.json({ success: true, data: { id: '1' } }))
      )
    );

    render(<CreateUserForm />);

    fireEvent.change(screen.getByLabelText('姓名'), { target: { value: 'Alice' } });
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'alice@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: '提交' }));

    await waitFor(() => {
      expect(screen.getByText('创建成功')).toBeInTheDocument();
    });
  });

  it('shows validation errors from server', async () => {
    server.use(
      rest.post('/api/users', (req, res, ctx) =>
        res(ctx.status(400), ctx.json({ error: { code: 'VALIDATION_ERROR', message: '邮箱格式错误' } }))
      )
    );

    render(<CreateUserForm />);
    fireEvent.change(screen.getByLabelText('姓名'), { target: { value: 'Alice' } });
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'invalid' } });
    fireEvent.click(screen.getByRole('button', { name: '提交' }));

    await waitFor(() => {
      expect(screen.getByText('邮箱格式错误')).toBeInTheDocument();
    });
  });
});
```

### 2.3 React Context / 状态管理集成

```typescript
// tests/integration/AuthFlow.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { AuthProvider } from '../../src/context/AuthContext';
import { LoginPage } from '../../src/pages/LoginPage';

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Auth flow integration', () => {
  it('logs in and stores token in context', async () => {
    server.use(
      rest.post('/api/auth/login', (req, res, ctx) =>
        res(ctx.json({ data: { token: '<JWT_TOKEN>', user: { name: 'Alice' } } }))
      )
    );

    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    );

    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'alice@example.com' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '<PASSWORD>' } });
    fireEvent.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('欢迎，Alice')).toBeInTheDocument();
    });
  });
});
```

## 3. 测试数据库策略

### 3.1 方案选择

| 方案                       | 适用场景       | 优点       | 缺点                     |
| -------------------------- | -------------- | ---------- | ------------------------ |
| **Testcontainers**         | 需要真实数据库 | 最接近生产 | 启动慢（5-10s）          |
| **内存数据库** (H2/SQLite) | 简单 CRUD      | 快         | 与生产 DB 行为可能不一致 |
| **测试数据库**             | 已有测试环境   | 真实       | 需要维护                 |
| **事务回滚**               | 单测级隔离     | 快、无残留 | 不支持跨事务测试         |

### 3.2 数据清理策略

```typescript
// 策略 1：每个测试前清理（推荐）
beforeEach(async () => {
  await prisma.user.deleteMany();
  await prisma.order.deleteMany();
});

// 策略 2：事务回滚（更快）
let tx: Prisma.TransactionClient;
beforeEach(async () => {
  tx = await prisma.$transaction(async (t) => t, { isolationLevel: 'Serializable' });
});
afterEach(async () => {
  await tx.$rollback?.();
});
```

## 4. 集成测试的 Mock 边界

### 应该 Mock 的

| 依赖                           | 原因               |
| ------------------------------ | ------------------ |
| 第三方 API（支付、邮件、短信） | 不可控、有成本     |
| 外部微服务                     | 独立部署，不应耦合 |
| 文件系统                       | 测试速度和隔离     |

### 不应该 Mock 的

| 依赖                      | 原因                           |
| ------------------------- | ------------------------------ |
| 数据库                    | 集成测试的核心就是验证 DB 交互 |
| 应用内部服务              | 要验证模块间协作               |
| HTTP 框架（Express/Nest） | 要验证路由和中间件             |
| 验证库（Zod/Joi）         | 要验证真实校验逻辑             |

## 5. 跨前后端契约集成测试

验证前端发送的 payload 与后端 schema 一致：

```typescript
// tests/integration/contract.test.ts
import { z } from 'zod';

// 后端定义的 User Schema
const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
});

// 前端表单提交的数据
const formData = { name: 'Alice', email: 'alice@example.com' };

it('frontend form data matches backend schema', () => {
  const result = CreateUserSchema.safeParse(formData);
  expect(result.success).toBe(true);
});
```

## 6. 集成测试性能优化

```typescript
// 1. 只启动一次数据库容器（beforeAll）
let container: StartedPostgreSqlContainer;
beforeAll(async () => {
  container = await new PostgreSqlContainer().start();
}, 120000);

// 2. 复用数据库连接
// 3. 数据清理用 TRUNCATE 而非 DROP/CREATE
beforeEach(async () => {
  await prisma.$executeRawUnsafe('TRUNCATE TABLE users, orders RESTART IDENTITY CASCADE');
});

// 4. 并行执行无依赖的测试
// jest.config.js: maxWorkers: '50%'
```

## 7. 检查清单

后端集成测试：
- [ ] 使用真实数据库（Testcontainers 或测试 DB）
- [ ] 不 mock Repository/数据访问层
- [ ] 每个测试独立（数据隔离）
- [ ] 第三方服务使用 WireMock/MSW mock
- [ ] 验证数据真实写入数据库
- [ ] 验证跨模块调用链完整

前端集成测试：
- [ ] 使用 MSW mock API，不 mock 内部组件
- [ ] 验证组件 + 状态管理 + API 调用链
- [ ] 覆盖成功和失败场景
- [ ] 验证用户可见的 UI 反馈
- [ ] 不测试实现细节，测试用户行为
