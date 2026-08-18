# DDD 领域层常用设计模式

> 本文档面向 **DDD 领域层中的模式落地**，不是 GoF 通用教程。
>
> 每个模式都给出：**适用场景 → 接口定义 → 抽象基类 → 具体实现 → 装配方式**。
>
> **领域纯洁性约束**：以下示例中，标注 `@Service / @Component` 的代码意味着**该实现类应放在 `application` / `infrastructure` 模块**，或交由 `app` 装配；`domain` 包内的接口与抽象基类保持 Plain Java，不打 Spring 注解。

## 目录

- [模板方法模式](#模板方法模式)
- [策略模式（含 Map 注入范式）](#策略模式含-map-注入范式)
- [责任链模式（含责任链工厂）](#责任链模式含责任链工厂)
- [用责任链表达 Node 流程编排](#用责任链表达-node-流程编排)
- [工厂模式](#工厂模式)
- [决策树模式](#决策树模式)
- [EnumVO 内嵌策略匹配](#enumvo-内嵌策略匹配)
- [模式选择指南](#模式选择指南)
- [什么时候不要急着上模式](#什么时候不要急着上模式)

## 模板方法模式

**场景**：流程骨架稳定，但部分步骤会因规则或策略不同而变化。

**典型应用**：抽奖流程、审批流程、退款流程、订单处理流程。

### 接口与抽象基类

```java
// domain 层：抽象基类（Plain Java）
public abstract class AbstractRefundOrderStrategy implements IRefundOrderStrategy {

    protected final ITradeRepository repository;

    protected AbstractRefundOrderStrategy(ITradeRepository repository) {
        this.repository = repository;
    }

    @Override
    public final RefundResult refundOrder(TradeRefundOrderEntity entity) {
        // 1. 前置校验（公共骨架）
        assertRefundable(entity);

        // 2. 执行退款（子类实现）
        RefundResult result = doRefund(entity);

        // 3. 后置处理（公共骨架）
        recordRefundLog(entity, result);

        return result;
    }

    protected void assertRefundable(TradeRefundOrderEntity entity) {
        if (!entity.canRefund()) {
            throw new BusinessException("订单状态不允许退款");
        }
    }

    protected abstract RefundResult doRefund(TradeRefundOrderEntity entity);

    protected void recordRefundLog(TradeRefundOrderEntity entity, RefundResult result) {
        repository.saveRefundLog(entity.getOrderId(), result);
    }
}
```

### 具体实现

```java
// 装配类：放 application / infrastructure（不在 domain）
@Service("paid2RefundStrategy")
public class Paid2RefundStrategy extends AbstractRefundOrderStrategy {

    public Paid2RefundStrategy(ITradeRepository repository) {
        super(repository);
    }

    @Override
    protected RefundResult doRefund(TradeRefundOrderEntity entity) {
        // 已支付未成团：原路退款 + 恢复锁单库存
        return repository.paid2Refund(entity);
    }
}
```

### 关键点

- **流程骨架在抽象基类中固化**：前置校验、后置日志这类公共动作不允许子类绕过
- **`final` 修饰模板方法**：防止子类覆盖骨架
- **构造器注入**：领域抽象基类不依赖 Spring，依赖通过构造器传入
- **`@Service` 放在子类**：因为抽象基类可能被定义在 domain 包，子类应放在 application/infrastructure

## 策略模式（含 Map 注入范式）

**场景**：同一行为有多种算法实现，运行时根据条件选择。

**典型应用**：抽奖算法、退款类型、推荐策略、计费策略、风控策略。

### 接口定义

```java
// domain 层
public interface IRefundOrderStrategy {

    /** 策略编码，用于 Map 注入时作为 key */
    String strategyCode();

    /** 执行退款 */
    RefundResult refund(TradeRefundOrderEntity entity);
}
```

### 具体策略实现

```java
@Service
public class Paid2RefundStrategy implements IRefundOrderStrategy {

    @Override
    public String strategyCode() {
        return "paid_unformed";
    }

    @Override
    public RefundResult refund(TradeRefundOrderEntity entity) {
        // 已支付未成团的退款逻辑
        return RefundResult.success();
    }
}

@Service
public class Unpaid2RefundStrategy implements IRefundOrderStrategy {

    @Override
    public String strategyCode() {
        return "unpaid_unlock";
    }

    @Override
    public RefundResult refund(TradeRefundOrderEntity entity) {
        // 未支付未成团的退款逻辑
        return RefundResult.success();
    }
}
```

### Map 注入范式（推荐）

**Spring 自动收集所有 `IRefundOrderStrategy` 实现，按 `strategyCode()` 索引**：

```java
@Service
public class RefundStrategyDispatcher {

    private final Map<String, IRefundOrderStrategy> strategyMap;

    /**
     * Spring 会把所有 IRefundOrderStrategy 的实现 Bean 自动收集成 Map：
     *   key = beanName（默认是类名首字母小写）
     *   value = bean 实例
     *
     * 这里我们重新按 strategyCode() 建索引，让业务编码更直观。
     */
    public RefundStrategyDispatcher(List<IRefundOrderStrategy> strategies) {
        this.strategyMap = strategies.stream()
                .collect(Collectors.toMap(IRefundOrderStrategy::strategyCode, Function.identity()));
    }

    public RefundResult dispatch(String code, TradeRefundOrderEntity entity) {
        IRefundOrderStrategy strategy = strategyMap.get(code);
        if (strategy == null) {
            throw new BusinessException("不支持的退款策略：" + code);
        }
        return strategy.refund(entity);
    }
}
```

### 在领域服务中使用

```java
@Service
public class TradeRefundOrderService implements ITradeRefundOrderService {

    private final RefundStrategyDispatcher dispatcher;

    public TradeRefundOrderService(RefundStrategyDispatcher dispatcher) {
        this.dispatcher = dispatcher;
    }

    @Override
    public RefundResult refund(TradeRefundOrderEntity entity) {
        // 由 EnumVO 决定策略编码（参见「EnumVO 内嵌策略匹配」一节）
        String code = RefundTypeEnumVO.match(entity).getCode();
        return dispatcher.dispatch(code, entity);
    }
}
```

### 关键点

- **新增策略只需新建一个 `@Service` 类**：分发器自动收录，无需改老代码（OCP）
- **不要在领域服务中写大量 `if-else` 路由**：把路由责任交给 Dispatcher
- **strategyCode 由策略自己声明**：而不是外部 Map 配置，避免散落

## 责任链模式（含责任链工厂）

**场景**：多个规则按顺序执行，每一步可终止或继续传递。

**典型应用**：黑名单 → 额度 → 库存 → 灰度规则的顺序过滤；下单前校验链；权限链。

### 设计要点：节点无状态，链路独立

**不要在节点 Bean 上挂 `next` 字段**。Spring 单例下，不同请求会互相覆盖 next 引用，导致串链、漏节点、并发污染。

正确做法：
- 节点是无状态单例 Bean，**只关心自己的逻辑**
- "下一节点"通过参数传入，不存储在节点字段中
- 工厂每次构造一个**不可变 Pipeline**，请求级隔离

### 接口与函数式组件

```java
// domain 层：节点接口（无 next 字段）
public interface ILogicChain<T, C, R> {

    /** 节点编码，用于 Factory 索引 */
    String chainCode();

    /**
     * 执行当前节点逻辑。
     * 命中规则 → 返回结果，链路终止
     * 不命中 → 调用 next.proceed(...) 继续传递
     */
    R logic(T request, C context, ChainNext<T, C, R> next);
}

/** 函数式接口：表示「调用下一节点」 */
@FunctionalInterface
public interface ChainNext<T, C, R> {
    R proceed(T request, C context);
}
```

### 具体节点

```java
@Service
public class BlackListLogicChain implements ILogicChain<RaffleRequest, RaffleContext, RaffleResult> {

    @Resource
    private IUserBlackListRepository blackListRepository;

    @Override
    public String chainCode() {
        return "blackList";
    }

    @Override
    public RaffleResult logic(RaffleRequest request, RaffleContext context,
                              ChainNext<RaffleRequest, RaffleContext, RaffleResult> next) {
        if (blackListRepository.isInBlackList(request.getUserId())) {
            return RaffleResult.fallback("BLACK_LIST_AWARD");
        }
        return next.proceed(request, context);
    }
}

@Service
public class StockLogicChain implements ILogicChain<RaffleRequest, RaffleContext, RaffleResult> {

    @Resource
    private IStockRepository stockRepository;

    @Override
    public String chainCode() {
        return "stock";
    }

    @Override
    public RaffleResult logic(RaffleRequest request, RaffleContext context,
                              ChainNext<RaffleRequest, RaffleContext, RaffleResult> next) {
        if (!stockRepository.hasStock(request.getStrategyId())) {
            return RaffleResult.fallback("NO_STOCK_AWARD");
        }
        return next.proceed(request, context);
    }
}

/** 兜底节点：链路最后一环，所有节点都不命中时返回默认值 */
@Service
public class DefaultLogicChain implements ILogicChain<RaffleRequest, RaffleContext, RaffleResult> {

    @Override
    public String chainCode() {
        return "default";
    }

    @Override
    public RaffleResult logic(RaffleRequest request, RaffleContext context,
                              ChainNext<RaffleRequest, RaffleContext, RaffleResult> next) {
        return RaffleResult.normal();
    }
}
```

### 不可变 Pipeline

每次工厂调用都构造一个新的 Pipeline，**节点本身不持有任何链路状态**：

```java
// domain 层：不可变链路包装
public final class LogicChainPipeline<T, C, R> {

    private final List<ILogicChain<T, C, R>> nodes;

    public LogicChainPipeline(List<ILogicChain<T, C, R>> nodes) {
        if (nodes == null || nodes.isEmpty()) {
            throw new IllegalArgumentException("责任链节点不能为空");
        }
        this.nodes = List.copyOf(nodes);
    }

    public R execute(T request, C context) {
        return executeAt(0, request, context);
    }

    private R executeAt(int idx, T request, C context) {
        if (idx >= nodes.size()) {
            return null;
        }
        ChainNext<T, C, R> next = (req, ctx) -> executeAt(idx + 1, req, ctx);
        return nodes.get(idx).logic(request, context, next);
    }
}
```

### 责任链工厂

```java
@Service
public class LogicChainFactory {

    /** 按 chainCode() 索引所有节点 */
    private final Map<String, ILogicChain<RaffleRequest, RaffleContext, RaffleResult>> chainMap;

    public LogicChainFactory(List<ILogicChain<RaffleRequest, RaffleContext, RaffleResult>> chains) {
        this.chainMap = chains.stream()
                .collect(Collectors.toMap(ILogicChain::chainCode, Function.identity()));

        // 启动期校验：必须有 default 兜底
        if (!chainMap.containsKey("default")) {
            throw new IllegalStateException("责任链缺少 default 兜底节点");
        }
    }

    /**
     * 按规则码顺序构造一条新的不可变链路；自动追加 default 兜底
     */
    public LogicChainPipeline<RaffleRequest, RaffleContext, RaffleResult> openLogicChain(List<String> ruleModels) {
        if (ruleModels == null || ruleModels.isEmpty()) {
            throw new IllegalArgumentException("规则码列表不能为空");
        }

        List<ILogicChain<RaffleRequest, RaffleContext, RaffleResult>> nodes = new ArrayList<>();
        for (String code : ruleModels) {
            ILogicChain<RaffleRequest, RaffleContext, RaffleResult> node = chainMap.get(code);
            if (node == null) {
                throw new IllegalArgumentException("未知规则节点：" + code);
            }
            nodes.add(node);
        }
        nodes.add(chainMap.get("default"));

        return new LogicChainPipeline<>(nodes);
    }
}
```

### 在领域服务中使用

```java
@Service
public class RaffleStrategyService {

    @Resource
    private LogicChainFactory chainFactory;

    public RaffleResult performRaffle(RaffleRequest request, RaffleContext context, List<String> ruleModels) {
        LogicChainPipeline<RaffleRequest, RaffleContext, RaffleResult> pipeline =
                chainFactory.openLogicChain(ruleModels);
        return pipeline.execute(request, context);
    }
}
```

### 关键点

- **节点单例无状态**：不持有 `next`、不持有调用时上下文，并发安全
- **Pipeline 每次构造**：链路状态在 Pipeline 中，请求级隔离
- **`chainCode()` 自声明**：避免外部 Map 配置散落
- **启动期校验 default**：避免运行时拿不到兜底节点
- **运行期校验未知规则**：拼错规则码立即报错，不静默跳过

## 用责任链表达 Node 流程编排

**这是责任链的进阶用法，用于替代 BPMN/工作流引擎**，适合中等复杂度的业务流程编排。

**对比小傅哥的 Node 模式**：

| 维度 | xfg Node 模式 | 责任链版 Node 编排 |
|---|---|---|
| 节点抽象 | `AbstractCaseSupport` | `AbstractFlowNode` |
| 流程开始 | `RootNode` | 链表头节点 |
| 流程结束 | `EndNode` | `next() == null` |
| 分支处理 | 节点内决定下一节点 | 节点内 `route()` 返回下一节点 |
| 上下文传递 | `DynamicContext` | 同样使用 `DynamicContext` |
| 装配方式 | `Default{Domain}CaseFactory` | `FlowNodeFactory` |

**核心思路**：把 xfg 的有向图 Node 简化为「线性责任链 + 节点内分支跳转」，更直观、更轻量。

### 场景示例：拼团下单流程

流程节点：**校验用户 → 校验活动 → 锁定库存 → 创建订单 → 完结**

### 节点接口与基类

**关键设计：每个流程一套自己的节点接口**。原因——Spring 注入 `List<IFlowNode<C>>` 时会因泛型擦除导致不同流程节点互相串入。给每个流程定义专属节点接口（继承通用 `IFlowNode<C>`），就能让 Spring 按接口类型精确收集。

```java
// domain 层：通用流程节点接口
public interface IFlowNode<C> {

    /** 节点编码，用于 FlowEngine 索引 */
    String nodeCode();

    /** 执行当前节点；返回下一个节点的编码（null = 流程结束） */
    String execute(C context);
}

public abstract class AbstractFlowNode<C> implements IFlowNode<C> {

    @Override
    public final String execute(C context) {
        before(context);
        String nextCode = doExecute(context);
        after(context);
        return nextCode;
    }

    protected abstract String doExecute(C context);

    /** 公共前置（埋点、日志） */
    protected void before(C context) { }

    /** 公共后置（指标上报） */
    protected void after(C context) { }
}

// domain 层：拼团下单流程的专属节点接口
public interface IGroupBuyOrderFlowNode extends IFlowNode<GroupBuyOrderFlowContext> { }
```

### 上下文对象

```java
// domain 层：流程上下文，承载流转中的数据
@Data
@Builder
public class GroupBuyOrderFlowContext {
    private String userId;
    private Long activityId;
    private String teamId;

    /** 中间结果：校验通过的用户实体 */
    private UserEntity userEntity;
    /** 中间结果：活动信息 */
    private PayActivityEntity payActivityEntity;
    /** 中间结果：锁库存返回的订单号 */
    private String lockedOrderId;
    /** 最终结果 */
    private OrderEntity orderEntity;
}
```

### 具体节点实现

注意：节点实现 `IGroupBuyOrderFlowNode`，**不直接实现** `IFlowNode<GroupBuyOrderFlowContext>`，确保 Spring 注入时能精确收集到本流程的节点。

```java
@Service
public class ValidateUserNode extends AbstractFlowNode<GroupBuyOrderFlowContext>
        implements IGroupBuyOrderFlowNode {

    @Resource
    private IUserRepository userRepository;

    @Override
    public String nodeCode() {
        return "validateUser";
    }

    @Override
    protected String doExecute(GroupBuyOrderFlowContext ctx) {
        UserEntity user = userRepository.findById(ctx.getUserId());
        if (user == null || user.isBlocked()) {
            throw new BusinessException("用户不存在或已被冻结");
        }
        ctx.setUserEntity(user);
        return "validateActivity";
    }
}

@Service
public class ValidateActivityNode extends AbstractFlowNode<GroupBuyOrderFlowContext>
        implements IGroupBuyOrderFlowNode {

    @Resource
    private IActivityRepository activityRepository;

    @Override
    public String nodeCode() {
        return "validateActivity";
    }

    @Override
    protected String doExecute(GroupBuyOrderFlowContext ctx) {
        PayActivityEntity activity = activityRepository.findById(ctx.getActivityId());
        activity.assertActive();
        ctx.setPayActivityEntity(activity);
        return "lockStock";
    }
}

@Service
public class LockStockNode extends AbstractFlowNode<GroupBuyOrderFlowContext>
        implements IGroupBuyOrderFlowNode {

    @Resource
    private IStockRepository stockRepository;

    @Override
    public String nodeCode() {
        return "lockStock";
    }

    @Override
    protected String doExecute(GroupBuyOrderFlowContext ctx) {
        String lockedOrderId = stockRepository.lock(ctx.getActivityId(), ctx.getUserId());
        ctx.setLockedOrderId(lockedOrderId);
        return "createOrder";
    }
}

@Service
public class CreateOrderNode extends AbstractFlowNode<GroupBuyOrderFlowContext>
        implements IGroupBuyOrderFlowNode {

    @Resource
    private IOrderRepository orderRepository;

    @Override
    public String nodeCode() {
        return "createOrder";
    }

    @Override
    protected String doExecute(GroupBuyOrderFlowContext ctx) {
        OrderEntity order = OrderEntity.create(
                ctx.getUserEntity(),
                ctx.getPayActivityEntity(),
                ctx.getLockedOrderId()
        );
        orderRepository.save(order);
        ctx.setOrderEntity(order);
        return null;  // null = 流程结束
    }
}
```

### 流程引擎（带环路 / 步数防护）

通用 `FlowEngine` 是普通类，**不直接 `@Service`**。每个流程通过 `@Configuration` 显式装配为 Bean，这样可以精确控制装哪些节点、绑定哪个上下文类型。

```java
// domain 层：通用流程引擎
public final class FlowEngine<C> {

    private final String flowCode;
    private final Map<String, IFlowNode<C>> nodeMap;
    private final int maxSteps;

    public FlowEngine(String flowCode, Collection<? extends IFlowNode<C>> nodes, int maxSteps) {
        if (maxSteps <= 0) {
            throw new IllegalArgumentException("maxSteps 必须 > 0");
        }
        this.flowCode = flowCode;
        this.maxSteps = maxSteps;
        this.nodeMap = nodes.stream().collect(Collectors.toUnmodifiableMap(
                IFlowNode::nodeCode, Function.identity()));
    }

    /**
     * 从指定起始节点开始执行流程；自动检测环路与超步数
     */
    public void run(String startNodeCode, C context) {
        Set<String> visited = new LinkedHashSet<>();
        String currentCode = startNodeCode;
        int steps = 0;

        while (currentCode != null) {
            if (++steps > maxSteps) {
                throw new IllegalStateException(
                        "流程 [" + flowCode + "] 超出最大步数 " + maxSteps + "，路径: " + visited);
            }
            if (!visited.add(currentCode)) {
                throw new IllegalStateException(
                        "流程 [" + flowCode + "] 检测到环路，路径: " + visited + " -> " + currentCode);
            }

            IFlowNode<C> node = nodeMap.get(currentCode);
            if (node == null) {
                throw new IllegalStateException(
                        "流程 [" + flowCode + "] 未找到节点: " + currentCode);
            }
            currentCode = node.execute(context);
        }
    }
}
```

### 装配（每个流程一个 Bean）

```java
// app / application 模块
@Configuration
public class GroupBuyOrderFlowConfig {

    /** 注入本流程的专属节点 List（不会串入其他流程节点） */
    @Bean
    public FlowEngine<GroupBuyOrderFlowContext> groupBuyOrderFlowEngine(
            List<IGroupBuyOrderFlowNode> nodes) {
        return new FlowEngine<>("groupBuyOrder", nodes, 50);
    }
}
```

### 在 application / use case 中使用

```java
@Service
public class CreateGroupBuyOrderUseCase {

    @Resource
    private FlowEngine<GroupBuyOrderFlowContext> groupBuyOrderFlowEngine;

    @Transactional(rollbackFor = Exception.class)
    public OrderEntity execute(CreateOrderCommand cmd) {
        GroupBuyOrderFlowContext ctx = GroupBuyOrderFlowContext.builder()
                .userId(cmd.getUserId())
                .activityId(cmd.getActivityId())
                .teamId(cmd.getTeamId())
                .build();

        groupBuyOrderFlowEngine.run("validateUser", ctx);
        return ctx.getOrderEntity();
    }
}
```

### 分支跳转示例

如果某个节点需要根据上下文走不同分支：

```java
@Service
public class CheckPaymentTypeNode extends AbstractFlowNode<OrderFlowContext> {

    @Override
    public String nodeCode() {
        return "checkPaymentType";
    }

    @Override
    protected String doExecute(OrderFlowContext ctx) {
        // 根据上下文条件决定下一节点
        if (ctx.isVip()) {
            return "vipDiscount";
        } else if (ctx.hasCoupon()) {
            return "applyCoupon";
        }
        return "createOrder";
    }
}
```

### 关键点

- **节点单一职责**：一个节点只做一件事，便于测试和复用
- **节点之间通过 Context 传递数据**：不通过返回值（返回值只用来决定下一步走向）
- **节点编码 `nodeCode()` 自声明**：避免外部 Map 配置散落
- **`null` 表示流程结束**：不需要专门的 EndNode
- **分支由当前节点决定**：根据 Context 计算下一节点编码
- **每个流程定义专属节点接口**：避免泛型擦除导致 Spring 注入串流程
- **FlowEngine 不直接 `@Service`**：每个流程通过 `@Configuration` 显式装配，传入 maxSteps
- **运行期防护**：内置环路检测（visited 集合）+ 最大步数（maxSteps）保护
- **流程编排逻辑放在 application / use case**：不要让流程引擎污染 domain
- **节点本身放在 domain 还是 application？**：如果节点纯粹处理领域规则（如 ValidateUser），可以放 domain；如果涉及编排/事务/外部协调（如调用多个领域服务），放 application

### 何时不要用 Node 编排

- 流程只有 2~3 步：直接在 use case 中顺序写就够了
- 流程是纯线性、无分支：用普通责任链即可
- 流程极度复杂、需要可视化/可配置：用 Flowable / Camunda 工作流引擎

## 工厂模式

**场景**：需要按配置或运行时条件动态组装规则对象图。

**典型应用**：责任链组装、节点组合、复杂聚合的构造、规则模型选择。

### 实现

工厂模式在领域层主要用于「按运行时配置组装对象图」。

参见前文 [责任链工厂](#责任链模式含责任链工厂) 中的 `LogicChainFactory`：它就是一个典型的工厂——按 `chainCode` 索引节点 Bean，按规则码列表构造不可变的 `LogicChainPipeline`。

类似地，[流程引擎装配](#装配每个流程一个-bean) 中的 `groupBuyOrderFlowEngine` Bean 装配也是工厂用法。

**工厂的关键约束**：

- **节点（被组装对象）保持无状态**：工厂返回的组合对象（Pipeline / Engine / Tree）才持有链路状态
- **启动期校验**：默认节点 / 兜底节点缺失要在 Bean 初始化时报错，而不是运行时
- **运行期校验**：未知规则码要立即抛异常，不要静默跳过

### 与策略 Map 的对比

| 模式 | 何时用 |
|---|---|
| 策略 Map 注入 | 单一选择：根据条件挑一个策略执行 |
| 工厂 + 责任链 | 组合执行：多个规则按顺序串起来跑 |
| 工厂 + 流程节点 | 复杂编排：有分支、有上下文流转 |

## 决策树模式

**场景**：业务规则不是单链路，而是多层条件分支，每层可能有多个子分支。

**典型应用**：多节点风控、多层审批、复杂营销准入、规则引擎。

### 接口与节点

```java
public interface ILogicTreeNode {

    /** 节点编码，用于子节点路由 */
    String nodeCode();

    /** 执行当前节点；返回下一节点编码 / 终止动作 */
    TreeActionEntity logic(String userId, Long strategyId, Integer awardId, String ruleValue);
}

public class RuleStockLogicTreeNode implements ILogicTreeNode {

    @Override
    public String nodeCode() {
        return "rule_stock";
    }

    @Override
    public TreeActionEntity logic(String userId, Long strategyId, Integer awardId, String ruleValue) {
        if (stockAvailable(awardId)) {
            // 库存充足 → 直接发奖
            return TreeActionEntity.takeOver(new StrategyAwardVO(awardId));
        }
        // 库存不足 → 走兜底节点
        return TreeActionEntity.routeTo("rule_fallback");
    }
}
```

### 决策树引擎

```java
@Service
public class DecisionTreeEngine {

    private final Map<String, ILogicTreeNode> nodeMap;

    public DecisionTreeEngine(Map<String, ILogicTreeNode> nodeMap) {
        this.nodeMap = nodeMap;
    }

    public StrategyAwardVO process(String startNode, Context ctx) {
        String currentNode = startNode;
        while (currentNode != null) {
            ILogicTreeNode node = nodeMap.get(currentNode);
            TreeActionEntity action = node.logic(ctx.getUserId(), ctx.getStrategyId(),
                                                  ctx.getAwardId(), ctx.getRuleValue());
            if (action.isTakeOver()) {
                return action.getAward();
            }
            currentNode = action.getNextNodeCode();
        }
        throw new IllegalStateException("决策树执行未返回结果");
    }
}
```

### 与责任链 / Node 编排的区别

| 模式 | 流转特点 | 适用场景 |
|---|---|---|
| 责任链 | 线性，依次过滤 | 顺序校验、过滤规则 |
| Node 流程编排 | 有向无环，节点决定下一步 | 业务流程串联，有少量分支 |
| 决策树 | 树形，多层多叉分支 | 复杂决策、规则引擎、多层风控 |

## EnumVO 内嵌策略匹配

**场景**：需要根据多个状态条件，匹配出对应的处理策略。

**典型应用**：退款类型判定、订单状态机、消息路由。

### 范式

```java
@Getter
@AllArgsConstructor
public enum RefundTypeEnumVO {

    UNPAID_UNLOCK("unpaid_unlock", "Unpaid2RefundStrategy", "未支付，未成团") {
        @Override
        public boolean matches(GroupBuyOrderEnumVO group, TradeOrderStatusEnumVO trade) {
            return GroupBuyOrderEnumVO.PROGRESS.equals(group)
                && TradeOrderStatusEnumVO.CREATE.equals(trade);
        }
    },

    PAID_UNFORMED("paid_unformed", "Paid2RefundStrategy", "已支付，未成团") {
        @Override
        public boolean matches(GroupBuyOrderEnumVO group, TradeOrderStatusEnumVO trade) {
            return GroupBuyOrderEnumVO.PROGRESS.equals(group)
                && TradeOrderStatusEnumVO.COMPLETE.equals(trade);
        }
    },

    PAID_FORMED("paid_formed", "Paid2RefundFormedStrategy", "已支付，已成团") {
        @Override
        public boolean matches(GroupBuyOrderEnumVO group, TradeOrderStatusEnumVO trade) {
            return GroupBuyOrderEnumVO.COMPLETE.equals(group)
                && TradeOrderStatusEnumVO.COMPLETE.equals(trade);
        }
    };

    private final String code;
    private final String strategy;
    private final String info;

    /** 由子枚举实现：判断当前状态是否匹配此退款类型 */
    public abstract boolean matches(GroupBuyOrderEnumVO group, TradeOrderStatusEnumVO trade);

    /** 静态工厂方法：按状态组合匹配出唯一的退款类型 */
    public static RefundTypeEnumVO match(GroupBuyOrderEnumVO group, TradeOrderStatusEnumVO trade) {
        return Arrays.stream(values())
                .filter(v -> v.matches(group, trade))
                .findFirst()
                .orElseThrow(() -> new BusinessException("不支持的退款状态组合"));
    }
}
```

### 与策略 Map 联动

```java
@Service
public class RefundDomainService {

    private final RefundStrategyDispatcher dispatcher;

    public RefundResult refund(TradeRefundOrderEntity entity) {
        // 1. EnumVO 自身判断走哪个策略
        RefundTypeEnumVO type = RefundTypeEnumVO.match(
                entity.getGroupBuyOrderStatus(),
                entity.getTradeOrderStatus()
        );

        // 2. Dispatcher 按 code 路由到具体策略
        return dispatcher.dispatch(type.getCode(), entity);
    }
}
```

### 关键点

- **状态判断逻辑收敛在 EnumVO 自身**：避免在 service 中写大堆 if-else
- **EnumVO 的 `matches()` 是纯函数**：不依赖任何外部资源，可以放在 domain 包中
- **`match()` 静态工厂方法返回唯一结果**：找不到就抛业务异常
- **EnumVO 和 Strategy 通过 code 解耦**：EnumVO 不直接持有 Strategy 实例

## 模式选择指南

| 场景 | 推荐模式 | 理由 |
|---|---|---|
| 流程骨架稳定，部分步骤可变 | 模板方法 | 父类锁住骨架，子类填空 |
| 多种算法选一个执行 | 策略 + Map 注入 | OCP，新增不改老代码 |
| 多规则按顺序过滤，命中即返回 | 责任链 + 工厂 | 规则可插拔、可复用 |
| 业务流程串联，有少量分支 | Node 流程编排（责任链版） | 比 use case 顺序代码更清晰，比工作流引擎更轻 |
| 多层条件分支，树形决策 | 决策树 | 风控/规则引擎首选 |
| 状态组合匹配出处理类型 | EnumVO + 策略 Map | 状态判断收敛在 Enum，分发交给 Map |
| 流程稳定但子步骤多变 | 模板方法 + 责任链/决策树 | 父类管骨架，子树管扩展 |

## 什么时候不要急着上模式

以下情况优先保持简单：

- **只有两三个清晰分支**，普通 `if-else` 已足够表达业务意图
- **规则变更频率低，且没有明显复用需求**
- **当前主要问题仍然是边界不清、依赖走错、模型贫血、缺测试**——这些问题不解决，上模式只会让代码更难懂
- **流程只有 2~3 步**：直接顺序写就行，别为了「未来扩展」预设抽象

**原则**：

1. **先解决边界问题，再解决模式问题**
2. **先做正确，再做优雅**
3. **三个相似的 if-else 不算重复，第四个出现时才考虑抽象**
4. **能用静态方法解决的别上策略类，能用顺序代码解决的别上责任链**
