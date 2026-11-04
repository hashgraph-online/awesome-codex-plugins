---

name: boss:upgrade
description: "更新 Boss Skill 到市场最新版本。"
allowed-tools: Bash, Read
---

# /boss:upgrade — 更新 Boss Skill

Boss 是纯 Markdown skill，通过 skill 市场分发，没有 npm 包或 CLI。
更新 = 让市场重新拉取仓库。

## 执行步骤

1. 检查当前安装的版本（读安装副本 `SKILL.md` 的 frontmatter `version:`）
2. 按安装方式更新：
   - Claude Code 插件：`/plugin marketplace update boss-skill`
   - Codex 插件：`codex plugin marketplace upgrade boss-skill`
   - skills.sh：`npx skills update boss`
   - git 安装：在 skill 源仓库 `git pull`
3. 显示升级前后的版本和变更摘要

## 用法

```
/boss:upgrade
```
