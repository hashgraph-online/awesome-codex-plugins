## 基本介绍

并发安全基本类型。

**使用场景**：

`gtype` 使用得非常频繁，任何需要并发安全的场景下都适用。

在普通的并发安全场景中，一个基本类型的变量，特别是一个 `struct` 含有若干的属性，往往使用互斥(读写)锁或者多把(读写)锁来进行安全管理。 但这样的使用中， `变量/struct/属性` 的操作性能 **十分低下**，且由于互斥锁机制的存在往往使得操作变得相当复杂，必须小心翼翼地维护好 `变量/属性` 的并发安全控制（特别是 `(RW)Mutex`）。

`gtype` 针对于最常用的基本数据类型，提供了对应的并发安全数据类型，便于在并发安全场景下更好地维护变量/属性，开发者无需在 `struct` 中再创建和维护繁琐的 `(RW)Mutex`。由于 `gtype` 维护的是基本类型的并发安全，因此内部基本都使用了 `atomic` 原子操作来维护并发安全性，因此效率往往会比 `(RW)Mutex` 互斥锁高出数十倍。

**使用方式**：

```go
import "github.com/gogf/gf/v2/container/gtype"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/container/gtype](https://pkg.go.dev/github.com/gogf/gf/v2/container/gtype)

## 相关文档