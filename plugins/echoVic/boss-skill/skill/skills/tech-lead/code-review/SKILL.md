---

name: tech-lead/code-review
description: 代码审查方法论，基于 Google Code Review、Clean Code、SOLID 等业界实践，提供分阶段审查流程、严重度分级、常见反模式识别与可执行反馈写法
version: 2.0.0
agent: tech-lead
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要审查代码时
- 需要评估代码质量时
  metadata:
  internal: true
  references:
  - "Google Code Review Developer Guide: https://google.github.io/eng-practices/review/"
  - "Clean Code (Robert C. Martin)"
  - "SOLID Principles: https://en.wikipedia.org/wiki/SOLID"
  - "OWASP Top 10: https://owasp.org/www-project-top-ten/"
  - "Code Review Checklist (standard/go): https://github.com/mre/idiomatic-go"

---

# 代码审查方法论

## 适用场景

对代码变更进行系统性审查，确保功能正确、质量达标、安全可控。本方法论提供**分阶段审查流程**和**可操作的检查项**，而非泛泛的「代码质量要好」。

## 审查流程

### 阶段 1：理解变更（5 分钟）

在逐行看代码之前，先回答：
1. **这个 PR 解决什么问题？** — 看 PR 描述、关联 issue、PRD
2. **变更范围多大？** — 看 diff stat，超过 400 行的 PR 要求拆分
3. **涉及哪些模块？** — 看变更文件列表，识别影响面

> **原则**（Google Code Review）：不理解上下文就不要给 review 意见。先理解「为什么改」，再看「改得对不对」。

### 阶段 2：正确性审查（必过）

这是**阻塞项**，有问题必须修复。

| 检查项     | 怎么查                                                      |
| ---------- | ----------------------------------------------------------- |
| 需求对齐   | 代码是否实现了 PRD/issue 描述的全部需求？有没有多做或少做？ |
| 边界条件   | 空值、零值、最大值、超长输入、并发是否处理？                |
| 错误处理   | 异常是否被正确捕获和处理？有没有吞异常？                    |
| 数据一致性 | 并发写入、事务边界、缓存失效是否正确？                      |
| 向后兼容   | API 变更是否破坏现有调用方？数据迁移是否可逆？              |

### 阶段 3：安全性审查（必过）

| 检查项   | 怎么查                                                |
| -------- | ----------------------------------------------------- |
| 输入验证 | 所有外部输入是否校验（类型、长度、格式、范围）？      |
| 注入防护 | SQL/命令/模板注入是否防护？用参数化查询而非字符串拼接 |
| XSS 防护 | 用户输入是否转义？CSP 是否配置？                      |
| 认证授权 | 敏感操作是否校验权限？越权访问是否拦截？              |
| 敏感信息 | 密钥、token、密码是否硬编码？日志是否泄露敏感数据？   |
| 依赖安全 | 新增依赖是否有已知漏洞？版本是否过旧？                |

> **参考**：OWASP Top 10 是必查清单。

### 阶段 4：代码质量审查（建议项）

| 检查项   | 怎么查                                                                 |
| -------- | ---------------------------------------------------------------------- |
| 命名     | 变量/函数/类名是否表达意图？避免 `data`、`temp`、`flag` 这类无意义命名 |
| 函数长度 | 单个函数是否超过 50 行？超过则考虑拆分                                 |
| 单一职责 | 一个函数/类是否只做一件事？                                            |
| 重复代码 | 是否有 3 行以上的重复？抽取为函数或常量                                |
| 注释     | 注释是否解释「为什么」而非「做什么」？过时的注释是否删除？             |
| 死代码   | 是否有未使用的变量、函数、import？                                     |
| 魔法值   | 是否有未命名的常量（`if (status === 3)`）？提取为枚举或常量            |

### 阶段 5：设计审查（建议项）

| 原则                | 检查内容                                       |
| ------------------- | ---------------------------------------------- |
| **SRP**（单一职责） | 类是否只有一个变更理由？                       |
| **OCP**（开闭原则） | 新增功能是扩展还是修改？是否需要改核心代码？   |
| **LSP**（里氏替换） | 子类是否能替换父类而不破坏行为？               |
| **ISP**（接口隔离） | 接口是否过于臃肿？调用方是否依赖不需要的方法？ |
| **DIP**（依赖倒置） | 是否依赖抽象而非具体实现？                     |

### 阶段 6：性能审查（按需）

| 检查项   | 怎么查                                   |
| -------- | ---------------------------------------- |
| N+1 查询 | 循环内是否有数据库查询？应批量查询       |
| 大数据集 | 是否一次性加载全量数据？应分页或流式处理 |
| 缓存     | 热点数据是否缓存？缓存失效策略是否正确？ |
| 异步     | 耗时操作是否异步化？是否阻塞主线程？     |

