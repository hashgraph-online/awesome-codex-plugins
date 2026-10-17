<p align="center">
  <img src="assets/logo-512.png" alt="anchor" width="280"/>
</p>

<h1 align="center">anchor</h1>

<p align="center">
  <em>engineering discipline for Claude Code &amp; Codex CLI</em>
</p>

<p align="center">
  <a href="https://github.com/biefan/anchor/actions/workflows/ci.yml"><img src="https://github.com/biefan/anchor/actions/workflows/ci.yml/badge.svg" alt="CI"/></a>
  <a href="https://github.com/biefan/anchor/releases"><img src="https://img.shields.io/github/v/release/biefan/anchor?sort=semver" alt="Release"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/></a>
  <a href="evals/regression/"><img src="https://img.shields.io/badge/regression-364%2F364-brightgreen.svg" alt="Tests"/></a>
  <a href="https://github.com/biefan/anchor/stargazers"><img src="https://img.shields.io/github/stars/biefan/anchor?style=social" alt="Stars"/></a>
</p>

<p align="center">
  <a href="README.en.md">English</a> · <strong>中文</strong>
</p>

> **Claude Code / Codex CLI 的工程化纪律包**  
> 让 AI 写代码"少走错路、不偏题、跑到完为止"，并且**真的记得住**跨 session 跨项目的经验。

| 维度 | 数量 | 内容 |
|---|---|---|
| Slash commands | **22** | 工作流 / 长任务 / 记忆 / 复盘 / 安全 / Token 经济 |
| Hooks | **5** | SessionStart / Stop / PreToolUse / PostToolUse / PreCompact |
| 防御 patterns | **277+** | 14 轮 audit / 残忍 obfuscation 测试 |
| Regression tests | **364/364** | 15 suites（hooks / 记忆 loop / install / manifest 等）|
| 长期记忆类别 | **7** | pitfalls / decisions / facts / preferences / todos / snapshots / saved-tasks |
| 跨 CLI | **2** | Claude Code + OpenAI Codex CLI |

**Quick links**:  
[安装](docs/install.md) · [22 个命令](docs/commands.md) · [设计原则](docs/design.md) · [Codex CLI](docs/codex.md) · [Playbook](docs/playbook.md) · [对比表](docs/competitors.md)

---

## 实测战报（v1.9.1 跑过 3 个真实场景）

在 Codex CLI 上跑 [`evals/stress/`](evals/stress/) 里的 3 个长任务测试，用 `evals/stress/grade.py`（codex-as-judge）评分。

| 场景 | v1.3 baseline | v1.4.6 | **v1.9.1** | 改进 |
|---|---|---|---|---|
| debug 5 个失败测试 | 6/1/1 | 5/2/1 | **6/1/1** | 回到 peak — CLAUDE.md 4-field format ✅ |
| refactor 保留行为 | 3/1/3 | 3/1/3 | **4/0/3** ⬆ | tests-before-refactor 第一次过 |
| scaffold Express + SQLite API | 2/3/0 | 3/2/2 | **3/2/2** | anti-borrow-deps 持续闭环 |
| **总计 (pass/fail/N-A)** | 11/5/4 | 11/5/6 | **13/3/6** | **+2 pass / -2 fail** |

**最有信号的 finding**：

> **anti-borrow-deps 跨场景闭环**：v1.3 抓到 agent 借 node_modules cheat → v1.3.3 SKILL.md 加 anti-pattern → v1.9.1 stress #1 agent 正确说 *"我没法在这里装依赖，请你本地跑 npm install 再跑测试"* 并停下。
>
> 三段闭环：`grade.py finding → SKILL.md update → 实测验证`。

跑自己的：`./evals/stress/run.sh <1|2|3>`

**和市面对比** → [`docs/competitors.md`](docs/competitors.md)（10+ 同类工具的诚实对比）

---

## 它解决什么

| 问题 | anchor 怎么解 |
|---|---|
| 中途偏题（被 tool 输出带跑、顺手做范围外的事）| `/lock` 锁用户原话当第一条 task / autonomous mode Stop hook 拦截 |
| 长任务记忆衰减（auto-compact 截掉 skill）| 关键规则前置 SKILL.md / PreCompact 提示 `/save` / `~/.anchor/active-task.md` 跨 session 续接 |
| 单测过 ≠ 功能正确 | `/done` checklist 强制走 E2E + 二阶自检 |
| 漏洞扫一遍说"干净" | `/scan` 多遍扫方法论 / `/codex:review` 交叉验证 |
| 修完 bug 转头就忘 | `/pit` 写当前项目 `CLAUDE.md` + 自动 sync 全局 |
| 自己审自己有盲点 | `/done` 按改动规模触发 codex review；trivial 跳过、复杂/安全/大改必跑 |
| **下次 session 不知道上次踩过什么坑** ⭐ | SessionStart 自动注入本项目 memory index → SKILL.md 规则 #8 "auto-recall reflex" |
| **跨项目复用经验** | `/recall <keyword>` grep `~/.anchor/memory/` 全部 7 个 category |
| **危险命令本能误操作** | PreToolUse hook 拦 277+ patterns（含组合绕过 / obfuscation / 跨平台变种）|

