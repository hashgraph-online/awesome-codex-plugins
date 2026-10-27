---

name: qa/test-execution
description: 测试执行方法，包含测试框架检测、覆盖率门禁、多框架结果解析、失败分级、增量测试选择、并行执行策略
version: 2.0.0
agent: qa
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要执行测试时
- 需要验证测试覆盖率时
- 需要解析测试结果时
  metadata:
  internal: true

---

# 测试执行方法

## 强制要求：真实执行测试

**你必须真正执行测试，禁止生成 Mock 数据！**

## 测试执行流程

1. **检测项目类型和测试框架**
2. **执行单元测试**（含覆盖率）
3. **执行集成测试**
4. **执行接口测试**
5. **执行 E2E 测试**
6. **解析测试输出**（总数、通过数、失败数、覆盖率）
7. **失败分级与处理**

## 测试框架检测

### JavaScript/TypeScript

| 框架       | 检测标志                                | 配置文件                            |
| ---------- | --------------------------------------- | ----------------------------------- |
| Jest       | `"jest"` in devDependencies             | `jest.config.js` / `jest.config.ts` |
| Vitest     | `"vitest"` in devDependencies           | `vitest.config.ts`                  |
| Playwright | `"@playwright/test"` in devDependencies | `playwright.config.ts`              |
| Cypress    | `"cypress"` in devDependencies          | `cypress.config.ts`                 |

### Python

| 框架     | 检测标志                   | 配置文件                        |
| -------- | -------------------------- | ------------------------------- |
| pytest   | `"pytest"` in dependencies | `pytest.ini` / `pyproject.toml` |
| unittest | 内置                       | -                               |

### Go

- `*_test.go` 文件存在 → 使用 `go test`
- 集成测试通常用 build tag 隔离：`//go:build integration`

### Java

| 框架    | 检测标志                     |
| ------- | ---------------------------- |
| JUnit 5 | `pom.xml` 含 `junit-jupiter` |
| TestNG  | `pom.xml` 含 `testng`        |

## 测试命令矩阵

| 语言    | 单元测试                      | 集成测试                           | 接口测试                   | E2E 测试              |
| ------- | ----------------------------- | ---------------------------------- | -------------------------- | --------------------- |
| Node.js | `npx vitest run` / `npx jest` | `npx vitest run tests/integration` | `npx vitest run tests/api` | `npx playwright test` |
| Python  | `pytest tests/unit`           | `pytest tests/integration`         | `pytest tests/api`         | `pytest tests/e2e`    |
| Go      | `go test ./internal/...`      | `go test -tags=integration ./...`  | `go test ./tests/api/...`  | -                     |
| Java    | `mvn test`                    | `mvn verify`                       | `mvn verify -Papi-test`    | -                     |

> 接口测试方法论见 `Skill(skill: "qa/api-testing")`，集成测试方法论见 `Skill(skill: "qa/integration-testing")`。

## 覆盖率度量与门禁

### 覆盖率采集

```bash
# Vitest
npx vitest run --coverage --reporter=json
# 输出 coverage/coverage-summary.json

# Jest
npx jest --coverage --coverageReporters=json-summary
# 输出 coverage/coverage-summary.json

# Python (pytest-cov)
pytest --cov=src --cov-report=json
# 输出 coverage.json

# Go
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out
```

### 覆盖率报告解析

`coverage-summary.json` 结构：

```json
{
  "total": {
    "lines": { "total": 100, "covered": 85, "pct": 85 },
    "statements": { "total": 120, "covered": 100, "pct": 83.3 },
    "functions": { "total": 40, "covered": 36, "pct": 90 },
    "branches": { "total": 30, "covered": 22, "pct": 73.3 }
  }
}
```

### 覆盖率门禁

