---
name: ddd-best-practices
description: "DDD（领域驱动设计）架构最佳实践指南。当用户在 Java/Spring Boot 项目中遇到分层架构、领域建模、模块边界、代码评审或测试分层问题时使用。包括：纠结是否引入 application/api/querys 模块；设计或审查实体、聚合、仓储、防腐层、领域事件；贫血模型重构（setter 全开、规则全在 Service）；多入口共享用例是否补 application 层；策略模式 Map 注入、责任链、Node 流程编排的取舍；Controller 测试 @WebMvcTest vs @SpringBootTest 选型；MVC 渐进迁移 DDD；DDD 命名规范。仅适用 Java/Spring Boot 生态，Go/Python/Node 等其他语言不适用。"
---

# DDD Best Practices

## Overview

面向 Java / Spring Boot 项目的 DDD 落地指南，提供分层决策、领域建模、代码模板、测试策略、审查清单与重构路线图。

**Core principle:** 先判断复杂度与边界 -> 先收紧依赖与模型 -> 先补关键测试 -> 再按真实信号演进分层与模式。

**Announce at start:** "正在使用 ddd-best-practices skill 为你提供 DDD 架构指导。"

## Prerequisites

- 目标项目为 Java / Spring Boot 技术栈
- 非 Java 项目（Go / Python / Node）请勿使用本 skill

## Workflow

### Phase 1: 判断当前阶段，选择对应参考

根据用户的问题类型，读取对应的 reference 文档：

| 用户场景 | 读取文档 |
|---|---|
| 初始化 / 新模块设计 | [layering-decision-matrix.md](references/layering-decision-matrix.md) → [project-structure.md](references/project-structure.md) |
| 领域建模 / 聚合 / ACL 设计 | [domain-modeling.md](references/domain-modeling.md) |
| 快速落地查模板 | [code-templates.md](references/code-templates.md)（~1100 行，用顶部对照表定位） |
| 命名拿不准 | [naming-conventions.md](references/naming-conventions.md) |
| 测试策略 / TDD 落地 | [testing-strategy.md](references/testing-strategy.md) |
| 代码审查 / 边界收紧 | [code-review-checklist.md](references/code-review-checklist.md) → [boundary-smells.md](references/boundary-smells.md) |
| MVC → DDD 渐进重构 | [refactoring-guide.md](references/refactoring-guide.md) |
| 复杂规则建模 / 流程编排 | [design-patterns.md](references/design-patterns.md)（~900 行，按目录跳转） |

### Phase 2: 确保最小闭环

在给出建议时，优先检查这 5 条基线是否满足，再考虑引入更多抽象：

1. `domain` 纯净，依赖方向正确
2. `trigger` 不直接依赖 `repository / mapper / 外部客户端`
3. `repository` 接口不暴露 `refreshCache / evictCache / cacheXxx` 等技术语义
4. ACL / 外部适配器返回领域对象，而不是把外部 DTO 直接带进领域
5. 关键不变量有领域单元测试，并按职责边界补齐各层测试

### Phase 3: 按场景执行

#### 场景 A: 新项目 / 新模块

1. 用 [layering-decision-matrix.md](references/layering-decision-matrix.md) 判断最小可行分层
2. 用 [project-structure.md](references/project-structure.md) 选择目录结构与 POM 多模块依赖
3. 用 [domain-modeling.md](references/domain-modeling.md) 设计实体 / 值对象 / 聚合 / 仓储 / Port
4. 用 [code-templates.md](references/code-templates.md) 按层拷贝代码骨架
5. 命名拿不准时查 [naming-conventions.md](references/naming-conventions.md)
6. 用 [testing-strategy.md](references/testing-strategy.md) 规划测试分层
7. 只在规则明显膨胀时，再引入 [design-patterns.md](references/design-patterns.md) 中的模式

#### 场景 B: 测试策略与 TDD 落地

1. 先判断当前要验证的是**领域规则**、**用例编排**、**HTTP 契约**，还是**持久化/外部集成**风险
2. 领域规则优先写纯单测，不启动 Spring；关键不变量在 Entity / VO / DomainService 层锁住
3. `application / use case` 只测编排、事务边界、幂等与跨聚合协调；可 mock 仓储接口、Port，不要 mock Entity / VO
4. Controller 默认使用 `@WebMvcTest + MockMvc`；默认 mock 应用服务 / use case
5. Repository / Adapter / 复杂 Mapper 通过集成测试验证，必要时使用 Testcontainers
6. 仅保留少量 `@SpringBootTest` 烟雾测试验证关键全链路 wiring

#### 场景 C: 审查与边界收紧

1. 用 [code-review-checklist.md](references/code-review-checklist.md) 做结构化检查
2. 用 [boundary-smells.md](references/boundary-smells.md) 对照常见反模式
3. 检查测试边界：是否用 controller 测试兜底领域规则、是否大量 mock mapper、是否缺少集成测试
4. 先修"依赖方向、边界绕过、DTO 穿透、缓存语义泄漏、测试边界错位"
5. 修完后立刻补领域测试与关键集成测试，锁住行为

#### 场景 D: MVC 到 DDD 重构

1. 先识别限界上下文与用例边界
2. 先封装 Repository / Port，再重构模型
3. 先做最小模块拆分，避免一次性把 `application / api / querys` 全预埋
4. 优先把关键规则沉回模型或领域服务
5. 每次边界收紧前后，优先补 `domain` 与 `application` 层的保护性测试

### Phase 4: 判断是否继续演进

只有当出现真实信号时，再建议引入：

| 信号 | 引入 |
|---|---|
| 多入口共用同一用例编排、跨聚合编排膨胀 | `application` 层 |
| 需要对外发布/复用 RPC 契约 | `api` 模块 |
| 出现独立读模型、CQRS、报表/搜索等读侧复杂性 | `querys` 模块 |
| 跨聚合一致性问题已真实出现 | 领域事件 / MQ |

## Common Mistakes

- **为了"像 DDD"而盲目补层**：模块数量不是成熟度的代名词，先满足当前复杂度
- **Domain 层混入技术细节**：不要在 `domain` 中放 Spring / MyBatis / Redis / HTTP 客户端
- **先上模式再有场景**：两个 `if-else` 不值得上责任链 / 决策树
- **用一种测试覆盖所有**：领域规则、编排、HTTP 契约和持久化风险应按责任边界分层测试
- **`@SpringBootTest` 当默认**：Controller 默认使用切片测试，Repository / Adapter 默认使用真实集成测试
- **大量 mock mapper**：若 `application / domain` 测试必须 mock mapper，优先回看职责划分是否混乱

## References

- [layering-decision-matrix.md](references/layering-decision-matrix.md) — 分层增减决策矩阵
- [project-structure.md](references/project-structure.md) — 渐进式项目结构与 Maven 多模块 POM
- [domain-modeling.md](references/domain-modeling.md) — 领域建模指南 + 速查模板
- [code-templates.md](references/code-templates.md) — 按层代码模板速查 + 端到端示例（~1100 行，用顶部对照表定位）
- [naming-conventions.md](references/naming-conventions.md) — 包/类/接口/方法/数据库命名速查
- [design-patterns.md](references/design-patterns.md) — 领域层模式落地范式（~900 行，按目录跳转）
- [testing-strategy.md](references/testing-strategy.md) — DDD 测试分层与 Mock 边界
- [code-review-checklist.md](references/code-review-checklist.md) — DDD 代码审查清单
- [boundary-smells.md](references/boundary-smells.md) — 常见边界异味与修复策略
- [refactoring-guide.md](references/refactoring-guide.md) — MVC 到 DDD 渐进重构指南