**两层防线**：
- **软**：SKILL.md 写明工作流，模型主动遵循
- **硬**：5 个 hooks 在关键时机自动触发

---

## 1 分钟上手

```bash
# 1. 安装（一键，含 Codex CLI 检测）
git clone https://github.com/biefan/anchor.git ~/anchor && cd ~/anchor && ./install.sh

# 2. 打开 Claude Code 进项目，第一次先建 CLAUDE.md
/init-claude-md

# 3. 锁定任务 scope
/lock 把 order-service 拆成 6 个模块

# 4. 启动 autonomous mode（做完才停）
touch ~/.claude/.efficient-coding-autonomous

# 5. 干完一阶段
/milestone phase-1-parse-extracted

# 6. 下班保存 / 第二天续接
/save end-of-day-refactor          # 收工
/resume-task end-of-day-refactor   # 续上

# 7. 修完 bug 写踩坑（跨项目可 /recall 到）
/pit

# 8. 收尾
/done
```

完整 walkthrough（5 个典型场景）→ [`docs/playbook.md`](docs/playbook.md)

---

## 22 个 slash commands（概览）

按使用阶段分 6 类：

| 阶段 | 命令 |
|---|---|
| **开始任务** | `/lock` `/init-claude-md` `/ec` |
| **干活中** | `/next` `/recap` `/status` `/diff` |
| **长任务跨 session** | `/save` `/resume-task` `/milestone` `/snapshot` |
| **跨项目记忆** | `/pit` `/decide` `/remember` `/recall` |
| **收尾 / 安全** | `/scan` `/cleanup` `/done` `/ship` |
| **复盘 / 成本** | `/spend` `/report` `/lean` |

每个命令的详细 + 何时用 → [`docs/commands.md`](docs/commands.md)

**自动触发**：不用 `/<cmd>` 也行 — Claude 看到符合 description 的任务自动调用 anchor skill。

---

## 设计原则

### 核心八条

1. 意图清晰才开工 · 2. 任务范围用 TaskCreate 锁住 · 3. 先读项目契约
4. 最小正确改动 · 5. 能派 agent 就派并行 · 6. 审查看情况调 codex
7. 踩坑回写 CLAUDE.md · 8. **遇到 topic 先 /recall** ⭐

每条详解 + 反模式 + 完成清单 → [`docs/design.md`](docs/design.md)

### 跨项目记忆 closed loop（v1.9.0+）

```
[写] /pit /decide /remember → ~/.anchor/memory/<category>/<project>/
   ↓
[索引] SessionStart 自动列本项目 memory titles
   ↓
[反射] SKILL.md 规则 #8: 用户提 matching topic 时先 /recall
   ↓
[读] /recall <keyword> 拉完整内容
```

之前缺中间 2 段，memory 是 write-only。v1.9.0 起 closed loop。

---

## Codex CLI 支持

`install.sh` 检测到 `codex` 自动同时装到 `~/.codex/skills/anchor/`。v1.11.0 起 SessionStart hook 自动 detect runtime + 注入对应工具名 hints（Claude Code 用 `TaskCreate`，Codex 用 `plan_tool`）。

完整跨平台覆盖矩阵 + plugin 安装 → [`docs/codex.md`](docs/codex.md)

---

## 和市面上对比

简表：

| 工具 | 类型 | 核心差异点 |
|---|---|---|
| **anchor** | 跨 CLI hook 包 | **唯一**：22 commands + 5 hooks + 277 防御 patterns + 跨项目记忆 closed loop + codex-as-judge auto-grader + 14 轮 audit |
| Praxis | 方法论 doc | 只 prompt 规则，无 hook 强制 |
| HOTL | 工作流 | 强制人工 confirm |
| Session Orchestrator | 跨 CLI runtime | 跨 Claude Code + Codex，但无 hook 防御 / 无记忆系统 |
| Aegis | 安全 audit | 偏向 audit phase，工作流弱 |
| Antigravity Workspace | codebase 理解 | **互补**：理解 codebase + 改动时不犯错 |

完整对比（10+）→ [`docs/competitors.md`](docs/competitors.md)

---

## 致谢与参考

- [anthropics/skills](https://github.com/anthropics/skills) 的官方 skill 范例（`skill-creator`、`claude-api`）
- [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) 的 `stop-review-gate` hook 实现
- Anthropic [claude-plugins-official/pr-review-toolkit](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/pr-review-toolkit) 的 6 个 PR review agents
- Anthropic [claude-plugins-official/code-modernization](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-modernization) 的 `security-auditor`

## License

MIT
