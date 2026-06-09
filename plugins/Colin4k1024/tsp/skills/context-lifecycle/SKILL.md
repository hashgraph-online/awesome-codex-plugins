---
name: context-lifecycle
description: >
  上下文生命周期管理总览：四层记忆架构（L0-L3）、任务阶段感知、
  渐进压缩策略、按需召回与四分区预算模型。
origin: harness-engineering
---

# Context Lifecycle Skill

管理 Claude Code 长时多轮任务中的上下文生命周期，避免压缩导致关键细节丢失。

## 架构概览

```
┌──────────────────────────────────────────────────────┐
│                 上下文窗口 (200K tokens)                │
│                                                        │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌────────┐ │
│  │  System   │ │  Ledger  │ │  Working   │ │ Buffer │ │
│  │  (10%)    │ │  (10%)   │ │  (65%)     │ │ (15%)  │ │
│  │ protected │ │ protected│ │ 主工作区    │ │ 溢出区  │ │
│  └──────────┘ └──────────┘ └────────────┘ └────────┘ │
└──────────────────────────────────────────────────────┘
         ↕ 渐进压缩                ↕ 按需召回
┌──────────────────────────────────────────────────────┐
│  L1: 摘要 + L2 引用   →   L2: 全文归档 (索引)         │
│  (替换 L0 原文)             (~/.claude/memory/)       │
│                                                        │
│  L3: 项目记忆 (跨会话)  →  docs/memory/ + Phase Ledger │
└──────────────────────────────────────────────────────┘
```

## 四层记忆模型

| 层级 | 名称 | 位置 | 内容 | 生命周期 |
|------|------|------|------|----------|
| L0 | 工作记忆 | 上下文窗口 | 当前对话、工具结果、代码 | 当前会话 |
| L1 | 摘要记忆 | 上下文窗口 (替换 L0) | 压缩摘要 + L2 归档引用 | 当前会话 |
| L2 | 详情归档 | `~/.claude/memory/sessions/{sid}/` | 完整原文、关键词索引 | 本地持久 |
| L3 | 项目记忆 | `docs/memory/` | Phase Ledger、决策日志、经验 | 跨会话持久 |

## 渐进压缩策略

压缩基于 **Working Zone** 使用率，而非整体上下文使用率：

| Working 使用率 | 压缩级别 | 操作 |
|----------------|----------|------|
| < 60% | 无 | 保持 L0 原文 |
| 60% | L0→L1 | 摘要工具结果、旧对话，原文归档到 L2 |
| 75% | L1→L2 | 摘要 L1 内容，更老的摘要归档到 L2 |
| 90% | L2→L3 | 紧急压缩，决策提升到项目记忆 |

### 阶段感知优先级

压缩时的保留/归档决策受当前任务阶段影响：

| 阶段 | 优先保留 | 优先归档 |
|------|----------|----------|
| Planning | 需求、边界、约束 | 探索性讨论 |
| Design | 架构决策、接口契约 | 备选方案分析 |
| Implementation | 当前文件、测试结果 | 设计讨论 |
| Testing | 测试结果、缺陷 | 实现细节 |
| Review | 评审结论、修改建议 | 测试细节 |

## 核心组件

### 库模块 (`scripts/lib/`)

| 模块 | 职责 |
|------|------|
| `phase_tracker.py` | 任务阶段状态机，多信号检测（命令 / handoff / 工具启发） |
| `phase_ledger.py` | 阶段交接账页，在阶段切换时生成结构化 Markdown |
| `context_budget.py` | 四分区预算模型，Zone-aware 压缩级别判定 |
| `context_archiver.py` | L2 归档写入、关键词索引、去重、批量归档 |
| `context_recall.py` | 按需召回：关键词 / 阶段 / 类型 / 决策多维检索 |
| `context_priority.py` | 上下文元素优先级评分（已有） |

### Hooks (`scripts/hooks/`)

| Hook | 触发点 | 作用 |
|------|--------|------|
| `session_start.py` | 会话开始 | 加载 Phase Timeline、未解决项、决策摘要 |
| `pre_compact.py` | 压缩前 | 分类元素为 keep/summarize/archive/discard |
| `suggest_compact.py` | 压缩建议 | 根据 Working Zone 使用率推荐渐进压缩策略 |

### Skills (`skills/`)

| Skill | 用途 |
|-------|------|
| `context-recall` | `/recall` 命令，按需从 L2 归档和 Phase Ledger 检索 |
| `context-lifecycle` | 本文档，整体架构说明 |
| `strategic-compact` | 已有的 trigger-based 上下文重组能力 |

## 数据流

### 写入路径

```
对话/工具结果 (L0)
    ↓ Working Zone > 60%
pre_compact → categorize as "archive"
    ↓
context_archiver.archive_and_index()
    ├── 写入 L2 文件: ~/.claude/memory/sessions/{sid}/archived/{hash}.md
    ├── 更新索引: ~/.claude/memory/sessions/{sid}/index.json
    └── 返回 L1 摘要 (替换上下文中的原文)
    
阶段切换时
    ↓
phase_ledger.generate_ledger() + save_ledger()
    ├── 写入 L3: docs/memory/sessions/{sid}/phase-{N}-{name}.md
    └── 更新索引: /tmp/harness-phase-ledger-{sid}.json
```

### 读取路径

```
会话启动
    ↓
session_start → get_recall_context_for_session_start()
    ├── 读取 Phase Ledger 索引 → phase_timeline
    ├── 统计未解决项 → pending_items
    └── 统计决策数 → recall_hint

用户请求 /recall
    ↓
context_recall → recall_by_keyword/phase/type/decisions()
    ├── 搜索 L2 索引 (index.json)
    ├── 加载 L2 完整内容
    └── 搜索 Phase Ledger
```

## 使用指南

### 自动行为（无需干预）

1. **会话启动**自动加载 Phase Timeline 和未解决项
2. **压缩时**自动按阶段优先级归档而非丢弃
3. **阶段切换时**自动生成 Phase Ledger

### 手动操作

1. **`/recall keyword`** — 从归档中按关键词搜索
2. **`/recall phase:design`** — 查看 design 阶段的完整交接记录
3. **`/recall decisions`** — 查看所有决策链路
4. **`/recall timeline`** — 查看阶段时间线

### 与现有能力的协同

- `strategic-compact`: 本系统的 L0→L1 压缩替代了 strategic-compact 的全量压缩，两者可共存
- `error-experience-library`: 错误经验在 L3 层跨会话持久保存
- `continuous-learning`: instinct 产物不受压缩影响，已在 L3 层

## 配置

可通过环境变量或 hooks.json 参数调整：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| Zone ratios | 10/10/65/15 | System/Ledger/Working/Buffer 分区比例 |
| L0→L1 threshold | 60% | Working Zone 使用率触发 L0→L1 |
| L1→L2 threshold | 75% | Working Zone 使用率触发 L1→L2 |
| L2→L3 threshold | 90% | Working Zone 使用率触发 L2→L3 |
