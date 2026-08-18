---
name: backend/testing-guide
description: 后端测试编写指南，包括单元测试、集成测试和E2E测试的编写方法和最佳实践
type: methodology
agent: boss-backend
---

# 后端测试编写指南

## 测试要求（强制）

> **职责边界**：Backend Agent 是测试的**编写者**，QA Agent 是测试的**验证者**。

### 测试金字塔

| 测试类型 | 占比 | 要求 |
|----------|------|------|
| **单元测试** | ~70% | Service 层、业务逻辑必须有测试 |
| **集成测试** | ~20% | API 端点、数据库操作测试 |
| **E2E 测试** | ~10% | **必须编写**，完整 API 流程测试 |

## 单元测试编写

### Service 层测试

```typescript
// services/userService.test.ts
import { UserService } from './userService';
import { UserRepository } from '../repositories/userRepository';

jest.mock('../repositories/userRepository');

describe('UserService', () => {
  let userService: UserService;
  let userRepository: jest.Mocked<UserRepository>;

  beforeEach(() => {
    userRepository = new UserRepository() as jest.Mocked<UserRepository>;
    userService = new UserService(userRepository);
  });

  describe('getById', () => {
    it('returns user when found', async () => {
      const mockUser = { id: '1', name: 'Alice', email: 'alice@example.com' };
      userRepository.findById.mockResolvedValue(mockUser);

      const result = await userService.getById('1');

      expect(result).toEqual(mockUser);
      expect(userRepository.findById).toHaveBeenCalledWith('1');
    });

    it('throws NotFoundError when user not found', async () => {
      userRepository.findById.mockResolvedValue(null);

      await expect(userService.getById('999')).rejects.toThrow('User not found');
    });
  });

  describe('create', () => {
    it('creates user with valid data', async () => {
      const createData = { name: 'Bob', email: 'bob@example.com' };
      const mockUser = { id: '2', ...createData };
      
      userRepository.findByEmail.mockResolvedValue(null);
      userRepository.create.mockResolvedValue(mockUser);

      const result = await userService.create(createData);

      expect(result).toEqual(mockUser);
      expect(userRepository.findByEmail).toHaveBeenCalledWith('bob@example.com');
      expect(userRepository.create).toHaveBeenCalledWith(createData);
    });

    it('throws ConflictError when email already exists', async () => {
      const createData = { name: 'Bob', email: 'existing@example.com' };
      userRepository.findByEmail.mockResolvedValue({ id: '1', name: 'Existing', email: 'existing@example.com' });

      await expect(userService.create(createData)).rejects.toThrow('Email already exists');
    });
  });
});
```

### 业务逻辑测试

```typescript
// services/orderService.test.ts
describe('OrderService', () => {
  describe('calculateTotal', () => {
    it('calculates total with discount', () => {
      const items = [
        { price: 100, quantity: 2 },
        { price: 50, quantity: 1 },
      ];
      const discount = 0.1; // 10% off

      const total = orderService.calculateTotal(items, discount);

      expect(total).toBe(225); // (200 + 50) * 0.9
    });

    it('handles zero discount', () => {
      const items = [{ price: 100, quantity: 1 }];
      const total = orderService.calculateTotal(items, 0);
      expect(total).toBe(100);
    });
  });

  describe('validateOrder', () => {
    it('validates order with sufficient stock', async () => {
      const order = { productId: '1', quantity: 5 };
      productRepository.findById.mockResolvedValue({ id: '1', stock: 10 });

      const result = await orderService.validateOrder(order);

      expect(result.valid).toBe(true);
    });

    it('rejects order with insufficient stock', async () => {
      const order = { productId: '1', quantity: 15 };
      productRepository.findById.mockResolvedValue({ id: '1', stock: 10 });

      const result = await orderService.validateOrder(order);

      expect(result.valid).toBe(false);
      expect(result.error).toBe('Insufficient stock');
    });
  });
});
```

## 集成测试编写

### API 端点测试

