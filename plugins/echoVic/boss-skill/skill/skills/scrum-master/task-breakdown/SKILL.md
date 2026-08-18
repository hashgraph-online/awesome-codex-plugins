---
name: scrum-master/task-breakdown
description: 任务拆解方法，将需求拆解为可执行的开发任务
version: 1.0.0
agent: scrum-master
type: methodology
user-invocable: false
agent-invocable: true
dependencies: []
triggers:
  - 需要拆解开发任务时
  - 需要估算工作量时
---

# 任务拆解方法

## WBS（工作分解结构）

将大任务拆解为小任务，遵循SMART原则：
- **Specific**：具体明确
- **Measurable**：可衡量
- **Achievable**：可实现
- **Relevant**：相关联
- **Time-bound**：有时限

## 拆解粒度

| 粒度 | 时长 | 适用场景 |
|------|------|----------|
| 小任务 | 2-4小时 | 单个功能点 |
| 中任务 | 1-2天 | 完整功能模块 |
| 大任务 | 3-5天 | 跨模块功能 |

**原则**：任务不超过2天，超过则继续拆分。

## 任务依赖

- **串行依赖**：B必须等A完成
- **并行任务**：A和B可同时进行
- **阻塞任务**：优先处理阻塞其他任务的任务
