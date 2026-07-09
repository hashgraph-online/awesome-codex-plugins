---
name: git-merge-request
description: "一键提交并创建合并请求（GitHub Pull Request 或 GitLab Merge Request）。当用户说「创建 PR」「创建 MR」「提交并创建合并请求」「push 并开 PR/MR」「提 PR」「提 MR」「open a pull request」「open a merge request」或类似意图时触发。自动识别 GitHub / GitLab 远端，调用对应的 gh / glab CLI，完成暂存、Conventional Commit、推送、读取仓库内 PR/MR 模板（若存在）、创建并指派合并请求。不适用于：仅本地提交（用 git-commit 技能）、纯推送但不开合并请求、Bitbucket / Gitea 等其他平台。"
---

# Git Merge Request

## Overview

一键提交并创建合并请求，覆盖 GitHub Pull Request 与 GitLab Merge Request 两种平台。统一识别远端、复用 git-commit 技能完成提交、自动探测仓库内 PR/MR 模板、生成标题与描述、调用对应 CLI 创建并指派。

**Core principle:** 检测平台 → 复用 git-commit 提交 → 推送 → 仓库模板优先于内置模板 → 用户确认后通过 CLI 创建并指派。

**Announce at start:** "正在使用 git-merge-request skill 帮你创建合并请求。"

## Prerequisites

- 当前目录为 git 仓库且 `origin` 指向 GitHub 或 GitLab
- 平台对应 CLI 已安装并认证：
  - GitHub → `gh`（用 `gh auth status` 验证）
  - GitLab → `glab`（用 `glab auth status` 验证）

如果检测到平台但对应 CLI 缺失，**直接终止并明确告知安装命令，不要静默回退到另一个 CLI**：

| 平台 | 安装命令（macOS） |
|------|------|
| GitHub | `brew install gh && gh auth login` |
| GitLab | `brew install glab && glab auth login` |

## Inputs

从用户输入中提取下列参数，未指定时使用默认值：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| target_branch | 仓库默认分支 | 合并目标分支 |
| assignee | 当前 CLI 登录用户 | 指派人 |
| title | 自动生成 | 合并请求标题，从 commit 历史推导 |
| template | 自动选择 | 多模板时让用户选 |
| -y | false | 跳过确认直接创建 |

## Workflow

### Phase 1: 检测平台

读取 `git remote get-url origin`，按 host 判定平台：

| Host 关键词 | 平台 | CLI |
|------|------|------|
| `github.com` 或自建 GHE 域名 | GitHub | `gh` |
| `gitlab.com` 或自建 GitLab 域名 | GitLab | `glab` |
| 其他 | 不支持 | 终止并告知 |

如果是企业自建域名无法明确判断，先看仓库根是否存在 `.github/` 或 `.gitlab/` 目录辅助判断；仍无法确定时询问用户。

### Phase 2: 检查环境

平台判定后，运行对应命令验证 CLI 已认证：

```
# GitHub
gh auth status

# GitLab
glab auth status
```

同时查看当前仓库状态与提交风格：

```
git status
git log --oneline -5
```

### Phase 3: 暂存与提交（复用 git-commit 技能）

**优先调用 `git-commit` 技能完成提交**，避免在本技能里重复实现 commit 流程。git-commit 已经处理：
- 排除 `.env` 等敏感文件
- 读取仓库提交规范并优先遵守
- 生成 Conventional Commit（emoji 默认关闭，仅 `--emoji` 时启用且置于冒号后）
- 按仓库规范处理描述语言与 body 标记（如 `[#AI]`）
- 仓库提交风格识别

如果 git-commit 技能不可用，按以下规则手工提交：
- 若无已暂存文件，`git add` 已修改 / 新增文件（排除 `.env` / `*.key` / `credentials*` 等敏感文件）
- 用 `git diff --cached` 分析变更，生成 Conventional Commit（emoji 仅在仓库 / 用户要求时启用、且置于冒号后，描述用中文）
- body 末尾追加 `[#AI]` 标记
- 执行 `git commit`

### Phase 4: 推送

```
git push origin <current_branch>
```

若远程分支不存在，使用 `git push -u origin <current_branch>`。

### Phase 5: 解析目标分支并同步远程

优先级：用户指定 > 仓库默认分支。

| 平台 | 获取默认分支命令 |
|------|------|
| GitHub | `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` |
| GitLab | `git remote show origin \| grep 'HEAD branch' \| awk '{print $NF}'` |

**关键：必须 fetch 远程目标分支以确保比较基准最新：**

```
git fetch origin <target_branch>
```

后续所有比较必须使用 `origin/<target_branch>` 而非本地 `<target_branch>`。本地分支可能滞后，会让 diff 与待合并 commit 列表不准确。

### Phase 6: 解析指派人

优先级：用户指定 > 当前 CLI 登录用户。

| 平台 | 获取当前用户命令 |
|------|------|
| GitHub | `gh api user --jq '.login'` |
| GitLab | `glab auth status 2>&1 \| grep 'Logged in' \| awk '{print $6}'` |

