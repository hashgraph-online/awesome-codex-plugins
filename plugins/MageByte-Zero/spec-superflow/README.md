<h1 align="center">spec-superflow</h1>

<p align="center">
  <strong>源码级融合 OpenSpec 规划引擎 + Superpowers 执行纪律的 AI 编程工作流插件</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License"></a>
  <a href="https://github.com/MageByte-Zero/spec-superflow/stargazers"><img src="https://img.shields.io/github/stars/MageByte-Zero/spec-superflow" alt="GitHub Stars"></a>
  <a href="https://www.npmjs.com/package/spec-superflow"><img src="https://img.shields.io/npm/v/spec-superflow" alt="npm version"></a>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> |
  <a href="#安装">安装</a> |
  <a href="#为什么需要它">为什么</a> |
  <a href="#核心-skills">Skills</a> |
  <a href="#工作流">工作流</a> |
  <a href="docs/README_en.md">English</a> |
  <a href="docs/showcase.html">Showcase</a> |
  <a href="#常见问题">FAQ</a>
</p>

---

## 快速开始

安装后，告诉 Agent 一句话即可启动：

```
用 workflow-start 开始
```

Agent 会自动检查当前工件目录，**内容级判断**（不看文件时间戳，而是比较 proposal 范围 vs 契约意图锁）你处于哪个阶段，然后路由到正确的下一个 skill。

- 启动新的变更 → `用 workflow-start 开始`
- 恢复旧的变更 → `继续上次的工作流`
- 不确定当前状态 → `帮我看看现在该干什么`

## 安装

### Claude Code（Marketplace）

Claude Code 的主流方式是插件 marketplace：

```bash
/plugin marketplace add MageByte-Zero/spec-superflow
/plugin install spec-superflow@spec-superflow
/plugin update spec-superflow@spec-superflow
```

Marketplace 安装自动加载 hooks，每次新会话自动注入上下文。

### Cursor（Skills 目录 / GitHub 导入）

```bash
# 方式一：通过 ssf CLI
npx spec-superflow@latest install-cursor

# 方式二：直接运行脚本
curl -fsSL https://raw.githubusercontent.com/MageByte-Zero/spec-superflow/main/scripts/install-cursor.mjs | node -
```

> Cursor 原生发现 `.cursor/skills/`、`.agents/skills/`、`~/.cursor/skills/` 等目录，也可以在 Customize → Rules → Remote Rule (Github) 导入。脚本会自动部署 skills、scripts、docs 等运行时依赖。

### OpenAI Codex CLI / App

Codex 的主流方式是 Plugin Directory / marketplace。本仓库已提供 `.codex-plugin/plugin.json` 和 `.agents/plugins/marketplace.json`。

```bash
# 在 Codex CLI 中打开插件目录
codex
/plugins

# 或添加社区 marketplace 后安装
codex plugin marketplace add hashgraph-online/awesome-codex-plugins
codex plugin add spec-superflow@awesome-codex-plugins

# 直接从指定 release tag 安装（不等待社区镜像同步）
codex plugin marketplace add MageByte-Zero/spec-superflow --ref v0.9.0
codex plugin add spec-superflow@spec-superflow

# 升级并验证社区 marketplace 安装
codex plugin marketplace upgrade awesome-codex-plugins
codex plugin add spec-superflow@awesome-codex-plugins
codex plugin list | rg spec-superflow
```

Codex App 打开 **Plugins** 面板，安装或启用 `spec-superflow`。通过 CLI 安装或升级后，重启 Codex App 并新开会话；旧会话不会热加载 skills。

### GitHub Copilot CLI

```bash
copilot plugin marketplace add MageByte-Zero/spec-superflow
copilot plugin install spec-superflow@spec-superflow
```

### Gemini CLI

```bash
gemini extensions install https://github.com/MageByte-Zero/spec-superflow
gemini extensions update spec-superflow   # 升级
```

### 更多平台（Cline / Kiro / Windsurf / Qwen / Amazon Q / Roo Code / Continue / Pi / Qoder / OpenCode / WorkBuddy / Trae）

