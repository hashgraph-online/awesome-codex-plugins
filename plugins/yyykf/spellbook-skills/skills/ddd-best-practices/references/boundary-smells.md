# DDD 边界异味与修复策略

这份清单用于识别“项目已经做了 DDD 分层，但边界仍然会逐渐走形”的典型问题。

## 1. Repository 接口泄漏技术语义

### 现象
- 领域仓储接口暴露 `refreshCache()`、`evictCache()`、`cacheXxx()` 一类方法
- 领域代码直接谈 Redis、缓存刷新、索引重建等技术动作

### 风险
- 技术细节反向污染领域
- 一旦缓存策略变化，领域接口也要改
- 容易把基础设施动作误当成业务动作

### 建议
- 优先把缓存失效、回填、刷新等逻辑内聚到仓储实现内部
- 如果“运行态重载”本身是一个业务/运维用例，使用**领域服务 + 专门 Port** 编排，而不是把它塞进 Repository

### 示例

**避免：**
```java
public interface IConfigRepository {
    void refreshCache();
    void evictCache(String key);
}
```

**推荐：**
```java
public interface IConfigRepository {
    List<ConfigEntity> findAll();
    Optional<ConfigEntity> findByKey(String key);
}

public interface IConfigRuntimePort {
    void replaceAvailableConfigs(List<ConfigEntity> configs);
}
```

## 2. Trigger 层绕过领域服务

### 现象
- Controller / Listener / Job 直接注入 Repository / Mapper
- Trigger 层中出现刷新缓存、拼装聚合、直接改 PO 等逻辑

### 风险
- 用例边界散落在入口层
- 以后补审计、事件、鉴权、幂等时会越来越难收敛
- 一个入口修了，另一个入口很容易漏掉

### 建议
- Trigger 只做：参数接收、基础校验、对象转换、调用应用/领域服务、封装响应
- 任何“有业务含义的动作”都通过应用服务或领域服务承接

## 3. ACL / Port 返回外部 DTO

### 现象
- Port 接口直接返回 `UserInfoDTO`、`RoleDTO`、三方 SDK 响应对象
- 领域服务直接操作外部字段结构

### 风险
- 外部系统数据结构穿透到领域层
- 外部字段变化时，领域被迫跟着改
- 领域语言无法稳定下来

### 建议
- Port 返回领域对象或领域导向的结果对象
- DTO → 领域对象的转换由 Adapter 完成

### 示例

**避免：**
```java
public interface IUserIdentityPort {
    UserInfoDTO getUserInfoById(String userId);
}
```

**推荐：**
```java
public interface IUserIdentityPort {
    UserIdentity getUserInfoById(String userId);
}
```

## 4. 贫血模型回潮

### 现象
- Entity 只有 getter/setter
- “只读不可修改”“状态不可逆”“密钥必须匹配”等规则全部堆在 DomainService
- Service 越写越像事务脚本

### 风险
- 模型只是数据袋，规则离对象太远
- 业务规则容易重复、遗漏或不一致

### 建议
- 把关键不变量和状态变化尽量沉到 Entity / VO
- 领域服务负责协作，不要吞掉所有规则

### 示例

**推荐：**
```java
@Value
@Builder(toBuilder = true)
public class DictionaryEntity {
    Long id;
    String value;
    boolean readonly;

    public void assertWritable() {
        if (readonly) {
            throw new BusinessException("该配置为只读，不可修改");
        }
    }

    public DictionaryEntity updateValue(String nextValue) {
        assertWritable();
        return toBuilder().value(nextValue).build();
    }
}
```

## 5. Service / UseCase 测试大量 mock mapper

### 现象
- 一个 service 测试要 mock `requestMapper / responseMapper / entityMapper / poMapper`
- 测试主体主要在 `when(...).thenReturn(...)` 与 `verify(...)`，很少断言真实业务状态

### 风险
- 用例层职责混入了过多边界转换细节
- 测试高度耦合实现过程，轻微重构就大面积破坏测试
- 真正的映射风险并没有被验证，只是被 mock 掉了

### 建议
- 让 `application / domain` 更聚焦业务编排与规则，减少直接感知 mapper 的机会
- 简单同构映射可在边界处顺带覆盖，不要在 use case 测试里过度 mock
- 复杂语义映射放到 Adapter / Repository 集成测试中验证

## 6. Controller 默认全量启动上下文

### 现象
- Controller 测试默认使用 `@SpringBootTest`
- 每个 HTTP 场景都依赖完整应用启动

### 风险
- 测试慢、脆、定位困难
- Controller 契约问题和装配问题耦在一起，失败信号不清晰

### 建议
- 默认使用 `@WebMvcTest + MockMvc`
- 只在需要验证安全链、过滤器、事务联动或关键 wiring 时保留少量 `@SpringBootTest`

## 7. 只有 Controller 测试，没有 Repository / Adapter 集成测试

### 现象
- Controller 切片测试很完整
- 但 Repository、PO ↔ Entity 映射、外部 Adapter 没有任何真实测试

### 风险
- SQL、JPA/MyBatis 映射、序列化/反序列化、DTO 防腐转换的问题无法提前发现
- 测试“看起来很多”，但真正的基础设施风险没有覆盖

### 建议
- 为 Repository / Adapter / 复杂 Mapper 补集成测试
- 把 HTTP 契约验证与技术风险验证拆开，不要让 Controller 测试承担基础设施兜底职责

## 8. 盲目补层 / Cargo Cult DDD

### 现象
- 项目一开始就把 `application / api / querys / event / aggregate` 全建好
- 目录很完整，但大多为空壳
- 团队把精力花在“放哪一层”而不是“业务规则是否表达正确”

### 风险
- 学习成本和维护成本上升
- 真实问题没有被解决，只有结构变复杂

### 建议
- 先保持最小闭环
- 只在出现明确复杂度信号后再补层
- 先修边界泄漏，再谈架构体面

## 9. 没有领域测试安全网

### 现象
- 结构上看似 DDD，但 `src/test` 为空
- 任何边界调整都只能靠手工回归

### 风险
- 每次充血模型、ACL 收紧、接口裁剪都容易引入回归
- 团队会越来越不敢继续做架构收敛

### 建议
优先为这些场景补单元测试：
- 唯一性校验
- 只读/状态流转限制
- 鉴权成功 / 失败
- AK/SK 或密钥匹配
- 运行态重载 / 缓存刷新编排

## 使用建议

做 DDD 审查时，不要只检查“有没有 `domain/infrastructure/trigger` 目录”。

更重要的是问：
1. 入口是否绕过了领域边界？
2. 领域接口是否泄漏了技术语义？
3. 外部系统结构是否穿透到了领域？
4. 关键规则是否沉在模型里？
5. 有没有测试保护这些规则？
