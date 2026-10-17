---
name: api-contract
description: >
  统一接口协议、请求响应、错误码、兼容性与上下游协作约束。
  当架构师、前后端开发或 QA 需要锁定 API 合同时使用。
---

# API Contract

## 用途

- 定义或审阅接口契约，避免“实现先行、契约滞后”。
- 对齐请求响应、鉴权、兼容性与错误处理。

## 默认做法

1. 使用 [api-contract.md](../../templates/api-contract.md) 固定接口定义。
2. 记录调用方、鉴权要求、错误码和兼容策略。
3. 若契约以 OpenAPI 形式维护，先结合 [api-lint-gates](../../docs/runbooks/api-lint-gates.md) 校验规范与结构，再用 [api-breaking-change-gates](../../docs/runbooks/api-breaking-change-gates.md) 做兼容性比对。
4. 若接口存在明确的 consumer/provider 边界，且需要把行为约定做成可执行验证，再结合 [contract-testing-playbook](../../docs/runbooks/contract-testing-playbook.md) 规划 pact 或 provider verification。
5. 指明需要同步给前端、后端、QA 的关键信息。
