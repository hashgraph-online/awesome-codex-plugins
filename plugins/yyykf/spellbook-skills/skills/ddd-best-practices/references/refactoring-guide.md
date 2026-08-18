# MVC 到 DDD 渐进重构指南

## 目录

- [重构前评估](#重构前评估)
- [步骤零：确定目标分层](#步骤零确定目标分层)
- [步骤一：识别领域边界](#步骤一识别领域边界)
- [步骤二：建立最小结构](#步骤二建立最小结构)
- [步骤三：补关键测试](#步骤三补关键测试)
- [步骤四：封装仓储](#步骤四封装仓储)
- [步骤五：封装防腐层](#步骤五封装防腐层)
- [步骤六：重构领域模型](#步骤六重构领域模型)
- [步骤七：收紧 Trigger 与编排层](#步骤七收紧-trigger-与编排层)
- [步骤八：按需引入领域事件](#步骤八按需引入领域事件)
- [渐进式策略](#渐进式策略)

## 重构前评估

**适合重构的信号**：
- Service 类膨胀，单类职责混杂
- DAO / Mapper / 外部客户端散落在多个 Service / Controller 中
- 新需求开发需要频繁修改多个不相关类
- 业务规则难以测试，回归风险高

**不建议大动干戈的情况**：
- 项目规模很小且即将下线
- 团队尚未能维护最基本的分层纪律
- 当前更紧急的问题是稳定性/交付，而不是结构演进

## 步骤零：确定目标分层

先决定你真正需要的目标结构，而不是默认上全套模块。

- 大多数项目先从 `types / domain / infrastructure / trigger / app` 开始
- 当用例编排膨胀时，再增加 `application`
- 当需要对外契约复用时，再增加 `api`
- 当读写分离真实出现时，再增加 `querys`

参见：[project-structure.md](project-structure.md)、[layering-decision-matrix.md](layering-decision-matrix.md)

## 步骤一：识别领域边界

1. 列出现有 Service / Controller / 定时任务 / MQ 消费者
2. 标注它们各自承载的业务职责
3. 将职责相近的能力归为同一限界上下文

**示例**：
```text
MVC 服务列表：
- UserService
- OrderService
- PaymentService
- ProductService
- CouponService

DDD 可能的子域：
- domain/user/
- domain/order/        # 可包含支付编排或订单支付相关规则
- domain/product/
- domain/marketing/
```

## 步骤二：建立最小结构

1. 创建最小必要模块/目录
2. 把公共异常、枚举、返回模型迁到 `types`
3. 把 Controller / Listener / Job 迁到 `trigger`
4. 把 Mapper / DAO / 外部网关迁到 `infrastructure`
5. 把业务规则、仓储接口、Port 接口迁到 `domain`

**原则**：
- 先把依赖方向做对
- 不急着拆 `application / api / querys`
- 不急着上聚合、事件、复杂模式

## 步骤三：补关键测试

在继续深度重构前，优先补测试保护这些规则：
- 唯一性校验
- 只读/状态流转限制
- 权限/认证成功与失败
- 密钥/签名匹配
- 运行态重载或配置刷新编排

**建议**：
- 优先写 `domain service` 单元测试
- 用 [testing-strategy.md](testing-strategy.md) 明确哪些测试应落在 `domain / application / trigger / infrastructure`
- 不要一开始就依赖重型集成测试保护结构改造

## 步骤四：封装仓储

**Before**：
```java
@Service
public class OrderService {
    @Autowired
    private OrderMapper orderMapper;

    public OrderVO getOrder(Long id) {
        OrderPO po = orderMapper.selectById(id);
        // 转换...
    }
}
```

**After**：
```java
public interface IOrderRepository {
    Optional<OrderEntity> findByOrderId(String orderId);
    void save(OrderEntity entity);
}

public class OrderDomainService {
    private final IOrderRepository orderRepository;

    public OrderDomainService(IOrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }
}
```

**关键点**：
- 仓储接口放 `domain`
- 仓储实现放 `infrastructure`
- 不把缓存刷新/失效语义暴露到领域接口

## 步骤五：封装防腐层

**Before**：
```java
@Service
public class OrderService {
    @Autowired
    private ThirdPartyPaymentClient paymentClient;
}
```

**After**：
```java
public interface IPaymentPort {
    PaymentResult processPayment(String orderId, BigDecimal amount);
}
```

**关键点**：
- Port 返回领域语义对象，而不是外部 DTO
- Adapter 负责 DTO 转换、异常语义转换、重试/降级细节

## 步骤六：重构领域模型

从最关键的不变量开始，而不是一上来追求“大而全”的聚合建模。

**Before（贫血）**：
```java
public class ConfigVO {
    private Long id;
    private String value;
    private Boolean readonly;
}
```

**After（补行为）**：
```java
@Value
@Builder(toBuilder = true)
public class ConfigEntity {
    Long id;
    String value;
    Boolean readonly;

    public void assertWritable() {
        if (Boolean.TRUE.equals(readonly)) {
            throw new BusinessException("只读配置不可修改");
        }
    }

    public ConfigEntity updateValue(String nextValue) {
        assertWritable();
        return toBuilder().value(nextValue).build();
    }
}
```

## 步骤七：收紧 Trigger 与编排层

**重点检查**：
- Controller 是否还在直接依赖 Repository / Mapper
- Trigger 是否还在直接操作缓存、PO、外部客户端
- 是否已有多个入口在重复同一段业务编排

**改造策略**：
- 简单场景：`trigger -> domain service`
- 编排膨胀场景：`trigger -> application/usecase -> domain`

**不要**因为引入了 `application`，就把业务规则从 `domain` 挪空；`application` 只负责编排。

## 步骤八：按需引入领域事件

当出现“跨聚合一致性 / 异步通知 / 读模型投影”的真实需求时，再引入领域事件。

**不要过早引入的信号**：
- 只是单聚合 CRUD
- 当前最大问题仍然是边界绕过、DTO 穿透、缺测试

## 渐进式策略

1. **先边界，后模式**：先修依赖方向和边界绕过
2. **先测试，后充血**：没有测试，不要大规模搬规则
3. **先收紧，再补层**：先把 Repository / ACL / Trigger 关系理顺
4. **先真实复杂度，再高级结构**：`application / api / querys / event` 都按信号引入
5. **保持系统持续可运行**：每轮改造都要能编译、能验证、能回滚
