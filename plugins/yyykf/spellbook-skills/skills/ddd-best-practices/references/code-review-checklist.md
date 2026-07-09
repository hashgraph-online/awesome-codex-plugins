# DDD 代码审查清单

## 分层决策

- [ ] 当前模块数量与项目复杂度匹配，没有为了对齐参考项目而机械补 `application / api / querys`
- [ ] `app` 只承载启动、配置、装配，不包含业务逻辑
- [ ] 如果已引入 `application`，它负责用例编排，而不是承载技术实现细节

## 依赖方向

- [ ] `domain` 模块只依赖 `types` 模块
- [ ] `infrastructure` 依赖 `domain`（实现其接口），不反向依赖
- [ ] `trigger` 依赖 `domain` 或可选的 `application / api`，不直接依赖 `Mapper / PO / 外部客户端`
- [ ] `types` 无任何项目内依赖
- [ ] 无循环依赖

## 领域层纯洁性

- [ ] `domain` 层无 Spring 组件注解（`@Service/@Component/@Repository/@Configuration`）
- [ ] `domain` 层无 MyBatis 注解（`@Mapper/@Select` 等）
- [ ] `domain` 层无 Redis / MQ / HTTP 客户端直接调用代码
- [ ] 领域服务通过构造函数依赖仓储/Port 接口，而不是实现类

## 领域模型设计

- [ ] 实体有明确业务标识，并承载关键行为或不变量
- [ ] 值对象不可变，无 setter
- [ ] 聚合只在真实事务边界明确时引入，而非为了凑结构
- [ ] 若实体只是数据袋、规则全部堆在 Service 中，应标记为贫血模型风险
- [ ] 初始化阶段没有强行给每个子域补齐 `aggregate / event / policy`

## 仓储、ACL 与映射

- [ ] 仓储接口定义在 `domain`，实现位于 `infrastructure`
- [ ] 仓储方法体现业务语义，而不是技术动作
- [ ] 领域接口中没有 `refreshCache / evictCache / cacheXxx` 等技术语义
- [ ] 外部系统调用通过 Port 隔离
- [ ] Port 接口返回领域对象或领域导向结果，而不是外部 DTO / SDK 对象
- [ ] DTO / PO → 领域对象的转换在 Adapter / Repository 实现中完成
- [ ] 简单同构映射可使用 MapStruct；复杂语义映射优先手写

## Trigger / Application 层

- [ ] Controller / Listener / Job 只做参数接收、基础校验、对象转换、调用应用/领域服务、封装响应
- [ ] Trigger 层没有直接注入 Repository / Mapper 的情况
- [ ] 触发层没有直接操作 PO、缓存客户端、外部 HTTP 客户端
- [ ] 若一个入口要协调多个领域动作，优先收敛到 `application` 或领域服务，而不是继续堆在 Trigger

## 领域事件

- [ ] 事件对象本身不依赖 MQ/框架实现
- [ ] 事件发布通过接口抽象
- [ ] 跨聚合一致性问题才引入事件，不是为了预埋架构
- [ ] 需要可靠投递时，有明确的本地消息/Task/Outbox 策略

## 测试

- [ ] 关键领域服务存在单元测试
- [ ] 至少覆盖关键不变量：唯一性、只读限制、状态流转、权限校验、密钥匹配等
- [ ] 关键领域规则优先在 `domain` 层通过纯单测保护，而不是依赖 `@SpringBootTest`
- [ ] `application / use case` 测试重点验证编排、事务边界、幂等与跨聚合协作
- [ ] Controller 默认通过 `@WebMvcTest + MockMvc` 覆盖参数绑定、校验、状态码、异常映射和响应结构
- [ ] Repository / Adapter / 复杂 Mapper 有真实集成测试覆盖 SQL、映射、防腐转换或外部协议风险
- [ ] 仅保留少量 `@SpringBootTest` 级别测试验证关键全链路 wiring
- [ ] `application / domain` 测试没有大量 mock `mapper`；若存在，已回看职责划分
- [ ] 没有用 Mockito-only 测试去替代持久化/映射/序列化风险验证
- [ ] 对“运行态重载 / 缓存刷新编排”这类边界收紧动作有测试保护

## 常见反模式（需避免）

- 为了“像 DDD”而盲目补 `application / api / querys`
- Controller 直接注入 Repository / Mapper
- Repository 接口暴露缓存刷新/失效方法
- Port 直接返回外部 DTO，导致外部结构穿透领域
- 实体与值对象大量公开 setter
- 领域层出现 Spring / MyBatis / Redis / HTTP 细节
- 只有目录分层，没有测试保护关键业务规则
- 用 controller 测试兜底领域规则，缺少 domain/application 层测试
- 默认用 `@SpringBootTest` 写所有 controller 测试
- 在 service / use case 测试中大量 mock mapper
