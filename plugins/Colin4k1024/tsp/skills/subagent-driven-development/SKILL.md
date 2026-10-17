---
name: subagent-driven-development
description: >
  融合 superpowers 的 subagent 驱动工作流，将大型实现任务拆分为独立子任务，
  委派给专门的 subagent 执行，主 agent 仅负责编排和质量把关。
  增强现有 parallel-execution 和 wave-execution 的实际执行能力。
---

# Subagent-Driven Development

## 用途

- 把"一个 agent 从头写到尾"改成"主 agent 编排 + 多个 subagent 分而治之"。
- 适合大型功能实现、跨模块重构、多文件同步修改等场景。
- 配合 wave-execution 使用：wave-execution 规划波次，subagent-driven-development 执行每个子任务。

## 核心模式

### 1. Context Brief（上下文简报）

每个 subagent 启动时接收一份独立的上下文简报，包含：

```markdown
## 任务目标
{一句话描述}

## 约束
- 只修改以下文件/目录：{范围}
- 遵循以下规则：{相关 rules 文件路径}
- 接口契约：{API/类型定义路径}

## 输入
- 上游任务产出：{文件路径或内容摘要}
- 相关测试：{已有测试文件路径}

## 期望产出
- 代码变更：{文件列表}
- 测试：{测试文件列表}
- 验证命令：{如何确认任务完成}
```

### 2. 编排策略

| 任务类型 | subagent 分派策略 |
|---------|-----------------|
| 模块实现 | 每个模块一个 subagent，共享接口契约 |
| 测试编写 | 独立 subagent，输入为实现代码的只读快照 |
| 代码审查 | 独立 subagent，审查其他 subagent 的产出 |
| 文档更新 | 独立 subagent，所有代码变更完成后执行 |
| Bug 修复 | 单个 subagent with systematic-debugging 技能 |

### 3. 两阶段 Review（来自 superpowers）

每个 subagent 产出后经历两阶段审查：

**第一阶段：自动验证**
- 代码编译/lint/type-check 通过
- 测试通过
- 不超出文件修改范围
- 遵循 conventional commit 格式

**第二阶段：cross-review**
- 另一个 subagent（或 code-reviewer agent）审查产出
- 检查目标：逻辑正确性、边界处理、与上游/下游的一致性
- 审查结果为 Abort 时，退回原 subagent 修改

## 默认做法

1. **任务拆分**：从 delivery plan 或 wave plan 接收任务列表。

2. **Context Brief 生成**：为每个子任务生成独立的 context brief。

3. **subagent 分派**：
   - 简单实现任务 → `backend-engineer` / `frontend-engineer` agent
   - 测试任务 → `tdd-guide` agent
   - 审查任务 → `code-reviewer` agent
   - 架构任务 → `architect` agent

4. **完成收口**：
   - 检查所有 subagent 产出的一致性
   - 确认无文件冲突
   - 运行集成测试
   - 合并所有变更

5. **异常处理**：
   - subagent 执行超时 → 收集当前进度，由主 agent 接管
   - subagent 反复失败 → 升级给 `tech-lead`
   - 文件冲突 → 主 agent 解决冲突或回退到顺序执行

## 触发信号

- 单次改动涉及 5 个以上文件或 3 个以上模块。
- wave-execution 产出的波次中存在可拆分的大任务。
- 用户要求"用多个 agent 并行处理"。
- 任务复杂度导致单个上下文窗口无法有效管理。

## 配套约束

1. **边界清晰**：每个 subagent 的修改范围必须无重叠，避免 merge conflict。
2. **接口先行**：涉及多 subagent 协作时，接口定义必须先锁定再分派。
3. **失败隔离**：单个 subagent 的失败不应影响其他 subagent 的产出。
4. **上下文独立**：每个 subagent 的 context brief 必须自包含，不依赖对话历史。
