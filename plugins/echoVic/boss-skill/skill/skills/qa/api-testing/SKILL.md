---

name: qa/api-testing
description: API 接口测试方法论，覆盖 RESTful/GraphQL 接口的功能、边界、安全、契约测试，参考 Supertest、REST Assured 等开源实践
version: 1.0.0
agent: qa
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要编写或执行 API 接口测试时
- 需要验证 API 契约一致性时
- 需要覆盖接口边界和安全场景时
  metadata:
  internal: true

---

# API 接口测试方法论

> 参考开源实践：Supertest、REST Assured、Postman/Newman、HTTPie、Testcontainers

## 适用场景

- 后端 API 端点需要功能验证
- 需要测试接口边界值、错误处理、权限控制
- 需要验证 API 契约（请求/响应 schema 一致性）
- 需要覆盖认证、授权、越权等安全场景
- 需要测试完整业务流程的 API 链路

## 测试类型矩阵

| 测试类型     | 目的                    | 工具                     | 示例                            |
| ------------ | ----------------------- | ------------------------ | ------------------------------- |
| **功能测试** | 验证接口正常行为        | Supertest / REST Assured | 创建资源返回 201                |
| **边界测试** | 验证边界值和错误处理    | Supertest                | 空 payload、超长字符串、非法 ID |
| **安全测试** | 认证、授权、越权        | Supertest + auth header  | 无 Token 访问受保护资源         |
| **契约测试** | 请求/响应 schema 一致性 | Zod / JSON Schema        | 响应字段类型校验                |
| **流程测试** | 多接口业务链路          | Supertest 链式调用       | 注册→登录→下单→支付             |

## 1. RESTful API 测试

### 1.1 Node.js (Supertest + Jest/Vitest)

```typescript
// tests/api/users.test.ts
import request from 'supertest';
import { app } from '../../src/app';

describe('User API', () => {
  describe('POST /api/users', () => {
    it('creates user with valid data', async () => {
      const res = await request(app)
        .post('/api/users')
        .send({ name: 'Alice', email: 'alice@example.com' })
        .expect(201)
        .expect('Content-Type', /json/);

      expect(res.body.success).toBe(true);
      expect(res.body.data).toMatchObject({ name: 'Alice', email: 'alice@example.com' });
      expect(res.body.data.id).toBeDefined();
    });

    it('rejects empty name with 400', async () => {
      const res = await request(app)
        .post('/api/users')
        .send({ name: '', email: 'test@example.com' })
        .expect(400);

      expect(res.body.error.code).toBe('VALIDATION_ERROR');
    });

    it('rejects duplicate email with 409', async () => {
      await request(app).post('/api/users').send({ name: 'A', email: 'dup@example.com' });
      const res = await request(app)
        .post('/api/users')
        .send({ name: 'B', email: 'dup@example.com' })
        .expect(409);

      expect(res.body.error.code).toBe('CONFLICT');
    });
  });
});
```

### 1.2 Python (pytest + requests)

```python
# tests/api/test_users.py
import pytest
import requests

BASE_URL = "http://localhost:3000"

def test_create_user():
    res = requests.post(f"{BASE_URL}/api/users", json={"name": "Alice", "email": "alice@example.com"})
    assert res.status_code == 201
    assert res.json()["data"]["name"] == "Alice"

def test_create_user_empty_name():
    res = requests.post(f"{BASE_URL}/api/users", json={"name": "", "email": "test@example.com"})
    assert res.status_code == 400
```

### 1.3 Go (net/http/httptest)

```go
// handlers/users_test.go
func TestCreateUser(t *testing.T) {
    app := setupTestApp()
    body := strings.NewReader(`{"name":"Alice","email":"alice@example.com"}`)
    req := httptest.NewRequest("POST", "/api/users", body)
    req.Header.Set("Content-Type", "application/json")
    w := httptest.NewRecorder()

    app.ServeHTTP(w, req)

    if w.Code != http.StatusCreated {
        t.Errorf("expected 201, got %d", w.Code)
    }
}
```

## 2. GraphQL API 测试

```typescript
// tests/api/graphql.test.ts
import request from 'supertest';
import { app } from '../../src/app';

describe('GraphQL API', () => {
  it('queries user by id', async () => {
    const query = `
      query GetUser($id: ID!) {
        user(id: $id) { id name email }
      }
    `;
    const res = await request(app)
      .post('/graphql')
      .send({ query, variables: { id: '1' } })
      .expect(200);

    expect(res.body.data.user).toBeDefined();
    expect(res.body.errors).toBeUndefined();
  });

  it('mutates: create user', async () => {
    const mutation = `
      mutation CreateUser($input: CreateUserInput!) {
        createUser(input: $input) { id name }
      }
    `;
    const res = await request(app)
      .post('/graphql')
      .send({ mutation, variables: { input: { name: 'Bob', email: 'bob@example.com' } } })
      .expect(200);

    expect(res.body.data.createUser.id).toBeDefined();
  });
});
```

## 3. 认证与授权测试

### 3.1 Token 认证

```typescript
describe('Protected endpoints', () => {
  let token: string;

  beforeAll(async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'admin@example.com', password: '<PASSWORD>' });
    token = res.body.data.token;
  });

  it('returns 401 without token', async () => {
    await request(app).get('/api/users/profile').expect(401);
  });

  it('returns 401 with invalid token', async () => {
    await request(app)
      .get('/api/users/profile')
      .set('Authorization', 'Bearer <INVALID_TOKEN>')
      .expect(401);
  });

  it('returns 200 with valid token', async () => {
    await request(app)
      .get('/api/users/profile')
      .set('Authorization', `Bearer ${token}`)
      .expect(200);
  });
});
```

### 3.2 权限/越权测试

