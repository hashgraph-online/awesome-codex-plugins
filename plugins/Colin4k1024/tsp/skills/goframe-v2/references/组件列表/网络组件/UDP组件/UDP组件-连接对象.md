`gudp` 模块提供了非常简便易用的 `gudp.Conn` 链接操作对象。

**使用方式**：

```go
import "github.com/gogf/gf/v2/net/gudp"
```

**接口文档**： [https://pkg.go.dev/github.com/gogf/gf/v2/net/gudp](https://pkg.go.dev/github.com/gogf/gf/v2/net/gudp)

## 基本介绍

`gudp.Conn` 的操作绝大部分类似于 `gtcp` 的操作方式（大部分的方法名称也相同），但由于 `UDP` 是面向非连接的协议，因此 `gudp.Conn`（底层通信端口）也只能完成最多一次数据写入和读取，客户端下一次再与目标服务端进行通信的时候，将需要创建新的 `Conn` 对象进行通信。

## 使用示例

```go
package main

import (
    "context"
    "fmt"
    "time"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/gudp"
    "github.com/gogf/gf/v2/os/gtime"
)

func main() {
    var (
        ctx    = context.Background()
        logger = g.Log()
    )
    // Server
    go gudp.NewServer("127.0.0.1:8999", func(conn *gudp.ServerConn) {
        defer conn.Close()
        for {
            data, addr, err := conn.Recv(-1)
            if len(data) > 0 {
                if err = conn.Send(append([]byte("> "), data...), addr); err != nil {
                    logger.Error(ctx, err)
                }
            }
            if err != nil {
                logger.Error(ctx, err)
            }
        }
    }).Run()

    time.Sleep(time.Second)

    // Client
    for {
        if conn, err := gudp.NewClientConn("127.0.0.1:8999"); err == nil {
            if b, err := conn.SendRecv([]byte(gtime.Datetime()), -1); err == nil {
                fmt.Println(string(b), conn.LocalAddr(), conn.RemoteAddr())
            } else {
                logger.Error(ctx, err)
            }
            conn.Close()
        } else {
            logger.Error(ctx, err)
        }
        time.Sleep(time.Second)
    }
}
```

该示例与 `gtcp.Conn` 中的通信示例类似，不同的是，客户端与服务端无法保持连接，每次通信都需要创建的新的连接对象进行通信。

执行后，输出结果如下：

```text
> 2018-07-21 23:13:31 127.0.0.1:33271 127.0.0.1:8999
> 2018-07-21 23:13:32 127.0.0.1:45826 127.0.0.1:8999
> 2018-07-21 23:13:33 127.0.0.1:58027 127.0.0.1:8999
> 2018-07-21 23:13:34 127.0.0.1:33056 127.0.0.1:8999
> 2018-07-21 23:13:35 127.0.0.1:39260 127.0.0.1:8999
> 2018-07-21 23:13:36 127.0.0.1:33967 127.0.0.1:8999
> 2018-07-21 23:13:37 127.0.0.1:52359 127.0.0.1:8999
...
```