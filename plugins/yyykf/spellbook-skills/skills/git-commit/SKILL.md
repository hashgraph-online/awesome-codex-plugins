---
name: git-commit
description: "准备并执行高质量 Git 提交。当用户要求提交代码、帮忙 commit、生成提交信息、拆分原子提交，或说 commit this / split commits / skip verify 时触发。先读仓库规范，按真实 diff 和暂存状态生成 Conventional Commit；emoji 默认关闭，仅 `--emoji` 时放在冒号后。不适用于创建 PR/MR（用 git-merge-request）或只推送。"
---

# Git Commit

## Overview

准备并执行高质量 Git 提交。目标不是写漂亮标题，而是产出**忠于 diff、便于 review、符合仓库约定、且如实说明校验状态**的提交。

**Core principle:** 仓库规则优先 → 读取真实状态与 diff → 判断提交边界 → 轻量校验 → 生成 Conventional Commit → 非交互提交 → 如实报告。

**Announce at start:** "正在使用 git-commit skill 帮你准备提交。"

## Prerequisites

- 当前目录为 git 仓库
- 已识别用户意图：真正提交 / 仅草拟消息 / 先拆分 diff

## Inputs

从用户输入中识别下列参数与意图，未指定时用默认值：

| 参数 / 意图 | 默认 | 说明 |
|------|------|------|
| `--emoji` | 关闭 | 启用 emoji，且置于 `type(scope):` 之后 |
| `--no-verify` / "跳过校验" / "直接提交" | 否 | 跳过轻量校验 |
| "只要 commit message" / "先给我消息" | 执行提交 | 只产出候选消息，**不**实际提交 |
| "拆开提交" / "split" | 自动判断 | 先给原子拆分方案，再按确认执行 |

## Workflow

### Phase 1: 读取仓库提交规范（最高优先级）

提交前先查本地约定，**仓库规则永远优先于本 skill 的默认值**。至少检查：

- `AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` / `README.md`
- 提交模板、项目文档、最近提交历史

提取提交语言、格式、emoji 要求、body/footer 标记、issue 引用和必须校验命令。仓库有明文要求时完全照其执行。

### Phase 2: 判定任务模式

尽早区分三种情况，避免误操作：

1. **执行提交**：用户说"提交""commit""帮我交上去"时，默认真实提交
2. **仅草拟**：用户只要 commit message 时，只给候选消息，不提交
3. **先拆分**：diff 混杂或用户要求 split 时，先给拆分方案

### Phase 3: 检查仓库状态与 diff

```
git status --short
```

判断是否已有暂存内容，再读对应 diff。**消息必须基于真实 diff，不要只看文件名。**

- 已有暂存：读 `git diff --cached --stat` 和 `git diff --cached`；默认只提交已暂存内容
- 无暂存：读 `git diff --stat` 和 `git diff`
- 有 untracked 文件：用 `git status --short` 列出，并按文件内容判断是否纳入；不要因为 `git diff` 为空就忽略它们

### Phase 4: 判断提交边界

只在变更形成一个连贯 review 单元时成组暂存并提交。出现以下信号时先停下来给拆分方案：

- 功能开发混入重构或纯文档改动
- 跨不相关模块的变更
- 大面积格式 churn 混入行为变更
- 暂存区和未暂存区表达的是不同主题

暂存时排除敏感文件，例如 `.env`、`*.key`、`credentials*`。不要盲目 `git add -A`。

### Phase 5: 轻量校验（除非明确跳过）

除非用户明确要求跳过，运行能给出有意义信心的最轻校验：

- 仓库文档声明的校验命令优先
- Node 项目先看 `package.json` 脚本，再按 lockfile 选择包管理器
- Maven 项目默认 `mvn compile`
- 混合仓库只跑与改动区域相关的轻量校验

更细的默认策略见 [commit-details.md](references/commit-details.md)。

校验失败时：

- 清晰汇报失败内容
- 绝不把提交说成"已验证"
- 仅在用户明确接受「带着失败继续」时才提交

### Phase 6: 生成符合规范的提交消息

仓库规则优先。仓库未明示时默认：

```text
<type>(<scope>): <description>
```

- 开头必须是 Conventional Commit type，例如 `feat`、`fix`、`docs`、`refactor`
- 描述语言：仓库指定优先；仓库未指定时跟随用户语言
- emoji 默认关闭；仅 `--emoji` 时写成 `feat(x): ✨ 描述`
- emoji 绝不放在最前面，避免破坏 release-please / semantic-release / commitlint 这类按开头 type 解析的工具
- 仓库要求的 body/footer 标记（issue ID、`[#AI]`、release notes 等）必须带上

需要类型表、emoji 表或示例时读取 [commit-details.md](references/commit-details.md)。

### Phase 7: 执行提交（非交互）

用非交互方式创建提交，避免进入交互式 git 流程。多个提交时按文件分组依次暂存、提交；body/footer 用多段 `-m` 或等价非交互方式写入。

### Phase 8: 如实报告

- 跑了哪些校验、或明确跳过了哪些
- 每个提交的消息与生成的 commit SHA（如可得）
- 是否还有未暂存 / 未提交的改动

## Common Mistakes

- **忽略已暂存内容**：有 staged diff 时，默认只围绕 staged diff 提交，除非用户要求纳入更多改动
- **遗漏 untracked 文件**：`git diff` 不显示 untracked，必须结合 `git status --short`
- **emoji 放在最前面**：`✨ feat: ...` 会破坏按 `^type` 解析的自动化工具
- **默认硬塞 emoji**：本 skill 默认不带 emoji，只有显式 `--emoji` 才加；仓库禁止时即使传了也不加
- **凭文件名写消息**：必须读真实 diff，描述要匹配实际改动
- **一锅烩提交**：diff 明显含不相关改动时，不要塞进一个 catch-all 提交，除非用户明确接受这个取舍
- **假装跑了校验**：没跑就说没跑，失败就如实汇报
- **误把"只要消息"当成提交**：用户只要 message 时不要真的 `git commit`

## References

- [commit-details.md](references/commit-details.md) — 类型表、emoji 规则、校验默认值和示例；当仓库没有明文规则或用户要求解释/示例时读取
- 配套技能 `git-merge-request` — 提交后推送并创建 PR/MR，其提交环节复用本 skill
