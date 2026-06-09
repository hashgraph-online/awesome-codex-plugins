## 基本介绍

动态大小的并发安全队列。同时， `gqueue` 也支持固定队列大小，固定队列大小时队列效率和标准库的 `channel` 无异。

**使用场景**：

该队列是并发安全的，常用于多 `goroutine` 数据通信且支持动态队列大小的场景。

**使用方式**：

```go
import "github.com/gogf/gf/v2/container/gqueue"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/container/gqueue](https://pkg.go.dev/github.com/gogf/gf/v2/container/gqueue)

**泛型支持**：

从 `v2.10` 版本开始，`gqueue` 提供了泛型队列类型：
- `TQueue[T]`：泛型队列，提供类型安全的队列操作
- 支持先进先出的数据结构操作
- 优化了队列长度计算逻辑，修复了测试用例中的循环结构问题
- 推荐在新项目中使用泛型队列

## 相关文档