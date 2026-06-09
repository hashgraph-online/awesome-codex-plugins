`gtcp` 模块支持 `TLS` 加密通信服务端及客户端，在对安全要求比较高的场景中非常必要。 `TLS` 服务端创建可以通过 `NewServerTLS` 或者 `NewServerKeyCrt` 方法实现。 `TLS` 客户端创建可以通过 `NewConnKeyCrt` 或者 `NewConnTLS` 方法实现。

使用示例：

[https://github.com/gogf/gf/tree/master/.example/net/gtcp/tls](https://github.com/gogf/gf/tree/master/.example/net/gtcp/tls)

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/gtcp"
    "github.com/gogf/gf/v2/util/gconv"
    "time"
)

func main() {
    address := "127.0.0.1:8999"
    crtFile := "server.crt"
    keyFile := "server.key"
    // TLS Server
    go gtcp.NewServerKeyCrt(address, crtFile, keyFile, func(conn *gtcp.Conn) {
        defer conn.Close()
        for {
            data, err := conn.Recv(-1)
            if len(data) > 0 {
                fmt.Println(string(data))
            }
            if err != nil {
                // if client closes, err will be: EOF
                g.Log().Error(err)
                break
            }
        }
    }).Run()

    time.Sleep(time.Second)

    // Client
    conn, err := gtcp.NewConnKeyCrt(address, crtFile, keyFile)
    if err != nil {
        panic(err)
    }
    defer conn.Close()
    for i := 0; i < 10; i++ {
        if err := conn.Send([]byte(gconv.String(i))); err != nil {
            g.Log().Error(err)
        }
        time.Sleep(time.Second)
        if i == 5 {
            conn.Close()
            break
        }
    }

    // exit after 5 seconds
    time.Sleep(5 * time.Second)
}
```

执行后，可以看到客户端执行时报错：

```
panic: x509: certificate has expired or is not yet valid
```

那是因为我们的证书是手动创建的，并且已经过期了，为了演示方便，我们在客户端代码中去掉客户端对证书的校验。

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/net/gtcp"
    "github.com/gogf/gf/v2/util/gconv"
    "time"
)

func main() {
    address := "127.0.0.1:8999"
    crtFile := "server.crt"
    keyFile := "server.key"
    // TLS Server
    go gtcp.NewServerKeyCrt(address, crtFile, keyFile, func(conn *gtcp.Conn) {
        defer conn.Close()
        for {
            data, err := conn.Recv(-1)
            if len(data) > 0 {
                fmt.Println(string(data))
            }
            if err != nil {
                // if client closes, err will be: EOF
                g.Log().Error(err)
                break
            }
        }
    }).Run()

    time.Sleep(time.Second)

    // Client
    tlsConfig, err := gtcp.LoadKeyCrt(crtFile, keyFile)
    if err != nil {
        panic(err)
    }
    tlsConfig.InsecureSkipVerify = true

    conn, err := gtcp.NewConnTLS(address, tlsConfig)
    if err != nil {
        panic(err)
    }
    defer conn.Close()
    for i := 0; i < 10; i++ {
        if err := conn.Send([]byte(gconv.String(i))); err != nil {
            g.Log().Error(err)
        }
        time.Sleep(time.Second)
        if i == 5 {
            conn.Close()
            break
        }
    }

    // exit after 5 seconds
    time.Sleep(5 * time.Second)
}
```

执行后，终端输出结果为：

```0
1
2
3
4
5
2019-06-05 00:13:12.488 [ERRO] EOF
Stack:
1. /Users/john/Workspace/Go/GOPATH/src/github.com/gogf/gf/v2/geg/net/gtcp/tls/gtcp_server_client.go:25
```

其中客户端在 `5` 秒后关闭了连接，因此服务端在接收数据时获取到了一个 `EOF` 错误，这种错误在正式使用中我们直接忽略，报错时服务端直接关闭客户端连接即可。