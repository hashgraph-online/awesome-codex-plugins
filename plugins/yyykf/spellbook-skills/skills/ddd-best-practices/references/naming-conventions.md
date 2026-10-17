# DDD 命名规范速查

> 这份文档是**命名规范的单一来源**。所有模板、审查清单中涉及的命名都以这里为准。
>
> 风格约定：保持 `application` / `UseCase` / `ApplicationService` 命名（经典 DDD 标准术语），不强制要求 xfg 风格的 `case` / `Case`。

## 目录

- [包命名](#包命名)
- [类命名](#类命名)
- [接口命名](#接口命名)
- [方法命名](#方法命名)
- [变量命名](#变量命名)
- [数据库命名](#数据库命名)
- [文件命名](#文件命名)
- [常见反模式](#常见反模式)

## 包命名

### 顶层包路径

```
{group}.{artifact-suffix}
```

例：
- `com.example.order.types` （types 模块）
- `com.example.order.domain.order` （domain 模块下的 order 子域）
- `com.example.order.infrastructure.adapter.repository`
- `com.example.order.application.order.usecase`
- `com.example.order.trigger.http.controller`

### 各层包路径模板

| 层 | 包路径模板 | 示例 |
|---|---|---|
| Types | `{group}.types.{kind}` | `com.example.types.exception` |
| Domain | `{group}.domain.{context}.{kind}` | `com.example.domain.order.model.entity` |
| Application | `{group}.application.{context}.{kind}` | `com.example.application.order.usecase` |
| Infrastructure | `{group}.infrastructure.{kind}` | `com.example.infrastructure.adapter.repository` |
| Trigger | `{group}.trigger.{kind}` | `com.example.trigger.http.controller` |

### Domain 子包

| 子包 | 用途 |
|---|---|
| `model.entity` | 实体（含 CommandEntity） |
| `model.valobj` | 值对象（含 EnumVO） |
| `model.aggregate` | 聚合（按需引入） |
| `model.event` | 领域事件（按需引入） |
| `service` | 领域服务接口与实现 |
| `repository` | 仓储接口 |
| `port` | 端口接口 |

### Infrastructure 子包

| 子包 | 用途 |
|---|---|
| `adapter.repository` | Repository 实现 |
| `adapter.port` | Port Adapter 实现 |
| `dao` | DAO 接口 |
| `dao.po` | 持久化对象 |
| `gateway` | HTTP/RPC 客户端 |
| `gateway.dto` | 远程调用 DTO |
| `redis` | Redis 操作封装 |
| `event` | 事件投递实现 |
| `config` | 框架配置类 |

## 类命名

| 类型 | 命名模式 | 示例 |
|---|---|---|
| 实体 | `{Domain}Entity` | `OrderEntity` |
| 命令实体 | `{Action}{Domain}CommandEntity` | `CreateOrderCommandEntity` |
| 值对象 | `{Concept}` 或 `{Concept}VO` | `Money`, `OrderStateVO` |
| 枚举值对象 | `{Concept}EnumVO` 或 `{Concept}VO` | `OrderStateVO`, `RefundTypeEnumVO` |
| 聚合 | `{Domain}Aggregate` | `OrderAggregate` |
| 领域服务实现 | `{Domain}DomainService` 或 `{Domain}Service`（domain 包内） | `OrderDomainService` |
| 用例 / 应用服务 | `{Action}{Domain}UseCase` 或 `{Domain}ApplicationService` | `CreateOrderUseCase` |
| 仓储实现 | `{Domain}Repository` | `OrderRepository` |
| 端口适配器 | `{ExternalSystem}Adapter` 或 `{ExternalSystem}Port` | `PaymentAdapter` |
| 持久化对象 | `{Domain}PO` | `OrderPO` |
| DAO 接口 | `I{Domain}Dao` | `IOrderDao` |
| Gateway 客户端 | `{ExternalSystem}Gateway` | `PaymentGateway` |
| 远程调用 DTO | `{Action}RequestDTO` / `{Action}ResponseDTO` | `PayRequestDTO`, `PayResponseDTO` |
| Controller | `{Domain}Controller` | `OrderController` |
| Listener | `{Event}Listener` | `OrderPaidListener` |
| Job | `{Domain}{Action}Job` | `OrderTimeoutJob` |
| HTTP Request | `{Action}{Domain}Request` | `CreateOrderRequest` |
| HTTP Response | `{Domain}Response` | `OrderResponse` |
| 异常 | `{Kind}Exception` | `BusinessException`, `ExternalException` |
| 配置类 | `{Subject}Config` | `MybatisConfig`, `RedisConfig` |

### 设计模式相关命名

| 类型 | 命名模式 | 示例 |
|---|---|---|
| 策略接口 | `I{Domain}Strategy` | `IRefundOrderStrategy` |
| 策略实现 | `{Variant}{Domain}Strategy` | `Paid2RefundStrategy` |
| 策略抽象基类 | `Abstract{Domain}Strategy` | `AbstractRefundOrderStrategy` |
| 策略分发器 | `{Domain}StrategyDispatcher` | `RefundStrategyDispatcher` |
| 责任链节点接口 | `ILogicChain` 或 `I{Domain}Filter` | `ILogicChain`, `ITradeRuleFilter` |
| 责任链节点实现 | `{Rule}LogicChain` 或 `{Rule}Filter` | `BlackListLogicChain` |
| 责任链工厂 | `{Domain}ChainFactory` | `LogicChainFactory` |
| 流程节点接口 | `IFlowNode` 或 `I{Domain}Node` | `IFlowNode` |
| 流程节点实现 | `{Step}Node` | `ValidateUserNode`, `LockStockNode` |
| 流程引擎 | `FlowEngine` 或 `{Domain}FlowEngine` | `FlowEngine` |
| 决策树节点 | `{Rule}LogicTreeNode` | `RuleStockLogicTreeNode` |

## 接口命名

**统一约定：领域层接口加 `I` 前缀**，便于与实现类区分。

| 接口类型 | 命名模式 | 示例 |
|---|---|---|
| 仓储接口 | `I{Domain}Repository` | `IOrderRepository` |
| 端口接口 | `I{ExternalSystem}Port` | `IPaymentPort` |
| 领域服务接口 | `I{Domain}DomainService` 或 `I{Domain}Service` | `IOrderDomainService` |
| DAO 接口 | `I{Domain}Dao` | `IOrderDao` |
| 策略接口 | `I{Domain}Strategy` | `IRefundOrderStrategy` |
| 责任链接口 | `ILogicChain` / `I{Domain}Filter` | `ILogicChain` |
| 流程节点接口 | `IFlowNode` 或 `I{Domain}Node` | `IFlowNode` |

**例外**：trigger 层的 Controller、Listener、Job 一般不写接口（它们就是入口实现，没有解耦需求）。

## 方法命名

### 仓储 / DAO 方法

| 操作 | 命名 | 示例 |
|---|---|---|
| 单条查询（按主键） | `findById` / `findByXxx` | `findByOrderId` |
| 单条查询（必返回，找不到抛异常） | `getByXxx` | `getByOrderId` |
| 列表查询 | `findByXxx` / `listByXxx` | `findByUserAndState` |
| 分页查询 | `findPage` / `queryPage` | `findPageByUser` |
| 新增 | `save` / `insert` | `save` |
| 更新（全量） | `update` / `save` | `update` |
| 更新（部分字段，仅 DAO 层） | `update{Field}` | `updateRemark`（仅出现在 `IXxxDao`，不出现在 `IXxxRepository`） |
| 删除 | `delete` / `remove` | `deleteById` |

> ⚠️ 仓储接口 `IXxxRepository` **不暴露** `update{Field}` 这类部分字段更新方法（它会让调用方绕过领域行为直接改字段，破坏不变量）。状态变化走「实体行为 + save」。详见 [boundary-smells.md](boundary-smells.md) §1。
| 计数 | `count` / `countByXxx` | `countByUser` |
| 存在性检查 | `exists` / `existsByXxx` | `existsByOrderId` |

### 领域行为方法

| 类别 | 命名 | 示例 |
|---|---|---|
| 状态变更 | 业务动词 | `pay()`, `cancel()`, `complete()` |
| 校验 | `validate` / `check` / `assertXxx` | `assertWritable()`, `validate()` |
| 状态判断 | `isXxx` / `canXxx` / `hasXxx` | `isPaid()`, `canRefund()`, `hasItems()` |
| 转换 | `toXxx` / `from` | `toEntity()`, `fromCode()` |
| 计算 | `calculateXxx` / `compute` | `calculateTotal()` |

### 用例 / 应用服务方法

```java
// 推荐：动词 + 名词
public OrderEntity createOrder(...);
public OrderEntity payOrder(...);
public void cancelOrder(...);

// 单一职责的 UseCase 用 execute()
public class CreateOrderUseCase {
    public OrderEntity execute(CreateOrderCommandEntity command) { }
}
```

### Controller 方法

```java
// REST 风格：HTTP 动词 + 资源
@PostMapping public Response<OrderResponse> create(...);     // POST /order
@GetMapping("/{id}") public Response<OrderResponse> get(...); // GET /order/{id}
@PutMapping("/{id}") public Response<Void> update(...);       // PUT /order/{id}
@DeleteMapping("/{id}") public Response<Void> delete(...);    // DELETE /order/{id}
```

## 变量命名

### 实体 / 值对象 / 聚合变量

| 类型 | 命名 | 示例 |
|---|---|---|
| 实体变量 | `{domain}Entity` 或 `{domain}` | `orderEntity` / `order` |
| 命令实体变量 | `{action}{Domain}Command` | `createOrderCommand` |
| 值对象变量 | `{concept}` 或 `{concept}VO` | `money`, `orderStateVO` |
| 聚合变量 | `{domain}Aggregate` | `orderAggregate` |
| PO 变量 | `{domain}PO` 或 `{domain}` | `orderPO` |

### 集合命名

```java
List<OrderEntity> orders;          // ✅ 复数
List<OrderEntity> orderList;       // ✅ 加 List 后缀
Map<String, OrderEntity> orderMap; // ✅ 加 Map 后缀
Set<String> orderIdSet;            // ✅ 加 Set 后缀

List<OrderEntity> order;           // ❌ 单复不符
```

### 缓存键 / 常量

```java
private static final String CACHE_KEY_ORDER = "order:%s";
private static final Duration CACHE_TTL = Duration.ofMinutes(30);
private static final int MAX_RETRY = 3;

// 字符串常量大写下划线
public static final String STATE_CREATED = "created";
```

## 数据库命名

### 表名

```
{domain}_{entity}
```

**全部小写、下划线分隔、单数形式**。

| 业务 | 表名 |
|---|---|
| 订单 | `order` 或 `trade_order` |
| 用户账号 | `user_account` |
| 拼团活动 | `group_buy_activity` |
| 优惠券 | `marketing_coupon` |

**保留字**：避免使用 SQL 保留字作为表名（如 `order` 在 MySQL 中需要反引号）。可加业务前缀：`trade_order`, `pay_order`。

### 列名

**全部小写、下划线分隔**：

```sql
CREATE TABLE `trade_order` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT,
    `order_id`        VARCHAR(64)  NOT NULL,
    `user_id`         VARCHAR(64)  NOT NULL,
    `total_amount`    DECIMAL(10,2) NOT NULL,
    `state`           VARCHAR(32)  NOT NULL,
    `create_time`     DATETIME     NOT NULL,
    `update_time`     DATETIME     NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_id` (`order_id`),
    KEY `idx_user_state` (`user_id`, `state`)
);
```

### 索引

| 类型 | 命名 | 示例 |
|---|---|---|
| 主键 | `pk_{table}` | `pk_trade_order` |
| 唯一索引 | `uk_{column}` | `uk_order_id` |
| 普通索引 | `idx_{column1}_{column2}` | `idx_user_state` |

### 通用列

每张业务表建议都包含：

```sql
`id`           BIGINT      NOT NULL AUTO_INCREMENT  -- 物理主键
`create_time`  DATETIME    NOT NULL                 -- 创建时间
`update_time`  DATETIME    NOT NULL                 -- 更新时间
-- 软删除（按需）
`is_deleted`   TINYINT(1)  NOT NULL DEFAULT 0
```

**业务唯一标识与物理主键分开**：`id` 是 DB 自增主键，业务标识（`order_id`、`user_id`）作为唯一索引，便于分库分表与跨库迁移。

## 文件命名

### 项目模块名

```
{project-name}-{module}
```

例：
- `order-system-types`
- `order-system-domain`
- `order-system-infrastructure`
- `order-system-application`
- `order-system-trigger`
- `order-system-app`

### MyBatis Mapper XML

放在 `app/src/main/resources/mybatis/mapper/`：

```
{table_name}_mapper.xml
```

例：
- `trade_order_mapper.xml`
- `user_account_mapper.xml`

XML 内的 namespace 与 DAO 接口全限定名一致：

```xml
<mapper namespace="com.example.infrastructure.dao.IOrderDao">
```

### 配置文件

```
application.yml                    # 默认配置
application-dev.yml                # 开发环境
application-test.yml               # 测试环境
application-prod.yml               # 生产环境
```

### 测试类

| 测试类型 | 命名 | 示例 |
|---|---|---|
| 单元测试 | `{ClassUnderTest}Test` | `OrderEntityTest` |
| 集成测试 | `{ClassUnderTest}IT` | `OrderRepositoryIT` |
| 端到端测试 | `{Feature}SmokeIT` | `OrderFlowSmokeIT` |

## 常见反模式

下面这些命名会触发审查质疑，应避免：

### 1. 类名与职责不匹配

```java
// ❌ 名为 Service 但实际是数据搬运
class OrderService {
    public OrderPO getOrder(Long id) {
        return orderMapper.selectById(id);  // 直接返回 PO
    }
}

// ✅ 要么是 Repository（搬数据），要么是 Service（执行业务）
```

### 2. Controller 后缀的非 Controller 类

```java
// ❌ 名为 Controller 但不是 HTTP 入口
@Component
class OrderController {
    public void process(Order o) { ... }
}

// ✅ Controller 只用于 HTTP 入口
```

### 3. Repository 方法暴露技术语义

```java
// ❌
interface IOrderRepository {
    void refreshCache();
    void evictCache(String orderId);
    void cacheOrderStock(...);
}

// ✅
interface IOrderRepository {
    Optional<OrderEntity> findByOrderId(String orderId);
    void save(OrderEntity entity);
}
```

参见 [boundary-smells.md](boundary-smells.md) §1。

### 4. 方法名是 CRUD 而不是业务意图

```java
// ❌ 暴露技术动作
order.setState(OrderStateVO.PAID);
order.updateUserBalance(amount);

// ✅ 表达业务意图
order.pay();
account.charge(amount);
```

### 5. PO 与 Entity 命名混用

```java
// ❌ 容易混淆
public OrderEntity findById(Long id);  // 但实际返回的是 PO

// ✅ 命名匹配返回类型
public Optional<OrderPO> selectById(Long id);     // DAO 层
public Optional<OrderEntity> findByOrderId(String orderId);  // Repository 层
```

### 6. 包名出现 `util` / `helper` / `common` 黑洞

```text
domain/util/                ❌ 容易堆放与领域无关的工具
domain/helper/              ❌ 同上
infrastructure/common/      ❌ 边界不清

# 改成具体职责的包
domain/order/calculation/   ✅ 订单金额计算
infrastructure/cache/       ✅ 缓存抽象
```

### 7. 后缀堆叠

```java
// ❌ 后缀冗余
class OrderServiceImpl extends OrderServiceAbstract implements IOrderServiceInterface {}

// ✅ 简洁
class OrderService implements IOrderService {}
```

### 8. application 层用 Repository 后缀

```java
// ❌ 用例服务不是 Repository
class CreateOrderRepository {
    public OrderEntity execute(...) { }
}

// ✅
class CreateOrderUseCase {
    public OrderEntity execute(...) { }
}
```
