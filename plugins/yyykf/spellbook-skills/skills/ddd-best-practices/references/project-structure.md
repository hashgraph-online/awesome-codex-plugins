# DDD 渐进式项目结构

## 目录

- [默认基线](#默认基线)
- [可选模块](#可选模块)
- [模块职责](#模块职责)
- [模块依赖关系](#模块依赖关系)
- [Domain 包结构](#domain-包结构)
- [Infrastructure 包结构](#infrastructure-包结构)
- [Trigger 包结构](#trigger-包结构)
- [App 与 Application 的区别](#app-与-application-的区别)
- [Infrastructure 子目录细化](#infrastructure-子目录细化)
- [Maven 多模块 POM 示例](#maven-多模块-pom-示例)
- [命名规范](#命名规范)

## 默认基线

对大多数 Java / Spring Boot 单体项目，优先从以下 5 模块起步：

```text
{project-name}
├── {project-name}-types
├── {project-name}-domain
├── {project-name}-infrastructure
├── {project-name}-trigger
└── {project-name}-app
```

适用前提：
- 主要入口是 HTTP / Job / Listener
- 无对外 RPC 契约复用需求
- 无独立读模型 / CQRS
- 用例编排尚未复杂到需要单独 application 层

## 可选模块

这些模块是**按需引入**的，不是默认标配：

```text
{project-name}
├── {project-name}-types
├── {project-name}-api           # 可选：对外接口契约
├── {project-name}-domain
├── {project-name}-application   # 可选：用例编排层
├── {project-name}-infrastructure
├── {project-name}-trigger
├── {project-name}-querys        # 可选：CQRS 读侧
└── {project-name}-app
```

### 判断规则

| 模块 | 是否默认需要 | 什么时候引入 |
|---|---|---|
| `types` | 是 | 共享类型、异常、通用模型、通用注解 |
| `domain` | 是 | 承载实体、值对象、领域服务、仓储接口、Port |
| `infrastructure` | 是 | 持久化、缓存、外部系统适配、仓储实现 |
| `trigger` | 是 | HTTP / Job / MQ / RPC 实现等入口 |
| `app` | 是 | 启动、配置、装配 |
| `application` | 否 | 用例编排跨聚合/跨入口开始膨胀 |
| `api` | 否 | 需要发布/复用 RPC 或 SDK 契约 |
| `querys` | 否 | 出现独立读模型 / CQRS / 搜索报表读侧 |

## 模块职责

| 模块 | 职责 |
|---|---|
| types | 共享类型：异常、枚举、公共模型、基础注解、跨切面轻量抽象 |
| domain | 业务规则：实体、值对象、聚合、领域服务、仓储接口、Port 接口 |
| infrastructure | 技术实现：Mapper/DAO、PO、缓存、外部网关、Repository/Port 实现 |
| trigger | 流量入口：Controller、Listener、Job、RPC 实现 |
| app | 启动与装配：Spring Boot 启动类、配置类、Bean 装配 |
| application（可选） | 用例编排：跨聚合流程、事务边界编排、幂等/审计/事件协调 |
| api（可选） | 对外契约：RPC 接口、共享 DTO |
| querys（可选） | 读侧查询模型、报表、搜索、聚合查询 |

## 模块依赖关系

### 最小 5 模块

```text
types <- domain <- infrastructure
         ^
         |
      trigger
         ^
         |
        app
```

说明：
- `domain` 只依赖 `types`
- `trigger` 调用 `domain`
- `app` 负责装配 `domain / infrastructure / trigger`

### 引入 application 后

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
- `application` 承接用例编排
- `trigger` 优先调用 `application`，而不是自己拼编排
- `app` 仍然只做装配，不承载业务逻辑

### 引入 api / querys 后

- `trigger` 可依赖 `api`（例如 RPC 实现）
- `querys` 不应反向污染 `domain`
- `api` 只放契约，不放实现

## Domain 包结构

### 推荐最小模板

```text
domain/
└── {context}/
    ├── model/
    ├── service/
    ├── repository/
    └── port/
```

### 按需扩展模板

```text
domain/
└── {context}/
    ├── model/
    │   ├── aggregate/
    │   ├── entity/
    │   ├── valobj/
    │   └── query/
    ├── service/
    ├── repository/
    ├── port/
    ├── event/
    └── policy/
```

说明：
- 并不是每个子域一开始都必须有 `aggregate / event / policy`
- 初始阶段可以先用轻量 `model/`，随着复杂度提升再细分
- `query/` 适合放分页条件、筛选条件等轻量查询对象，即使还没拆 `querys` 模块也可以使用

## Infrastructure 包结构

```text
infrastructure/
├── adapter/
│   ├── repository/      # 实现 domain IRepository
│   └── port/            # 实现 domain IPort
├── dao/                 # MyBatis / JPA DAO 接口
│   └── po/              # 持久化对象
├── gateway/             # HTTP / RPC 客户端
│   └── dto/             # 远程调用 DTO
├── redis/               # Redis 操作封装
├── event/               # 领域事件投递实现
└── config/              # 框架配置
```

说明：
- `adapter/repository` 实现领域仓储接口，内部组合 `dao/` + `redis/`
- `adapter/port` 实现领域 Port 接口，内部调用 `gateway/`
- DTO / PO → 领域对象的转换收敛在 `adapter/` 实现内
- **不要使用 `persistent/` 目录**，它会模糊「适配实现层」与「数据访问层」的边界

详细的子目录职责与模板见下文 [Infrastructure 子目录细化](#infrastructure-子目录细化)。

## Trigger 包结构

```text
trigger/
├── http/
│   ├── controller/
│   ├── request/
│   └── response/
├── listener/
├── job/
├── rpc/
├── filter/
├── interceptor/
├── aspect/
└── handler/
```

说明：
- 只保留与入口相关的内容
- `trigger` 不应该直接依赖 `Mapper / PO / 外部客户端 / Repository 实现`
- 如果暂时只有 HTTP，也可以先用更轻的 `controller/dto` 结构，后续再细化为 `http/request/response`

## App 与 Application 的区别

### `app`
- Spring Boot 启动
- Bean 装配
- 配置类
- 资源文件

### `application`
- 用例编排
- 跨聚合流程组织
- 多入口复用同一业务流程
- 幂等、事务、审计、事件发布的协调

**不要把两者混为一谈。**

如果当前复杂度不足以支撑单独模块，也可以先在 `app/usecase` 或独立包中沉淀，再视情况抽成 `application` 模块。

## Infrastructure 子目录细化

前文已经给出 Infrastructure 的高层结构，这里展开各子目录的具体职责，避免落地时「不知道某个类该放哪」。

### 完整推荐结构

```text
infrastructure/
├── adapter/
│   ├── repository/                      # 实现 domain 层 IRepository
│   │   └── OrderRepository.java
│   └── port/                            # 实现 domain 层 IPort
│       └── PaymentAdapter.java
├── dao/                                 # MyBatis / JPA DAO 接口
│   ├── IOrderDao.java
│   └── po/                              # 持久化对象
│       ├── OrderPO.java
│       └── base/
│           └── BasePO.java
├── gateway/                             # HTTP / RPC 客户端
│   ├── PaymentGateway.java
│   └── dto/                             # 远程调用请求/响应 DTO
│       ├── PayRequestDTO.java
│       └── PayResponseDTO.java
├── redis/                               # Redis 操作封装
│   └── OrderCacheRepository.java
├── event/                               # 事件投递实现（MQ / Outbox）
│   └── DomainEventPublisherImpl.java
└── config/                              # 框架/中间件配置
    ├── MybatisConfig.java
    └── RedisConfig.java
```

### 子目录职责速查

| 目录 | 职责 | 典型类型 | 依赖 |
|---|---|---|---|
| `adapter/repository/` | 实现 domain `IRepository`，组合 dao/redis/config | `XxxRepository` | dao, redis, config |
| `adapter/port/` | 实现 domain `IPort`，调用 gateway | `XxxAdapter` / `XxxPort` | gateway |
| `dao/` | DAO 接口（MyBatis Mapper / JPA Repository） | `IXxxDao` | DB |
| `dao/po/` | 持久化对象，与表字段一一对应 | `XxxPO` | 无（POJO） |
| `gateway/` | 远程服务客户端 | `XxxGateway` | OkHttp/Retrofit/Feign |
| `gateway/dto/` | 远程调用 DTO | `XxxRequestDTO`/`XxxResponseDTO` | 无（POJO） |
| `redis/` | Redis 读写封装 | `XxxCacheRepository` | Redis |
| `event/` | 领域事件投递实现 | `XxxEventPublisher` | MQ |
| `config/` | 框架配置类 | `XxxConfig` | Spring/中间件 |

### 关键约束

1. **adapter/repository 内组合 dao + redis**：缓存与 DB 协调逻辑（先查缓存→落库→回写）放这里，**不要泄漏到 domain**
2. **adapter/port 内组合 gateway**：DTO ↔ 领域对象转换放这里
3. **不要使用 `persistent/` 目录**：用 `adapter/repository/` + `dao/`（清晰区分实现层和数据层）
4. **PO 与 Entity 不互相引用**：在 Repository 实现中做 `toPO` / `toEntity` 转换
5. **MyBatis Mapper XML 放 `app/src/main/resources/mybatis/mapper/`**：与 DAO 接口同 namespace

### Repository 实现的标准模板

> ⚠️ 下面是**教学版**：演示分层与对象转换。生产版需要额外考虑：
>
> - **缓存读写一致性**：高频写入聚合慎用「读时回填 + 写后删」（read-after-write 旧值会回写缓存）。建议用短 TTL + 写后双删 / 版本戳 / Redis Lua 比较；
> - **缓存失效时机**：失效操作应放在事务 `afterCommit` 阶段，否则事务回滚后缓存被错误清空；
> - **并发插入**：`save()` 的 SELECT-then-INSERT 在并发下会双插。表上必须加 `UNIQUE(order_id)` 并捕获 `DuplicateKeyException` 兜底。

```java
@Repository
public class OrderRepository implements IOrderRepository {

    @Resource
    private IOrderDao orderDao;
    @Resource
    private RedisTemplate<String, OrderEntity> redisTemplate;

    @Override
    public Optional<OrderEntity> findByOrderId(String orderId) {
        // 1. 查缓存
        String cacheKey = "order:" + orderId;
        OrderEntity cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) return Optional.of(cached);

        // 2. 缓存未命中查 DB
        OrderPO po = orderDao.selectByOrderId(orderId);
        if (po == null) return Optional.empty();

        // 3. PO → Entity 转换
        OrderEntity entity = toEntity(po);

        // 4. 回写缓存（教学版直接 set，生产版见上方注意事项）
        redisTemplate.opsForValue().set(cacheKey, entity, Duration.ofMinutes(30));

        return Optional.of(entity);
    }

    @Override
    public void save(OrderEntity entity) {
        OrderPO po = toPO(entity);
        if (po.getId() == null) {
            orderDao.insert(po);
        } else {
            orderDao.updateById(po);
        }
        // 失效缓存（教学版直接 delete；生产版应放 afterCommit）
        redisTemplate.delete("order:" + entity.getOrderId());
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

### Port Adapter 的标准模板

```java
@Component
public class PaymentAdapter implements IPaymentPort {

    @Resource
    private PaymentGateway paymentGateway;

    @Override
    public PaymentResult charge(String orderId, BigDecimal amount) {
        // 1. 领域对象 → 外部 DTO
        PayRequestDTO request = new PayRequestDTO();
        request.setOutTradeNo(orderId);
        request.setAmount(amount);

        // 2. 调用外部网关
        PayResponseDTO response;
        try {
            response = paymentGateway.pay(request);
        } catch (Exception e) {
            throw new ExternalException("支付网关调用失败", e);
        }

        // 3. 外部响应 → 领域结果（防腐转换）
        if (!response.isSuccess()) {
            return PaymentResult.failed(response.getErrorMsg());
        }
        return PaymentResult.success(response.getTxId());
    }

    @Override
    public PaymentResult refund(String orderId, BigDecimal amount) {
        // 同上
        return PaymentResult.success(null);
    }
}
```

## Maven 多模块 POM 示例

### Parent POM（项目根）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>order-system</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <packaging>pom</packaging>

    <modules>
        <module>order-system-types</module>
        <module>order-system-domain</module>
        <module>order-system-infrastructure</module>
        <module>order-system-trigger</module>
        <module>order-system-app</module>
    </modules>

    <properties>
        <java.version>17</java.version>
        <spring-boot.version>3.2.0</spring-boot.version>
        <lombok.version>1.18.30</lombok.version>
        <mybatis-spring.version>3.0.3</mybatis-spring.version>
    </properties>

    <dependencyManagement>
        <dependencies>
            <!-- 内部模块版本统一 -->
            <dependency>
                <groupId>${project.groupId}</groupId>
                <artifactId>order-system-types</artifactId>
                <version>${project.version}</version>
            </dependency>
            <dependency>
                <groupId>${project.groupId}</groupId>
                <artifactId>order-system-domain</artifactId>
                <version>${project.version}</version>
            </dependency>
            <dependency>
                <groupId>${project.groupId}</groupId>
                <artifactId>order-system-infrastructure</artifactId>
                <version>${project.version}</version>
            </dependency>
            <dependency>
                <groupId>${project.groupId}</groupId>
                <artifactId>order-system-trigger</artifactId>
                <version>${project.version}</version>
            </dependency>

            <!-- Spring Boot BOM -->
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-dependencies</artifactId>
                <version>${spring-boot.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
</project>
```

### types 模块 POM

`types` 不应该依赖任何项目内模块，也尽量少依赖外部框架。

```xml
<project>
    <parent>
        <groupId>com.example</groupId>
        <artifactId>order-system</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>
    <artifactId>order-system-types</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <scope>provided</scope>
        </dependency>
    </dependencies>
</project>
```

### domain 模块 POM

**关键约束：domain 只依赖 types，不依赖任何基础设施框架**。

```xml
<project>
    <parent>
        <groupId>com.example</groupId>
        <artifactId>order-system</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>
    <artifactId>order-system-domain</artifactId>

    <dependencies>
        <!-- 只依赖 types -->
        <dependency>
            <groupId>${project.groupId}</groupId>
            <artifactId>order-system-types</artifactId>
        </dependency>

        <!-- Lombok（编译期） -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <scope>provided</scope>
        </dependency>

        <!-- 测试 -->
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.assertj</groupId>
            <artifactId>assertj-core</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.mockito</groupId>
            <artifactId>mockito-core</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```

**反例**：domain 模块出现 `mybatis`、`spring-boot-starter-web`、`spring-boot-starter-data-redis`、`okhttp` 等依赖 → 立刻是错误信号，需要把对应代码挪到 infrastructure。

### infrastructure 模块 POM

```xml
<project>
    <parent>
        <groupId>com.example</groupId>
        <artifactId>order-system</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>
    <artifactId>order-system-infrastructure</artifactId>

    <dependencies>
        <!-- 依赖 domain，实现其接口 -->
        <dependency>
            <groupId>${project.groupId}</groupId>
            <artifactId>order-system-domain</artifactId>
        </dependency>

        <!-- MyBatis -->
        <dependency>
            <groupId>org.mybatis.spring.boot</groupId>
            <artifactId>mybatis-spring-boot-starter</artifactId>
            <version>${mybatis-spring.version}</version>
        </dependency>

        <!-- Redis -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis</artifactId>
        </dependency>

        <!-- HTTP 客户端 -->
        <dependency>
            <groupId>com.squareup.okhttp3</groupId>
            <artifactId>okhttp</artifactId>
            <version>4.12.0</version>
        </dependency>
    </dependencies>
</project>
```

### trigger 模块 POM

```xml
<project>
    <parent>
        <groupId>com.example</groupId>
        <artifactId>order-system</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>
    <artifactId>order-system-trigger</artifactId>

    <dependencies>
        <!-- 依赖 domain（直接调用领域服务时） -->
        <dependency>
            <groupId>${project.groupId}</groupId>
            <artifactId>order-system-domain</artifactId>
        </dependency>

        <!-- Spring Web -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
    </dependencies>
</project>
```

**反例**：trigger 模块出现 `mybatis`、`okhttp`、`spring-boot-starter-data-redis` 直接依赖 → trigger 在做不该做的事，把它推回 infrastructure / domain。

### app 模块 POM（启动模块）

```xml
<project>
    <parent>
        <groupId>com.example</groupId>
        <artifactId>order-system</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>
    <artifactId>order-system-app</artifactId>

    <dependencies>
        <!-- 装配所有模块 -->
        <dependency>
            <groupId>${project.groupId}</groupId>
            <artifactId>order-system-domain</artifactId>
        </dependency>
        <dependency>
            <groupId>${project.groupId}</groupId>
            <artifactId>order-system-infrastructure</artifactId>
        </dependency>
        <dependency>
            <groupId>${project.groupId}</groupId>
            <artifactId>order-system-trigger</artifactId>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

### 引入 application 后的依赖关系

如果增加了 `application` 模块（用例编排），依赖调整为：

```text
types
  ↑
domain
  ↑
application ← infrastructure（实现 domain 接口）
  ↑
trigger
  ↑
app（装配全部）
```

`trigger` 优先依赖 `application`，不再直接依赖 `domain`：

```xml
<!-- trigger -->
<dependency>
    <groupId>${project.groupId}</groupId>
    <artifactId>order-system-application</artifactId>
</dependency>
```

## 命名规范

| 类型 | 命名规则 | 示例 |
|---|---|---|
| 实体 | `{Name}Entity` | `OrderEntity` |
| 值对象 | `{Name}VO` / 语义化名称 | `OrderStateVO` |
| 聚合 | `{Name}Aggregate` | `CreateOrderAggregate` |
| 持久化对象 | `{Name}PO` / `{Name}` | `OrderPO` |
| 仓储接口 | `I{Name}Repository` | `IOrderRepository` |
| 仓储实现 | `{Name}Repository` | `OrderRepository` |
| 端口接口 | `I{Name}Port` | `IUserIdentityPort` |
| 端口实现 | `{Name}Adapter` / `{Name}Port` | `UserIdentityAdapter` |
| 领域服务 | `{Name}DomainService` | `OrderDomainService` |
| 应用服务 | `{Name}ApplicationService` / `{Name}UseCase` | `CreateOrderUseCase` |
| Controller | `{Name}Controller` | `OrderController` |
