# DDD 落地代码模板速查

> 这份文档面向**快速落地**：当你已经决定好分层结构、要开始写代码时，按层拷贝模板改写。
>
> 模板对应的设计原则、决策依据请参见：
> - [domain-modeling.md](domain-modeling.md) — 领域建模指南
> - [project-structure.md](project-structure.md) — 包结构与模块依赖
> - [design-patterns.md](design-patterns.md) — 设计模式落地范式
> - [naming-conventions.md](naming-conventions.md) — 命名规范

## 目录

- [快速对照表](#快速对照表)
- [Domain 层模板](#domain-层模板)
- [Application 层模板](#application-层模板)
- [Infrastructure 层模板](#infrastructure-层模板)
- [Trigger 层模板](#trigger-层模板)
- [Types 层模板](#types-层模板)
- [端到端示例：订单创建-支付](#端到端示例订单创建-支付)

## 快速对照表

| 我要写什么 | 放哪个层 | 模板锚点 |
|---|---|---|
| 不可变实体 | domain/model/entity | [Entity（不可变）](#entity不可变推荐) |
| ORM 友好的实体 | domain/model/entity | [Entity（可变）](#entity可变退化版本) |
| 命令实体 | domain/model/entity | [CommandEntity](#commandentity) |
| 普通值对象 | domain/model/valobj | [ValueObject](#valueobject普通值对象) |
| 枚举值对象 | domain/model/valobj | [EnumVO](#valueobject枚举值对象) |
| 聚合 | domain/model/aggregate | [Aggregate](#aggregate) |
| 仓储接口 | domain/repository | [Repository 接口](#repository-接口domain-层) |
| 端口接口 | domain/port | [Port 接口](#port-接口domain-层) |
| 领域服务 | domain/service | [Domain Service](#domain-service) |
| 用例编排 | application（按需） | [UseCase](#usecase用例编排) |
| 仓储实现 | infrastructure/adapter/repository | [Repository 实现](#repository-实现infrastructure-层) |
| 端口实现 | infrastructure/adapter/port | [Port Adapter](#port-adapterinfrastructure-层) |
| MyBatis DAO | infrastructure/dao | [DAO + PO](#dao--po) |
| HTTP 客户端 | infrastructure/gateway | [Gateway](#gateway-+-dto) |
| Controller | trigger/http/controller | [Controller](#http-controller) |
| MQ 监听 | trigger/listener | [MQ Listener](#mq-listener) |
| 定时任务 | trigger/job | [Job](#scheduled-job) |
| 统一响应 | types/common | [Response](#response-统一响应) |
| 业务异常 | types/exception | [BusinessException](#businessexception) |

---

## Domain 层模板

### Entity（不可变 / 推荐）

```java
package com.example.domain.order.model.entity;

import com.example.domain.order.model.valobj.OrderStateVO;
import com.example.types.exception.BusinessException;
import lombok.Builder;
import lombok.Value;

import java.math.BigDecimal;

@Value
@Builder(toBuilder = true)
public class OrderEntity {

    String orderId;
    String userId;
    BigDecimal totalAmount;
    OrderStateVO state;

    public OrderEntity pay() {
        if (state != OrderStateVO.CREATED) {
            throw new BusinessException("订单状态不允许支付");
        }
        return toBuilder().state(OrderStateVO.PAID).build();
    }

    public OrderEntity cancel() {
        if (state == OrderStateVO.PAID) {
            throw new BusinessException("已支付订单不可取消");
        }
        return toBuilder().state(OrderStateVO.CANCELED).build();
    }

    public boolean canRefund() {
        return state == OrderStateVO.PAID;
    }
}
```

### Entity（可变 / 退化版本）

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

    public void pay() {
        if (state != OrderStateVO.CREATED) {
            throw new BusinessException("订单状态不允许支付");
        }
        this.state = OrderStateVO.PAID;
    }

    public void cancel() {
        if (state == OrderStateVO.PAID) {
            throw new BusinessException("已支付订单不可取消");
        }
        this.state = OrderStateVO.CANCELED;
    }
}
```

### CommandEntity

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

### ValueObject（普通值对象）

```java
@Value
@Builder
public class Money {
    BigDecimal amount;
    String currency;

    public Money add(Money other) {
        if (!currency.equals(other.currency)) {
            throw new BusinessException("币种不一致");
        }
        return Money.builder()
                .amount(amount.add(other.amount))
                .currency(currency)
                .build();
    }
}
```

### ValueObject（枚举值对象）

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
                .orElseThrow(() -> new BusinessException("无效状态码：" + code));
    }
}
```

### Aggregate

> **概念提醒**：`OrderEntity` 是聚合根，`OrderAggregate` 是装载视图（持有聚合根 + 内部对象）。
>
> 外部不要直接修改 `aggregate.getItems()`，所有变更必须通过聚合根 `OrderEntity` 的方法完成。
> 详见 [domain-modeling.md](domain-modeling.md#聚合aggregate)。

```java
@Value
@Builder
public class OrderAggregate {

    OrderEntity order;             // 聚合根（承载身份 + 核心行为）
    List<OrderItemEntity> items;   // 受聚合根管理的内部实体
    AddressVO address;             // 内部值对象

    public BigDecimal calculateTotal() {
        return items.stream()
                .map(OrderItemEntity::getSubtotal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    public void assertValid() {
        if (items.isEmpty()) {
            throw new BusinessException("订单不能为空");
        }
    }
}
```

### Repository 接口（domain 层）

```java
package com.example.domain.order.repository;

import com.example.domain.order.model.entity.OrderEntity;
import com.example.domain.order.model.valobj.OrderStateVO;

import java.util.List;
import java.util.Optional;

public interface IOrderRepository {

    Optional<OrderEntity> findByOrderId(String orderId);

    /**
     * 保存订单（新增或全量更新）。
     *
     * 说明：仓储接口只暴露领域语义的 save，不暴露 updateState / updateXxx。
     * 状态变化必须通过实体行为（{@link OrderEntity#pay()} 等）+ save 完成，
     * 这样不变量始终被实体守住，无法绕过。
     */
    void save(OrderEntity entity);

    List<OrderEntity> findByUserAndState(String userId, OrderStateVO state);
}
```

### Port 接口（domain 层）

```java
package com.example.domain.order.port;

import com.example.domain.order.model.valobj.PaymentResult;
import java.math.BigDecimal;

public interface IPaymentPort {

    PaymentResult charge(String orderId, BigDecimal amount);

    PaymentResult refund(String orderId, BigDecimal amount);
}
```

### Domain Service

**接口**：

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

**实现（Plain Java，推荐）**：

```java
package com.example.domain.order.service.impl;

public class OrderDomainService implements IOrderDomainService {

    private final IOrderRepository orderRepository;

    public OrderDomainService(IOrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    @Override
    public OrderEntity createOrder(CreateOrderCommandEntity command) {
        OrderEntity entity = OrderEntity.builder()
                .orderId(UUID.randomUUID().toString().replace("-", ""))
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

**退化版本（domain 直接打 Spring 注解）**：

```java
@Service
@RequiredArgsConstructor
public class OrderDomainService implements IOrderDomainService {
    private final IOrderRepository orderRepository;
    // ...
}
```

---

## Application 层模板

> Application 层只在「多入口共用编排 / 跨聚合协作 / 编排逻辑明显膨胀」时引入。简单场景下 trigger 直接调 domain service 即可。

### UseCase（用例编排）

```java
package com.example.application.order.usecase;

import com.example.domain.order.model.entity.CreateOrderCommandEntity;
import com.example.domain.order.model.entity.OrderEntity;
import com.example.domain.order.model.valobj.PaymentResult;
import com.example.domain.order.port.IPaymentPort;
import com.example.domain.order.service.IOrderDomainService;
import com.example.types.exception.BusinessException;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

/**
 * 创建并支付订单用例
 *
 * 职责：
 * 1. 编排「创建订单 → 调用支付 → 更新订单状态」
 * 2. 管理事务边界
 * 3. 处理跨聚合协作
 *
 * 不承载业务规则（业务规则在 domain）。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CreateAndPayOrderUseCase {

    private final IOrderDomainService orderDomainService;
    private final IPaymentPort paymentPort;

    @Transactional(rollbackFor = Exception.class)
    public OrderEntity execute(CreateOrderCommandEntity command, BigDecimal amount) {
        log.info("创建并支付订单 userId:{} amount:{}", command.getUserId(), amount);

        // 1. 创建订单（领域服务）
        OrderEntity order = orderDomainService.createOrder(command);

        // 2. 调用支付（端口适配器）
        PaymentResult result = paymentPort.charge(order.getOrderId(), amount);
        if (!result.isSuccess()) {
            throw new BusinessException("支付失败：" + result.getErrorMsg());
        }

        // 3. 标记订单已支付
        return orderDomainService.payOrder(order.getOrderId());
    }
}
```

---

## Infrastructure 层模板

### Repository 实现（infrastructure 层）

```java
package com.example.infrastructure.adapter.repository;

import com.example.domain.order.model.entity.OrderEntity;
import com.example.domain.order.model.valobj.OrderStateVO;
import com.example.domain.order.repository.IOrderRepository;
import com.example.infrastructure.dao.IOrderDao;
import com.example.infrastructure.dao.po.OrderPO;

import jakarta.annotation.Resource;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Repository;

import java.time.Duration;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Repository
public class OrderRepository implements IOrderRepository {

    @Resource
    private IOrderDao orderDao;
    @Resource
    private RedisTemplate<String, OrderEntity> redisTemplate;

    private static final Duration CACHE_TTL = Duration.ofMinutes(30);

    @Override
    public Optional<OrderEntity> findByOrderId(String orderId) {
        String cacheKey = cacheKey(orderId);
        OrderEntity cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) return Optional.of(cached);

        OrderPO po = orderDao.selectByOrderId(orderId);
        if (po == null) return Optional.empty();

        OrderEntity entity = toEntity(po);
        // 教学版：直接回填缓存。生产版需要考虑 read-after-write 一致性：
        //   - 高频变更聚合慎用「读时回填」，否则旧读线程可能覆盖新值
        //   - 推荐策略：短 TTL + 写后双删 / 版本戳 / Redis Lua 原子比较
        redisTemplate.opsForValue().set(cacheKey, entity, CACHE_TTL);
        return Optional.of(entity);
    }

    @Override
    public void save(OrderEntity entity) {
        OrderPO po = toPO(entity);
        OrderPO existing = orderDao.selectByOrderId(entity.getOrderId());
        if (existing == null) {
            // 教学版：依赖 SELECT-then-INSERT。生产版应在表上加 UNIQUE(order_id)
            // 并捕获 DuplicateKeyException 兜底，避免并发下双插。
            orderDao.insert(po);
        } else {
            po.setId(existing.getId());
            orderDao.updateById(po);
        }
        // 教学版：先写 DB 再失效缓存。生产版应在事务 afterCommit 阶段失效，
        // 否则事务回滚时缓存已被删，下个读请求会回填旧值。
        redisTemplate.delete(cacheKey(entity.getOrderId()));
    }

    @Override
    public List<OrderEntity> findByUserAndState(String userId, OrderStateVO state) {
        List<OrderPO> list = orderDao.selectByUserAndState(userId, state.getCode());
        return list.stream().map(this::toEntity).collect(Collectors.toList());
    }

    private String cacheKey(String orderId) {
        return "order:" + orderId;
    }

    private OrderEntity toEntity(OrderPO po) {
        return OrderEntity.builder()
                .orderId(po.getOrderId())
                .userId(po.getUserId())
                .totalAmount(po.getTotalAmount())
                .state(OrderStateVO.fromCode(po.getState()))
                .build();
    }

    private OrderPO toPO(OrderEntity entity) {
        OrderPO po = new OrderPO();
        po.setOrderId(entity.getOrderId());
        po.setUserId(entity.getUserId());
        po.setTotalAmount(entity.getTotalAmount());
        po.setState(entity.getState().getCode());
        return po;
    }
}
```

### Port Adapter（infrastructure 层）

```java
package com.example.infrastructure.adapter.port;

import com.example.domain.order.model.valobj.PaymentResult;
import com.example.domain.order.port.IPaymentPort;
import com.example.infrastructure.gateway.PaymentGateway;
import com.example.infrastructure.gateway.dto.PayRequestDTO;
import com.example.infrastructure.gateway.dto.PayResponseDTO;
import com.example.types.exception.ExternalException;

import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;

@Component
public class PaymentAdapter implements IPaymentPort {

    @Resource
    private PaymentGateway paymentGateway;

    @Override
    public PaymentResult charge(String orderId, BigDecimal amount) {
        PayRequestDTO request = new PayRequestDTO();
        request.setOutTradeNo(orderId);
        request.setAmount(amount);

        PayResponseDTO response;
        try {
            response = paymentGateway.pay(request);
        } catch (Exception e) {
            throw new ExternalException("支付网关调用失败", e);
        }

        if (!response.isSuccess()) {
            return PaymentResult.failed(response.getErrorMsg());
        }
        return PaymentResult.success(response.getTxId());
    }

    @Override
    public PaymentResult refund(String orderId, BigDecimal amount) {
        // 同上结构
        return PaymentResult.success(null);
    }
}
```

### DAO + PO

**PO**：

```java
package com.example.infrastructure.dao.po;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class OrderPO {
    private Long id;
    private String orderId;
    private String userId;
    private BigDecimal totalAmount;
    private String state;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
```

**DAO 接口**：

```java
package com.example.infrastructure.dao;

import com.example.infrastructure.dao.po.OrderPO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface IOrderDao {

    int insert(OrderPO po);

    int updateById(OrderPO po);

    OrderPO selectByOrderId(@Param("orderId") String orderId);

    List<OrderPO> selectByUserAndState(@Param("userId") String userId,
                                       @Param("state") String state);
}
```

**Mapper XML**（放 `app/src/main/resources/mybatis/mapper/order_mapper.xml`）：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.example.infrastructure.dao.IOrderDao">

    <resultMap id="orderResult" type="com.example.infrastructure.dao.po.OrderPO">
        <id column="id" property="id"/>
        <result column="order_id" property="orderId"/>
        <result column="user_id" property="userId"/>
        <result column="total_amount" property="totalAmount"/>
        <result column="state" property="state"/>
        <result column="create_time" property="createTime"/>
        <result column="update_time" property="updateTime"/>
    </resultMap>

    <insert id="insert" parameterType="com.example.infrastructure.dao.po.OrderPO"
            useGeneratedKeys="true" keyProperty="id">
        INSERT INTO `order` (order_id, user_id, total_amount, state, create_time, update_time)
        VALUES (#{orderId}, #{userId}, #{totalAmount}, #{state}, NOW(), NOW())
    </insert>

    <update id="updateById" parameterType="com.example.infrastructure.dao.po.OrderPO">
        UPDATE `order`
        SET user_id      = #{userId},
            total_amount = #{totalAmount},
            state        = #{state},
            update_time  = NOW()
        WHERE id = #{id}
    </update>

    <select id="selectByOrderId" resultMap="orderResult">
        SELECT * FROM `order` WHERE order_id = #{orderId}
    </select>

    <select id="selectByUserAndState" resultMap="orderResult">
        SELECT * FROM `order`
        WHERE user_id = #{userId} AND state = #{state}
        ORDER BY create_time DESC
    </select>
</mapper>
```

### Gateway + DTO

**DTO**：

```java
package com.example.infrastructure.gateway.dto;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class PayRequestDTO {
    private String outTradeNo;
    private BigDecimal amount;
    private String returnUrl;
}

@Data
public class PayResponseDTO {
    private boolean success;
    private String txId;
    private String errorMsg;
}
```

**Gateway**：

```java
package com.example.infrastructure.gateway;

import com.example.infrastructure.gateway.dto.PayRequestDTO;
import com.example.infrastructure.gateway.dto.PayResponseDTO;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import jakarta.annotation.Resource;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class PaymentGateway {

    @Resource
    private OkHttpClient okHttpClient;
    @Resource
    private ObjectMapper objectMapper;

    @Value("${payment.gateway.url}")
    private String gatewayUrl;

    public PayResponseDTO pay(PayRequestDTO request) throws Exception {
        String body = objectMapper.writeValueAsString(request);
        Request httpReq = new Request.Builder()
                .url(gatewayUrl + "/pay")
                .post(RequestBody.create(body, MediaType.get("application/json")))
                .build();
        try (Response response = okHttpClient.newCall(httpReq).execute()) {
            if (!response.isSuccessful()) {
                throw new RuntimeException("HTTP " + response.code());
            }
            return objectMapper.readValue(response.body().string(), PayResponseDTO.class);
        }
    }
}
```

---

## Trigger 层模板

### HTTP Controller

```java
package com.example.trigger.http.controller;

import com.example.application.order.usecase.CreateAndPayOrderUseCase;
import com.example.domain.order.model.entity.CreateOrderCommandEntity;
import com.example.domain.order.model.entity.OrderEntity;
import com.example.trigger.http.request.CreateOrderRequest;
import com.example.trigger.http.response.OrderResponse;
import com.example.types.common.Response;

import jakarta.annotation.Resource;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/api/v1/order")
public class OrderController {

    @Resource
    private CreateAndPayOrderUseCase createAndPayOrderUseCase;

    @PostMapping("/create-and-pay")
    public Response<OrderResponse> createAndPay(@Valid @RequestBody CreateOrderRequest request) {
        log.info("创建并支付订单 request:{}", request);

        CreateOrderCommandEntity command = CreateOrderCommandEntity.builder()
                .userId(request.getUserId())
                .activityId(request.getActivityId())
                .teamId(request.getTeamId())
                .quantity(request.getQuantity())
                .build();

        OrderEntity order = createAndPayOrderUseCase.execute(command, request.getAmount());

        return Response.success(OrderResponse.from(order));
    }
}
```

**Request DTO**：

```java
package com.example.trigger.http.request;

import jakarta.validation.constraints.*;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class CreateOrderRequest {

    @NotBlank(message = "用户ID不能为空")
    private String userId;

    @NotNull(message = "活动ID不能为空")
    private Long activityId;

    private String teamId;

    /** 注意：@Min 对 null 值默认放行，必填字段必须显式加 @NotNull */
    @NotNull(message = "数量不能为空")
    @Min(value = 1, message = "数量必须大于 0")
    private Integer quantity;

    @NotNull(message = "金额不能为空")
    @DecimalMin(value = "0.01", message = "金额必须大于 0")
    private BigDecimal amount;
}
```

**Response DTO**：

```java
package com.example.trigger.http.response;

import com.example.domain.order.model.entity.OrderEntity;
import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;

@Data
@Builder
public class OrderResponse {
    private String orderId;
    private String state;
    private BigDecimal totalAmount;

    public static OrderResponse from(OrderEntity entity) {
        return OrderResponse.builder()
                .orderId(entity.getOrderId())
                .state(entity.getState().getCode())
                .totalAmount(entity.getTotalAmount())
                .build();
    }
}
```

### MQ Listener

```java
package com.example.trigger.listener;

import com.example.domain.order.service.IOrderDomainService;
import com.example.types.exception.BusinessException;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class OrderPaidListener {

    @Resource
    private IOrderDomainService orderDomainService;
    @Resource
    private ObjectMapper objectMapper;

    @RabbitListener(queues = "order.paid")
    public void onMessage(String message) {
        log.info("收到订单支付完成消息: {}", message);
        try {
            OrderPaidEvent event = objectMapper.readValue(message, OrderPaidEvent.class);
            orderDomainService.payOrder(event.getOrderId());
        } catch (BusinessException e) {
            log.warn("业务异常，丢弃消息: {}", e.getMessage());
        } catch (Exception e) {
            log.error("处理订单支付消息失败", e);
            throw new RuntimeException(e);  // 触发 MQ 重试
        }
    }
}
```

### Scheduled Job

```java
package com.example.trigger.job;

import com.example.domain.order.model.entity.OrderEntity;
import com.example.domain.order.model.valobj.OrderStateVO;
import com.example.domain.order.repository.IOrderRepository;
import com.example.domain.order.service.IOrderDomainService;

import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

@Slf4j
@Component
public class OrderTimeoutJob {

    @Resource
    private IOrderRepository orderRepository;
    @Resource
    private IOrderDomainService orderDomainService;

    /** 每 5 分钟扫描一次未支付超时订单 */
    @Scheduled(cron = "0 */5 * * * ?")
    public void cancelTimeoutOrders() {
        log.info("开始处理超时未支付订单");

        List<OrderEntity> timeoutOrders = orderRepository.findByUserAndState(null, OrderStateVO.CREATED);
        // ...筛选超时...

        for (OrderEntity order : timeoutOrders) {
            try {
                orderDomainService.cancelOrder(order.getOrderId());
            } catch (Exception e) {
                log.error("取消超时订单失败 orderId:{}", order.getOrderId(), e);
            }
        }
    }
}
```

---

## Types 层模板

### Response 统一响应

```java
package com.example.types.common;

import lombok.Data;

@Data
public class Response<T> {

    public static final String SUCCESS_CODE = "0000";
    public static final String SUCCESS_INFO = "成功";

    private String code;
    private String info;
    private T data;

    public static <T> Response<T> success(T data) {
        Response<T> r = new Response<>();
        r.code = SUCCESS_CODE;
        r.info = SUCCESS_INFO;
        r.data = data;
        return r;
    }

    public static <T> Response<T> fail(String code, String info) {
        Response<T> r = new Response<>();
        r.code = code;
        r.info = info;
        return r;
    }
}
```

### BusinessException

```java
package com.example.types.exception;

public class BusinessException extends RuntimeException {

    private final String code;

    public BusinessException(String message) {
        this("BIZ_ERROR", message);
    }

    public BusinessException(String code, String message) {
        super(message);
        this.code = code;
    }

    public String getCode() {
        return code;
    }
}
```

### ExternalException

```java
package com.example.types.exception;

public class ExternalException extends RuntimeException {

    public ExternalException(String message, Throwable cause) {
        super(message, cause);
    }
}
```

### 全局异常处理（trigger 层）

```java
package com.example.trigger.handler;

import com.example.types.common.Response;
import com.example.types.exception.BusinessException;
import com.example.types.exception.ExternalException;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<Response<Void>> onBusiness(BusinessException e) {
        log.warn("业务异常: code={} msg={}", e.getCode(), e.getMessage());
        return ResponseEntity.ok(Response.fail(e.getCode(), e.getMessage()));
    }

    @ExceptionHandler(ExternalException.class)
    public ResponseEntity<Response<Void>> onExternal(ExternalException e) {
        log.error("外部依赖异常", e);
        return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                .body(Response.fail("EXT_ERROR", "外部服务暂不可用"));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Response<Void>> onValidation(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getFieldErrors().stream()
                .findFirst()
                .map(err -> err.getField() + ": " + err.getDefaultMessage())
                .orElse("参数校验失败");
        return ResponseEntity.badRequest().body(Response.fail("PARAM_INVALID", msg));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Response<Void>> onUnknown(Exception e) {
        log.error("未知异常", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Response.fail("SYS_ERROR", "系统异常"));
    }
}
```

---

## 端到端示例：订单创建-支付

把上面的模板拼起来，是一个完整可运行的「创建并支付订单」用例。

### 1. 调用流程

```
HTTP POST /api/v1/order/create-and-pay
        │
        ▼
OrderController.createAndPay
        │
        ▼
CreateAndPayOrderUseCase.execute    ←─ application 层（事务边界）
        │
        ├──► IOrderDomainService.createOrder      ──► OrderEntity
        │            │
        │            ▼
        │     OrderRepository.save                ──► OrderDao + Redis
        │
        ├──► IPaymentPort.charge                  ──► PaymentAdapter
        │                                                │
        │                                                ▼
        │                                         PaymentGateway（HTTP）
        │
        └──► IOrderDomainService.payOrder         ──► OrderEntity.pay()
                     │
                     ▼
              OrderRepository.save
```

### 2. 关键文件清单

| 路径 | 类型 |
|---|---|
| `domain/order/model/entity/OrderEntity.java` | 实体（充血） |
| `domain/order/model/entity/CreateOrderCommandEntity.java` | 命令实体 |
| `domain/order/model/valobj/OrderStateVO.java` | 枚举值对象 |
| `domain/order/model/valobj/PaymentResult.java` | 普通值对象 |
| `domain/order/repository/IOrderRepository.java` | 仓储接口 |
| `domain/order/port/IPaymentPort.java` | 端口接口 |
| `domain/order/service/IOrderDomainService.java` | 领域服务接口 |
| `domain/order/service/impl/OrderDomainService.java` | 领域服务实现（Plain Java） |
| `application/order/usecase/CreateAndPayOrderUseCase.java` | 用例编排 |
| `infrastructure/adapter/repository/OrderRepository.java` | 仓储实现 |
| `infrastructure/adapter/port/PaymentAdapter.java` | 端口适配器 |
| `infrastructure/dao/IOrderDao.java` | DAO 接口 |
| `infrastructure/dao/po/OrderPO.java` | 持久化对象 |
| `infrastructure/gateway/PaymentGateway.java` | HTTP 客户端 |
| `infrastructure/gateway/dto/PayRequestDTO.java` | 远程调用 DTO |
| `app/src/main/resources/mybatis/mapper/order_mapper.xml` | MyBatis XML |
| `app/config/DomainServiceConfig.java` | 装配（domain Plain Java 时） |
| `trigger/http/controller/OrderController.java` | HTTP 入口 |
| `trigger/http/request/CreateOrderRequest.java` | HTTP 请求 DTO |
| `trigger/http/response/OrderResponse.java` | HTTP 响应 DTO |
| `trigger/handler/GlobalExceptionHandler.java` | 全局异常处理 |
| `types/common/Response.java` | 统一响应 |
| `types/exception/BusinessException.java` | 业务异常 |

### 3. 测试覆盖建议

| 层 | 测试文件 | 覆盖什么 |
|---|---|---|
| domain | `OrderEntityTest` | 状态流转、不变量、`pay()` / `cancel()` |
| domain | `OrderDomainServiceTest` | 仓储 mock，验证编排逻辑 |
| application | `CreateAndPayOrderUseCaseTest` | 验证「创建-支付-标记已支付」三步协调 + 失败回滚 |
| infrastructure | `OrderRepositoryIT` | 真实数据库，验证 SQL + PO↔Entity 映射 |
| infrastructure | `PaymentAdapterIT` | 用 MockWebServer 验证 HTTP 调用与 DTO 转换 |
| trigger | `OrderControllerTest` | `@WebMvcTest`，mock UseCase，验证参数绑定+响应结构 |
| app | `OrderFlowSmokeIT` | 1~2 条主链路 `@SpringBootTest` 兜底 |

详见 [testing-strategy.md](testing-strategy.md)。

### 4. 演进信号

这套结构默认是 5 模块基线 + application（用例编排）。后续演进信号：

- 若**只有**这一个用例 → 不需要 application 模块，trigger 直接调 domain service
- 若有**多个 controller / job / listener** 触发同一个「创建并支付」流程 → 保留 application
- 若需要**对外发布 RPC 契约** → 增加 api 模块
- 若读侧出现独立模型 / CQRS → 增加 querys 模块（参见 [layering-decision-matrix.md](layering-decision-matrix.md)）
