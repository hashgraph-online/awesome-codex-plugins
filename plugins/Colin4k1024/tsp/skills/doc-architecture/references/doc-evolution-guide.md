# Doc Evolution Guide

用于已有文档场景（Evolution / Gap-fill）的增量更新。

## 变更分类

1. 范围变更：新增或删除模块/服务
2. 契约变更：接口字段、错误码、鉴权变化
3. 非功能变更：性能、可用性、安全目标更新

## 更新原则

- 只改受影响文档，不做无关重排。
- 每次变更要能追溯到任务 slug。
- 关键设计取舍使用 ADR 留痕。

## 推荐顺序

1. 更新 `arch-design.md`
2. 更新 `api-contract.md`
3. 更新 `test-plan.md` 风险与验证
4. 更新 `release-plan.md` 观察与回滚
5. 更新 `docs/memory/decisions.md` 或 `docs/adr/`
