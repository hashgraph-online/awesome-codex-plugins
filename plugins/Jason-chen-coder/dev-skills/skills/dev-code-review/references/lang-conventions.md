# Language-Specific Conventions

主 SKILL.md 在执行规范检查时按需查阅本文件。**只读本次 diff 实际涉及的语言小节**,不要全文加载。

每条规范分两层优先级:
1. **项目本地 lint 配置**(`.eslintrc*`、`analysis_options.yaml`、`pyproject.toml` 等)优先于本文件
2. 本文件作为 fallback,代表该语言的官方/社区主流实践

以下条目是按需检查提示,不是自动 finding。检查可达风险和项目约定;CLI 输出、刻意的后台任务、已证明不变量下的断言等可能合理。不要仅凭 API 名字、代码长度或风格差异提升严重度。

---

## Dart / Flutter

**参考**:Effective Dart、`dart analyze`、`flutter analyze`

**关键检查点**:
- `lowerCamelCase` 变量/方法、`UpperCamelCase` 类型、`snake_case.dart` 文件名
- `final` / `const` 优先于 `var`
- Future 应被 await、返回或显式交给后台任务管理;`unawaited()` 本身不处理异步异常
- `BuildContext` 跨 async gap 需检查 `mounted`
- 在拥有资源的 State 生命周期中释放 controller/subscription 等;StatefulWidget 本身不提供 `dispose()`,外部拥有的资源不要重复释放
- 不在 `build()` 里做副作用(网络、状态修改)

---

## TypeScript / JavaScript

**参考**:ESLint / Prettier、TS strict mode

**关键检查点**:
- `camelCase` 变量、`PascalCase` 类型/组件/类
- 不滥用 `any`(优先 `unknown` + narrow);不用 `// @ts-ignore` 不带原因
- 移除非预期调试输出和 `debugger`,保留有用途的日志及 CLI 输出
- Promise 应被 await、返回或交给后台任务管理;`void promise` 本身不处理 rejection
- React hooks 依赖数组完整,无 stale closure
- 检查隐式类型转换和 nullish 路径是否符合契约;遵守项目允许的比较惯例

---

## Python

**参考**:PEP 8 / PEP 257、`ruff` / `black` / `mypy`

**关键检查点**:
- `snake_case` 函数变量、`PascalCase` 类、`UPPER_SNAKE` 常量
- 公共 API 加 type hints
- 不写 bare `except:`(指定异常类型);不用 `except: pass` 静默吞掉错误
- 不用 mutable default args(`def f(x=[])` ✗)
- 文件 I/O / 锁 / DB 连接用 `with` context manager
- 区分残留调试 `print()` 与 CLI 正常输出,日志遵守项目策略

---

## Go

**参考**:Effective Go、`gofmt` / `golangci-lint`

**关键检查点**:
- exported `PascalCase` / unexported `camelCase`
- 检查错误是否被有意处理或传播;有证据可忽略的错误应说明原因
- 长函数避免 naked returns
- `defer` 顺序正确(后进先出),不在循环里 defer 资源关闭
- goroutine 必须有退出路径(context / channel close),无泄漏
- 区分调试输出与 CLI 正常输出,服务日志遵守项目策略

---

## Rust

**参考**:Rust API Guidelines、`clippy`

**关键检查点**:
- `snake_case` 函数/变量、`PascalCase` 类型/trait、`SCREAMING_SNAKE` 常量
- 对可恢复/外部输入失败优先返回 `Result` / `Option`;检查 `unwrap()` / `expect()` 的不变量是否成立
- ownership / borrow 正确;`clone()` 不滥用
- 无 unused `mut`、无 unused imports(`cargo check` 会报)
- `?` 操作符传播错误优于手写 `match`
- 区分非预期调试输出与 CLI 正常输出,服务日志遵守项目策略

---

## Java / Kotlin

**参考**:Google Java Style、Kotlin Coding Conventions

**关键检查点**:
- `camelCase` 方法/变量、`PascalCase` 类、`UPPER_SNAKE` 常量
- Kotlin 不滥用 `!!`(force unwrap);用 `?.` / `?:` / `requireNotNull`
- 资源用 try-with-resources(Java)或 `.use {}`(Kotlin)
- 无 raw types(Java);Kotlin 用 `data class` 表示数据
- 协程必须 scope 化,不用 `GlobalScope`
- `equals` / `hashCode` / `toString` 一致性

---

## C / C++

**参考**:Google C++ Style、clang-tidy、cppcoreguidelines

**关键检查点**:
- C++ 资源优先使用 RAII;手动分配和 C API 交互需检查所有权及释放路径
- C++ 用 `nullptr`,不用 `NULL` / `0`
- const-correctness(参数、方法、返回值)
- 头文件保护:`#pragma once` 或 include guard
- 检查数组边界与生命周期;根据接口/布局需求选择 raw array、`std::array` 或 `std::vector`
- 注意 integer overflow / signed-unsigned 比较

---

## Swift

**参考**:Swift API Design Guidelines、SwiftLint

**关键检查点**:
- `lowerCamelCase` 函数/变量、`UpperCamelCase` 类型
- 检查 closure 所有权是否形成循环引用,必要时 weak capture;不要无条件削弱任务所需的生命周期
- `guard let` early return 优于深嵌套 `if let`
- 检查 force unwrap/cast/try 的不变量;外部输入和可恢复失败应走明确错误路径
- `Codable` / `Equatable` / `Hashable` 优先合成
- 新异步逻辑遵守项目约定;与 completion handler 桥接时检查恢复次数、错误与取消传播

---

## Shell (bash/sh)

**参考**:ShellCheck、Google Shell Style

**关键检查点**:
- 检查脚本失败传播与 shell 兼容性;`set -euo pipefail` 可用但不能代替关键命令的显式状态处理
- 变量永远加引号:`"$var"` 不是 `$var`
- 用 `[[ ]]` 不用 `[ ]`(bash);test 文件存在用 `-f`
- 不解析 `ls` 输出(用 glob 或 `find`)
- subshell 与 `()` / `$()` 嵌套清晰
- 临时文件用 `mktemp`,trap 清理

---

## SQL

**参考**:团队风格优先,无则采用以下惯例

**关键检查点**:
- 关键字大小写一致(全大写 OR 全小写,不要混用)
- 必须参数化查询,严禁字符串拼接 user input
- 生产代码不用 `SELECT *`(明确列名,防止 schema 漂移)
- 检查 JOIN 的连接语义与基数;`ON`、`USING` 和明确需要的 `CROSS JOIN` 均可能合理
- 检查谓词是否能利用目标数据库的索引;函数/表达式索引可能支持 `LOWER(email)` 等条件
- 按迁移框架约定检查重复执行保护、事务边界和失败恢复;不可逆迁移需要明确备份/前向修复方案,不伪造无损 rollback

---

## 其他语言

如果本次 diff 涉及未在上面列出的语言(Ruby、PHP、Elixir、Scala、Haskell、Lua、R、MATLAB 等),按以下思路处理:

1. 优先查项目本地 lint / formatter 配置
2. 退回到该语言的官方 style guide(通常 Google 或语言官方维护)
3. 按主 SKILL.md 追溯行为、边界和集成路径,只报告有实际影响的问题
4. 缺少语言专属配置本身不是 finding;仅在影响评审可信度时说明限制