---

## 严重度分级

审查意见必须标注严重度，让作者知道哪些必须改、哪些可选。

| 等级        | 标记 | 含义                             | 处理             |
| ----------- | ---- | -------------------------------- | ---------------- |
| **Blocker** | 🔴   | 功能错误、安全漏洞、数据丢失风险 | 必须修复才能合并 |
| **Major**   | 🟠   | 设计缺陷、可维护性问题、性能隐患 | 建议本轮修复     |
| **Minor**   | 🟡   | 命名、风格、小优化               | 可本轮或后续修复 |
| **Nit**     | 🔵   | 偏好、可选优化                   | 作者自行决定     |

---

## 常见反模式（Anti-patterns）

### 命名反模式

```typescript
// ❌ 模糊命名
const data = getUsers();
const temp = process(data);
const flag = check(temp);

// ✅ 意图明确
const activeUsers = fetchActiveUsers();
const validationResult = validateUsers(activeUsers);
const isEligible = hasRequiredPermissions(validationResult);
```

### 函数反模式

```typescript
// ❌ 超长函数，做了三件事
function handleSubmit(data) {
  const validated = validate(data);
  if (!validated) showError();
  const result = api.save(validated);
  cache.set(result.id, result);
  notify(result);
  log(result);
  return result;
}

// ✅ 拆分，单一职责
async function handleSubmit(data) {
  const validated = validateOrThrow(data);
  const saved = await saveAndCache(validated);
  notifyAndLog(saved);
  return saved;
}
```

### 错误处理反模式

```typescript
// ❌ 吞异常
try {
  await api.save(data);
} catch (e) {
  // 什么都不做
}

// ❌ 捕获过宽
try {
  // 100 行代码
} catch (e) {
  console.log(e);
}

// ✅ 精确捕获 + 处理 + 上报
try {
  await api.save(data);
} catch (e) {
  if (e instanceof ValidationError) {
    showValidationError(e.errors);
  } else {
    reportError(e);
    throw e; // 让上层处理
  }
}
```

### 安全反模式

```typescript
// ❌ SQL 注入
db.query(`SELECT * FROM users WHERE name = '${name}'`);

// ✅ 参数化查询
db.query('SELECT * FROM users WHERE name = ?', [name]);
```

---

## 如何写好 Review 意见

### 差的意见

> 「这段代码不好，重写一下」

问题：没说为什么不好，没说怎么改，作者无法行动。

### 好的意见

> 🔴**Blocker**：这里直接拼接 SQL 字符串，存在 SQL 注入风险。用户输入 `name` 未经过滤直接拼入查询语句。
>
> 建议使用参数化查询：
>
> ```typescript
> db.query('SELECT * FROM users WHERE name = ?', [name]);
> ```

要素：**严重度 + 问题 + 原因 + 建议方案**。

### 意见写作原则

1. **对事不对人** — 批评代码，不批评作者
2. **给出理由** — 不只说「不好」，要说「为什么不好」
3. **提供方案** — 不只说「改」，要说「怎么改」
4. **区分必改和建议** — 用严重度标记，不要所有意见都一个语气
5. **正面反馈** — 写得好的地方也要表扬，鼓励好的实践

---

## 审查效率

- **单次 review 不超过 400 行** — 超过则要求作者拆分 PR
- **review 时间不超过 60 分钟** — 超过则分多次
- **优先看设计和正确性** — 风格问题可以让 linter 处理
- **不要在 review 中提新需求** — 超出 PR 范围的建议另开 issue

---

## 自检清单

- [ ] 我先理解了 PR 的目的和范围再看代码
- [ ] 正确性（功能、边界、错误处理）已检查
- [ ] 安全性（输入验证、注入、权限、敏感信息）已检查
- [ ] 代码质量（命名、长度、重复、死代码）已检查
- [ ] 设计原则（SOLID）已检查
- [ ] 每条意见都有严重度标记
- [ ] 每条意见都说明了「为什么」和「怎么改」
- [ ] 没有提出超出 PR 范围的新需求
- [ ] 有正面反馈，不全是批评

## 常见误区

❌ **逐行挑刺** — 纠结空格和换行，忽略功能和安全问题
❌ **只说不好不说怎么改** — 作者无法行动
❌ **review 超时** — 60 分钟看不完说明 PR 太大，应要求拆分
❌ **在 review 中加需求** — 「顺便加个 XX 功能」不属于 review
❌ **不看测试** — 测试代码和生产代码同等重要
❌ **忽略依赖** — 新增依赖不检查版本和漏洞
