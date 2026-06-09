## 基本介绍

支持并发安全开关的环结构，循环双向链表。

**使用场景**：

`ring` 这种数据结构在底层开发中用得比较多一些，如：并发锁控制、缓冲区控制、循环缓冲、滑动窗口等场景。`ring` 的特点在于，其必须有固定的大小，当不停地往 `ring` 中追加写数据时，如果数据大小超过容量大小，新值将会将旧值覆盖。

**使用方式**：

```go
import "github.com/gogf/gf/v2/container/gring"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/container/gring](https://pkg.go.dev/github.com/gogf/gf/v2/container/gring)

:::tip
`gring` 支持链式操作。
:::

## 泛型支持

:::tip
版本要求：`v2.10.0`
:::

从 `v2.10.0` 版本开始，`gring` 提供了泛型类型 `TRing[T]`，提供类型安全的环形队列操作。

### 基本使用

使用 `NewTRing[T]` 创建泛型环：

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/container/gring"
)

func main() {
    // 创建一个容量为 10 的整型环
    r := gring.NewTRing[int](10)
    
    // 向环中添加元素
    for i := 0; i < 5; i++ {
        r.Put(i)
    }
    
    fmt.Println("Len:", r.Len()) // 输出: Len: 5
    fmt.Println("Cap:", r.Cap()) // 输出: Cap: 10
    
    // 移动到起始位置并获取值
    r.Move(-5)
    fmt.Println("Val:", r.Val()) // 输出: Val: 0
}
```

### 类型安全的优势

泛型版本提供编译时类型检查，避免了类型断言：

```go
// 传统方式（需要类型断言）
r := gring.New(10)
r.Put(1)
val := r.Val().(int) // 需要类型断言

// 泛型方式（类型安全）
r := gring.NewTRing[int](10)
r.Put(1)
val := r.Val() // val 直接是 int 类型，无需断言
```

### 自定义类型示例

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/container/gring"
)

type Player struct {
    Position int  // 位置
    Name     string // 名称
    Alive    bool   // 是否存活
}

func main() {
    // 创建玩家环
    r := gring.NewTRing[*Player](10)
    
    // 添加玩家
    for i := 1; i <= 10; i++ {
        r.Put(&Player{
            Position: i,
            Name:     fmt.Sprintf("Player%d", i),
            Alive:    true,
        })
    }
    
    // 遍历环中的所有玩家
    r.Move(-10) // 移动到起始位置
    r.RLockIteratorNext(func(player *Player) bool {
        fmt.Printf("Position: %d, Name: %s, Alive: %v\n", 
            player.Position, player.Name, player.Alive)
        return true
    })
}
```

### 并发安全的泛型环

```go
package main

import (
    "fmt"
    "sync"
    "github.com/gogf/gf/v2/container/gring"
)

func main() {
    // 创建并发安全的泛型环
    r := gring.NewTRing[int](10, true)
    
    var wg sync.WaitGroup
    
    // 并发写入
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            r.Put(n * 10)
        }(i)
    }
    
    wg.Wait()
    
    fmt.Println("Len:", r.Len())
    fmt.Println("Values:", r.SliceNext())
}
```

### 泛型环的常用方法

泛型环 `TRing[T]` 提供了以下常用方法：

| 方法 | 说明 |
| --- | --- |
| `Val() T` | 获取当前位置的元素值，无需类型断言 |
| `Set(value T) *TRing[T]` | 设置当前位置的值 |
| `Put(value T) *TRing[T]` | 设置当前位置的值并移动到下一位置 |
| `Len() int` | 获取环中已使用的元素数量 |
| `Cap() int` | 获取环的容量 |
| `Move(n int) *TRing[T]` | 移动 n 个位置 |
| `Next() *TRing[T]` | 移动到下一个位置 |
| `Prev() *TRing[T]` | 移动到上一个位置 |
| `Link(s *TRing[T]) *TRing[T]` | 连接两个环 |
| `Unlink(n int) *TRing[T]` | 从环中移除 n 个元素 |
| `SliceNext() []T` | 从当前位置向后获取所有元素切片 |
| `SlicePrev() []T` | 从当前位置向前获取所有元素切片 |
| `RLockIteratorNext(f func(value T) bool)` | 向后遍历（只读锁） |
| `RLockIteratorPrev(f func(value T) bool)` | 向前遍历（只读锁） |

### 类型安全的遍历

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/container/gring"
)

func main() {
    r := gring.NewTRing[string](5)
    words := []string{"GoFrame", "is", "awesome", "and", "powerful"}
    
    for _, word := range words {
        r.Put(word)
    }
    
    // 向后遍历 - 类型安全，无需断言
    r.Move(-5)
    r.RLockIteratorNext(func(word string) bool {
        fmt.Printf("Word: %s\n", word)
        return true
    })
}
```

## 性能说明

- `gring` 基于标准库 `container/ring` 实现，在此基础上增加了并发安全控制和更多实用方法
- 环形结构在固定大小的缓冲场景下性能优异，避免了频繁的内存分配
- 泛型版本在保持相同性能的同时，提供了更好的类型安全性
- 推荐在需要循环缓冲、滑动窗口等场景使用