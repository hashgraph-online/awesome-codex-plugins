---
name: langfuse-coding-trace
description: 为编码工作流提供 Langfuse 链路追踪能力。当执行 logic-layer-method-impl 等编码 skill 时，自动上报每个大步骤（识别模式、代码生成、编译、启动、单元测试、代码修复）的开始/结束事件到自部署 Langfuse，实现全流程可观测。凡用户涉及编码流程监控、追踪、可观测性、Langfuse 上报时均应触发此 skill，配合其他编码类 skill 联合使用。
---

# Langfuse 编码流程追踪

为编码工作流每个关键步骤异步上报 Trace/Span 到 Langfuse，不阻塞主流程。

## 前置条件

需设置以下环境变量（未设置时静默跳过追踪）：

```
LANGFUSE_PUBLIC_KEY   # Langfuse 公钥
LANGFUSE_SECRET_KEY   # Langfuse 私钥
LANGFUSE_HOST         # 自部署地址，如 http://192.168.1.100:3000
```

## 脚本位置

```
<skills_dir>/langfuse-coding-trace/scripts/trace.py
```

> 调用前先确认 `LANGFUSE_PUBLIC_KEY` 是否存在，不存在则跳过所有追踪调用。

---

## 追踪点规范

### 第一步：开始编码会话 → 创建 Trace（同步，获取 trace_id）

```bash
TRACE_ID=$(python "<skills_dir>/langfuse-coding-trace/scripts/trace.py" trace-start \
  --name "logic-layer-method-impl" \
  --input '{"method": "目标方法名", "mode": "首次编码/需求变更"}')
echo "Trace started: $TRACE_ID"
```

### 中间步骤：每个大步骤 → 创建 Span（异步，后台执行）

```bash
# 开始 Span（同步获取 span_id，耗时极短）
SPAN_ID=$(python "<skills_dir>/langfuse-coding-trace/scripts/trace.py" span-start \
  --trace-id "$TRACE_ID" \
  --name "maven-qa")

# 执行实际步骤 ...（编译/运行/测试等）

# 结束 Span（异步，后台执行）
python "<skills_dir>/langfuse-coding-trace/scripts/trace.py" span-end \
  --span-id "$SPAN_ID" \
  --output '{"exit_code": 0, "result": "通过"}' \
  --level DEFAULT &

# 若失败，用 ERROR 级别
python "<skills_dir>/langfuse-coding-trace/scripts/trace.py" span-end \
  --span-id "$SPAN_ID" \
  --output '{"error": "错误摘要"}' \
  --level ERROR &
```

### 最后一步：结束 Trace（异步）

```bash
python "<skills_dir>/langfuse-coding-trace/scripts/trace.py" trace-end \
  --trace-id "$TRACE_ID" \
  --output '{"status": "success", "loops": 1, "compile": "pass", "run": "pass", "test": "95%"}' &
```

---

## 标准追踪点列表

| 步骤 | Span 名称 | input 字段 | output 字段 | 失败 level |
|------|-----------|------------|-------------|-----------|
| 识别编码模式 | `identify-mode` | `{}` | `{"mode": "首次/变更"}` | WARNING |
| 代码生成 | `code-generation` | `{"files": [...]}` | `{"files_modified": N}` | ERROR |
| QA 质量闸口 | `maven-qa` | `{}` | `{"compile": "pass", "pass_rate": "XX%", "criticalIssues": 0, "run": "pass"}` | ERROR |
| 代码修复 | `code-fix` | `{"error": "..."}` | `{"files_fixed": [...]}` | WARNING |

---

## 完整调用示例（配合 logic-layer-method-impl）

```bash
# 检查环境变量
if [ -z "$LANGFUSE_PUBLIC_KEY" ]; then
  echo "Langfuse 未配置，跳过追踪"
  LANGFUSE_ENABLED=false
else
  LANGFUSE_ENABLED=true
fi

SCRIPT="<skills_dir>/langfuse-coding-trace/scripts/trace.py"

# 1. 开始 Trace
[ "$LANGFUSE_ENABLED" = true ] && \
  TRACE_ID=$(python "$SCRIPT" trace-start --name "logic-layer-method-impl" --input '{"method":"xxx"}')

# 2. 识别模式 Span
[ "$LANGFUSE_ENABLED" = true ] && \
  SPAN_MODE=$(python "$SCRIPT" span-start --trace-id "$TRACE_ID" --name "identify-mode")
# ... 执行识别逻辑 ...
[ "$LANGFUSE_ENABLED" = true ] && \
  python "$SCRIPT" span-end --span-id "$SPAN_MODE" --output '{"mode":"首次编码"}' &

# 3. 代码生成 Span（同上模式）

# 4. QA 验证 Span（编译 + 单测 + 静态分析）
[ "$LANGFUSE_ENABLED" = true ] && \
  SPAN_QA=$(python "$SCRIPT" span-start --trace-id "$TRACE_ID" --name "maven-qa")
# ... 调用 maven-qa skill ...
[ "$LANGFUSE_ENABLED" = true ] && \
  python "$SCRIPT" span-end --span-id "$SPAN_QA" --output '{"compile":"pass","pass_rate":"98%","criticalIssues":0,"run":"pass"}' &

# 5. 结束 Trace
[ "$LANGFUSE_ENABLED" = true ] && \
  python "$SCRIPT" trace-end --trace-id "$TRACE_ID" --output '{"status":"success"}' &
```

---

## Overview

为编码工作流的每个关键步骤（识别模式、代码生成、编译、启动、单元测试、代码修复）异步上报 Trace/Span 到自部署 Langfuse，实现全流程可观测。环境变量未配置时静默跳过，不阻塞主流程。

本 skill **不执行编码逻辑**，只做可观测性上报，配合其他编码类 skill 联合使用。
