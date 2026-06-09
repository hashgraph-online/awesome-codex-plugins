---
name: continuous-learning
description: >
  基于 instinct 的持续学习系统，通过 hooks 观察会话，创建带置信度评分的 atomic instincts，
  并将高置信度 instinct 演进为 skills/commands/agents。v2.1 增加项目级 instincts 防止跨项目污染。
origin: adapted from ECC
version: 2.1.0
---

# Continuous Learning v2.1 - Instinct-Based Architecture

一个高级学习系统，通过 atomic "instincts" 将 Claude Code 会话转化为可重用知识。

**v2.1** 增加 **项目级 instincts** — React 模式保留在 React 项目中，Python 约定保留在 Python 项目中，通用模式（如"始终验证输入"）全局共享。

## 何时激活

- 设置从 Claude Code 会话自动学习
- 配置基于 hooks 的行为提取
- 调优学习行为的置信度阈值
- 审查、导出或导入 instinct 库
- 将 instincts 演进为完整 skills、commands 或 agents
- 管理项目级 vs 全局 instincts
- 将 instincts 从项目级提升到全局级

## Instinct 模型

一个 instinct 是一个小的学习行为：

```yaml
---
id: prefer-component-colocation
trigger: "当多个组件使用相同状态时"
confidence: 0.7
domain: "frontend-architecture"
source: "session-observation"
scope: project
project_id: "a1b2c3d4e5f6"
project_name: "points-frontend"
---

# 组件状态共置

## 行为
当多个组件使用相同状态时，考虑将状态提升到共同祖先。

## 证据
- 在 5 个实例中观察到状态提升模式
- 用户在 2026-03-29 将组件本地状态改为共享状态
```

**属性**:
- **Atomic** -- 一个 trigger，一个 action
- **Confidence-weighted** -- 0.3 = 试探性，0.9 = 几乎确定
- **Domain-tagged** -- code-style, testing, git, debugging, workflow 等
- **Evidence-backed** -- 跟踪创建它的观察
- **Scope-aware** -- `project`（默认）或 `global`

## 存储结构

```
~/.claude/homunculus/
+-- projects.json           # 项目注册表: hash -> name/path
+-- observations.jsonl      # 全局观察（fallback）
+-- instincts/
|   +-- personal/          # 全局自动学习的 instincts
|   +-- inherited/         # 全局导入的 instincts
+-- evolved/
|   +-- agents/           # 全局生成的 agents
|   +-- skills/           # 全局生成的 skills
|   +-- commands/         # 全局生成的 commands
+-- projects/
    +-- a1b2c3d4e5f6/    # 项目 hash（来自 git remote URL）
        +-- project.json    # 项目元数据
        +-- observations.jsonl
        +-- instincts/
        |   +-- personal/  # 项目特定自动学习
        |   +-- inherited/  # 项目特定导入
        +-- evolved/
            +-- skills/
            +-- commands/
            +-- agents/
```

## 项目检测

系统自动检测当前项目：

1. **`CLAUDE_PROJECT_DIR` env var**（最高优先级）
2. **`git remote get-url origin`** -- hash 生成项目 ID
3. **`git rev-parse --show-toplevel`** -- fallback
4. **全局 fallback** -- 如果未检测到项目，instincts 进入全局范围

## 置信度评分

| 分数 | 含义 | 行为 |
|------|------|------|
| 0.3 | 试探性 | 建议但不强制 |
| 0.5 | 中等 | 相关时应用 |
| 0.7 | 强 | 自动批准应用 |
| 0.9 | 几乎确定 | 核心行为 |

**置信度增加**当:
- 模式被重复观察
- 用户不纠正建议的行为
- 相似 instincts 同意

**置信度减少**当:
- 用户明确纠正行为
- 模式长时间未观察到
- 出现矛盾证据

## 与 Skills 的区别

| 特性 | Skills | Instincts |
|------|--------|-----------|
| 粒度 | 完整工作流 | Atomic 行为 |
| 触发 | 手动调用 | 自动观察 |
| 置信度 | 无 | 0.3-0.9 |
| 演化 | 直接成为 skill | 先 instinct 再 cluster |

## 相关工具

- `scripts/lib/memory_store.py` - 底层存储接口
- Error Experience Library - 错误模式的专门 instinct

## 命令接入

- `/instinct-status` - 显示学习的 instincts
- `/evolve` - 将 instincts 聚类为 skills/commands
- `/instinct-export` - 导出 instincts 到文件
- `/instinct-import` - 从文件导入 instincts
- `/promote` - 将项目 instincts 提升到全局

## 最佳实践

1. **观察** -- 启用 hooks 捕获所有工具调用
2. **分析** -- 定期运行 observer agent 分析观察
3. **演进** -- 将高置信度 instincts 演进为 skills
4. **分享** -- 通过导出/导入在团队中共享 instincts
