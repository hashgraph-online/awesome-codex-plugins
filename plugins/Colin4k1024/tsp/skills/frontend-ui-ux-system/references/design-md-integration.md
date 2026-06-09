# DESIGN.md 字段映射参考

> 本文件说明 DESIGN.md 9 个区块的字段，与 Team Skills Platform 现有 token 体系（Color / Typography / Spacing / Radius / Shadow / Motion）和设计工具的对应关系。
>
> **用途**：帮助 `frontend-engineer` 和 `qa-engineer` 在读取 DESIGN.md 后，准确将值映射到代码 CSS/JS token，确保实现与设计文件一致。

---

## 字段映射总表

### Section 02 → Color Tokens

| DESIGN.md 字段 | harness token 域 | CSS 变量命名约定 | Tailwind / 代码等价 |
|----------------|-----------------|----------------|---------------------|
| Background Surfaces | Color - Background | `--bg-page`, `--bg-surface`, `--bg-elevated`, `--bg-hover` | `bg-white`, `bg-neutral-50` |
| Text & Content | Color - Text | `--text-primary`, `--text-secondary`, `--text-tertiary`, `--text-link` | `text-neutral-900`, `text-neutral-500` |
| Brand & Accent | Color - Brand | `--brand`, `--brand-hover`, `--brand-subtle` | `text-indigo-500`, `bg-indigo-100` |
| Status Colors | Color - State | `--color-success`, `--color-warning`, `--color-error`, `--color-info` | `text-green-600`, `text-red-500` |
| Border & Dividers | Color - Border | `--border-strong`, `--border-subtle`, `--border-focus` | `border-neutral-200` |

**实现要求**：代码中**不允许**直接写 hex 值（如 `color: #5e6ad2`），必须通过 CSS 变量（`var(--brand)`）或 Tailwind token 引用。

---

### Section 03 → Typography Tokens

| DESIGN.md 字段 | harness token 域 | CSS 变量命名约定 | 说明 |
|----------------|-----------------|----------------|------|
| Font Families | Typography - Family | `--font-sans`, `--font-mono` | 在 `:root` 定义，不在组件中硬编码 |
| Display | Typography - Scale | `--text-display` | `font-size + line-height + letter-spacing` 组合 |
| Heading 1–3 | Typography - Scale | `--text-h1`, `--text-h2`, `--text-h3` | 对应 `<h1>`, `<h2>`, `<h3>` 默认样式 |
| Body Large/Medium/Small | Typography - Scale | `--text-body-lg`, `--text-body-md`, `--text-body-sm` | 正文段落 |
| Caption | Typography - Scale | `--text-caption` | 标签、时间戳 |
| Mono Body | Typography - Scale | `--text-mono` | 代码、key 展示 |

---

### Section 05 → Spacing Tokens

| DESIGN.md 字段 | harness token 域 | Tailwind 等价 | 说明 |
|----------------|-----------------|--------------|------|
| Spacing Scale（4px 刻度） | Spacing | `p-1`=4px, `p-2`=8px, `p-3`=12px, `p-4`=16px, `p-6`=24px, `p-8`=32px, `p-12`=48px | Tailwind 4-base spacing 与 DESIGN.md 4px 刻度完全对齐 |
| Grid Column Gap | Spacing - Layout | `gap-4`, `gap-5`, `gap-6` | 按断点取值 |
| Section Spacing | Spacing - Section | `mb-10`（40px）, `mb-16`（64px） | 组间距 |

---

### Section 04 → Component Tokens (Radius + Shadow)

| DESIGN.md 字段 | harness token 域 | CSS 变量命名约定 | 说明 |
|----------------|-----------------|----------------|------|
| Button 圆角 `6px` | Radius - Component | `--radius-btn` | 按钮圆角 |
| Card 圆角 `8px` | Radius - Component | `--radius-card` | 卡片容器 |
| Input 圆角 `6px` | Radius - Component | `--radius-input` | 表单控件 |
| Badge 圆角 `9999px` | Radius - Component | `--radius-pill` | Pill 标签 |

