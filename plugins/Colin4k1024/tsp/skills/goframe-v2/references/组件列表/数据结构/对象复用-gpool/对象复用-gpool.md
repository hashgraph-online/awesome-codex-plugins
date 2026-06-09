## 基本介绍

对象复用池（并发安全）。将对象进行缓存复用，支持 `过期时间`、 `创建方法` 及 `销毁方法` 定义。

**使用场景**：

任何需要支持定时过期的对象复用场景。

**使用方式**：

```go
import "github.com/gogf/gf/v2/container/gpool"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/container/gpool](https://pkg.go.dev/github.com/gogf/gf/v2/container/gpool)

需要注意几点：

1. `New` 方法的过期时间类型为 `time.Duration`。
2. 对象 `创建方法`( `newFunc NewFunc`)返回值包含一个 `error` 返回，当对象创建失败时可由该返回值反馈原因。
3. 对象 `销毁方法`( `expireFunc...ExpireFunc`)为可选参数，用以当对象超时/池关闭时，自动调用自定义的方法销毁对象。

## 泛型支持

:::tip
版本要求：`v2.10.0`
:::

从 `v2.10.0` 版本开始，`gpool` 提供了泛型类型 `TPool[T]`，提供类型安全的对象池操作。

### 基本使用

使用 `NewTPool[T]` 创建泛型对象池：

```go
type MyObject struct {
    ID   int
    Name string
}

// 创建对象池，设置 3 秒过期时间
pool := gpool.NewTPool[*MyObject](
    3*time.Second,
    func() (*MyObject, error) {
        // 对象创建方法
        return &MyObject{ID: 1, Name: "example"}, nil
    },
    func(obj *MyObject) {
        // 对象销毁方法（可选）
        fmt.Printf("Destroying object: %+v\n", obj)
    },
)
defer pool.Close()

// 从池中获取对象
obj, err := pool.Get()
if err != nil {
    panic(err)
}
fmt.Printf("Got object: %+v\n", obj)

// 使用完对象后放回池中
pool.MustPut(obj)
```

### 类型安全的优势

泛型版本提供编译时类型检查，避免了类型断言：

```go
// 传统方式（需要类型断言）
pool := gpool.New(3*time.Second, func() (interface{}, error) {
    return &MyObject{}, nil
})
obj, _ := pool.Get()
myObj := obj.(*MyObject) // 需要类型断言

// 泛型方式（类型安全）
pool := gpool.NewTPool[*MyObject](3*time.Second, func() (*MyObject, error) {
    return &MyObject{}, nil
})
obj, _ := pool.Get() // obj 直接是 *MyObject 类型，无需断言
```

## `gpool` 与 `sync.Pool`

`gpool` 与 `sync.Pool` 都可以达到对象复用的作用，但是两者的设计初衷和使用场景不太一样。

`sync.Pool` 的对象生命周期不支持自定义过期时间，究其原因， `sync.Pool` 并不是一个 `Cache`； `sync.Pool` 设计初衷是为了缓解GC `压力`， `sync.Pool` 中的对象会在 `GC` 开始前全部清除；并且 `sync.Pool` 不支持对象创建方法及销毁方法。

## 相关文档