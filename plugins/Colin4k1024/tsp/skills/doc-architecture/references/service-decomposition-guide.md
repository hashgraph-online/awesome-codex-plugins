# Service Decomposition Guide

用于将业务能力拆分为可落盘、可验证的服务边界。

## Step 1: 能力枚举

- 从用户旅程或核心流程列出能力清单。
- 对每个能力明确输入、输出、状态变更。

## Step 2: 领域分类

- Core Domain：业务竞争力核心。
- Supporting Domain：支撑能力。
- Generic Domain：通用能力。

## Step 3: 边界判定

- 数据主权：谁是 Source of Truth。
- 事务边界：跨服务强一致是否必要。
- 变更频率：是否需要独立演进。

## Step 4: 通信矩阵

- source -> target -> protocol -> contract
- 同步：REST/gRPC
- 异步：事件/消息

## 回落映射

- 服务目录与职责：`arch-design.md`
- 接口契约：`api-contract.md`
- 风险与验证：`test-plan.md`
