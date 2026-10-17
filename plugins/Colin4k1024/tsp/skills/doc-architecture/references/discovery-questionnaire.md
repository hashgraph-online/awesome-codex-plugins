# Discovery Questionnaire

用于在 `/team-intake` 与 `/team-plan` 收集文档产出所需的最小信息。

## Phase A: Project Profile Card

1. 项目名称与目标是什么？
2. 当前技术栈（后端/前端/中间件）是什么？
3. 架构风格是单体、模块化单体还是微服务？
4. 部署平台与环境约束是什么？
5. API 风格（REST/gRPC/GraphQL）是什么？
6. 是否涉及企业内控、敏感数据、7x24 或跨境合规？

输出回落：`prd.md` + `delivery-plan.md`

## Phase B: Domain & Service Discovery

1. 业务核心流程有哪些？
2. 每个流程的核心实体、命令、事件是什么？
3. 哪些能力归属 Core / Supporting / Generic Domain？
4. 服务间调用关系和协议是什么？

输出回落：`arch-design.md` + `api-contract.md`

## Phase C: NFR

1. 可用性目标（例如 99.9%）
2. 性能目标（P95/P99、吞吐）
3. 安全与鉴权模型（RBAC/ABAC/JWT/OIDC）
4. 可观测性要求（日志、指标、链路）

输出回落：`arch-design.md` + `test-plan.md`

## Phase D: Delivery

1. 里程碑与排期
2. 风险与缓解
3. 发布与回滚窗口

输出回落：`delivery-plan.md` + `release-plan.md`