### Phase 7: 探测并选择仓库内模板

**核心规则：仓库内有模板就用仓库的，没有再用内置模板。** 团队往往在模板里放了 checklist、签署声明、影响范围说明等约定项，覆盖这些约定会让 review 流程出岔子。

按以下顺序查找模板文件，**第一个命中即停**：

#### GitHub（PR 模板）

1. `.github/PULL_REQUEST_TEMPLATE.md`
2. `.github/pull_request_template.md`
3. `.github/PULL_REQUEST_TEMPLATE/` 目录下任意 `.md` 文件（多模板）
4. 仓库根目录 `PULL_REQUEST_TEMPLATE.md` / `pull_request_template.md`
5. `docs/PULL_REQUEST_TEMPLATE.md` / `docs/pull_request_template.md`

#### GitLab（MR 模板）

1. `.gitlab/merge_request_templates/` 目录下任意 `.md` 文件（多模板）
2. `.gitlab/merge_request_template.md`

#### 多模板处理

如果命中的是模板目录且包含多个 `.md` 文件：
- 列出所有候选模板（文件名 + 第一行标题）
- 让用户选择，未指定时使用 `default.md`（若存在），否则使用第一个
- 用户传了 `template=<filename>` 参数时按指定的来

#### 模板填充策略

仓库内模板不要原样照搬，而是当作骨架填入生成内容：

1. **保留模板的所有结构**：标题层级、checklist、HTML 注释 `<!-- -->`、placeholder 占位符
2. **识别可填充段落**：常见 section 标题如 `## Description` / `## 描述` / `## 变更说明` / `## 改动说明` / `## What changed` / `## Why` / `## 主要改动` 等，把生成的「变更概述 / 主要改动」内容替换占位文本填进去
3. **不动 checklist**：保留 `- [ ]` 项原样，让作者后续手工勾选
4. **末尾追加 `[#AI]` 标记**

如果没找到任何仓库内模板，退回内置模板：

```markdown
## 变更概述

<一两句话说明本次变更的目的和背景>

## 主要改动

- <改动点 1>
- <改动点 2>
- ...

[#AI]
```

### Phase 8: 生成标题

分析待合并 commit（必须用 `origin/<target_branch>` 比较）：

```
git log --oneline origin/<target_branch>..HEAD
```

- 1 个 commit → 直接用 commit 主题作为标题
- 多个 commit → 概括总结

### Phase 9: 确认或直接创建

若未传 `-y`，先向用户展示预览，等待确认：

```
即将创建 <PR 或 MR>：
  平台：<GitHub 或 GitLab>
  标题：<title>
  源分支：<current_branch>
  目标分支：<target_branch>
  指派人：<assignee>
  模板来源：<repo:.github/PULL_REQUEST_TEMPLATE.md 或 builtin>

描述：
  <description 内容>
```

用户确认后（或传了 `-y` 时直接）执行：

| 平台 | 创建命令 |
|------|------|
| GitHub | `gh pr create --base <target_branch> --head <current_branch> --title "<title>" --body "<description>" --assignee <assignee>` |
| GitLab | `glab mr create --source-branch <current_branch> --target-branch <target_branch> --title "<title>" --description "<description>" --assignee <assignee> --no-editor` |

`--body` / `--description` 内容用 heredoc 传入以保留换行与 Markdown 格式。

### Phase 10: 输出结果

返回合并请求链接，并明确告知：
- 平台与目标分支
- 指派人
- 模板来源（仓库模板路径或 builtin）

## Common Mistakes

- **静默回退 CLI**：检测到 GitLab 但 `glab` 没装，绝对不要去找 `gh` 试着创建 —— 会推送到错的地方或直接报错。明确告知缺失并终止
- **未 fetch 就比较**：用本地 `main` 而非 `origin/main` 计算待合并 commit，会漏掉队友刚推上来的提交，导致 PR 描述错乱
- **覆盖仓库模板的 checklist**：把 `<!-- 请勾选 -->` 之类占位整段抹掉，让模板形同虚设。保留 checklist 原样
- **多模板时静默选第一个**：团队会按模板分类（feature / bugfix / hotfix），错选模板会触发错误的审查流程。多模板时主动询问
- **目标分支硬编码 `main`**：很多老仓库默认分支是 `master` 或 `develop`，应通过 CLI 查询
- **commit 流程重新发明**：项目已有 `git-commit` 技能，不要在本技能里复制粘贴一份
- **`[#AI]` 标记位置错放**：必须在描述末尾，不要塞进标题里
- **擅自勾选 checklist**：不要替用户在 `- [ ]` 上打勾，那是作者的自我确认动作

## References

- 项目 `git-commit` 技能 — 提交消息生成与暂存策略，本技能 Phase 3 优先复用
- GitHub Docs: [About PR templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository)
- GitLab Docs: [Description templates](https://docs.gitlab.com/ee/user/project/description_templates.html)
