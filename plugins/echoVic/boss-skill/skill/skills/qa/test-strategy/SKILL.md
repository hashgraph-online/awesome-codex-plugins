---

name: qa/test-strategy
description: 测试策略与测试金字塔原则，定义测试优先级、风险驱动测试、测试类型决策、环境与数据策略
version: 2.0.0
agent: qa
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 开始测试工作时
- 需要制定测试计划时
  metadata:
  internal: true

---

# 测试策略与测试金字塔

## 测试金字塔原则

```
          /\
         /  \
        / E2E \          ← ~10%：端到端用户流程【必须编写】
       /--------\
      /  集成测试  \       ← ~20%：组件/服务/API 交互
     /--------------\
    /    单元测试     \    ← ~70%：函数/组件/服务逻辑
   /--------------------\
```

### E2E 测试是强制要求

**每个项目必须编写 E2E 测试**，最少覆盖：
- 创建流程
- 编辑流程
- 删除流程
- 列表展示
- 核心业务流程

### 前端 vs 后端测试分布

| 层级         | 前端测试                     | 后端测试                                   | 方法论                   |
| ------------ | ---------------------------- | ------------------------------------------ | ------------------------ |
| **单元测试** | 组件渲染、Hooks、工具函数    | Service 层、业务逻辑、工具类               | `qa/unit-testing`        |
| **集成测试** | 组件交互、状态管理、API 调用 | API 端点、数据库操作、服务间调用           | `qa/integration-testing` |
| **接口测试** | -                            | RESTful/GraphQL 接口功能、边界、安全、契约 | `qa/api-testing`         |
| **E2E 测试** | UI 用户流程                  | API 完整流程、跨服务调用                   | `qa/e2e-playwright`      |

> 详细方法论请加载对应 skill：单元测试见 `qa/unit-testing`，接口测试见 `qa/api-testing`，集成测试见 `qa/integration-testing`，E2E 见 `qa/e2e-playwright`。

## 测试类型决策树

面对一个需求/变更时，按以下流程决定写哪些测试：

```
变更是否涉及用户可见 UI 或完整业务流程？
├─ 是 → 必须写 E2E（qa/e2e-playwright）
└─ 否 → 继续判断

变更是否涉及多个模块/服务协作？
├─ 是 → 必须写集成测试（qa/integration-testing）
└─ 否 → 继续判断

变更是否暴露 API 端点？
├─ 是 → 必须写接口测试（qa/api-testing）
└─ 否 → 继续判断

变更是否包含纯函数/组件逻辑？
└─ 是 → 必须写单元测试（shared/tdd）
```

**规则**：
- 单一函数逻辑 → 单元测试即可
- 跨函数/跨模块 → 单元 + 集成
- 暴露 API → 单元 + 接口 + 集成
- 用户可见流程 → 全部四层

## 风险驱动的测试优先级

按风险等级决定测试投入和执行顺序：

| 风险等级      | 判定标准                           | 测试要求                     | 执行优先级         |
| ------------- | ---------------------------------- | ---------------------------- | ------------------ |
| **P0 - 致命** | 核心业务流程、支付、认证、数据丢失 | 单元 + 集成 + E2E + 安全测试 | 最先执行，必须全绿 |
| **P1 - 高**   | 主要功能、数据一致性、权限控制     | 单元 + 集成 + E2E            | 高优先             |
| **P2 - 中**   | 次要功能、UI 展示、非核心逻辑      | 单元 + 集成                  | 中优先             |
| **P3 - 低**   | 边缘功能、文案、样式               | 单元测试（可选）             | 最后执行           |

### 风险评估维度

评估每个变更的风险时，考虑：
1. **影响范围**：影响多少用户/功能？
2. **失败后果**：失败会导致什么（数据丢失/资金损失/体验下降）？
3. **变更复杂度**：改动了多少文件/模块？
4. **外部依赖**：是否涉及第三方服务/数据库？
5. **历史缺陷率**：该模块是否频繁出 bug？

## 测试设计技术

### 等价类划分

将输入域划分为有效等价类和无效等价类，每个等价类取一个代表值：

