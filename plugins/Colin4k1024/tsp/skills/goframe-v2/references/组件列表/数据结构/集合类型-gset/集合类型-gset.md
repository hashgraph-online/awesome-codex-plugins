## 基本介绍

集合，即不可重复的一组元素，元素项可以为任意类型。

同时， `gset` 支持可选的并发安全参数选项，支持并发安全的场景。

**使用场景**：

集合操作。

**使用方式**：

```go
import "github.com/gogf/gf/v2/container/gset"
```

**接口文档**： [https://pkg.go.dev/github.com/gogf/gf/v2/container/gset](https://pkg.go.dev/github.com/gogf/gf/v2/container/gset)

**泛型支持**：

从 `v2.10` 版本开始，`gset` 提供了泛型集合类型：
- `TSet[T]`：泛型集合，提供类型安全的集合操作
- 支持 `NewTSetWithChecker` 系列函数，可自定义 `nil` 值检查器
- 推荐在新项目中使用泛型集合，享受编译时类型检查带来的安全性

## 相关文档