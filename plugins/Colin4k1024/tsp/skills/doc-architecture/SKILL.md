---
name: doc-architecture
description: >
  将需求发现、领域建模、一致性审计整合到 /team-* 主链，
  以 artifacts/adr/memory 为唯一落盘目标产出可审计文档。
  当 Tech Lead、Architect、QA 需要补齐或演进架构文档时使用。
---

# Doc Architecture

## 用途

- 将文档能力拆入现有 team-skills 主链，不新增并行文档体系。
- 统一 Discovery、Service Decomposition、NFR、Audit 的输入输出结构。
- 保证文档可追溯落盘到 `docs/artifacts/`、`docs/adr/` 与 `docs/memory/`。

## 完整工作流

### Step 1: Discovery

1. 使用 [discovery-questionnaire.md](references/discovery-questionnaire.md) 收集项目背景、技术栈、架构风格与约束。
2. 若是既有项目（brownfield），先补做现状扫描：盘点现有模块、入口、外部依赖、关键数据流和历史包袱；必要时借助 `/update-codemaps` 生成 token-lean 结构快照。
2. 形成 Project Profile Card。
3. 按 [tech-stack-profiles.md](references/tech-stack-profiles.md) 锁定文档术语风格。

输出回落：`prd.md`、`delivery-plan.md`

### Step 2: Modeling

1. 使用 [service-decomposition-guide.md](references/service-decomposition-guide.md) 识别领域与服务边界。
2. 产出 Service Catalog 与 Communication Matrix。
3. 收集 NFR（可用性、性能、安全、可观测性）。

输出回落：`arch-design.md`、`api-contract.md`

### Step 3: Generation Mapping

1. 按 [artifact-mapping.md](references/artifact-mapping.md) 将文档输出映射到 artifacts。
2. 参考 `references/templates/` 选择章节结构。
3. 若属于 brownfield 任务，把现状扫描结果回落为 brownfield context snapshot，写入 `delivery-plan.md` / `arch-design.md`，不要新建平行事实源。
3. 对缺失信息使用 `<!-- TODO: ... -->` 标记，不虚构业务事实。

输出回落：`delivery-plan.md`、`arch-design.md`、`api-contract.md`

### Step 4: Execute Backfill

1. 在执行阶段记录实现偏差、接口漂移、事件变更。
2. 关键取舍进入 ADR，轻量决策进入 decisions。

输出回落：`execute-log.md`、`docs/adr/*.md`、`docs/memory/decisions.md`

### Step 5: Consistency Audit

1. 使用 [audit-checklist.md](references/audit-checklist.md) 做一致性审计。
2. 审计服务名、API 覆盖、事件覆盖、鉴权一致性、索引完整性。

输出回落：`test-plan.md`

### Step 6: Release & Evolution

1. 将发布、监控、回滚与观察项落入发布产物。
2. 按 [doc-evolution-guide.md](references/doc-evolution-guide.md) 做增量演进。

输出回落：`release-plan.md`、`docs/memory/sessions/*.md`

## 最小产物清单

1. `docs/artifacts/{date}-{slug}/prd.md`
2. `docs/artifacts/{date}-{slug}/delivery-plan.md`
3. `docs/artifacts/{date}-{slug}/arch-design.md`
4. `docs/artifacts/{date}-{slug}/api-contract.md`（按需）
5. `docs/artifacts/{date}-{slug}/execute-log.md`
6. `docs/artifacts/{date}-{slug}/test-plan.md`
7. `docs/artifacts/{date}-{slug}/release-plan.md`
8. `docs/adr/ADR-{NNN}-{slug}.md`（按需）
9. `docs/memory/project-context.md`、`docs/memory/decisions.md`、`docs/memory/lessons-learned.md`、`docs/memory/sessions/*.md`

## 何时优先调用

- `tech-lead` 需要把架构文档能力并入主链而不新增命令时。
- `architect` 需要在 `arch-design.md` 与 `api-contract.md` 形成可执行契约时。
- `qa-engineer` 需要把文档一致性纳入放行证据时。

## 参考资料

- [doc-architecture-integration.md](../../docs/runbooks/doc-architecture-integration.md)
- [team-command-output-contracts.md](../../docs/runbooks/team-command-output-contracts.md)
- [artifact-standards.md](../../rules/artifact-standards.md)
- [discovery-questionnaire.md](references/discovery-questionnaire.md)
- [service-decomposition-guide.md](references/service-decomposition-guide.md)
- [audit-checklist.md](references/audit-checklist.md)
- [doc-evolution-guide.md](references/doc-evolution-guide.md)
- [artifact-mapping.md](references/artifact-mapping.md)
