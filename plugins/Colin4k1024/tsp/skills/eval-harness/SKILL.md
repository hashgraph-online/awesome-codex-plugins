---
name: eval-harness
description: >
  正式评估框架，实现 eval-driven development (EDD) 原则。
  用于定义 pass/fail 标准、测量 pass@k 指标、创建回归测试套件。
origin: adapted from ECC
---

# Eval Harness Skill

一个用于 Claude Code 会话的正式评估框架，实现 eval-driven development (EDD) 原则。

## 何时激活

- 为 AI 辅助工作流设置 EDD
- 定义 Claude Code 任务完成的 pass/fail 标准
- 使用 pass@k 指标测量 agent 可靠性
- 为 prompt 或 agent 更改创建回归测试套件
- 跨模型版本基准测试 agent 性能

## 理念

Eval-Driven Development 将评估视为"AI 开发的单元测试":
- **在实现前**定义预期行为
- 在开发期间**持续运行**评估
- 用每次变更**追踪回归**
- 使用 pass@k 指标**测量可靠性**

## 评估类型

### Capability Evals
测试 Claude 能否做以前不能做的事:
```markdown
[CAPABILITY EVAL: points-calculation]
Task: 计算用户积分并确定等级
Success Criteria:
  - [ ] 积分正确累加
  - [ ] 等级边界正确
  - [ ] 权益解锁逻辑正确
Expected Output: 用户总积分 = 1500，等级 = L3
```

### Regression Evals
确保变更不破坏现有功能:
```markdown
[REGRESSION EVAL: login-flow]
Baseline: sha-abc123
Tests:
  - existing-login: PASS
  - session-management: PASS
  - logout-flow: PASS
Result: 3/3 passed (previously 3/3)
```

## Grader 类型

### 1. Code-Based Grader
使用代码的确定性检查:
```bash
# 检查文件是否包含预期模式
grep -q "export function handlePoints" src/points.ts && echo "PASS" || echo "FAIL"

# 检查测试是否通过
npm test -- --testPathPattern="points" && echo "PASS" || echo "FAIL"
```

### 2. Model-Based Grader
使用 Claude 评估开放式输出:
```markdown
[MODEL GRADER PROMPT]
评估以下代码变更：
1. 它是否解决了陈述的问题？
2. 结构是否良好？
3. 边界情况是否处理？
4. 错误处理是否适当？

Score: 1-5 (1=差, 5=优秀)
Reasoning: [解释]
```

### 3. Human Grader
标记为手动审查:
```markdown
[HUMAN REVIEW REQUIRED]
Change: 描述变更内容
Reason: 为什么需要人工审查
Risk Level: LOW/MEDIUM/HIGH
```

## 指标

### pass@k
"k 次尝试中至少一次成功"
- pass@1: 首次尝试成功率
- pass@3: 3 次内成功
- 典型目标: pass@3 > 90%

### pass^k
"所有 k 次试验都成功"
- 更高可靠性标准
- 用于关键路径

## 评估工作流

### 1. 定义（编码前）
```markdown
## EVAL DEFINITION: points-system

### Capability Evals
1. 可以计算用户积分
2. 可以确定用户等级
3. 可以解锁权益

### Regression Evals
1. 现有登录仍然有效
2. 会话管理未改变
3. 登出流程完整

### Success Metrics
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
```

### 2. 实现
编写代码通过定义的评估。

### 3. 评估
```bash
# 运行 capability evals
[Run each capability eval, record PASS/FAIL]

# 运行 regression evals
npm test -- --testPathPattern="existing"

# 生成报告
```

### 4. 报告
```markdown
EVAL REPORT: points-system
==========================

Capability Evals:
  calculate-points:  PASS (pass@1)
  determine-level:  PASS (pass@2)
  unlock-benefits: PASS (pass@1)
  Overall:         3/3 passed

Regression Evals:
  login-flow:      PASS
  session-mgmt:   PASS
  logout-flow:    PASS
  Overall:         3/3 passed

Metrics:
  pass@1: 67% (2/3)
  pass@3: 100% (3/3)

Status: READY FOR REVIEW
```

## 评估存储

在项目中存储评估:
```
.claude/
  evals/
    points-system.md      # 评估定义
    points-system.log     # 评估运行历史
    baseline.json         # 回归基线
```

## 最佳实践

1. **编码前定义评估** - 强制清晰思考成功标准
2. **频繁运行评估** - 尽早捕获回归
3. **追踪 pass@k 趋势** - 监控可靠性趋势
4. **尽可能使用 code graders** - 确定性 > 概率性
5. **人工审查安全** - 永远不完全自动化安全检查
6. **保持评估快速** - 慢评估不会被运行
7. **版本评估与代码** - 评估是一级 artifacts

## 与 Error Experience Library 的关系

- Error Experience Library 记录**已解决的错误**
- Eval Harness 验证**新能力是否正确实现**
- 两者都可用于回归测试