| 指标           | 门槛  | 未达标处理                         |
| -------------- | ----- | ---------------------------------- |
| 行覆盖率       | ≥ 80% | 列出未覆盖行，报 `REVISION_NEEDED` |
| 语句覆盖率     | ≥ 80% | 同上                               |
| 函数覆盖率     | ≥ 80% | 同上                               |
| 分支覆盖率     | ≥ 75% | 列出未覆盖分支                     |
| 变更文件覆盖率 | ≥ 80% | 重点检查本次变更文件               |

**覆盖率检查脚本**（Node.js）：

```bash
# 检查覆盖率是否达标
node -e "
const cov = require('./coverage/coverage-summary.json').total;
const thresholds = { lines: 80, statements: 80, functions: 80, branches: 75 };
let failed = false;
for (const [key, min] of Object.entries(thresholds)) {
  const pct = cov[key].pct;
  if (pct < min) {
    console.log(\`❌ \${key}: \${pct}% < \${min}%\`);
    failed = true;
  } else {
    console.log(\`✅ \${key}: \${pct}%\`);
  }
}
process.exit(failed ? 1 : 0);
"
```

## 测试结果解析

### Jest / Vitest JSON 输出

```bash
npx jest --json --outputFile=test-results.json
# 或
npx vitest run --reporter=json --outputFile=test-results.json
```

解析关键字段：

```json
{
  "numTotalTests": 50,
  "numPassedTests": 48,
  "numFailedTests": 2,
  "numPendingTests": 0,
  "success": false,
  "testResults": [
    {
      "name": "tests/api/users.test.ts",
      "status": "failed",
      "assertionResults": [
        {
          "title": "creates user with valid data",
          "status": "passed",
          "duration": 15
        },
        {
          "title": "rejects empty name with 400",
          "status": "failed",
          "failureMessages": ["Expected 400, received 201"]
        }
      ]
    }
  ]
}
```

### pytest JSON 输出

```bash
pytest tests/ -v --json-report --json-report-file=test-results.json
```

解析：
```json
{
  "summary": {
    "total": 30,
    "passed": 28,
    "failed": 2,
    "skipped": 0,
    "duration": 2.5
  }
}
```

### Go test 输出

```bash
go test ./... -json > test-results.json
```

解析（每行一个 JSON）：
```bash
# 统计通过/失败
go test ./... -v 2>&1 | grep -E "^(=== RUN|--- (PASS|FAIL|SKIP))" | \
  awk '/PASS/{p++} /FAIL/{f++} /SKIP/{s++} END{print "passed:"p" failed:"f" skipped:"s}'
```

### Playwright JSON 输出

| 字段               | 说明               |
| ------------------ | ------------------ |
| `stats.expected`   | 通过的测试数       |
| `stats.unexpected` | 失败的测试数       |
| `stats.flaky`      | 重试后通过的测试数 |
| `stats.skipped`    | 跳过的测试数       |

## 失败分级与处理

### 失败分级

| 级别         | 判定标准                           | 处理方式           |
| ------------ | ---------------------------------- | ------------------ |
| **Blocker**  | 核心功能不可用、数据丢失、安全漏洞 | 立即修复，阻止发布 |
| **Critical** | 主要功能异常、数据不一致           | 必须修复，阻塞发布 |
| **Major**    | 次要功能异常、有 workaround        | 修复后发布         |
| **Minor**    | UI 展示问题、文案错误              | 可带 issue 发布    |

### 失败处理流程

```
测试失败
  │
  ├─ 是环境问题吗？（DB 连接、端口占用、依赖未启动）
  │   └─ 是 → 修复环境，重跑
  │
  ├─ 是测试本身问题吗？（断言错误、测试数据过期、时序问题）
  │   └─ 是 → 修复测试，重跑
  │
  ├─ 是产品代码 bug 吗？
  │   └─ 是 → 报 REVISION_NEEDED，交给开发修复
  │
  └─ 是 flaky 吗？（间歇性失败）
      └─ 是 → 重试 1 次，仍失败则标记 flaky 并排查根因
```

### 禁止行为

- ❌ 禁止为通过测试而修改断言或删除用例
- ❌ 禁止用 `.skip` / `xit` 跳过失败测试
- ❌ 禁止将失败测试标记为"预期失败"而不修复
- ❌ 禁止在报告中隐瞒失败

