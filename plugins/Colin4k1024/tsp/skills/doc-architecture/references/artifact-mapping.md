# Artifact Mapping

将 discovery/modeling/audit 的输出映射到现有 artifacts。

| 能力输出 | 目标文件 |
|---|---|
| Project Profile Card | `prd.md`, `delivery-plan.md` |
| Service Catalog | `arch-design.md` |
| Communication Matrix | `arch-design.md`, `api-contract.md` |
| NFR Summary | `arch-design.md`, `test-plan.md` |
| API/Auth 约束 | `api-contract.md` |
| 实施偏差与决策 | `execute-log.md`, `docs/memory/decisions.md`, `docs/adr/*.md` |
| 一致性审计结论 | `test-plan.md` |
| 发布与回滚手册化 | `release-plan.md`, `docs/memory/sessions/*.md` |

注意：不新增并行主目录作为交付事实源。