```
邮箱字段校验：
- 有效等价类：合法格式 (a@b.com)
- 无效等价类：无 @ (ab.com)、无域名 (a@)、超长 (>254)、含特殊字符
```

### 边界值分析

在等价类边界上选取测试值：

```
分页 pageSize 限制 1-100：
- 边界值：0, 1, 50, 100, 101
- 测试：0→400, 1→200, 50→200, 100→200, 101→400
```

### 决策表测试

当多个条件组合产生不同结果时使用：

```
订单取消决策表：
| 条件              | 规则1 | 规则2 | 规则3 |
|-------------------|-------|-------|-------|
| 订单状态 = pending | T     | F     | F     |
| 订单状态 = paid    | F     | T     | F     |
| 用户角色 = admin   | -     | T     | F     |
| 结果              | 允许  | 允许  | 拒绝  |
```

### 状态转换测试

对有状态的实体（订单、用户会话），测试所有合法和非法的状态转换：

```
订单状态机：pending → paid → shipped → delivered
                        ↘ cancelled
非法转换：paid → pending（应拒绝）、delivered → cancelled（应拒绝）
```

## QA Attack Protocol

- **重放核心用户路径**：证明核心用户路径真实可用
- **捕获真实 payload 与服务端响应**：验证请求 payload、服务端响应和 schema 一致性
- **攻击认证授权**：覆盖匿名、授权、非授权、过期、越权
- **攻击数据边界**：empty state、pagination、第二页、旧数据、illegal enum、long input、double submit
- **攻击业务一致性**：核对界面展示与服务端业务常量一致
- **验证产物类功能**：验证核心产物、记录或状态存在、可展示、可继续用于下游流程
- **标记未验证路径**：若核心用户路径只由 Mock 或桩数据证明，必须标记为未验证，不能作为发布证据

## 安全测试方法论

安全测试不是可选项，每个暴露的接口和用户输入点都必须覆盖。

### 安全测试清单

| 类别         | 测试内容     | 具体用例                                                           |
| ------------ | ------------ | ------------------------------------------------------------------ |
| **认证**     | Token 有效性 | 无 Token → 401、无效 Token → 401、过期 Token → 401、伪造签名 → 401 |
| **授权**     | 权限边界     | 普通用户访问 admin 资源 → 403、跨用户访问他人数据 → 403            |
| **输入校验** | 边界与格式   | 空值、超长、特殊字符、SQL 注入、XSS、路径遍历                      |
| **速率限制** | 防暴力破解   | 连续失败登录 N 次后限流、API 调用频率限制                          |
| **敏感数据** | 信息泄露     | 响应中不含密码/Token、错误信息不暴露内部结构                       |
| **会话管理** | 会话安全     | 登出后 Token 失效、会话超时、并发会话限制                          |

### SQL 注入测试

```typescript
// 所有接受用户输入的查询参数都要测试
const injectionPayloads = [
  "' OR '1'='1",
  '1; DROP TABLE users--',
  "' UNION SELECT password FROM users--",
  "admin'--",
];

for (const payload of injectionPayloads) {
  const res = await request(app)
    .get(`/api/users?id=${encodeURIComponent(payload)}`)
    .expect(400); // 不应返回数据或 500
}
```

### XSS 测试

```typescript
const xssPayloads = [
  '<script>alert(1)</script>',
  '<img src=x onerror=alert(1)>',
  'javascript:alert(1)',
  '<svg onload=alert(1)>',
];

// 存储型 XSS：提交后检查响应是否转义
for (const payload of xssPayloads) {
  await request(app).post('/api/comments').send({ content: payload }).expect(201);

  // 读取时应被转义
  const res = await request(app).get('/api/comments').expect(200);
  expect(res.body.items[0].content).not.toContain('<script>');
}
```

### 越权测试

```typescript
// 水平越权：用户 A 访问用户 B 的资源
const userAToken = await login('userA@example.com', 'pass');
const userBId = await createUser('userB@example.com', 'pass');

// 用户 A 尝试读取用户 B 的数据
await request(app)
  .get(`/api/users/${userBId}/private-data`)
  .set('Authorization', `Bearer ${userAToken}`)
  .expect(403);
```

