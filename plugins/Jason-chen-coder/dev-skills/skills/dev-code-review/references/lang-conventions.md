# Language-Specific Conventions

主 SKILL.md 在执行规范检查时按需查阅本文件。**只读本次 diff 实际涉及的语言小节**,不要全文加载。

每条规范分两层优先级:
1. **项目本地 lint 配置**(`.eslintrc*`、`analysis_options.yaml`、`pyproject.toml` 等)优先于本文件
2. 本文件作为 fallback,代表该语言的官方/社区主流实践

---

## Dart / Flutter

**参考**:Effective Dart、`dart analyze`、`flutter analyze`

**关键检查点**:
- `lowerCamelCase` 变量/方法、`UpperCamelCase` 类型、`snake_case.dart` 文件名
- `final` / `const` 优先于 `var`
- `async` / `await` 配对,Future 必须 await 或显式 `unawaited()`
- `BuildContext` 跨 async gap 需检查 `mounted`
- StatefulWidget / Stream / AnimationController / TextEditingController 必须 `dispose()`
- 不在 `build()` 里做副作用(网络、状态修改)

---

## TypeScript / JavaScript

**参考**:ESLint / Prettier、TS strict mode

**关键检查点**:
- `camelCase` 变量、`PascalCase` 类型/组件/类
- 不滥用 `any`(优先 `unknown` + narrow);不用 `// @ts-ignore` 不带原因
- 无残留 `console.log` / `debugger`
- Promise 必须 `await` 或显式 `void promise`
- React hooks 依赖数组完整,无 stale closure
- 无 `==`(用 `===`),无未处理的 `null` / `undefined` 路径

---

## Python

**参考**:PEP 8 / PEP 257、`ruff` / `black` / `mypy`

**关键检查点**:
- `snake_case` 函数变量、`PascalCase` 类、`UPPER_SNAKE` 常量
- 公共 API 加 type hints
- 不写 bare `except:`(指定异常类型);不用 `except: pass` 静默吞掉错误
- 不用 mutable default args(`def f(x=[])` ✗)
- 文件 I/O / 锁 / DB 连接用 `with` context manager
- 无残留 `print()`(应用 logging)

---

## Go

**参考**:Effective Go、`gofmt` / `golangci-lint`

**关键检查点**:
- exported `PascalCase` / unexported `camelCase`
- 每个 `err` 都被处理,不写 `_ = err`
- 长函数避免 naked returns
- `defer` 顺序正确(后进先出),不在循环里 defer 资源关闭
- goroutine 必须有退出路径(context / channel close),无泄漏
- 无残留 `fmt.Println`(应用 `log` 或结构化日志)

---

## Rust

**参考**:Rust API Guidelines、`clippy`

**关键检查点**:
- `snake_case` 函数/变量、`PascalCase` 类型/trait、`SCREAMING_SNAKE` 常量
- 库代码无 `unwrap()` / `expect()`(应返回 `Result` / `Option`)
- ownership / borrow 正确;`clone()` 不滥用
- 无 unused `mut`、无 unused imports(`cargo check` 会报)
- `?` 操作符传播错误优于手写 `match`
- 无残留 `dbg!()` / `println!()`(应用 `tracing` / `log`)

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
- RAII 管理资源,不直接 `new` / `delete`(用 smart pointer)
- C++ 用 `nullptr`,不用 `NULL` / `0`
- const-correctness(参数、方法、返回值)
- 头文件保护:`#pragma once` 或 include guard
- 无 raw array(用 `std::array` / `std::vector`)
- 注意 integer overflow / signed-unsigned 比较

---

## Swift

**参考**:Swift API Design Guidelines、SwiftLint

**关键检查点**:
- `lowerCamelCase` 函数/变量、`UpperCamelCase` 类型
- closure 内捕获 `self` 用 `[weak self]` 防止循环引用
- `guard let` early return 优于深嵌套 `if let`
- 生产代码无 force unwrap `!`、无 force cast `as!`、无 `try!`
- `Codable` / `Equatable` / `Hashable` 优先合成
- 异步代码用 `async/await`,不混用 completion handler

---

## Shell (bash/sh)

**参考**:ShellCheck、Google Shell Style

**关键检查点**:
- 脚本头 `set -euo pipefail`(bash)
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
- JOIN 必须有 ON 条件(防止笛卡尔积)
- 索引列上不要包裹函数(`WHERE LOWER(email) = ...` 会让索引失效)
- 迁移脚本必须可幂等 + 可回滚

---

## 其他语言

如果本次 diff 涉及未在上面列出的语言(Ruby、PHP、Elixir、Scala、Haskell、Lua、R、MATLAB 等),按以下思路处理:

1. 优先查项目本地 lint / formatter 配置
2. 退回到该语言的官方 style guide(通常 Google 或语言官方维护)
3. 应用主 SKILL.md 中的"通用项"(命名一致、无调试输出、错误处理、无未用导入等)
4. 在 Findings 中明确标注"未找到 <语言> 专属配置,按通用规范评审"
