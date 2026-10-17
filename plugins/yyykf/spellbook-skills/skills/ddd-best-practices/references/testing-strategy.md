# DDD 测试分层与 Mock 边界指南

## 目录

- [目标](#目标)
- [基本原则](#基本原则)
- [按层测试策略](#按层测试策略)
- [Mock 边界](#mock-边界)
- [关于 Mapper](#关于-mapper)
- [JUnit 5 / AssertJ / Mockito 组合建议](#junit-5--assertj--mockito-组合建议)
- [推荐测试目录](#推荐测试目录)
- [常见反模式](#常见反模式)
- [TDD 落地顺序](#tdd-落地顺序)

## 目标

帮助你在 DDD Java / Spring Boot 项目中回答这些高频问题：

- 单测到底测 `domain` 还是 `service`
- Controller 测试该用 `@WebMvcTest` 还是 `@SpringBootTest`
- 哪些依赖适合 mock，哪些不应该 mock
- `mapper` 要不要 mock、要不要单测、要不要集成测试
- 什么时候必须补 Repository / Adapter 集成测试

核心原则只有一句：

**在责任真正所在的边界上验证行为。**

## 基本原则

1. **领域规则在 domain 层验证**：不要依赖启动 Spring 上下文去证明领域规则是对的。
2. **HTTP 契约在 trigger/controller 层验证**：参数绑定、校验、状态码、异常映射、响应结构不应该主要靠 service 测试兜底。
3. **技术风险在 infrastructure 层验证**：SQL、JPA/MyBatis 映射、ACL 转换、序列化、外部适配器风险必须用真实集成测试兜底。
4. **少量全链路测试兜底 wiring**：`@SpringBootTest` 只保留给关键主链路，不作为默认控制器测试方式。
5. **状态断言优先于交互断言**：优先断言结果、状态变化、异常；仅在外部副作用重要时使用 `verify(...)`。

## 按层测试策略

### 1. Domain 测试

**适合验证：**
- 不变量
- 状态流转
- 权限判断
- 唯一性/只读限制
- 值对象约束
- 领域服务中的业务规则

**推荐方式：**
- 纯 JUnit 5 + AssertJ
- 不启动 Spring
- 不连数据库
- 尽量直接 new 实体 / 值对象 / 领域服务

**可 mock：**
- Repository 接口
- 外部 Port
- 事件发布接口（若领域服务协调它）

**不建议 mock：**
- Entity
- Value Object
- Domain Policy
- 领域异常

### 2. Application / UseCase 测试

**适合验证：**
- 用例编排
- 事务边界上的流程协调
- 幂等/审计/事件发布编排
- 跨聚合协作

**推荐方式：**
- 轻量单元测试
- 关注“是否正确协调协作者”，而不是 HTTP 或 SQL 细节

**可 mock：**
- Repository 接口
- Port 接口
- Event Publisher
- Clock / IdGenerator 等不稳定协作者

**不建议 mock：**
- Entity / VO
- 领域规则对象
- 本应在 infrastructure 层实现的 mapper 细节

### 3. Trigger / Controller 测试

**适合验证：**
- 参数绑定
- Bean Validation
- 状态码
- 响应体结构
- 异常映射
- Jackson 序列化/反序列化配置

**默认推荐：**
- `@WebMvcTest + MockMvc`

**推荐协作者：**
- mock `ApplicationService / UseCase`

**避免：**
- 默认起 `@SpringBootTest`
- 在 Controller 中直接注入 Repository / Mapper / 外部客户端
- 让 Controller 测试承担领域规则回归保护

### 4. Infrastructure 集成测试

**适合验证：**
- Repository 实现
- JPA/MyBatis 查询与映射
- PO ↔ Entity 转换
- ACL / Adapter 的 DTO → 领域对象转换
- Redis / MQ / HTTP Adapter 行为

**推荐方式：**
- 真实框架组件 + 测试环境依赖
- 数据库/中间件行为明显时优先 Testcontainers
- 不要 mock 你正在验证的技术对象本体

**典型切片：**
- JPA：`@DataJpaTest`
- MVC：`@WebMvcTest`
- MyBatis：使用对应测试切片；若切片能力不足，使用最小 Spring 集成测试

### 5. Full Context / Smoke Test

**适合验证：**
- 配置装配
- AOP / Filter / Interceptor / Security 链
- 事务与异常处理的全链路效果
- 关键 happy path / failure path

**推荐方式：**
- 少量 `@SpringBootTest`
- 覆盖最重要的 1~3 条业务主链路即可

## Mock 边界

### 适合 mock 的对象

- Repository 接口
- 外部系统 Port
- RPC / HTTP Client
- MQ 发送器
- Event Publisher
- Clock / UUID / SnowflakeId 生成器

### 通常不应 mock 的对象

- Entity
- Value Object
- Domain Policy
- 领域事件对象
- Command / Query / Response DTO
- Repository 实现本体

## 关于 Mapper

### 可以不重点测试 / 不值得大量 mock 的情况

- 只是简单字段搬运
- MapStruct 同构映射
- 没有业务语义和默认值规则

这种情况下：
- 不要在 service / use case 测试里大量 mock 它
- 可以在 controller / repository / adapter 边界顺带覆盖

### 必须认真测试的情况

- 状态码 / 枚举语义转换
- 金额、时间、时区、精度转换
- DTO 组合成领域对象
- 外部响应做防腐转换
- PO 到 Entity 的默认值/嵌套组装

这种情况下：
- 优先直接测 mapper / adapter
- 或者在 repository / adapter 集成测试里验证

如果一个 `service` 测试必须 mock 一堆 mapper，通常不是 Mockito 技巧问题，而是**职责边界已经混乱**。

## JUnit 5 / AssertJ / Mockito 组合建议

### JUnit 5

负责测试结构与生命周期：
- `@Test`
- `@Nested`
- `@ParameterizedTest`
- `@BeforeEach`

### AssertJ

优先用来验证：
- 返回值
- 状态变化
- 集合内容
- 异常语义

优先写这种断言：

```java
assertThat(order.getStatus()).isEqualTo(OrderStatus.PAID);

assertThatThrownBy(order::cancel)
        .isInstanceOf(BusinessException.class)
        .hasMessage("已支付订单不可取消");
```

### Mockito

只在协作者边界上使用：
- stub 外部返回值
- verify 关键副作用

避免让测试退化成“全是 `verify(...)` 的实现细节测试”。

## 推荐测试目录

```text
src/test/java
├── domain
│   └── order
│       ├── OrderEntityTest
│       ├── OrderDomainServiceTest
│       └── MoneyTest
├── application
│   └── order
│       ├── CreateOrderUseCaseTest
│       └── CancelOrderUseCaseTest
├── trigger
│   └── http
│       └── OrderControllerTest
├── infrastructure
│   ├── repository
│   │   └── OrderRepositoryIT
│   └── adapter
│       └── UserIdentityAdapterIT
└── app
    └── OrderFlowIT
```

命名建议：
- 单元测试：`*Test`
- 集成测试：`*IT`

## 常见反模式

1. **用 controller 测试兜底领域规则**
   - 结果：测试慢、定位差、规则保护不稳定

2. **默认所有 controller 测试都起 `@SpringBootTest`**
   - 结果：测试沉重且维护成本高

3. **Application / Service 测试里大量 mock mapper**
   - 结果：边界混乱，测试高度耦合实现细节

4. **Repository 没有任何集成测试**
   - 结果：SQL、映射、索引、事务问题要到联调甚至线上才暴露

5. **全部依赖 `verify(...)`，几乎没有状态断言**
   - 结果：重构时测试脆弱，无法真正保护业务行为

## TDD 落地顺序

1. 先确定当前变化属于哪一层：`domain / application / trigger / infrastructure`
2. 先写该层最小失败测试
3. 明确失败原因正确，再写最小实现
4. 当前层通过后，再补受影响的相邻层测试
5. 涉及 SQL / 映射 / 外部协议变化时，补真实集成测试
6. 关键主流程最后补或回归少量 smoke test
