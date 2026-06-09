---
name: strategic-compact
description: >
  上下文优化技能，通过 trigger-based 懒加载和 context composition awareness
  自动重组长会话上下文。
origin: adapted from ECC
---

# Strategic Compact Skill

上下文优化技能，通过 trigger-based 懒加载和 context composition awareness 自动重组长会话上下文。

## 何时激活

- 会话上下文超过 70% 使用率
- 需要重组上下文以保留关键信息
- 长会话中需要压缩早期对话
- 需要按重要性重新组织 specialist 输出

## 核心功能

### 1. Trigger-Based 懒加载

只在特定 trigger 发生时加载上下文:

| Trigger | 条件 | 行为 |
|---------|------|------|
| `context_70%` | 上下文使用 > 70% | 触发压缩建议 |
| `context_85%` | 上下文使用 > 85% | 强制压缩 |
| `logical_break` | 检测到逻辑断点 | 建议整理 |
| `specialist_done` | specialist 完成 | 归档输出 |

### 2. Context Composition Awareness

理解上下文不同部分的价值:

**高价值（总是保留）**:
- 决策和结论
- 任务输出和验证结果
- 待处理项和 hints
- 架构决策记录 (ADR)

**中等价值（根据大小决定）**:
- 工具输出（超过阈值时压缩）
- 对话历史（保留首尾，压缩中间）
- 文件内容（保留路径和关键符号）

**低价值（安全丢弃）**:
- 纯搜索结果
- 重复信息
- 工具调用追踪

## 压缩策略

### Phase 1: 保存决策到内存
提取所有决策，保存到 `~/.claude/memory/error_experience/decisions/`

### Phase 2: 保存待办到摘要
提取 pending items 和 next hints，保存到 session summary

### Phase 3: 压缩对话
保留系统提示和最近 20 轮对话，压缩中间部分

### Phase 4: 精简工具输出
将长工具输出替换为摘要：`[File X read, Y lines]`

## 与 Other Skills 的关系

| Skill | 关系 |
|-------|------|
| Memory Persistence | Strategic Compact 使用其存储来保存决策和摘要 |
| Error Experience Library | 从压缩的上下文中提取错误模式 |
| Continuous Learning | Instincts 从归档的上下文中生成 |

## 使用场景

### 场景 1：长会话自动整理

```
用户：连续工作 2 小时后
系统：检测到上下文使用率 75%
系统：触发 suggest_compact hook
系统：提供 4 阶段压缩计划
用户：确认执行
系统：执行压缩，保留关键决策和待办
```

### 场景 2：Specialist 输出归档

```
用户：运行 /code-review
Specialist：输出详细代码审查报告
系统：检测到 specialist_done trigger
系统：提取关键结论，丢弃详细追踪
系统：保存结论到 memory store
```

## 触发阈值

| 使用率 | 紧迫度 | 建议操作 |
|--------|--------|---------|
| < 70% | low | 无需操作 |
| 70-85% | medium | 建议压缩，可选择性执行 |
| 85-95% | high | 强烈建议压缩 |
| > 95% | critical | 必须立即压缩 |

## 命令接入

- `/compact` - 手动触发压缩
- `/compact status` - 显示当前上下文使用率
- `/compact plan` - 显示压缩计划而不执行
