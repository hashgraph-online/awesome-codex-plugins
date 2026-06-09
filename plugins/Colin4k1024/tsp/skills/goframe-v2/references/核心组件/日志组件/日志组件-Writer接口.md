:::tip
`Writer` 接口是最底层的 `IO` 写入接口，如果业务需要自定义日志内容打印，建议使用 `Handler` 特性，参考章节： [日志组件-Handler](日志组件-Handler.md)
:::
## 自定义 `Writer` 接口

`glog` 模块实现了标准输出以及文件输出的日志内容打印。当然，开发者也可以通过自定义 `io.Writer` 接口实现自定义的日志内容输出。 `io.Writer` 是标准库提供的内容输出接口，其定义如下：

```go
type Writer interface {
    Write(p []byte) (n int, err error)
}
```

我们可以通过 `SetWriter` 方法或者链式方法 `To` 来实现自定义 `Writer` 输出，开发者可以在该 `Writer` 中实现定义的操作，也可以在其中整合其他的模块功能。

此外， `glog.Logger` 对象已经实现了 `io.Writer` 接口，因此开发者可以非常方便地将 `glog` 整合使用到其他的模块中。

## 示例1，实现日志 `HOOK`

在该示例中，我们实现了一个自定义的 `Writer` 对象 `MyWriter`，在该对象实现的 `Writer` 接口中我们对日志内容进行判断，如果出现了 `PANI` 或者 `FATA` 错误，那么表示是非常严重的错误，该接口将会第一时间通过 `HTTP` 接口告知 `Monitor` 监控服务。随后再将日志内容通过 `glog` 模块按照配置写入到文件和标准输出。

```go
package main

import (
    "context"
    "fmt"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/os/glog"
    "github.com/gogf/gf/v2/text/gregex"
)

type MyWriter struct {
    logger *glog.Logger
}

func (w *MyWriter) Write(p []byte) (n int, err error) {
    var (
        s   = string(p)
        ctx = context.Background()
    )
    if gregex.IsMatchString(`PANI|FATA`, s) {
        fmt.Println("SERIOUS ISSUE OCCURRED!! I'd better tell monitor in first time!")
        g.Client().PostContent(ctx, "http://monitor.mydomain.com", s)
    }
    return w.logger.Write(p)
}

func main() {
    var ctx = context.Background()
    glog.SetWriter(&MyWriter{
        logger: glog.New(),
    })
    glog.Fatal(ctx, "FATAL ERROR")
}
```

执行后，输出结果为：

```html
SERIOUS ISSUE OCCURRED!! I'd better tell monitor in first time!
2019-05-23 20:14:49.374 [FATA] FATAL ERROR
Stack:
1. /Users/john/Workspace/Go/GOPATH/src/github.com/gogf/gf/v2/geg/os/glog/glog_writer_hook.go:27
```

## 示例2，整合 `graylog`

假如我们需要输出日志到文件及标准输出，并且同时也需要输出日志到 `Graylog`，很明显这个也是需要自定义 `Writer` 才能实现。当然同理，我们也可以自定义输出到其他的日志收集组件或者数据库中。

> `Graylog` 是与 `ELK` 可以相提并论的一款集中式日志管理方案，支持数据收集、检索、可视化 `Dashboard`。

示例代码：

```go
package main

import (
    "context"

    "github.com/gogf/gf/v2/os/glog"
    "github.com/robertkowalski/graylog-golang"
)

type MyGrayLogWriter struct {
    gelf    *gelf.Gelf
    logger  *glog.Logger
}

func (w *MyGrayLogWriter) Write(p []byte) (n int, err error) {
    w.gelf.Send(p)
    return w.logger.Write(p)
}

func main() {
    var ctx = context.Background()
    glog.SetWriter(&MyGrayLogWriter{
        logger : glog.New(),
        gelf   : gelf.New(gelf.Config{
            GraylogPort     : 80,
            GraylogHostname : "graylog-host.com",
            Connection      : "wan",
            MaxChunkSizeWan : 42,
            MaxChunkSizeLan : 1337,
        }),
    })
    glog.Println(ctx, "test log")
}
```