```typescript
// controllers/userController.test.ts
import request from 'supertest';
import { app } from '../app';
import { db } from '../db';

describe('User API', () => {
  beforeEach(async () => {
    // 清理测试数据库
    await db.user.deleteMany();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  describe('POST /api/users', () => {
    it('creates a new user', async () => {
      const userData = {
        name: 'Alice',
        email: 'alice@example.com',
      };

      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toMatchObject(userData);
      expect(response.body.data.id).toBeDefined();
    });

    it('returns 400 for invalid email', async () => {
      const userData = {
        name: 'Bob',
        email: 'invalid-email',
      };

      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error.code).toBe('VALIDATION_ERROR');
    });

    it('returns 409 for duplicate email', async () => {
      const userData = {
        name: 'Charlie',
        email: 'duplicate@example.com',
      };

      // 创建第一个用户
      await request(app).post('/api/users').send(userData);

      // 尝试创建重复邮箱的用户
      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(409);

      expect(response.body.error.code).toBe('CONFLICT');
    });
  });

  describe('GET /api/users/:id', () => {
    it('returns user by id', async () => {
      // 创建测试用户
      const createResponse = await request(app)
        .post('/api/users')
        .send({ name: 'Dave', email: 'dave@example.com' });

      const userId = createResponse.body.data.id;

      // 获取用户
      const response = await request(app)
        .get(`/api/users/${userId}`)
        .expect(200);

      expect(response.body.data.id).toBe(userId);
      expect(response.body.data.name).toBe('Dave');
    });

    it('returns 404 for non-existent user', async () => {
      const response = await request(app)
        .get('/api/users/non-existent-id')
        .expect(404);

      expect(response.body.error.code).toBe('NOT_FOUND');
    });
  });

  describe('PUT /api/users/:id', () => {
    it('updates user', async () => {
      // 创建用户
      const createResponse = await request(app)
        .post('/api/users')
        .send({ name: 'Eve', email: 'eve@example.com' });

      const userId = createResponse.body.data.id;

      // 更新用户
      const response = await request(app)
        .put(`/api/users/${userId}`)
        .send({ name: 'Eve Updated' })
        .expect(200);

      expect(response.body.data.name).toBe('Eve Updated');
      expect(response.body.data.email).toBe('eve@example.com');
    });
  });

  describe('DELETE /api/users/:id', () => {
    it('deletes user', async () => {
      // 创建用户
      const createResponse = await request(app)
        .post('/api/users')
        .send({ name: 'Frank', email: 'frank@example.com' });

      const userId = createResponse.body.data.id;

      // 删除用户
      await request(app)
        .delete(`/api/users/${userId}`)
        .expect(200);

      // 验证用户已删除
      await request(app)
        .get(`/api/users/${userId}`)
        .expect(404);
    });
  });
});
```

### 数据库操作测试

```typescript
// repositories/userRepository.test.ts
import { UserRepository } from './userRepository';
import { db } from '../db';

describe('UserRepository', () => {
  let userRepository: UserRepository;

  beforeEach(async () => {
    userRepository = new UserRepository();
    await db.user.deleteMany();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  describe('create', () => {
    it('creates user in database', async () => {
      const userData = { name: 'Alice', email: 'alice@example.com' };
      const user = await userRepository.create(userData);

      expect(user.id).toBeDefined();
      expect(user.name).toBe('Alice');

      // 验证数据库中存在
      const found = await db.user.findUnique({ where: { id: user.id } });
      expect(found).toBeTruthy();
    });
  });

  describe('findByEmail', () => {
    it('finds user by email', async () => {
      await userRepository.create({ name: 'Bob', email: 'bob@example.com' });

      const user = await userRepository.findByEmail('bob@example.com');

      expect(user).toBeTruthy();
      expect(user?.name).toBe('Bob');
    });

    it('returns null for non-existent email', async () => {
      const user = await userRepository.findByEmail('nonexistent@example.com');
      expect(user).toBeNull();
    });
  });
});
```

## E2E 测试编写（必须）

### API E2E 测试必须覆盖

- ✅ 创建资源（POST）
- ✅ 读取资源（GET）
- ✅ 更新资源（PUT/PATCH）
- ✅ 删除资源（DELETE）
- ✅ 完整业务流程（如：注册→登录→操作）

### 完整 CRUD 流程测试

```typescript
// e2e/user-crud.test.ts
import request from 'supertest';
import { app } from '../app';
import { db } from '../db';

describe('User CRUD E2E', () => {
  beforeAll(async () => {
    await db.user.deleteMany();
  });

  afterAll(async () => {
    await db.$disconnect();
  });

  it('completes full user lifecycle', async () => {
    // 1. 创建用户
    const createResponse = await request(app)
      .post('/api/users')
      .send({
        name: 'John Doe',
        email: 'john@example.com',
        password: 'password123',
      })
      .expect(201);

    expect(createResponse.body.success).toBe(true);
    const userId = createResponse.body.data.id;

    // 2. 读取用户
    const getResponse = await request(app)
      .get(`/api/users/${userId}`)
      .expect(200);

    expect(getResponse.body.data.name).toBe('John Doe');
    expect(getResponse.body.data.email).toBe('john@example.com');

    // 3. 更新用户
    const updateResponse = await request(app)
      .put(`/api/users/${userId}`)
      .send({ name: 'John Updated' })
      .expect(200);

    expect(updateResponse.body.data.name).toBe('John Updated');

    // 4. 验证更新
    const verifyResponse = await request(app)
      .get(`/api/users/${userId}`)
      .expect(200);

    expect(verifyResponse.body.data.name).toBe('John Updated');

    // 5. 删除用户
    await request(app)
      .delete(`/api/users/${userId}`)
      .expect(200);

    // 6. 验证删除
    await request(app)
      .get(`/api/users/${userId}`)
      .expect(404);
  });
});
```

### 认证流程 E2E 测试