| 平台 | 安装方式 | 状态 |
|------|---------|------|
| **Cline** | `npx spec-superflow@latest install-cline` | 已提供安装器 |
| **Kiro** | `npx spec-superflow@latest install-kiro` | 已提供安装器 |
| **Windsurf** | `npx spec-superflow@latest install-windsurf` | 已提供安装器 |
| **Qwen Code** | `npx spec-superflow@latest install-qwen` | 已提供安装器 |
| **Amazon Q Developer** | `npx spec-superflow@latest install-amazon-q` | 已提供安装器 |
| **Roo Code** | `npx spec-superflow@latest install-roocode` | 已提供安装器 |
| **Continue** | `npx spec-superflow@latest install-continue` | 已提供安装器 |
| **Pi** | `npx spec-superflow@latest install-pi` | 已提供安装器 |
| **Qoder** | `npx spec-superflow@latest install-qoder` | 已提供安装器 |
| **OpenCode** | `.opencode/plugins/spec-superflow.js` 或 `.agents/skills -> skills/` | 已提供入口 |
| **WorkBuddy** | `npx spec-superflow@latest install-workbuddy` | 已提供安装器 |
| **Trae IDE / TRAE Work** | `.trae/skills/`、`~/.trae/skills/` 或上传 zip/.skill | 手动/导入 |

> 共支持 18 个平台，完整安装说明见 [INSTALL.md](INSTALL.md)，支持矩阵见 [docs/platform-matrix.md](docs/platform-matrix.md)。

### CLI 工具链

```bash
npm install -g spec-superflow    # 全局安装
npx spec-superflow list          # 或通过 npx 使用
```

| 命令 | 功能 |
|------|------|
| `ssf list` | 列出所有 changes 及状态 |
| `ssf validate <dir>` | 验证工件完整性 |
| `ssf doctor` | 健康检查（版本、hooks、skills、文档一致性） |
| `ssf version <semver>` | 一键同步版本号到所有 manifest |
| `ssf state <sub> <dir>` | 管理 `.spec-superflow.yaml` 状态文件 |
| `ssf inject <dir>` | 生成 phase-guard 产物；仅在检测到单一平台标记时可省略 `--platforms` |
| `ssf audit <dir>` | 生成决策点审计报告 |
| `ssf checkpoint save <dir> --task <id> --next <text>` | 保存任务级会话恢复点 |
| `ssf checkpoint list <dir>` | 列出 checkpoint 及 stale 状态 |
| `ssf checkpoint show <dir> <id>` | 查看单个恢复点 |
| `ssf resume [change]` | 只读恢复摘要；唯一活跃 change 可自动选择 |
| `ssf switch <change>` | 只读返回明确 change 的恢复上下文；adapter 可据此切换当前 AI 对话关注对象 |
| `ssf save <change> --task <id> --next <text>` | 手动写入兼容 checkpoint；不自动 commit、push 或 sync |
| `ssf handoff create <dir> --type <type> ...` | 创建 prototype/research/experiment handoff |
| `ssf handoff list <dir>` | 列出 handoff 生命周期状态 |
| `ssf handoff finish <dir> <id>` | 校验 handoff 结果 |
| `ssf handoff resolve <dir> <id> --decision <decision>` | 记录显式 handoff 决策 |
| `ssf execution recommend <dir> ...` | 基于任务量、wave 和工作流列出可用执行方式并给出推荐 |
| `ssf execution plan <dir> ...` | 在用户确认选择后，为 full/hotfix 保存受 guard 保护的执行计划 |
| `ssf execution show <dir> [--json]` | 查看并校验当前执行计划、wave 与 receipt |
| `ssf execution revise <dir> ...` | 将已有计划保留/升级为 SDD，并生成新 revision；不允许降级 |
| `ssf execution review <dir> ...` | 为一个计划 wave 记录 review receipt |
| `ssf install-cursor` | 部署到 Cursor `.cursor/` 目录 |
| `ssf install-workbuddy` | 部署到 WorkBuddy marketplace 插件（含 skills/rules/runtime） |
| `ssf install-cline` | 部署到 Cline `.cline/` + `.clinerules/` |
| `ssf install-kiro` | 部署到 Kiro `.kiro/` + `.kiro/steering/` |
| `ssf install-windsurf` | 部署到 Windsurf `.windsurf/` + `.windsurf/rules/` |
| `ssf install-qwen` | 部署到 Qwen Code `.qwen/` + `.qwen/rules/` |
| `ssf install-amazon-q` | 部署到 Amazon Q `.amazonq/` + `.amazonq/rules/` |
| `ssf install-roocode` | 部署到 Roo Code `.roo/` + `.roo/rules/` |
| `ssf install-continue` | 部署到 Continue `.continue/` + `.continue/rules/` |
| `ssf install-pi` | 部署到 Pi `.pi/skills/`（无规则目录） |
| `ssf install-qoder` | 部署到 Qoder `.qoder/` + `.qoder/rules/` |

