---
name: cross-model-review
description: >
  跨模型第二意见技能，融合 gstack 的 cross-model second opinion 能力。
  当检测到高风险改动时，可选触发不同模型提供独立审查意见，
  作为 multi-perspective-review 的可选叠加层。
---

# Cross-Model Review

## 用途

- 把"同一个模型既写又审"改成"用不同模型交叉审查，降低系统性盲区"。
- 适合高风险改动（鉴权、支付、数据迁移）、架构决策、安全关键路径。
- 作为可选增强层叠加在 `multi-perspective-review` 或 `code-reviewer` 之上。

## 自动检测触发

以下条件命中时，**建议** cross-model review（不强制）：

| 检测条件 | 风险原因 |
|---------|---------|
| 改动涉及 `auth`/`permission`/`security` 路径 | 鉴权逻辑错误可能导致越权 |
| 改动涉及 `payment`/`billing`/`transaction` 路径 | 资金相关错误代价极高 |
| 改动涉及数据库 migration 或 schema 变更 | 不可逆的数据结构变更 |
| 改动涉及 API 契约的 breaking change | 影响所有下游消费方 |
| 单次改动超过 500 行 | 大范围变更的审查覆盖率下降 |
| 代码审查中发现 CRITICAL 级别问题 | 需要独立确认修复的正确性 |

检测到时输出：
```
💡 检测到高风险改动：{原因}
建议启用 cross-model review 获取第二意见。
是否启用？[Y/n]
```

## 默认做法

### 1. 准备审查上下文

从当前改动中提取：
- 变更的 diff（精简到相关部分）
- 涉及的接口契约
- 相关测试
- 已有的 review 意见

### 2. 构建独立 prompt

为第二模型构建独立审查 prompt，要求：
- 不包含第一模型的审查结论（避免锚定）
- 只包含代码变更和背景上下文
- 明确审查维度和期望输出格式

### 3. 审查维度

第二模型审查聚焦在：
- **逻辑正确性**：边界条件、状态转换、错误路径
- **安全性**：输入验证、权限检查、数据泄露
- **一致性**：与现有模式、命名规范、架构约定的一致性
- **遗漏**：第一模型可能忽略的场景

### 4. 意见对比

将两个模型的审查意见合并对比：

```markdown
## Cross-Model Review 对比

### 共识项（两个模型都发现）
- {问题描述}：高可信度，优先处理

### 仅模型 A 发现
- {问题描述}：需要确认是否为真实问题

### 仅模型 B 发现
- {问题描述}：需要确认是否为真实问题

### 冲突项（两个模型意见相反）
- {问题描述}：需要人工仲裁
```

### 5. 最终建议

- **共识项** → 直接按 Revision / Abort Gate 处理
- **单方发现** → 由 `code-reviewer` 或 `tech-lead` 确认后决定
- **冲突项** → 升级给 `tech-lead` 仲裁

## 与 model-profiles 的关系

cross-model review 使用 `manifests/model-profiles.json` 中的模型配置：
- 默认使用与主模型不同的模型作为第二意见（如主用 Sonnet，第二用 Opus）
- `quality-first` profile 下自动启用 cross-model review
- `cost-optimized` profile 下默认关闭，仅对 Abort Gate 项启用

## 触发信号

- 自动检测命中（上述检测条件）
- 用户显式要求"第二意见"或"cross review"
- `/team-review` 中发现 CRITICAL 问题后的确认审查
- 架构方案评审中的分歧点

## 配套约束

1. **可选能力**：cross-model review 永远是建议而非强制，用户可以拒绝。
2. **成本意识**：每次 cross-model review 会额外消耗 token，需要在风险收益之间权衡。
3. **不替代人工判断**：冲突项最终由人类裁定，不依赖模型投票。
4. **不循环引用**：第二模型不审查第一模型的 review 意见，只审查原始代码变更。
