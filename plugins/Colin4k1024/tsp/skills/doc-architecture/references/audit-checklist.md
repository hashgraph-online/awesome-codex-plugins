# Audit Checklist

用于 `/team-review` 阶段的一致性核对。

## 元数据完整性

- artifact frontmatter 是否完整（artifact/task/date/role/status）
- INDEX 是否包含本任务

## 服务名一致性

- `arch-design.md` 服务名是否与 `api-contract.md` 一致
- 服务名是否与实现说明一致

## API 与事件覆盖

- 核心 API 是否都有契约条目
- 核心事件是否在文档中可追溯

## 鉴权一致性

- 契约中的鉴权要求是否与实现控制点一致

## 发布可追溯性

- `release-plan.md` 是否包含监控、回滚、观察项
- `docs/memory/sessions/` 是否有会话摘要

## 审计输出

- Pass/Fail
- 阻塞项
- 非阻塞风险
- 补救动作与 owner
