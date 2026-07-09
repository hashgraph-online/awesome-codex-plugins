# DDD 领域建模指南

## 目录

- [实体（Entity）](#实体entity)
- [值对象（Value Object）](#值对象value-object)
- [聚合（Aggregate）](#聚合aggregate)
- [仓储（Repository）](#仓储repository)
- [防腐层端口（Port / Adapter）](#防腐层端口port--adapter)
- [领域事件（Domain Event）](#领域事件domain-event)
- [领域服务（Domain Service）](#领域服务domain-service)
- [充血模型](#充血模型)
- [速查模板](#速查模板)
- [初始化阶段的建模克制](#初始化阶段的建模克制)

## 实体（Entity）

**定义**：具有唯一标识、需要被持续追踪的领域对象。

**建议**：
- 有唯一业务标识（如 `orderId`、`userId`、`configId`）
- 除了属性，还应尽量承载关键业务行为
- 避免把实体设计成“公开 setter 的数据袋”
- 可以是可变对象，也可以是不可变快照；关键是**不变量要靠近对象本身**

**Lombok 建议**：
- 简单实体可使用 `@Value + @Builder(toBuilder = true)`
- 或使用 `@Getter + 显式行为方法`
- 不推荐默认用 `@Data` 把 setter 全放开

**示例**：
```java
@Value
@Builder(toBuilder = true)
public class DictionaryEntity {
    Long id;
    String parentCode;
    String code;
    String value;
    String remark;
    Boolean readonly;

    public void assertWritable() {
        if (Boolean.TRUE.equals(readonly)) {
            throw new BusinessException("该配置为只读，不可修改");
        }
    }

    public DictionaryEntity updateValue(String nextValue, String nextRemark) {
        assertWritable();
        return toBuilder()
                .value(nextValue)
                .remark(nextRemark)
                .build();
    }
}
```

**判断依据**：问自己“这个对象需要唯一标识来追踪吗？”——如果是，优先考虑实体。

## 值对象（Value Object）

**定义**：无唯一标识、通过值相等、用于表达状态/属性/概念的对象。

**特征**：
- 不可变
- 无 setter
- 可复用
- 可用枚举或不可变类表示

**枚举值对象示例**：
```java
@Getter
@AllArgsConstructor
public enum OrderStateVO {
    CREATED("created", "已创建"),
    PAID("paid", "已支付"),
    COMPLETED("completed", "已完成");

    private final String code;
    private final String desc;
}
```

**复杂值对象示例**：
```java
@Value
@Builder
public class UserRole {
    String code;
    String name;
}
```

**判断依据**：问自己“它是在描述一个状态/属性/概念，而不是一个可独立追踪的对象吗？”——如果是，优先考虑值对象。

## 聚合（Aggregate）

**定义**：一组需要在同一事务边界内保持一致的领域对象集合。

**核心规则**：
- 聚合内：事务一致性
- 聚合间：最终一致性（必要时通过领域事件）
- 外部通过聚合根访问聚合内部对象

**聚合 vs 聚合根**：

很多人把 `XxxAggregate` 当成「装一组对象的 DTO」，这是误区。准确语义是：

- **聚合根（Aggregate Root）**：是一个**实体**，承载身份与核心业务行为（如 `OrderEntity`）
- **聚合（Aggregate）**：是聚合根 + 它管理的所有内部对象（OrderItem、Address 等）的**整体**

工程上有两种表达方式，二选一即可：

1. **聚合根直接持有内部对象**（DDD 主流派）：
   ```java
   public class OrderEntity {  // 同时是聚合根
       private List<OrderItemEntity> items;
       private AddressVO address;

       public BigDecimal calculateTotal() { ... }
       public void addItem(OrderItemEntity item) { ... }
   }
   ```
   仓储直接 `findById` 返回 `OrderEntity`，外部通过 `order.getItems()` 受控访问。

2. **聚合作为装载视图**（xfg 风格 / 国内常见）：
   ```java
   public class OrderAggregate {  // 不是实体，是装载结构
       private OrderEntity order;  // ← 聚合根在里面
       private List<OrderItemEntity> items;
   }
   ```
   这种写法下，**外部只读访问聚合内对象**，所有变更必须经过聚合根 `OrderEntity` 的方法。

**注意**：
- 不是每个子域都必须先建一个 Aggregate
- 只有当你已经识别出"这些对象必须同事务变更"时，再引入聚合更合适
- **不要把 Aggregate 当 DTO**：它不是「把几个 Entity 打包传输」，而是「事务边界 + 一致性边界」的领域概念

**示例（装载视图风格）**：
```java
@Value
@Builder
public class CreateOrderAggregate {
    OrderEntity order;             // 聚合根
    List<OrderItemEntity> items;
    PaymentEntity payment;
}
```

**边界划分问题**：
1. 哪些对象必须同一事务成功或失败？
2. 哪些对象可以接受延迟一致？

## 仓储（Repository）

**定义**：封装持久化访问的领域接口，由 `domain` 定义，由 `infrastructure` 实现。

**接口设计原则**：
- 方法名体现业务语义
- 不暴露缓存、索引、DB 方言等技术细节
- `PO ↔ Entity` 转换放在实现中

**推荐接口示例**：
```java
public interface IOrderRepository {
    Optional<OrderEntity> findByOrderId(String orderId);
    void save(OrderEntity entity);
    List<OrderEntity> findByUserAndState(String userId, OrderStateVO state);
}
```

**关键约束**：

- `save(entity)` 走全量保存（领域行为已在实体内完成状态变更），实现层负责拆 INSERT / UPDATE
- 不在仓储接口上暴露 `updateState / updateStatus / updateXxx` 这类纯字段更新方法 —— 它们会让调用方绕过实体不变量直接改字段
- 状态变化必须通过：`entity.pay()` / `entity.cancel()` / `entity.complete()` 等领域行为 → `repository.save(entity)`

**避免的接口示例**：
```java
public interface IOrderRepository {
    void refreshCache();
    void evictCache(String orderId);
    void cacheOrderStock(String cacheKey, Integer stock);
}
```

**实现层建议**：
- 可以在仓储实现中自行完成 `Redis -> DB -> 回写 Redis`
- 也可以组合缓存组件，但**不要把技术动作上提到领域接口**

**映射建议**：
- 简单同构映射可使用 MapStruct
- 涉及语义转换、值对象组装、部分更新时优先手写

## 防腐层端口（Port / Adapter）

**定义**：隔离外部系统依赖，防止外部变化直接污染领域。

**Port 接口（domain）建议返回领域语义对象**：
```java
public interface IUserIdentityPort {
    String getUserIdByToken(String accessToken);
    UserIdentity getUserInfoById(String userId);
}
```

**Adapter（infrastructure）负责做 DTO 转换**：
```java
public class UserIdentityAdapter implements IUserIdentityPort {
    private final UserCenterClient userCenterClient;

    @Override
    public UserIdentity getUserInfoById(String userId) {
        UserInfoDTO dto = userCenterClient.queryUser(userId);
        return UserIdentity.builder()
                .id(dto.getUserId())
                .nickname(dto.getNickname())
                .mobile(dto.getMobile())
                .build();
    }
}
```

**与 Repository 的区别**：
- Repository：封装本域持久化访问
- Port：封装外部系统访问

## 领域事件（Domain Event）

**定义**：有明确业务意义的事件，用于表达“领域中已经发生了什么”。

**设计原则**：
- 事件对象本身应保持 Plain Java，不依赖 MQ/框架注解
- 发布能力通过接口抽象
- 具体 MQ / Task 表 / Outbox 实现在 infrastructure / application

**事件对象示例**：
```java
@Value
@Builder
public class OrderCreatedEvent {
    String orderId;
    String userId;
    BigDecimal totalAmount;
    Instant occurredAt;
}
```

**发布接口示例**：
```java
public interface IDomainEventPublisher {
    void publish(Object event);
}
```

**可靠投递常见模式**：
1. 业务操作 + 写本地消息/Task 表（同一事务）
2. 异步任务扫描并投递消息
3. 消费端完成下游逻辑

## 领域服务（Domain Service）

**定义**：承载不适合放进单个实体/值对象，但仍属于领域规则的逻辑。

**设计要点**：
- 保持无状态
- 只依赖 Repository / Port 接口
- 本身保持 Plain Java，不在 `domain` 中加 Spring 注解
- Bean 装配放到 `app` / `application`

**示例**：
```java
public class AuthDomainService {
    private final IUserIdentityPort userIdentityPort;
    private final IPermissionPort permissionPort;

    public AuthDomainService(IUserIdentityPort userIdentityPort,
                             IPermissionPort permissionPort) {
        this.userIdentityPort = userIdentityPort;
        this.permissionPort = permissionPort;
    }

    public AuthenticatedUser authenticate(String accessToken) {
        // 领域认证逻辑
    }
}
```

## 充血模型

**目标**：把对象的属性与关键行为收拢在一起，而不是让 Service 独占全部规则。

**优先顺序**：
1. 先把关键不变量放进 Entity / VO
2. 再让领域服务协调多个对象
3. 只有规则复杂到明显分支化时，再上策略 / 责任链 / 决策树

**常见信号**：
- 若“只读不可改”“状态不可逆”“密钥必须匹配”都在 Service 里 → 模型偏贫血
- 若 Entity 只是 getter/setter → 需要考虑补行为

## 速查模板

> 这一节是**落地速查**，给出领域层各类对象的标准代码骨架，可直接拷贝改写。
>
> **风格选择**：默认推荐**不可变 + `@Value + @Builder(toBuilder=true)`**，仅在确实需要 ORM 反射构造、JSON 反序列化默认无参构造或运行时大量改字段时，才退化到可变的 `@Data + @Builder + @AllArgsConstructor + @NoArgsConstructor`。

### Entity 模板（不可变 / 推荐）

```java
package com.example.domain.order.model.entity;

import com.example.domain.order.model.valobj.OrderStateVO;
import com.example.types.exception.BusinessException;
import lombok.Builder;
import lombok.Value;

import java.math.BigDecimal;

/**
 * 订单实体（不可变充血模型）
 */
@Value
@Builder(toBuilder = true)
public class OrderEntity {

    String orderId;
    String userId;
    BigDecimal totalAmount;
    OrderStateVO state;

    /** 业务行为：支付 */
    public OrderEntity pay() {
        if (state != OrderStateVO.CREATED) {
            throw new BusinessException("订单状态不允许支付");
        }
        return toBuilder().state(OrderStateVO.PAID).build();
    }

    /** 业务行为：取消 */
    public OrderEntity cancel() {
        if (state == OrderStateVO.PAID) {
            throw new BusinessException("已支付订单不可取消");
        }
        return toBuilder().state(OrderStateVO.CANCELED).build();
    }

    /** 业务断言 */
    public boolean canRefund() {
        return state == OrderStateVO.PAID;
    }
}
```

### Entity 模板（可变 / 退化版本）

仅在以下场景使用可变实体：
- ORM 反射构造（MyBatis 自动映射）
- 项目历史代码大量使用 `@Data`，新代码风格需要保持一致

```java
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class OrderEntity {

    private String orderId;
    private String userId;
    private BigDecimal totalAmount;
    private OrderStateVO state;

    /** 即使可变，关键行为仍然要写在实体上，避免贫血 */
    public void pay() {
        if (state != OrderStateVO.CREATED) {
            throw new BusinessException("订单状态不允许支付");
        }
        this.state = OrderStateVO.PAID;
    }

    public boolean canRefund() {
        return state == OrderStateVO.PAID;
    }
}
```

### CommandEntity 模板

**命令实体（CommandEntity）** 表达「外部要求领域执行某个动作」的请求快照，常用于责任链 / 流程节点的输入。

放在 `model/entity/` 包下，**不要**单独建 `command/` 子包（避免目录碎片）。

```java
@Value
@Builder
public class CreateOrderCommandEntity {
    String userId;
    Long activityId;
    String teamId;
    Integer quantity;
}
```

### ValueObject 模板（普通值对象）

```java
@Value
@Builder
public class Money {
    BigDecimal amount;
    String currency;

    public Money add(Money other) {
        if (!currency.equals(other.currency)) {
            throw new BusinessException("币种不一致，无法相加");
        }
        return Money.builder()
                .amount(amount.add(other.amount))
                .currency(currency)
                .build();
    }
}
```

### ValueObject 模板（枚举值对象）

```java
@Getter
@AllArgsConstructor
public enum OrderStateVO {

    CREATED("created", "已创建"),
    PAID("paid", "已支付"),
    CANCELED("canceled", "已取消"),
    COMPLETED("completed", "已完成");

    private final String code;
    private final String desc;

    public static OrderStateVO fromCode(String code) {
        return Arrays.stream(values())
                .filter(v -> v.code.equals(code))
                .findFirst()
                .orElseThrow(() -> new BusinessException("无效的订单状态码：" + code));
    }
}
```

### Aggregate 模板

```java
package com.example.domain.order.model.aggregate;

import com.example.domain.order.model.entity.OrderEntity;
import com.example.domain.order.model.entity.OrderItemEntity;
import com.example.domain.order.model.valobj.AddressVO;
import lombok.Builder;
import lombok.Value;

import java.math.BigDecimal;
import java.util.List;

/**
 * 订单聚合：订单主体 + 订单项 + 收货地址
 *
 * 聚合根 = OrderEntity；外部只能通过聚合访问 items / address。
 */
@Value
@Builder
public class OrderAggregate {

    OrderEntity order;
    List<OrderItemEntity> items;
    AddressVO address;

    /** 聚合内的一致性规则：总金额 = 各订单项金额之和 */
    public BigDecimal calculateTotal() {
        return items.stream()
                .map(OrderItemEntity::getSubtotal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    public void assertValid() {
        if (items.isEmpty()) {
            throw new BusinessException("订单不能为空");
        }
        if (!order.getTotalAmount().equals(calculateTotal())) {
            throw new BusinessException("订单总金额与订单项不一致");
        }
    }
}
```

### Repository 接口模板（domain 层）

```java
package com.example.domain.order.repository;

import com.example.domain.order.model.aggregate.OrderAggregate;
import com.example.domain.order.model.entity.OrderEntity;
import com.example.domain.order.model.valobj.OrderStateVO;

import java.util.List;
import java.util.Optional;

/**
 * 订单仓储接口
 *
 * 注意：
 * - 接口方法体现业务语义，不暴露 Redis / 缓存刷新等技术动作
 * - 返回领域对象（Entity / Aggregate），不返回 PO
 */
public interface IOrderRepository {

    Optional<OrderEntity> findByOrderId(String orderId);

    OrderAggregate findAggregateByOrderId(String orderId);

    /**
     * 保存（新增或全量更新）。
     *
     * 注意：仓储接口不暴露 updateState / updateXxx 这类技术语义方法。
     * 状态变化必须通过实体行为（如 OrderEntity.pay()）+ save() 完成，
     * 这样不变量始终被实体守住，无法绕过。
     */
    void save(OrderEntity entity);

    void saveAggregate(OrderAggregate aggregate);

    List<OrderEntity> findByUserAndState(String userId, OrderStateVO state);
}
```

### Port 接口模板（domain 层）

```java
package com.example.domain.order.port;

import com.example.domain.order.model.valobj.PaymentResult;

/**
 * 支付端口：对接外部支付网关
 *
 * 注意：
 * - 返回领域语义对象（PaymentResult），不返回外部 SDK 响应
 * - 入参也用领域类型，不用外部 DTO
 */
public interface IPaymentPort {

    PaymentResult charge(String orderId, java.math.BigDecimal amount);

    PaymentResult refund(String orderId, java.math.BigDecimal amount);
}
```

### Domain Service 接口与实现模板

**接口（domain 层 / Plain Java）**：

```java
package com.example.domain.order.service;

import com.example.domain.order.model.entity.CreateOrderCommandEntity;
import com.example.domain.order.model.entity.OrderEntity;

public interface IOrderDomainService {

    OrderEntity createOrder(CreateOrderCommandEntity command);

    OrderEntity payOrder(String orderId);

    OrderEntity cancelOrder(String orderId);
}
```

**实现（domain 层保持 Plain Java；@Service 装配交给 application/app）**：

```java
package com.example.domain.order.service.impl;

import com.example.domain.order.model.entity.CreateOrderCommandEntity;
import com.example.domain.order.model.entity.OrderEntity;
import com.example.domain.order.model.valobj.OrderStateVO;
import com.example.domain.order.repository.IOrderRepository;
import com.example.domain.order.service.IOrderDomainService;

/**
 * 默认订单领域服务实现
 *
 * 注意：
 * - 这里不打 @Service，由 app/application 模块的 @Configuration 装配为 Bean
 * - 依赖通过构造器注入，便于纯单元测试
 */
public class OrderDomainService implements IOrderDomainService {

    private final IOrderRepository orderRepository;

    public OrderDomainService(IOrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    @Override
    public OrderEntity createOrder(CreateOrderCommandEntity command) {
        OrderEntity entity = OrderEntity.builder()
                .orderId(generateOrderId())
                .userId(command.getUserId())
                .state(OrderStateVO.CREATED)
                .build();
        orderRepository.save(entity);
        return entity;
    }

    @Override
    public OrderEntity payOrder(String orderId) {
        OrderEntity order = orderRepository.findByOrderId(orderId)
                .orElseThrow(() -> new BusinessException("订单不存在"));
        OrderEntity paid = order.pay();
        orderRepository.save(paid);
        return paid;
    }

    @Override
    public OrderEntity cancelOrder(String orderId) {
        OrderEntity order = orderRepository.findByOrderId(orderId)
                .orElseThrow(() -> new BusinessException("订单不存在"));
        OrderEntity canceled = order.cancel();
        orderRepository.save(canceled);
        return canceled;
    }

    private String generateOrderId() {
        return java.util.UUID.randomUUID().toString().replace("-", "");
    }
}
```

**装配（app 层）**：

```java
@Configuration
public class DomainServiceConfig {

    @Bean
    public IOrderDomainService orderDomainService(IOrderRepository orderRepository) {
        return new OrderDomainService(orderRepository);
    }
}
```

### 退化版本：domain 直接打 Spring 注解

如果团队已经接受 Spring 作为领域层基础设施（不打算把 domain 移植到非 Spring 环境），可以退化为：

```java
@Service
@RequiredArgsConstructor
public class OrderDomainService implements IOrderDomainService {

    private final IOrderRepository orderRepository;

    // ... 同上
}
```

**取舍**：
- **保持 Plain Java**：可移植性好、可纯单测、与框架解耦；代价是多写一份 `@Configuration`
- **直接打 `@Service`**：写起来快、对齐 xfg 风格；代价是 domain 模块对 Spring 强依赖

**默认推荐保持 Plain Java**，除非项目已有强约定或团队对 Spring 强依赖无异议。

### 五件套 vs 三件套

「五件套」= `model/{aggregate, entity, valobj}` + `service` + `repository` + `port` + `event`

并不是每个子域一开始都需要五件套：

| 复杂度 | 建议 |
|---|---|
| 简单 CRUD 子域 | `model/entity` + `service` + `repository`（三件套足够） |
| 中等复杂度 | + `valobj`（需要值对象表达概念时）+ `port`（有外部依赖时） |
| 高复杂度 | + `aggregate`（明确事务边界时）+ `event`（跨聚合一致性时） |

不要为了「标准 DDD 结构」预埋大量空目录。

## 初始化阶段的建模克制

在初始化阶段，以下做法通常更稳妥：
- 不强求每个子域都有 `aggregate / event / policy`
- 不为了“标准 DDD 结构”预埋大量空目录
- 先把边界做对，把核心规则表达清楚
- 复杂性真实出现后，再补聚合、事件、application、querys
