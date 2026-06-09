---
name: open-design
description: >
  Use Open Design as an external local-first design workbench for prototypes,
  decks, mobile screens, dashboards, DESIGN.md systems, and exportable visual
  artifacts. Keep TSP responsible for team workflow, handoff, and quality gates.
origin: nexu-io/open-design (reference-only controlled integration)
---

# Open Design

## 用途

- 用 Open Design 生成或迭代高保真视觉 artifacts：web prototype、dashboard、mobile flow、deck、poster、social carousel、runbook/spec 类页面。
- 在前端任务中把 `DESIGN.md`、设计方向、skill、preview 和 export 结果作为证据回落到 TSP 主链。
- 让 `product-manager`、`frontend-engineer`、`qa-engineer` 在同一套可预览 artifact 上讨论，而不是只靠文字描述。

## 触发信号

- 用户要“像 Claude Design 那样”快速生成可编辑原型、deck、营销页、移动界面或设计系统。
- 需求还没有稳定视觉方向，需要先通过表单、方向 picker 或 `DESIGN.md` 锁定风格。
- `/team-plan` 或 `/team-execute` 进入 UI 实施前，需要可截图、可导出、可评审的设计证据。
- `/team-review` 需要对 artifact 做视觉、响应式、可访问性、反 AI 味、导出完整性检查。

## 默认工作流

1. 先完成 TSP 侧任务收敛：
   - 目标、受众、页面/屏幕范围、数据真实性、品牌约束、响应式范围、A11y/性能门禁。
   - 若任务来自 `/team-*`，把这些约束写入 artifact 或 handoff，不只留在聊天里。
2. 检查目标项目是否已有 `DESIGN.md`：
   - 有：把它作为 Open Design 的 active design system 或直接放入 OD 项目工作目录。
   - 无：先用 `frontend-ui-ux-system` 或 OD 的 design-system 能力生成候选 `DESIGN.md`。
3. 若用户安装的是 TSP `full` profile，Open Design 默认会由 TSP 安装器准备到 `~/.tsp/open-design`；否则在独立 Open Design checkout 中运行上游工具，不在 TSP 仓库里启动 OD daemon：
   ```bash
   # full profile 自动路径
   cd ~/.tsp/open-design

   # 手动路径
   git clone https://github.com/nexu-io/open-design.git
   cd open-design
   corepack enable
   pnpm install
   pnpm tools-dev
   ```
4. 在 OD 中选择合适 surface：
   - prototype：`web-prototype`、`saas-landing`、`dashboard`、`mobile-app` 等。
   - deck：`guizang-ppt`、`simple-deck`、`weekly-update` 等。
   - document-like：`pm-spec`、`eng-runbook`、`finance-report`、`team-okrs` 等。
5. 生成后把关键产物回落到 TSP：
   - artifact 路径或导出文件
   - 使用的 OD skill、design system、visual direction
   - 约束与自检结论
   - 对 `/team-plan`、`/team-execute`、`/team-review` 或 `/team-release` 的决策影响
6. 若 artifact 会进入实现，frontend 角色必须继续执行 TSP 前端门禁：
   - 响应式、键盘访问、对比度、性能、加载/空态/错误态
   - 真实数据与授权素材检查
   - 不能把 OD 输出直接视为生产代码完成

## 输出约定

- TSP 侧只沉淀集成证据，不复制 Open Design 源码或生成数据库。
- 推荐在消费方项目中落盘：
  - `docs/artifacts/<date>-open-design-brief.md`
  - `docs/artifacts/<date>-open-design-review.md`
  - 需要长期复用时，将最终 `DESIGN.md` 放在项目根目录或设计文档目录。
- 最小交付字段：
  - 任务目标
  - 使用的 OD skill / design system / visual direction
  - 产物路径或导出格式
  - 主要设计决策及证据
  - 风险、未验证项、下一步 TSP 命令

## 边界与禁用项

- 只有 TSP `full` profile 会自动 clone/update Open Design；其他 profile 只安装 TSP 侧 skill/runbook。
- 不把 Open Design 当作 TSP 的默认 npm 依赖；它要求独立 Node/pnpm/daemon 生命周期。
- 不在本仓库 vendoring Open Design 的 `skills/`、`design-systems/`、daemon、web app 或 SQLite 数据。
- 不把 OD 的视觉结果绕过 `/team-review` 直接发布。
- 不使用未授权品牌素材、字体、截图或第三方图片作为可分发 artifact。
- 不在 TSP 管理仓库中运行会改写本仓库 hooks、AGENTS 或 MCP 契约的外部 setup 命令。

## 推荐组合

- 需求到原型：`/team-intake -> frontend-ui-ux-system -> open-design -> /team-plan`
- UI 实施：`/team-execute -> open-design artifact evidence -> frontend-engineering -> /handoff`
- 视觉评审：`/team-review -> open-design artifact review -> browser-smoke-testing`
- Deck / 汇报材料：`frontend-slides -> open-design deck mode -> /team-release`