```typescript
// e2e/auth-flow.test.ts
describe('Authentication Flow E2E', () => {
  it('completes registration and login flow', async () => {
    // 1. 注册
    const registerResponse = await request(app)
      .post('/api/auth/register')
      .send({
        name: 'Alice',
        email: 'alice@example.com',
        password: 'password123',
      })
      .expect(201);

    expect(registerResponse.body.data.token).toBeDefined();
    const token = registerResponse.body.data.token;

    // 2. 使用 Token 访问受保护资源
    const profileResponse = await request(app)
      .get('/api/auth/profile')
      .set('Authorization', `Bearer ${token}`)
      .expect(200);

    expect(profileResponse.body.data.email).toBe('alice@example.com');

    // 3. 登出
    await request(app)
      .post('/api/auth/logout')
      .set('Authorization', `Bearer ${token}`)
      .expect(200);

    // 4. 登录
    const loginResponse = await request(app)
      .post('/api/auth/login')
      .send({
        email: 'alice@example.com',
        password: 'password123',
      })
      .expect(200);

    expect(loginResponse.body.data.token).toBeDefined();
  });

  it('rejects invalid credentials', async () => {
    await request(app)
      .post('/api/auth/login')
      .send({
        email: 'alice@example.com',
        password: 'wrong-example',
      })
      .expect(401);
  });
});
```

### 业务流程 E2E 测试

```typescript
// e2e/order-flow.test.ts
describe('Order Flow E2E', () => {
  let authToken: string;
  let productId: string;

  beforeAll(async () => {
    // 注册并登录
    const registerResponse = await request(app)
      .post('/api/auth/register')
      .send({ name: 'Buyer', email: 'buyer@example.com', password: 'pass123' });
    authToken = registerResponse.body.data.token;

    // 创建测试商品
    const productResponse = await request(app)
      .post('/api/products')
      .set('Authorization', `Bearer ${authToken}`)
      .send({ name: 'Test Product', price: 100, stock: 10 });
    productId = productResponse.body.data.id;
  });

  it('completes order creation and payment flow', async () => {
    // 1. 创建订单
    const orderResponse = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        items: [{ productId, quantity: 2 }],
      })
      .expect(201);

    const orderId = orderResponse.body.data.id;
    expect(orderResponse.body.data.status).toBe('pending');
    expect(orderResponse.body.data.total).toBe(200);

    // 2. 支付订单
    const paymentResponse = await request(app)
      .post(`/api/orders/${orderId}/pay`)
      .set('Authorization', `Bearer ${authToken}`)
      .send({ paymentMethod: 'credit_card' })
      .expect(200);

    expect(paymentResponse.body.data.status).toBe('paid');

    // 3. 验证库存减少
    const productResponse = await request(app)
      .get(`/api/products/${productId}`)
      .expect(200);

    expect(productResponse.body.data.stock).toBe(8); // 10 - 2

    // 4. 获取订单历史
    const ordersResponse = await request(app)
      .get('/api/orders')
      .set('Authorization', `Bearer ${authToken}`)
      .expect(200);

    expect(ordersResponse.body.data.items).toHaveLength(1);
    expect(ordersResponse.body.data.items[0].id).toBe(orderId);
  });
});
```

## 测试最佳实践

### 测试数据库隔离

使用测试数据库或事务回滚：

```typescript
// 方案 1：使用测试数据库
beforeAll(async () => {
  process.env.DATABASE_URL = 'postgresql://localhost:5432/test_db';
  await db.$connect();
});

// 方案 2：使用事务回滚
beforeEach(async () => {
  await db.$transaction(async (tx) => {
    // 测试在事务中运行
  });
});
```

### Mock 外部服务

```typescript
// 模拟第三方 API
jest.mock('../services/paymentGateway', () => ({
  processPayment: jest.fn().mockResolvedValue({ success: true, transactionId: 'tx123' }),
}));

// 模拟邮件服务
jest.mock('../services/emailService', () => ({
  sendEmail: jest.fn().mockResolvedValue(true),
}));
```

### 测试边界条件

```typescript
describe('Boundary conditions', () => {
  it('handles empty list', async () => {
    const response = await request(app).get('/api/users').expect(200);
    expect(response.body.data.items).toEqual([]);
  });

  it('handles maximum page size', async () => {
    const response = await request(app)
      .get('/api/users?pageSize=1000')
      .expect(400);
    expect(response.body.error.message).toContain('pageSize');
  });

  it('handles invalid UUID', async () => {
    await request(app)
      .get('/api/users/invalid-uuid')
      .expect(400);
  });
});
```

### 测试并发场景

```typescript
it('handles concurrent requests', async () => {
  const requests = Array(10).fill(null).map(() =>
    request(app).post('/api/users').send({ name: 'User', email: `user${Math.random()}@example.com` })
  );

  const responses = await Promise.all(requests);

  responses.forEach(response => {
    expect(response.status).toBe(201);
  });
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
| 单元测试 | `src/services/userService.test.ts` | UserService 业务逻辑测试 |
| 集成测试 | `src/controllers/userController.test.ts` | User API 端点集成测试 |
| **E2E 测试** | `e2e/user-crud.test.ts` | 用户 CRUD 完整流程 E2E 测试 |

**测试结果**：
- 通过：42 / 失败：0
- 覆盖率：87%
- E2E 测试：✅ 已编写并通过