## 增量测试选择

为了加速反馈，只运行受变更影响的测试：

### 基于变更文件的测试选择

```bash
# 获取变更的源文件
git diff --name-only main...HEAD -- 'src/**/*.ts'

# Vitest: 只运行受影响的测试（需配置 coverage analysis）
npx vitest run --changed

# Jest: 只运行变更相关测试
npx jest --changedSince=main
```

### 测试目录约定

```
tests/
├── unit/           # 单元测试，快速，CI 必跑
├── integration/    # 集成测试，较慢，CI 必跑
├── api/            # 接口测试，CI 必跑
└── e2e/            # E2E 测试，最慢，PR 必跑
```

### 按标签选择性执行

```typescript
// Vitest
import { describe, it } from 'vitest';

describe('@critical 用户认证', () => {
  it('@smoke 登录成功', async () => {
    /* ... */
  });
  it('登录失败', async () => {
    /* ... */
  });
});
```

```bash
# 只跑 critical 标签
npx vitest run -t @critical

# Playwright
npx playwright test --grep @critical
```

## 并行执行策略

### Jest / Vitest 并行

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    // 文件间并行（默认）
    // 文件内串行（避免共享状态冲突）
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: false, // 每个文件一个 fork
      },
    },
  },
});
```

### 集成测试串行执行

集成测试通常操作数据库，需要串行避免冲突：

```bash
# Jest: 串行执行集成测试
npx jest tests/integration --runInBand

# Vitest: 串行
npx vitest run tests/integration --pool=forks --poolOptions.forks.singleFork=true
```

### Go 并行控制

```bash
# 默认并行（CPU 核数）
go test ./...

# 限制并行数
go test -p 2 ./...

# 串行
go test -p 1 ./...
```

### pytest 并行

```bash
# 使用 pytest-xdist 并行
pytest -n auto          # 自动检测 CPU 核数
pytest -n 4             # 4 个 worker
pytest tests/integration -n 0  # 串行
```

## 接口测试执行

接口测试通常使用 Supertest（Node.js）或 requests（Python）直接调用应用，无需启动独立服务器。

```bash
# Node.js (Jest + Supertest)
npx jest tests/api --runInBand

# Python (pytest + requests)
pytest tests/api -v

# 输出覆盖率
npx jest tests/api --coverage
```

## 集成测试执行

集成测试需要数据库等依赖，使用 Testcontainers 或测试数据库：

```bash
# Node.js (需要 Docker 运行 Testcontainers)
npx jest tests/integration --runInBand

# Python
pytest tests/integration -v

# Go
go test ./tests/integration/... -v
```

> 集成测试通常 `--runInBand` 串行执行，避免数据库并发冲突。

## Playwright E2E 执行细节

> **完整方法论**：详见 `Skill(skill: "qa/e2e-playwright")`

### 执行命令

```bash
# 安装浏览器（首次或 CI 环境）
npx playwright install --with-deps

# 运行全部 E2E 测试
npx playwright test

# 仅 critical 标签（门禁加速）
npx playwright test --grep @critical

# 指定浏览器
npx playwright test --project=chromium

# JSON 报告（门禁解析用）
npx playwright test --reporter=json
```

### 失败排查

```bash
# 查看 trace（失败时自动生成）
npx playwright show-trace <trace.zip路径>

# 打开 HTML 报告
npx playwright show-report
```

## 测试执行检查清单

- [ ] 已检测项目使用的测试框架
- [ ] 单元测试已执行并通过
- [ ] 集成测试已执行并通过
- [ ] 接口测试已执行并通过
- [ ] E2E 测试已执行并通过
- [ ] 覆盖率已采集并达标（≥ 80%）
- [ ] 所有失败用例已分类和处理
- [ ] 测试结果有完整记录（命令、退出码、通过/失败数、失败详情）
- [ ] 无 flaky 测试未处理