---

### Section 06 → Shadow Tokens

| Level | CSS Shadow | CSS 变量 | 对应 Tailwind |
|-------|-----------|---------|--------------|
| Level 0 | `none` | `--shadow-0` | `shadow-none` |
| Level 1 | `0 1px 2px rgba(0,0,0,0.05)` | `--shadow-1` | `shadow-sm` |
| Level 2 | `0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)` | `--shadow-2` | `shadow` |
| Level 3 | `0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)` | `--shadow-3` | `shadow-md` |
| Level 4 | `0 10px 30px rgba(0,0,0,0.12), 0 4px 10px rgba(0,0,0,0.06)` | `--shadow-4` | `shadow-lg` |
| Focus Ring | `0 0 0 3px rgba(94,106,210,0.25)` | `--shadow-focus` | 无对应，需手写 |

---

### Motion（Section 08 的动效暗示）

> DESIGN.md 格式未设独立 Motion 区块，但 Section 08（响应行为）通常包含过渡时间参考值。

| 场景 | 推荐值 | CSS 变量 |
|------|--------|---------|
| 微交互（hover、focus） | `150ms ease-out` | `--motion-fast` |
| 展开/折叠、导航切换 | `250ms ease-in-out` | `--motion-normal` |
| 页面过渡 | `300ms ease` | `--motion-slow` |
| prefers-reduced-motion | 禁用或缩减至 `instant` | 用 `@media (prefers-reduced-motion: reduce)` 覆盖 |

---

## DESIGN.md 9 区块用途速查

| 区块 | 主要消费者 | 实现时机 |
|------|-----------|---------|
| 01 Visual Theme | agent 生成前阅读，定下基调 | 任何 UI 实现前 |
| 02 Color Palette | CSS 变量/token 定义 | 项目初始化，建立 `tokens.css` |
| 03 Typography | 全局字体/排版样式 | 项目初始化，设置 `typography.css` 或 Tailwind `fontFamily` |
| 04 Component Styles | 各组件 default/hover/focus/error/disabled 实现 | 每个组件编写时 |
| 05 Layout | 栅格、间距、Tailwind `spacing` 配置 | 项目初始化，布局组件 |
| 06 Depth | `box-shadow` 工具类/变量 | 项目初始化 |
| 07 Do's & Don'ts | 代码 review 参考，agent 生成时的护栏 | review 阶段对照 |
| 08 Responsive | 断点定义、组件折叠规则 | 每个组件的响应式处理 |
| 09 Agent Prompt Guide | 快速生成 prompt，减少 agent 猜色 | 每次 AI 代码生成前粘贴相关片段 |

---

## 与 design-system-brief.md 第 3 节 Token 策略的对应关系

`design-system-brief.md` 第 3 节用**表格**记录 6 个 token 域的策略，DESIGN.md 提供这些策略的**具体执行值**：

| brief 第 3 节 token 域 | DESIGN.md 对应区块 |
|-----------------------|------------------|
| Color | Section 02 |
| Typography | Section 03 |
| Spacing | Section 05 |
| Radius | Section 04（组件圆角） |
| Shadow | Section 06 |
| Motion | Section 08（隐含）|

**工作流**：先在 `design-system-brief` 确定策略方向 → 再在 DESIGN.md 落定具体值 → 最后在 `ui-implementation-plan` 规划组件实现次序。

---

## 参考资料

- [templates/DESIGN.md](../../../templates/DESIGN.md) — 9 区块主模板
- [docs/runbooks/design-md-workflow.md](../../../docs/runbooks/design-md-workflow.md) — 创建与维护工作流
- [references/design-tokens.md](design-tokens.md) — 现有 token 体系定义
- [rules/frontend-ui-ux-standards.md](../../../rules/frontend-ui-ux-standards.md) — 前端 UI/UX 规范
