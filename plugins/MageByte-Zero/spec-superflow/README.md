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
codex plugin add spec-superflow@spec-superflow
```

Codex App 打开 **Plugins** 面板，安装或启用 `spec-superflow`。如果通过 CLI 安装，重启 App 后在 Plugins 面板启用。

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

### 更多平台（Cline / Kiro / Windsurf / Qwen / Amazon Q / Roo Code / Continue / Pi / OpenCode / WorkBuddy / Trae）

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
| **OpenCode** | `.opencode/plugins/spec-superflow.js` 或 `.agents/skills -> skills/` | 已提供入口 |
| **WorkBuddy** | `npx spec-superflow@latest install-workbuddy` | 已提供安装器 |
| **Trae IDE / TRAE Work** | `.trae/skills/`、`~/.trae/skills/` 或上传 zip/.skill | 手动/导入 |

> 共支持 17 个平台，完整安装说明见 [INSTALL.md](INSTALL.md)，支持矩阵见 [docs/platform-matrix.md](docs/platform-matrix.md)。

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

### 版本

- 当前版本：`v0.8.17`
- 自包含插件，不需要运行时安装 OpenSpec 或 Superpowers
- 上游来源：[Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) 和 [obra/superpowers](https://github.com/obra/superpowers)
- 版本历史见 [CHANGELOG.md](CHANGELOG.md)

`ssf inject` 示例：

```bash
ssf inject changes/my-change --platforms cursor
ssf inject changes/my-change --platforms all
```

省略 `--platforms` 时，只有在项目中**恰好检测到一个**平台标记时才会自动写入；如果检测到多个平台，必须显式指定 `--platforms <platform>` 或 `--platforms all`。

Delta spec 的规范路径是 `specs/<capability>/spec.md`；扁平的 `specs/<capability>.md` 和根级 `specs/spec.md` 不会被视为合法规范。

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
| 8 | `release-archivist` | 收口 | 验证前完成铁律 + 归档 + 风险总结 |
| 9 | `spec-merger` | 同步 | Delta Spec → 主规范智能合并 |

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
       ▼
   closing            release-archivist 验证 + 归档
       ▼
   syncing            spec-merger（delta spec → 主规范）
```

**关键约束：** 没有 `execution-contract.md` 或未被批准 → 不允许实现；需求变更 → 强制回退；遇到 bug → 强制走 debugging，不允许"随便试试"。

### 快速路径（hotfix / tweak）

- **hotfix** — ≤2 文件、无新模块时，走 `exploring -> bridging -> approved-for-build -> executing`。可跳过 `proposal.md`、`design.md`、`tasks.md`、`specs/` 等完整规划工件，但仍必须先生成一份新的最小 `execution-contract.md`，并完成 DP-3 批准后才能进入实现
- **tweak** — ≤4 文件、纯配置/文档修改时，跳过规划+桥接，直接编辑

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

每任务循环：派实施子代理 → 生成 review diff → 派审查子代理 → 双向判断（spec 合规 + 代码质量）→ 不合格 → 修复 → 重新审查。进度台账防止会话压缩后丢失进度。

</details>

---

**Star 一下，下次需要的时候能找到。**
