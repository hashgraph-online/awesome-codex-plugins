---
name: qa/test-execution
description: 测试执行方法，包含测试框架检测、测试运行、结果解析
version: 1.0.0
agent: qa
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
  - shared/tech-stack-detection
triggers:
  - 需要执行测试时
  - 需要验证测试覆盖率时
---

# 测试执行方法

## 强制要求：真实执行测试

**你必须真正执行测试，禁止生成 Mock 数据！**

## 测试执行流程

1. **检测项目类型和测试框架**
2. **根据项目类型执行测试**
3. **执行 E2E / 集成测试**
4. **解析测试输出**（总数、通过数、失败数、覆盖率）

## 测试框架检测

### JavaScript/TypeScript
- Jest: `jest.config.js`, `"jest"` in package.json
- Vitest: `vitest.config.js`, `"vitest"` in package.json
- Playwright: `playwright.config.js`
- Cypress: `cypress.json`

### Python
- pytest: `pytest.ini`, `"pytest"` in dependencies
- unittest: 内置

### Go
- `*_test.go` 文件

## 测试命令

| 语言 | 单元测试 | E2E测试 |
|------|----------|---------|
| Node.js | `npm test` | `npx playwright test` |
| Python | `pytest` | `pytest tests/e2e` |
| Go | `go test ./...` | - |

## Playwright E2E 执行细节

> **完整方法论**：详见 `Skill(skill: "qa/e2e-playwright")`

### 检测 Playwright 项目

检查以下标志确认项目使用 Playwright：
- `playwright.config.ts` 或 `playwright.config.js` 存在
- `package.json` 中包含 `@playwright/test` 依赖
- `e2e/` 或 `tests/e2e/` 目录存在

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

### 结果解析

Playwright JSON 报告关键字段：

| 字段 | 说明 |
|------|------|
| `stats.expected` | 通过的测试数 |
| `stats.unexpected` | 失败的测试数 |
| `stats.flaky` | 重试后通过的测试数 |
| `stats.skipped` | 跳过的测试数 |

### 失败排查

```bash
# 查看 trace（失败时自动生成）
npx playwright show-trace <trace.zip路径>

# 打开 HTML 报告
npx playwright show-report
```
