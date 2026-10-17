---
name: error-experience-library
description: >
  错误经验库：自动捕获错误模式、根因和解决方案，支持查询和反馈更新。
  当遇到 build error、runtime error 或需要查找历史错误解决方案时使用。
---

# Error Experience Library

## 用途

- 自动从错误中学习：每次错误解决后，将根因-解决方案对沉淀到经验库
- 历史查询：遇到错误时，先查询经验库是否有已知模式
- 反馈更新：根据实际解决结果更新经验库的成功/失败计数
- 持续优化：高成功率的模式优先推荐，低成功率的模式标记为警示

## 核心操作

### 1. 记录错误模式 (record)

当成功解决一个错误后，将经验沉淀：

```
错误类型: [如: build_error, runtime_error, type_error]
错误信息片段: [可匹配的关键词]
根因: [为什么会发生]
解决方案: [如何修复]
语言/框架: [如: python, typescript, react]
文件模式: [可选，如: **/*.ts]
标签: [如: null-check, async, import]
```

### 2. 查询错误模式 (search)

遇到错误时，先查询经验库：

```
查询关键词: [错误信息或类型]
返回: 按成功率排序的匹配模式
```

### 3. 提供反馈 (feedback)

解决方案验证后，更新成功率：

```
pattern_id: 模式ID
success: true/false
```

## 存储位置

- 本地：`~/.claude/memory/error_experience/patterns/`
- 每个模式一个 JSON 文件，包含 success_count 和 failure_count

## 触发信号

- 遇到 build error 或 runtime error 时
- 成功解决错误后，应该记录到经验库
- 使用 `/error-lookup` 命令快速查询

## 配合约束

1. 记录时尽量包含具体的错误信息片段，便于后续匹配
2. 根因要具体，不要只写"代码有 bug"
3. 解决方案要包含具体的修改内容
4. 标签要准确，便于按领域查询
5. 验证结果后务必提供反馈，更新成功率

## 相关工具

- `scripts/lib/memory_store.py` - 底层存储接口
- `search_error_patterns()` - 查询模式
- `save_error_pattern()` - 保存新模式
- `record_pattern_feedback()` - 记录反馈

## 命令接入

- `/error-lookup <关键词>` - 查询历史错误模式
- `/error-record` - 记录当前错误的解决方案
- `/error-feedback <pattern_id> <success|failure>` - 更新反馈
