---
name: context-recall
description: >
  按需召回已归档的上下文细节：支持按关键词、阶段、类型和决策维度检索，
  从 L2 归档和 Phase Ledger 中恢复压缩丢失的信息。
origin: harness-engineering
---

# Context Recall Skill

按需召回已归档的上下文细节，从 L2 归档索引和 Phase Ledger 中恢复压缩过程中被移出工作记忆的信息。

## 何时激活

- 用户输入 `/recall` 命令
- 需要恢复早期对话中的代码细节、工具输出或决策上下文
- 当前上下文中缺少之前阶段的关键信息
- 用户提到"之前讨论过"、"之前的方案"、"找一下之前的…"等表述

## 使用方式

### 基本命令

```
/recall <keyword>              # 按关键词搜索归档
/recall phase:<phase_name>     # 按阶段召回（如 phase:implementation）
/recall type:<element_type>    # 按类型召回（如 type:tool_result）
/recall decisions              # 召回所有决策记录
/recall timeline               # 显示阶段时间线概览
```

### 组合查询

```
/recall phase:design keyword   # 在 design 阶段中搜索关键词
/recall type:code_change api   # 在代码变更中搜索 api 相关内容
```

## 核心功能

### 1. 关键词召回

从 L2 归档索引中按关键词匹配，返回相关的归档元素摘要和完整内容引用。

**工作原理**:
1. 搜索 `~/.claude/memory/sessions/{sid}/index.json` 中的 keywords 字段
2. 按匹配度排序返回结果
3. 提供 L1 摘要和 L2 完整内容的访问路径

### 2. 阶段召回

从 Phase Ledger 中按阶段名称检索，返回该阶段的结构化交接记录。

**输出包含**:
- 阶段目标与完成情况
- 关键决策列表
- 代码变更清单
- 未解决项

### 3. 决策召回

跨所有阶段收集决策记录，构建完整的决策链路。适用于需要理解"为什么这样做"的场景。

### 4. 类型召回

按上下文元素类型检索：
- `tool_result`: 工具执行结果
- `assistant_message`: 助手回复
- `user_message`: 用户消息
- `code_change`: 代码变更
- `decision`: 决策记录

## 技术实现

### 依赖模块

| 模块 | 路径 | 职责 |
|------|------|------|
| `context_recall` | `scripts/lib/context_recall.py` | 召回逻辑核心 |
| `context_archiver` | `scripts/lib/context_archiver.py` | L2 归档索引读取 |
| `phase_ledger` | `scripts/lib/phase_ledger.py` | Phase Ledger 读取 |

### 数据源

| 源 | 路径 | 内容 |
|----|------|------|
| L2 归档索引 | `~/.claude/memory/sessions/{sid}/index.json` | 关键词索引、元素摘要 |
| L2 归档文件 | `~/.claude/memory/sessions/{sid}/archived/*.md` | 完整归档内容 |
| Phase Ledger | `docs/memory/sessions/{sid}/phase-*.md` | 阶段交接记录 |
| Ledger 索引 | `/tmp/harness-phase-ledger-{sid}.json` | Ledger 快速索引 |

### 调用示例

```python
from scripts.lib.context_recall import (
    recall_by_keyword,
    recall_by_phase,
    recall_by_type,
    recall_decisions,
    get_phase_timeline,
    format_recall_results,
)

# 按关键词
results = recall_by_keyword(session_id, "api contract")
print(format_recall_results(results))

# 按阶段
results = recall_by_phase(session_id, "design", project_path)
print(format_recall_results(results))

# 所有决策
results = recall_decisions(session_id, project_path)
print(format_recall_results(results))

# 阶段时间线
timeline = get_phase_timeline(session_id, project_path)
print(timeline)
```

## 输出格式

召回结果以 Markdown 格式返回:

```markdown
## 召回结果: "api contract"

### 匹配 1: [tool_result] API 设计讨论
- **阶段**: design
- **归档时间**: 2025-01-15 14:30
- **摘要**: 确定了 RESTful API 契约，包括认证方式和错误码规范...
- **完整内容**: ~/.claude/memory/sessions/abc123/archived/a1b2c3d4e5f6.md

### 匹配 2: [decision] 选择 OpenAPI 3.0
- **阶段**: design
- **摘要**: 决定使用 OpenAPI 3.0 作为 API 契约格式...
```

## 与其他能力的关系

| 能力 | 关系 |
|------|------|
| `strategic-compact` | compact 时归档 → recall 时恢复 |
| `pre_compact` hook | 产生 L2 归档和索引 → recall 消费 |
| `session_start` hook | 启动时自动加载 Phase Timeline |
| `phase_tracker` | 提供阶段上下文用于精确召回 |
| `phase_ledger` | 提供结构化阶段交接 → recall 检索 |

## 限制

- 召回内容来自归档，可能不包含最近未被压缩的对话
- 关键词匹配基于词频提取，复杂语义查询可能不精确
- Phase Ledger 依赖阶段检测正确性，手动阶段切换可能遗漏
- L2 归档文件存储在本地，跨机器不可用
