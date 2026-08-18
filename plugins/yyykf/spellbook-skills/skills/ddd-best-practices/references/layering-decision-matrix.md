# DDD 分层增减决策矩阵

## 目标

帮助你判断：当前项目到底应该保持最小 5 模块，还是继续引入 `application / api / querys`。

**原则：先满足当前复杂度，再为真实演进预留空间。不要为了对齐某个参考项目而机械补层。**

## 默认基线：5 模块

当项目满足以下条件时，优先采用：
- 主要入口是 HTTP
- 没有对外发布或复用 RPC 契约的需求
- 没有独立读模型 / CQRS / 搜索报表系统
- 用例编排还比较轻，`trigger -> domain service` 依然清晰可控

推荐基线：

```text
{project}-types
{project}-domain
{project}-infrastructure
{project}-trigger
{project}-app
```

## 什么时候增加 `application`

| 信号 | 说明 | 建议 |
|---|---|---|
| 多个 Controller / Job / Listener 复用同一用例编排 | 编排逻辑开始重复 | 增加 `application` 层或先在 `app/usecase` 建包 |
| 一个请求要协调多个领域服务 / 多个聚合 | 领域服务开始被迫承担流程编排 | 抽离用例服务 |
| 事务边界、幂等、权限、审计、事件发布的编排变复杂 | 触发层或领域服务变得过重 | 用 `application` 层承接流程编排 |

**反向信号**：
- 只是几个简单 CRUD/配置管理接口
- `trigger` 直接调用一个领域服务仍然很清晰

此时**不要**为了“看起来完整”先创建空的 `application` 模块。

## 什么时候增加 `api`

| 信号 | 说明 | 建议 |
|---|---|---|
| 需要对外提供 Dubbo / gRPC / Feign / SDK 契约 | 接口定义需要独立复用 | 增加 `api` 模块 |
| 多个进程 / 服务需要共享同一套请求响应 DTO 与接口签名 | 契约复用已成为事实需求 | 增加 `api` 模块 |

**反向信号**：
- 只有单体 HTTP Controller
- DTO 只在本仓库内部使用

此时 `api` 模块通常是多余的。

## 什么时候增加 `querys`

| 信号 | 说明 | 建议 |
|---|---|---|
| 出现独立读模型 / CQRS | 读侧与写侧明显分离 | 增加 `querys` 模块 |
| 查询依赖 ES / ClickHouse / 宽表 / 报表模型 | 读模型复杂度明显高于写模型 | 增加 `querys` 模块 |
| 查询接口不再适合复用领域实体 | 需要专门的 View / Query Model | 单独沉淀查询层 |

**反向信号**：
- 普通分页、列表、详情查询仍能由仓储直接支撑
- 暂无独立读存储与读侧模型

此时没有必要预埋 `querys`。

## 典型场景判断

### 场景 A：内部管理后台 / 基础配置服务
- HTTP 为主
- 无 RPC
- 无 CQRS
- 读写复杂度低到中等

**建议**：保持 5 模块，重点做边界纯化与建模，而不是补层。

### 场景 B：入口越来越多，但仍是单体
- 有 HTTP + Job + MQ Listener
- 同一业务流程被多个入口触发

**建议**：先增加 `application`，不一定要马上加 `api/querys`。

### 场景 C：平台能力要对外复用
- 需要输出 RPC 契约
- 多服务共享 DTO / 接口签名

**建议**：增加 `api`，但仍然不要自动增加 `querys`。

### 场景 D：读写明显分离
- 报表 / 搜索 / 大屏 / 聚合查询很多
- 读侧模型与写侧对象差异巨大

**建议**：增加 `querys`，必要时再结合事件驱动构建读模型。

## 依赖建议

### 最小 5 模块

```text
types <- domain <- infrastructure / trigger <- app
```

### 增加 application 后

```text
types <- domain <- infrastructure
         ^
         |
    application <- trigger
         ^
         |
        app
```

说明：
- `application` 负责编排用例
- `domain` 仍然只承载业务规则与领域协作
- `app` 仍然只负责启动、配置、装配

## 常见误判

1. **因为参考项目有 `api/querys`，所以我也要有**
   - 错。先看真实需求，不看别人模块数量。

2. **因为 DDD 很复杂，所以一开始就把 aggregate / event / application 全建好**
   - 错。先建最小闭环，按演进信号再加。

3. **因为没有 `application`，所以 Controller 直接调 Repository 也没关系**
   - 错。没有 `application` 不等于可以绕过领域服务。

4. **因为暂时没有 CQRS，所以查询对象都塞进 Entity**
   - 错。即使不拆 `querys`，也可以在子域内部定义轻量 Query / View 对象。
