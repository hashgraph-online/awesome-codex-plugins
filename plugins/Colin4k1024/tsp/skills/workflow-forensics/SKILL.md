---
name: workflow-forensics
description: >
  对失败或卡住的团队工作流进行事后调查：时间线重建、角色交接审计、
  产出缺失定位、重复循环检测和根因归类。
  与 systematic-debugging（代码级调试）互补，本 skill 面向工作流级诊断。
origin: gsd-forensics + harness-engineering
---

# Workflow Forensics

## 用途

- 当一个团队工作流（`/team-*` 链路）失败、卡住、超时或产出不符合预期时，进行 **结构化事后调查**。
- 重建工作流时间线，定位失败点，区分 **流程问题**（角色交接缺失、产出缺失、门禁跳过）和 **技术问题**（代码错误、环境故障）。
- 为 `tech-lead` 提供可操作的诊断报告，而不是模糊的"某步出了问题"。

## 触发信号

- `/team-execute` 或 `/team-review` 连续 2 次以上未能推进。
- 角色之间 handoff 被拒绝或回退。
- 同一任务在 `/team-plan` 和 `/team-execute` 之间来回超过 2 次。
- 发布后发现关键产出缺失（如无 test-plan、无 deployment-context）。
- 线上事故调查需要追溯"哪一步遗漏了什么"。
- agent 在自主循环中陷入重复（同一工具调用 > 3 次无进展）。

## 调查流程

### Phase 1: 证据收集

```
收集来源：
├── docs/artifacts/{slug}/     → 正式产出文件
├── docs/memory/sessions/      → 会话日志
├── docs/memory/decisions.md   → 决策记录
├── STATE.md                   → 运行时状态
├── HANDOFF.json               → 暂停/恢复快照
├── git log --oneline -20      → 最近提交历史
└── .claude/memory/            → agent 记忆文件
```

**收集约束：**
- 不读不相关任务的文件——按 `{slug}` 限定范围。
- 对每个证据源标注 **时间戳** 和 **产出角色**。

### Phase 2: 时间线重建

按时间顺序列出所有工作流事件：

```markdown
## 工作流时间线

| # | 时间 | 事件 | 角色 | 产出 | 状态 |
|---|------|------|------|------|------|
| 1 | T1 | /team-intake 完成 | tech-lead | PRD draft | ✅ |
| 2 | T2 | handoff → architect | tech-lead | handoff record | ✅ |
| 3 | T3 | arch-design 开始 | architect | — | ⏳ |
| 4 | T4 | arch-design 阻塞 | architect | — | ❌ 缺依赖 |
| 5 | T5 | 回退到 tech-lead | architect | escalation | 🔄 |
```

### Phase 3: 失败模式识别

对照以下常见失败模式检查时间线：

| 失败模式 | 症状 | 根因类别 |
|----------|------|----------|
| **Handoff 断裂** | 角色交接记录缺失或不完整 | 流程 |
| **产出缺失** | 应有 artifact 不存在或为空 | 流程 |
| **门禁跳过** | 未通过 quality gate 就推进到下一阶段 | 流程 |
| **循环陷阱** | 同一步骤反复执行 > 2 次无进展 | 流程 / 技术 |
| **范围蠕变** | 执行阶段的产出超出计划范围 | 需求 |
| **依赖阻塞** | 等待外部输入或其他角色产出 | 协调 |
| **上下文丢失** | 关键决策在会话中丢失未落盘 | 上下文 |
| **工具失败** | 构建/测试/部署工具连续失败 | 技术 |
| **权限/环境** | 环境配置、权限、依赖不可用 | 基础设施 |

### Phase 4: 根因定位

```
对每个识别到的失败模式：
1. 标注第一次出现的时间线位置
2. 追溯：该位置之前最后一个正常状态是什么
3. 差异：正常 → 异常之间发生了什么变化
4. 归类：流程 / 需求 / 协调 / 上下文 / 技术 / 基础设施
5. 影响：该失败导致了后续哪些连锁问题
```

### Phase 5: 诊断报告

输出格式：

```markdown
# Workflow Forensics Report — {slug}

## 概览
- 调查对象: {task/slug}
- 调查时间: {ISO timestamp}
- 调查触发: {触发原因}
- 严重程度: Critical / High / Medium / Low

## 时间线
（Phase 2 的表格）

## 失败模式
| 模式 | 位置 | 根因类别 | 严重程度 |
|------|------|----------|----------|

## 根因分析
### 根因 1: {名称}
- 第一次出现: 时间线 #{N}
- 最后正常状态: ...
- 变化点: ...
- 类别: ...
- 连锁影响: ...

## 建议措施
| # | 措施 | 目标 | Owner | 优先级 |
|---|------|------|-------|--------|

## 预防建议
- 流程改进: ...
- 工具改进: ...
- 文档改进: ...
```

## 与既有能力的关系

| 能力 | 关注层 | 关系 |
|------|--------|------|
| `systematic-debugging` | 代码级根因 | 互补：forensics 定位到技术根因后交给 debugging |
| `error-experience-library` | 错误模式复用 | 互补：forensics 发现的模式可录入经验库 |
| `escalation-policy` | 升级决策 | 互补：forensics 为升级提供证据 |
| `incident-brief` | 事故模板 | 互补：forensics 报告可填充 incident brief |

## 自动化检查（快速模式）

当不需要完整调查时，可运行快速检查：

```
快速检查清单（< 5 分钟）：
□ docs/artifacts/{slug}/ 下是否有 PRD、arch-design、execute-log
□ 每个 handoff 记录是否包含完整字段（handoff-contract.md）
□ STATE.md 最后更新时间是否 > 24h 前
□ git log 是否有与 {slug} 相关的提交
□ 是否有未解决的阻塞项
```

## 配套约束

1. 诊断报告存放到 `docs/artifacts/{slug}/forensics-report.md`。
2. 诊断结论中的预防建议如果涉及流程变更，必须通过 `tech-lead` 确认后才能修改规则或模板。
3. 涉及代码级问题时，转交 `systematic-debugging` 或相应角色，不在 forensics 中直接修代码。
4. 调查过程中发现的可复用失败模式，录入 `error-experience-library`。
5. 不做"谁的错"的归责——聚焦于"哪一步断了" + "怎么防止再断"。

## 验证标准

- [ ] 时间线覆盖从 intake 到当前的所有工作流事件
- [ ] 每个失败模式都有明确的根因类别和时间线定位
- [ ] 建议措施有明确 Owner 和优先级
- [ ] 报告已存档到 `docs/artifacts/{slug}/`
- [ ] 可复用模式已录入 error-experience-library（如适用）
