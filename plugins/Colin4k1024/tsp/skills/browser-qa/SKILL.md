---
name: browser-qa
description: >
  自动化视觉测试与 UI 交互验证。部署功能后使用浏览器自动化验证关键页面、核心路径和发布前回归。
  当任务需要真实浏览器验证渲染、导航、交互或前端上线风险时使用。
origin: ECC
---

# Browser QA — 自动化视觉测试与交互验证

## When to Use / 用途

- After deploying a feature to staging/preview
- When you need to verify UI behavior across pages
- Before shipping — confirm layouts, forms, interactions actually work
- When reviewing PRs that touch frontend code
- Accessibility audits and responsive testing
- 把"前端已经改完"变成"关键页面和核心路径在浏览器里确实可用"
- 适合页面、交互、静态资源发布、关键用户路径和上线前回归确认场景

## Trigger Signals / 触发信号

- 需求包含页面、组件、路由、表单、导航、权限跳转或静态资源变更
- `/team-release` 需要关键页面 smoke 范围和发布后验证证据
- 代码层测试通过了，但仍需确认真实浏览器中的渲染、交互、缓存或网络行为
- QA 或实现角色需要快速确认"关键路径能跑通"而不是一次性补完整 E2E 套件

## How It Works

Uses the browser automation MCP (claude-in-chrome, Playwright, or Puppeteer) to interact with live pages like a real user.

### Default Approach / 默认做法

1. 先锁定 smoke 范围：目标环境、入口 URL、关键页面、核心用户路径、预期可见结果和不在本轮覆盖的内容
2. 明确运行方式：优先复用当前环境可用的真实浏览器能力，例如 Playwright CLI、agent-browser 或项目已有 E2E harness；不要为了 ad-hoc smoke 临时搭一整套新测试框架
3. 对动态页面，先等页面完成首屏渲染、关键请求返回或交互状态稳定，再判断是否通过；不要在骨架屏、占位态或旧缓存状态下过早下结论
4. 优先验证高风险路径：页面可打开、核心导航可达、主操作可完成、关键异常态可触发、静态资源无明显 404/缓存错配
5. 用截图、控制台错误、失败步骤和环境说明留下证据，并把结论回交 `/team-review`、`/team-release` 或角色 handoff

### Phase 1: Smoke Test
```
1. Navigate to target URL
2. Check for console errors (filter noise: analytics, third-party)
3. Verify no 4xx/5xx in network requests
4. Screenshot above-the-fold on desktop + mobile viewport
5. Check Core Web Vitals: LCP < 2.5s, CLS < 0.1, INP < 200ms
```

### Phase 2: Interaction Test
```
1. Click every nav link — verify no dead links
2. Submit forms with valid data — verify success state
3. Submit forms with invalid data — verify error state
4. Test auth flow: login → protected page → logout
5. Test critical user journeys (checkout, onboarding, search)
```

### Phase 3: Visual Regression
```
1. Screenshot key pages at 3 breakpoints (375px, 768px, 1440px)
2. Compare against baseline screenshots (if stored)
3. Flag layout shifts > 5px, missing elements, overflow
4. Check dark mode if applicable
```

### Phase 4: Accessibility
```
1. Run axe-core or equivalent on each page
2. Flag WCAG AA violations (contrast, labels, focus order)
3. Verify keyboard navigation works end-to-end
4. Check screen reader landmarks
```

## Output Format

```markdown
## QA Report — [URL] — [timestamp]

### Smoke Test
- Console errors: 0 critical, 2 warnings (analytics noise)
- Network: all 200/304, no failures
- Core Web Vitals: LCP 1.2s ✓, CLS 0.02 ✓, INP 89ms ✓

### Interactions
- [✓] Nav links: 12/12 working
- [✗] Contact form: missing error state for invalid email
- [✓] Auth flow: login/logout working

### Visual
- [✗] Hero section overflows on 375px viewport
- [✓] Dark mode: all pages consistent

### Accessibility
- 2 AA violations: missing alt text on hero image, low contrast on footer links

### Verdict: SHIP WITH FIXES (2 issues, 0 blockers)
```

## Integration

Works with any browser MCP:
- `mChild__claude-in-chrome__*` tools (preferred — uses your actual Chrome)
- Playwright via `mcp__browserbase__*`
- Direct Puppeteer scripts

Pair with `/canary-watch` for post-deploy monitoring.

## TSP Integration / TSP 集成

- 先遵循 [frontend-quality-gates](../../../rules/frontend-quality-gates.md) 中的 smoke 范围、回滚触发条件和前端证据要求
- 需要补齐页面范围、产品类型和 UI 约束时，先看 [frontend-governance](../../../docs/runbooks/frontend-governance.md)
- 若 smoke 目的是发布验证或回滚判断，直接连同 `/team-release`、[release-plan.md](../../../templates/release-plan.md) 和相关发布治理 runbook 一起使用
- 需要系统化留痕、失败归因或多轮确认时，分别接 [systematic-debugging](../systematic-debugging/SKILL.md) 和 `/verify`
- 如果被环境、登录、测试数据或后端依赖阻塞，明确记录 blocker 和前置条件，不把"环境没起来"误写成产品缺陷