## 性能测试方法论

### 性能指标

| 指标     | 前端目标 | 后端目标 | 测量方式                |
| -------- | -------- | -------- | ----------------------- |
| 首屏加载 | < 3s     | -        | Lighthouse / Web Vitals |
| API P50  | -        | < 100ms  | 压测工具 (k6/Artillery) |
| API P99  | -        | < 500ms  | 压测工具                |
| 并发用户 | -        | ≥ 100    | 压测工具                |
| 内存泄漏 | 无       | 无       | 长时间运行监控          |
| 错误率   | < 1%     | < 1%     | 监控                    |

### 性能测试类型

| 类型         | 目的                 | 工具                  |
| ------------ | -------------------- | --------------------- |
| **负载测试** | 验证预期负载下的性能 | k6, Artillery, JMeter |
| **压力测试** | 找到系统崩溃点       | k6, JMeter            |
| **浸泡测试** | 长时间运行稳定性     | k6 (long duration)    |
| **尖峰测试** | 突发流量处理         | k6 (stages)           |

### k6 示例

```javascript
// tests/performance/api-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 }, // 50 并发
    { duration: '1m', target: 100 }, // 升到 100
    { duration: '30s', target: 0 }, // 降下来
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get(`${__ENV.BASE_URL}/api/users`);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  sleep(1);
}
```

```bash
# 运行性能测试
k6 run -e BASE_URL=http://localhost:3000 tests/performance/api-load.js
```

## 测试环境策略

| 环境        | 用途       | 数据                 | 测试类型          |
| ----------- | ---------- | -------------------- | ----------------- |
| **local**   | 开发自测   | Mock/测试数据        | 单元测试          |
| **dev**     | 集成验证   | 测试数据             | 单元 + 集成       |
| **staging** | 预发布验证 | 生产数据副本（脱敏） | 集成 + E2E + 性能 |
| **prod**    | 生产       | 真实数据             | 监控 + 灰度验证   |

### 环境配置原则

- 测试环境应与生产环境架构一致（数据库类型、缓存、消息队列）
- 敏感数据必须脱敏（用户密码、邮箱、手机号）
- 测试环境的第三方服务使用沙箱账号
- 每个环境有独立的数据库，不共享

## 测试数据策略

### 数据管理原则

| 原则         | 说明                                   |
| ------------ | -------------------------------------- |
| **测试隔离** | 每个测试用例有独立数据，不依赖其他用例 |
| **可重复**   | 相同输入多次运行结果一致               |
| **确定性**   | 不依赖时间、随机数、外部状态           |
| **清理**     | 测试后清理数据，不残留                 |

### 数据准备方式

```typescript
// 方式 1：beforeEach 创建数据（推荐，隔离最好）
beforeEach(async () => {
  await db.user.create({ data: { name: 'test', email: 'test@example.com' } });
});

// 方式 2：全局种子数据（适合大量基础数据）
beforeAll(async () => {
  await seedDatabase(); // 创建角色、权限、基础配置
});

// 方式 3：Fixture 工厂（复杂场景）
import { createUser, createOrder } from './fixtures';
const user = await createUser({ role: 'admin' });
const order = await createOrder({ userId: user.id });
```

### 数据脱敏

测试日志和报告中不得出现真实敏感数据：

```typescript
// 测试中使用合成数据
const testEmail = `test-${Date.now()}@example.com`;
const testPhone = `1380000${String(Math.random()).slice(2, 6)}`;
```

## 检查清单

制定测试策略时，对照确认：
- [ ] 测试金字塔比例合理（70/20/10）
- [ ] E2E 测试已规划，覆盖核心用户路径
- [ ] 变更风险已评估，测试优先级已确定
- [ ] 安全测试用例已规划（认证、授权、输入校验）
- [ ] 性能指标已明确（P50/P99/并发数）
- [ ] 测试环境已就绪，与生产架构一致
- [ ] 测试数据策略已确定（隔离、可重复、脱敏）
- [ ] 每个变更点都有对应的测试类型覆盖