```typescript
describe('Authorization', () => {
  let adminToken: string;
  let userToken: string;

  beforeAll(async () => {
    adminToken = await login('admin@example.com', '<PASSWORD>');
    userToken = await login('user@example.com', '<PASSWORD>');
  });

  it('admin can delete any user', async () => {
    await request(app)
      .delete('/api/users/123')
      .set('Authorization', `Bearer ${adminToken}`)
      .expect(200);
  });

  it('regular user cannot delete others (403)', async () => {
    await request(app)
      .delete('/api/users/123')
      .set('Authorization', `Bearer ${userToken}`)
      .expect(403);
  });
});
```

## 4. 边界值与错误用例

### 4.1 输入边界

```typescript
describe('Input boundaries', () => {
  it('rejects email exceeding max length', async () => {
    const longEmail = 'a'.repeat(256) + '@example.com';
    await request(app).post('/api/users').send({ name: 'Test', email: longEmail }).expect(400);
  });

  it('rejects invalid UUID format', async () => {
    await request(app).get('/api/users/not-a-uuid').expect(400);
  });

  it('rejects negative quantity', async () => {
    await request(app)
      .post('/api/orders')
      .send({ items: [{ productId: '1', quantity: -1 }] })
      .expect(400);
  });

  it('rejects SQL injection attempt', async () => {
    await request(app).get("/api/users?id=1' OR '1'='1").expect(400);
  });
});
```

### 4.2 业务状态机管控

当接口涉及状态流转时，必须测试状态管控：

```typescript
describe('Order state machine', () => {
  it('cannot cancel a paid order', async () => {
    // 创建并支付订单
    const order = await createAndPayOrder();

    // 尝试取消已支付订单
    const res = await request(app)
      .post(`/api/orders/${order.id}/cancel`)
      .set('Authorization', `Bearer ${token}`)
      .expect(409);

    expect(res.body.error.code).toBe('INVALID_STATE_TRANSITION');
  });

  it('cannot modify a confirmed order', async () => {
    const order = await createConfirmedOrder();

    await request(app)
      .put(`/api/orders/${order.id}`)
      .set('Authorization', `Bearer ${token}`)
      .send({ items: [] })
      .expect(409);
  });
});
```

## 5. 契约测试（Schema 校验）

使用 Zod 或 JSON Schema 校验响应结构：

```typescript
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  createdAt: z.string().datetime(),
});

it('response matches user schema', async () => {
  const res = await request(app).get('/api/users/1').expect(200);
  const result = UserSchema.safeParse(res.body.data);
  expect(result.success).toBe(true);
});
```

## 6. 数据依赖管理

### 6.1 预取数据（Prefetch）

当用例依赖已有数据时，先预取真实 ID 注入变量池：

```typescript
describe('Dependent endpoints', () => {
  let existingUserId: string;

  beforeAll(async () => {
    // 预取一个真实存在的用户 ID
    const res = await request(app).get('/api/users?limit=1');
    existingUserId = res.body.data.items[0]?.id;
  });

  it('updates existing user', async () => {
    await request(app).put(`/api/users/${existingUserId}`).send({ name: 'Updated' }).expect(200);
  });
});
```

### 6.2 破坏性操作安全保护

对 DELETE/逻辑删除类用例，使用假 ID 避免污染真实数据：

```typescript
it('returns 404 when deleting non-existent user', async () => {
  await request(app).delete('/api/users/00000000-0000-0000-0000-000000000000').expect(404);
});
```

### 6.3 测试数据隔离

```typescript
beforeEach(async () => {
  // 每个测试前清理相关表
  await db.user.deleteMany({ where: { email: { startsWith: 'test-' } } });
});
```

## 7. 性能与并发测试

```typescript
it('handles 10 concurrent user creations', async () => {
  const promises = Array.from({ length: 10 }, (_, i) =>
    request(app)
      .post('/api/users')
      .send({ name: `User${i}`, email: `user${i}@test.com` }),
  );

  const responses = await Promise.all(promises);
  responses.forEach((res) => expect(res.status).toBe(201));
});
```

## 8. 断言策略

### 分层判定原则

| 场景     | 主判据                       | 辅判据                  |
| -------- | ---------------------------- | ----------------------- |
| 正常请求 | HTTP 状态码 2xx              | 响应体字段              |
| 参数错误 | HTTP 400 + 业务码            | 错误消息                |
| 业务错误 | **业务码**（非 HTTP 状态码） | 错误消息                |
| 认证失败 | HTTP 401                     | WWW-Authenticate header |
| 授权失败 | HTTP 403                     | -                       |

> ⚠️ 当后端使用「200 + 业务码」表达错误时，断言应以**业务码语义**为主，不应因 HTTP 200 就判定通过。

## 9. 测试报告要求

每个 API 测试文件必须覆盖：
- [ ] 正常流程（happy path）
- [ ] 参数校验（必填、格式、长度、类型）
- [ ] 认证（无 Token、无效 Token、过期 Token）
- [ ] 授权（角色权限、越权访问）
- [ ] 业务状态机（状态流转限制）
- [ ] 边界值（空、超长、非法、特殊字符）
- [ ] 安全（SQL 注入、XSS、路径遍历）
- [ ] 并发与幂等

## 10. 检查清单

- [ ] 所有 CRUD 端点都有功能测试
- [ ] 每个端点至少有 1 个错误/边界用例
- [ ] 认证端点覆盖成功和失败场景
- [ ] 受保护资源覆盖 401/403 场景
- [ ] 响应体通过 schema 校验
- [ ] 测试数据相互隔离，可重复运行
- [ ] 破坏性操作使用假 ID 或测试数据
- [ ] 不依赖外部服务（mock 第三方 API）
