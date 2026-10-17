---
name: boss:extend
description: "引导式扩展 Boss：5 分钟加一个自定义 Agent、pipeline pack 或 gate 插件。把扩展 Boss 变成一等公民体验，落到 .boss/plugins 与 .boss/pipeline-packs。"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /boss:extend — 引导式扩展 Boss

`/boss:extend` 引导用户在**当前项目**里加一个自定义扩展，无需读源码。产出落到项目级扩展点，`/boss` 下次运行时自动发现。

> 这是 Boss 的自我繁殖层：像 superpowers 的 `writing-skills` 一样，让生态自己长。

## 能扩展什么

| 类型 | 落地位置 | 用途 |
|------|----------|------|
| **自定义 Agent** | `.boss/plugins/<name>/` | 加一个新角色（如 Security Reviewer、Data Engineer） |
| **Pipeline Pack** | `.boss/pipeline-packs/<name>/` | 定制阶段/角色组合（如只跑 backend + qa） |
| **Gate 插件** | `.boss/plugins/<name>/` | 加一道自定义质量门禁 |

## 执行步骤

1. 读取 `references/extending-boss.md` 取得扩展契约与 schema。
2. 一次一个问题，确认：扩展类型 + 名称 + 触发/挂载时机。
3. 按对应模板生成文件（见下）。
4. 校验：
   - Pack → `boss packs detect <dir> --json` 应能列出新 pack（有 CLI 时）。
   - Plugin → `boss runtime register-plugins <feature>` 应发现它（有 CLI 时）。
   - 无 CLI → 提示用户文件已就位，`/boss` 会按 `references/no-cli-fallback.md` 手动加载。
5. 输出：新扩展路径 + 如何在 `/boss` 中启用。

## Pipeline Pack 模板

```json
{
  "name": "<pack-name>",
  "version": "1.0.0",
  "type": "pipeline-pack",
  "description": "<一句话说明>",
  "author": "<you>",
  "license": "MIT",
  "when": { "fileExists": ["package.json"], "noFileExists": [] },
  "priority": 3,
  "config": {
    "stages": [1, 2, 3, 4],
    "roles": "custom",
    "agents": ["boss-pm", "boss-architect", "boss-backend", "boss-qa"],
    "gates": ["gate0", "gate1"],
    "agentStages": { "boss-pm": 1, "boss-architect": 1, "boss-backend": 3, "boss-qa": 3 }
  },
  "enabled": true
}
```

## Gate 插件模板

```json
{
  "name": "<gate-name>",
  "version": "1.0.0",
  "type": "gate",
  "description": "<一句话说明>",
  "author": "<you>",
  "license": "MIT",
  "hooks": { "gate": "gate.js" },
  "config": { "passThreshold": 0.7 },
  "stages": [3],
  "enabled": true
}
```

配套 `gate.js` 契约见 `references/extending-boss.md`。

## 自定义 Agent 模板

以 `agents/boss-*.md` 为范式，产出 `.boss/plugins/<name>/agent.md`：角色定位、输入产物、输出产物、状态报告（沿用 `DONE`/`BLOCKED`/`REVISION_NEEDED` 协议）。

## 用法

```
/boss:extend                      # 引导式选择类型
/boss:extend pack backend-only    # 直接建一个 pack
/boss:extend agent security       # 直接建一个 agent
```
