---
name: context-engineering
description: >
  项目级上下文工程框架：通过 PROJECT / REQUIREMENTS / ROADMAP / STATE 四层文档
  为每个任务建立结构化上下文，控制 token 预算，防止上下文腐烂，
  确保跨会话连续性。与 context-lifecycle 的 L0-L3 层互补。
origin: gsd-get-shit-done + harness-engineering
---

# Context Engineering

## 用途

- 为复杂、多会话、多角色任务建立 **结构化项目上下文**，保证每轮 agent 启动时拿到完整且受控的项目背景。
- 与 `context-lifecycle`（运行时记忆管理）互补：本 skill 管 **项目级文档层**（L3+），`context-lifecycle` 管 **运行时窗口层**（L0-L2）。
- 控制文档 token 预算，避免"文档越来越多、上下文越来越模糊"的腐烂问题。

## 触发信号

- 新任务 intake 阶段需要建立或刷新项目上下文。
- `/team-intake`、`/team-plan` 输出后需要落盘为结构化文档。
- 跨会话恢复时需要快速加载上下文而不丢失关键决策。
- 多个 agent 并行工作需要共享一致的项目背景。
- 上下文窗口利用率接近阈值，需裁剪文档到预算范围。

## 四层文档模型

```
docs/artifacts/{slug}/
├── PROJECT.md          # 项目愿景、边界、关键假设   (≤ 3000 tokens)
├── REQUIREMENTS.md     # 范围化需求与验收标准       (≤ 5000 tokens)
├── ROADMAP.md          # 阶段路线与里程碑           (≤ 3000 tokens)
└── STATE.md            # 运行时状态：决策、阻塞、进度 (≤ 4000 tokens)
```

### PROJECT.md — 项目愿景（≤ 3000 tokens）

不变频率最低，只在项目方向调整时更新。

```markdown
# {Project Name}

## 愿景
一句话说明项目存在的原因和最终目标。

## 边界
- In Scope: ...
- Out of Scope: ...

## 关键假设
- [ ] 假设 1（待验证 / 已验证 / 已推翻）
- [ ] 假设 2

## 技术栈
- 语言 / 框架 / 基础设施

## 利益相关方
- 角色: 关注点
```

### REQUIREMENTS.md — 范围化需求（≤ 5000 tokens）

每个 `/team-intake` 结束后由 `product-manager` 或 `tech-lead` 刷新。

```markdown
# Requirements — {slug}

## 用户故事
- US-001: 作为…我希望…以便…
  - AC: 验收标准 1, 2, 3

## 功能需求
| ID | 需求 | 优先级 | 状态 |
|----|------|--------|------|

## 非功能需求
| 维度 | 目标 | 验证方式 |

## 约束
- 技术约束
- 业务约束
- 时间约束
```

### ROADMAP.md — 阶段路线（≤ 3000 tokens）

里程碑粒度的阶段划分，由 `project-manager` 维护。

```markdown
# Roadmap — {slug}

## 当前阶段
Phase N: {name} — {status}

## 阶段划分
| Phase | 名称 | 关键产出 | 完成标准 | 状态 |
|-------|------|----------|----------|------|

## 依赖图
Phase 1 → Phase 2 → Phase 3
              ↘ Phase 2b ↗
```

### STATE.md — 运行时状态（≤ 4000 tokens）

频率最高，每个 `/team-execute`、`/team-review`、`/pause` 后刷新。

```markdown
# State — {slug}

## 最后更新
{ISO timestamp} by {role}

## 当前焦点
当前正在推进的工作项。

## 决策日志（最近 10 条）
| # | 日期 | 决策 | 原因 | 影响 |
|---|------|------|------|------|

## 阻塞项
| 阻塞 | Owner | 状态 |

## 进度快照
| 工作项 | 状态 | 负责角色 | 备注 |

## 下一步
1. ...
2. ...
```

## Token 预算管理

### 预算分配

| 文档 | 上限 | 占上下文比例 | 更新频率 |
|------|------|-------------|----------|
| PROJECT.md | 3000 tokens | ~1.5% | 极低 |
| REQUIREMENTS.md | 5000 tokens | ~2.5% | 低 |
| ROADMAP.md | 3000 tokens | ~1.5% | 低 |
| STATE.md | 4000 tokens | ~2% | 高 |
| **合计** | **15000 tokens** | **~7.5%** | — |

### 超限处理

1. **STATE.md 超限**：只保留最近 10 条决策日志，历史归档到 `docs/memory/decisions.md`。
2. **REQUIREMENTS.md 超限**：已完成需求标注 `[DONE]` 后迁移到 `docs/artifacts/{slug}/requirements-archive.md`。
3. **ROADMAP.md 超限**：已完成阶段折叠为单行摘要。
4. **PROJECT.md 超限**：审查假设列表，移除已验证项。

## 工作流集成

### 写入时机

| 命令 / 事件 | 写入文档 | 操作 |
|-------------|----------|------|
| `/team-intake` 完成 | PROJECT.md, REQUIREMENTS.md | 创建或刷新 |
| `/team-plan` 完成 | ROADMAP.md, STATE.md | 创建或刷新 |
| `/team-execute` 每步完成 | STATE.md | 更新进度和决策 |
| `/team-review` 完成 | STATE.md | 更新放行结论 |
| `/pause` | STATE.md | 写入暂停快照 |
| `/resume` | — | 读取全部四层作为恢复上下文 |
| 角色 handoff | STATE.md | 追加交接记录 |

### 读取策略

```
Agent 启动时加载顺序：
1. PROJECT.md   → 建立背景
2. ROADMAP.md   → 确认阶段
3. STATE.md     → 获取当前焦点和阻塞
4. REQUIREMENTS.md → 按需参考（仅在需求相关任务时）
```

### 与既有体系映射

| context-engineering 文档 | Team Skills Platform 既有产物 | 关系 |
|--------------------------|---------------------|------|
| PROJECT.md | PRD 背景/约束 + Delivery Plan 版本目标 | 精简聚合 |
| REQUIREMENTS.md | PRD 用户故事/验收标准 | token 受控子集 |
| ROADMAP.md | Delivery Plan 工作拆解 | 阶段视图 |
| STATE.md | Execute Log + docs/memory/decisions.md | 运行时快照 |

## 配套约束

1. 四层文档是 **快速加载视图**，不替代 PRD / Delivery Plan / ADR 等正式交付物。
2. 预算上限是硬约束：超限时必须裁剪而非放任增长。
3. STATE.md 的决策日志必须与 `docs/memory/decisions.md` 双向同步。
4. 多 agent 并行写同一个 STATE.md 时，以最后合并为准；冲突时保留更高信息密度的版本。
5. 不在这四层文档中存放代码片段、完整测试结果或大段日志——这些属于 L2 归档。

## 验证标准

- [ ] 四层文档均在 token 预算之内
- [ ] STATE.md 最后更新时间 < 当前会话开始时间（即已经在会话初始化时加载）
- [ ] 决策日志条数 ≤ 10 条，超出部分已归档
- [ ] 已完成需求有 `[DONE]` 标记或已归档
- [ ] `/resume` 能在 < 15s 内加载全部四层并展示当前焦点
