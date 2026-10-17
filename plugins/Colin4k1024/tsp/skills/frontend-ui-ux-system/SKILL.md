---
name: frontend-ui-ux-system
description: >
  提供公司级前端 UI/UX 设计知识库，覆盖产品类型、视觉方向、设计 token、布局、
  交互、可访问性、动效与交付检查。当前端任务需要统一设计语言或体验门禁时使用。
---

# Frontend UI/UX System

## 用途

- 把 UI/UX 决策前置到计划和方案阶段，不把视觉和体验变成实现末端的补丁。
- 让 `tech-lead`、`frontend-engineer`、`qa-engineer` 在同一套设计语言下协作。

## 默认做法

0. 检查项目根目录是否存在 `DESIGN.md`：
   - **若存在**：读取 DESIGN.md，将其 Section 02（色盘）、Section 03（排版）、Section 04（组件）的具体值作为后续所有设计决策的基准，不得与之冲突。
   - **若不存在**：在 [design-system-brief.md](../../templates/design-system-brief.md) 第 7 节确认参考品牌，通过 `npx getdesign@latest add <brand>` 或直接填写 [DESIGN.md 模板](../../templates/DESIGN.md) 生成，放置于项目根目录。
   - 参考：[DESIGN.md 使用工作流](../../docs/runbooks/design-md-workflow.md) · [字段映射说明](references/design-md-integration.md)

1. 先阅读 [frontend-ui-ux-standards.md](../../rules/frontend-ui-ux-standards.md) 和 [frontend-quality-gates.md](../../rules/frontend-quality-gates.md) 明确硬性门禁。
2. 用 [product-style-map.md](references/product-style-map.md) 与 [design-tokens.md](references/design-tokens.md) 锁定产品类型、视觉方向和 token 策略。
3. 对新界面或大改版先补齐 [design-system-brief.md](../../templates/design-system-brief.md)，对进入实现的任务补齐 [ui-implementation-plan.md](../../templates/ui-implementation-plan.md)。
4. 在交付评审前使用 [interaction-accessibility.md](references/interaction-accessibility.md)、[delivery-checklist.md](references/delivery-checklist.md) 与 [ui-review-checklist.md](../../templates/ui-review-checklist.md) 做闭环检查。

## 何时优先调用

- `tech-lead` 需要判断某个需求的 UI 范围、设计约束和体验门禁是否已经足够明确。
- `frontend-engineer` 需要在多种视觉方向和交互模式中选定统一方案。
- `qa-engineer` 需要把视觉、交互、无障碍和性能检查标准从“主观观感”变成一致规则。
