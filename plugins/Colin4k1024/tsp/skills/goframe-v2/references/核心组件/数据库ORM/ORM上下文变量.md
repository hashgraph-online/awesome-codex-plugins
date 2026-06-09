`ORM` 支持传递自定义的 `context` 上下文变量，用于异步 `IO` 控制、上下文信息传递（特别是链路跟踪信息的传递）、以及嵌套事务支持。

我们可以通过 `Ctx` 方法传递自定义的上下文变量给 `ORM` 对象， `Ctx` 方法其实是一个链式操作方法，该上下文传递进去后仅对当前 `DB` 接口对象有效，方法定义如下：

```go
func Ctx(ctx context.Context) DB
```

## 请求超时控制

我们来看一个通过上下文变量控制请求超时时间的示例。

```go
ctx, cancel := context.WithTimeout(context.Background(), time.Second)
defer cancel()
_, err := db.Ctx(ctx).Query("SELECT SLEEP(10)")
fmt.Println(err)
```

该示例中执行会 `sleep 10` 秒中，因此必定会引发请求的超时。执行后，输出结果为：

```html
context deadline exceeded, SELECT SLEEP(10)
```

## 链路跟踪信息

上下文变量也可以传递链路跟踪信息，并且可以和日志组件结合，将链路信息打印到日志中（仅当 `ORM` 日志开启时），具体请参考链路跟踪专题介绍章节： [服务链路跟踪](../../服务可观测性/服务链路跟踪/服务链路跟踪.md)

## 模型上下文操作

模型对象也支持上下文变量的传递，同样也是通过 `Ctx` 方法。我们来看一个简单的示例，我们将示例2的例子通过模型操作调整一下。

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    _, err := g.DB().Model("user").Ctx(gctx.New()).All()
    if err != nil {
        panic(err)
    }
}
```

执行后，终端输出为：

```html
2020-12-28 23:46:56.349 [DEBU] {38d45cbf2743db16f1062074f7473e5c} [  5 ms] [default] [rows:0  ] SHOW FULL COLUMNS FROM `user`
2020-12-28 23:46:56.354 [DEBU] {38d45cbf2743db16f1062074f7473e5c} [  5 ms] [default] [rows:100] SELECT * FROM `user`
```
:::tip
其中 ``SHOW FULL COLUMNS FROM `user` `` 为 `ORM` 组件的数据表字段获取查询，每个表在执行操作之前仅会查询一次并缓存结果到内存中。
:::
## 嵌套事务支持

嵌套事务的支持依赖 `Context` 上下文变量的层级传递，具体请参考章节： [ORM事务处理](ORM事务处理/ORM事务处理.md)