### 版本

- 当前版本：`v0.10.0`
- v0.9.1 highlights：DP-4 执行模式推荐、跨 17 个平台的 portable runtime，以及无插件根路径的 raw-package smoke；详见 [CHANGELOG.md](CHANGELOG.md)
- v0.9.0 highlights：支持 Node 20/22、model profiles 只读解析，以及 code-reviewer 的最小性审查
- 自包含插件，不需要运行时安装 OpenSpec 或 Superpowers
- 上游来源：[Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) 和 [obra/superpowers](https://github.com/obra/superpowers)
- 版本历史见 [CHANGELOG.md](CHANGELOG.md)

`ssf inject` 示例：

```bash
ssf inject changes/my-change --platforms cursor
ssf inject changes/my-change --platforms all
```

省略 `--platforms` 时，只有在项目中**恰好检测到一个**平台标记时才会自动写入；如果检测到多个平台，必须显式指定 `--platforms <platform>` 或 `--platforms all`。

会话恢复与可选 prototype：

```bash
ssf resume                         # 只在唯一活跃 change 时自动选择
ssf resume changes/my-change       # 只读恢复指定 change 的摘要
ssf switch changes/another-change  # 只读返回明确 change 的恢复上下文
ssf save changes/my-change --task 1.1 --next "Run focused tests"
ssf checkpoint save changes/my-change --task 1.1 --next "Run focused tests"
ssf checkpoint list changes/my-change
ssf handoff create changes/my-change --type research --objective "Compare approaches" --expected-output "Recommendation" --acceptance "Evidence recorded"
```

`resume` 与 `switch` 都是只读恢复操作；`resume` 只会在恰好一个活跃 change 时自动选择目标。`switch` 只返回明确目标的恢复上下文，不修改 cwd、TUI 会话或任何隐藏指针；CLI 本身不切换当前对话关注对象，CodeBuddy/WorkBuddy adapter 或宿主 Agent 可用该上下文完成该动作。`save` 仅手动写入既有 checkpoint 协议，绝不自动 commit、push 或 sync。`/ssf:resume`、`/ssf:switch`、`/ssf:save` 是 CodeBuddy/WorkBuddy 使用的 Markdown command adapter：它们分发到同一 CLI guard，不为其他平台承诺完全相同的 slash 名称。

Prototype 只在用户明确确认后创建；后端、CLI、配置和内部重构不会自动进入 prototype 流程。handoff 结果不会自动修改 `design.md` 或 `tasks.md`。

Delta spec 的规范路径是 `specs/<capability>/spec.md`；扁平的 `specs/<capability>.md` 和根级 `specs/spec.md` 不会被视为合法规范。

### 受 guard 保护的执行计划

对 full/hotfix，DP-4 不是一段任意文本：开始实现前必须保存并校验 current
execution plan。它位于 `<change>/.superpowers/sdd/execution-plan.json`，不写入
`execution-contract.md`。先运行 `ssf execution recommend`，它会根据任务量和 wave
策略列出 `inline`、`batch-inline`、`sdd`，并给出可审计的推荐理由，同时把当前 wave 的
推荐凭据保存为 `<change>/.superpowers/sdd/execution-recommendation.json`；Agent 必须将这些
候选项和推荐展示给用户。`plan` 或 `revise` 只接受匹配当前 artifact、contract 和 wave 的
凭据。用户用 `--confirm` 明确确认选择；若选择与推荐不同，必须额外
传入 `--acknowledge-recommendation` 记录已知风险。Batch Inline 始终串行，绝不冒充并行。
`tweak` 保持轻量例外，不要求 execution plan 或 wave receipt。

```bash
ssf execution recommend changes/my-change \
  --wave foundation:parallel:1.1,1.2 \
  --wave integration:serial:2.1:foundation --json
ssf execution plan changes/my-change --mode sdd --confirm --reason "independent work" \
  --wave foundation:parallel:1.1,1.2 \
  --wave integration:serial:2.1:foundation
ssf execution show changes/my-change --json
# 将已有 inline/batch-inline 计划升级为 sdd，或重规划已有 sdd 计划；不能降级。
# 每次修订都会生成新 revision 并清除旧 review receipt。
ssf execution recommend changes/my-change \
  --wave foundation:parallel:1.1,1.2 \
  --wave integration:serial:2.1:foundation --json
ssf execution revise changes/my-change --mode sdd --confirm --reason "need parallel work" \
  --wave foundation:parallel:1.1,1.2 \
  --wave integration:serial:2.1:foundation
# 每个 wave 都先写入非空 review report，再记录 receipt。
ssf execution review changes/my-change --wave foundation --base <sha> --head <sha> \
  --report .superpowers/sdd/reviews/foundation.md --verdict pass
```

`--report` 相对于 `<change>` 解析，且必须位于
`<change>/.superpowers/sdd/reviews/` 之下。`--base` 和 `--head` 必须是该
`<change>` Git 工作树中的真实 commit，且 `base` 必须是 `head` 的祖先。
`<change>/.superpowers/sdd/reviews/` 的目录层级必须是物理、非符号链接目录；
report 本身必须为普通、非空、非符号链接文件。

每个 wave 的 review receipt 必须是当前 revision 的 `pass`，依赖 wave 和 closing
才会放行；修订计划会使旧 receipt 失效。恢复、切换和手动保存是 control-plane
overlay，不会增加第九个状态；其 CLI 与 CodeBuddy/WorkBuddy Markdown adapter 保持相同 guard。

---

## 为什么需要它

用 AI 写代码时，最常碰到两个失控点：

- **还没想清楚要做什么，AI 就开始写代码。** 你说了句"帮我加个权限控制"，它就开始改几十个文件。改到一半才发现 —— 到底要 RBAC 还是 ABAC？

- **规划文档写得明明白白，但执行阶段还是会跑偏。** proposal 写了、design 画了，但实现过程中没人盯着测试、没人卡 review，等到合并才发现行为不对。

**spec-superflow 在这两个失控点之间建起一道硬墙：** 需求澄清 → 工件沉淀（Schema 引擎验证格式）→ 执行契约桥接 → TDD + SDD + Review Gate 三重纪律强制执行 → 验证收口 → delta spec 同步防止规范腐烂。

| 设计原则 | 说明 |
|---|---|
| Spec First | 没有稳定的规划工件，不允许进入实现 |
| Guarded Handoff | `execution-contract.md` 是规划到实现的唯一交接层 |
| Strong Guardrails | 实现中违反契约的行为被明确拦截并回退 |
| Schema Validated | 规划期工件经过 Schema 引擎验证 |
| Execute Disciplined | TDD 铁律 + SDD 子代理驱动 + Review Gate |
| Self-Contained | 不需要安装 OpenSpec 或 Superpowers，一个插件全包 |

### 适用场景

**✅ 推荐：** 大型功能开发、多人协作项目、长期维护项目、需要 TDD + Review Gate 的棕地项目。

**❌ 不推荐：** 一次性脚本/工具、纯咨询/问答。

> **v0.6.0 起自动模式检测**：hotfix（≤2 文件，最小契约 + DP-3 后执行）和 tweak（≤4 文件，纯配置/文档，直接编辑）让小型变更也能高效使用。

---

## 核心 Skills

| # | Skill | 阶段 | 职责 |
|---|---|---|---|
| 1 | `workflow-start` | 入口 | 内容级状态检测、8 状态路由、阻止非法跳转 |
| 2 | `need-explorer` | 探索 | 一次一问 + 方案对比 + 推荐 |
| 3 | `spec-writer` | 规格 | 产出 proposal/specs/design/tasks，Schema 引擎实时验证 |
| 4 | `contract-builder` | 桥接 | 解析引擎自动提取 4 工件 → 压缩为 execution-contract.md |
| 5 | `build-executor` | 执行 | TDD 铁律 + SDD 子代理驱动 + Review Gate |
| 6 | `bug-investigator` | 调试 | 4 阶段根因分析，3+ 修复失败 → 质疑架构 |
| 7 | `code-reviewer` | 审查 | 结构化审查，三级问题分级 |
| 8 | `release-archivist` | 执行内收尾 | 验证前完成铁律 + 归档 + 风险总结 |
| 9 | `spec-merger` | 执行内收尾 | Delta Spec → 主规范智能合并 |

---

## 工作流

```text
你说"帮我加一个权限控制"
       │
       ▼
   workflow-start     ← 唯一入口。内容级状态检测、路由到正确 skill
       │
       ▼
   exploring          need-explorer："你要 RBAC 还是 ABAC？多大粒度？"
       ▼
   specifying         spec-writer 产出 4 份工件 + Schema 引擎验证
       ▼
   bridging           contract-builder 自动提取 → execution-contract.md
       │
  ◇ 用户批准 ◇         ← 唯一一次人工介入
       │
       ▼
   executing          build-executor: TDD → SDD → Review Gate
       │
       ├──[bug]──→ debugging  → bug-investigator
       │
       ▼
   pre-closing（仍属于 executing 的收尾步骤，不是新增状态）
       │ release-archivist 验证 → spec-merger 同步 → 归档确认
       ▼
   closing            CLOSED 成功终态（无 next skill）
```

**关键约束：** 没有 `execution-contract.md` 或未被批准 → 不允许实现；full/hotfix 没有 current execution plan、或任一 wave 缺少 `pass` review receipt → 不允许推进；需求变更 → 强制回退；遇到 bug → 强制走 debugging，不允许"随便试试"。

### 快速路径（hotfix / tweak）

- **hotfix** — ≤2 文件、无新模块时，走 `exploring -> bridging -> approved-for-build -> executing`。可跳过 `proposal.md`、`design.md`、`tasks.md`、`specs/` 等完整规划工件，但仍必须先生成一份新的最小 `execution-contract.md`，并完成 DP-3 批准后才能进入实现
- **tweak** — ≤4 文件、纯配置/文档修改时，跳过规划+桥接，直接编辑

---

## 模型 Profile（可选配置）

可以在项目根目录的 `spec-superflow.config.json` 中，为不同执行角色配置平台模型 ID：

```json
{
  "models": {
    "mechanical": "vendor-small",
    "standard": "vendor-standard",
    "strong": "vendor-strong",
    "review": "vendor-review"
  }
}
```

| Profile | 角色 |
|---|---|
| `mechanical` | 低成本、机械性修改 |
| `standard` | 集成与判断任务 |
| `strong` | 架构、设计与最终审查 |
| `review` | 与 diff 匹配的代码审查 |

使用以下命令只读解析一个 profile：

```bash
ssf config --resolve-model mechanical
```

该命令只解析本地配置，不调用平台 API，也不切换当前会话模型。支持 `model` 字段的平台由控制器显式传入返回的模型 ID；若结果为 `configured: false`，则没有自动选择能力，不能臆造供应商模型，仍须遵守现有的显式指定 `model` 要求。

---

## FAQ

<details>
<summary><strong>spec-superflow 和 OpenSpec / Superpowers 什么关系？</strong></summary>

源码级融合，不是简单并列。吸收了两者的引擎（Schema/验证/解析 + TDD/SDD/调试/审查），独创了 contract-builder 桥接层和 8 状态路由。自包含，不需要安装上游运行时。

</details>

<details>
<summary><strong>能和我已有的 OpenSpec 或 Superpowers 共存吗？</strong></summary>

建议不要在同一会话混用。已有 OpenSpec 工件目录的项目可以直接用 spec-superflow 接管 —— `contract-builder` 能读取现有文件生成 execution contract。

</details>

<details>
<summary><strong>execution contract 怎么知道该更新了？</strong></summary>

内容级检测（不是文件时间戳）：proposal 范围变了、specs 已批准需求改了、design 架构约束变了、tasks 批次变了 → 视为过时，回退到 `contract-builder`。

</details>

<details>
<summary><strong>SDD (Subagent-Driven Development) 怎么工作的？</strong></summary>

full/hotfix 先由 `ssf execution recommend` 根据任务量和 wave 策略列出 Inline、Batch Inline、SDD 并推荐一种；Agent 展示候选项和理由，用户以 `--confirm` 确认后才保存 plan。若选择非推荐方式，`--acknowledge-recommendation` 会记录风险确认。SDD 按可执行 wave 派实施子代理；每个 wave 先有 review report，再写 `pass`/`fail` review receipt。Batch Inline 仍是串行。进度台账防止会话压缩后丢失进度。

</details>

---

**Star 一下，下次需要的时候能找到。**
