---
name: frontend-engineering
description: >
  提供 React/Next 优先的前端工程规范，覆盖组件结构、状态分层、语义化、可访问性、
  性能与交付质量。当前端工程师、架构师或 Tech Lead 需要统一工程做法时使用。
---

# Frontend Engineering

## 用途

- 在前端需求开始前统一工程边界，避免实现阶段临时发明组件模式和代码规范。
- 把 React/Next/Tailwind 的默认做法沉淀为可迁移的工程规则，供角色协作复用。

## 默认做法

0. 若项目根目录存在 `DESIGN.md`，**实现前必须读取**，所有 token 值（色值、字号、间距、圆角、阴影）以 DESIGN.md 为基准。代码中不允许出现与 DESIGN.md 不一致的硬编码原始值（如 `color: #5e6ad2`），必须通过 CSS 变量或 Tailwind token 引用。参考：[DESIGN.md 使用工作流](../../docs/runbooks/design-md-workflow.md)

1. 先阅读 [frontend-engineering-standards.md](../../rules/frontend-engineering-standards.md) 锁定技术基线和质量红线。
2. 企业内部应用补看 [enterprise-architecture-governance.md](../../rules/common/enterprise-architecture-governance.md) 与 [enterprise-component-baseline.md](../../rules/common/enterprise-component-baseline.md)，确认是否受统一框架、组件和兼容性约束。
3. 若目标项目明确采用自定义前端样式 profile，再补看 [frontend-enterprise-style-profile.md](../../docs/runbooks/frontend-enterprise-style-profile.md)，确认是否需要附加样式与 Figma 映射约束。
4. 使用 [react-next-baseline.md](references/react-next-baseline.md) 和 [component-patterns.md](references/component-patterns.md) 决定页面、组件、hooks、状态与数据流分层。
5. 若是新界面或大改版，先补齐 [ui-implementation-plan.md](../../templates/ui-implementation-plan.md) 再进入编码。
6. 若启用了公司前端样式 profile，把附加样式约束同步回写到 `ui-implementation-plan.md`、`/team-execute` 和 `/handoff`。
7. 提交给 QA 前，结合 [quality-checklist.md](references/quality-checklist.md) 与 [ui-review-checklist.md](../../templates/ui-review-checklist.md) 留下可追溯证据。

## 何时优先调用

- `frontend-engineer` 需要确定组件结构、状态分层、Next 边界与样式约束。
- `architect` 需要把前端实现约束沉淀进方案，而不是只给页面草图。
- `tech-lead` 需要判断某个 UI 需求是否具备进入执行阶段的工程条件。
