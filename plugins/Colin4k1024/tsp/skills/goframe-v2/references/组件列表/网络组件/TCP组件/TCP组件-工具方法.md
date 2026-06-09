`gtcp` 模块也提供了一些常用的工具方法。

**使用方式**：

```go
import "github.com/gogf/gf/v2/net/gtcp"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/net/gtcp](https://pkg.go.dev/github.com/gogf/gf/v2/net/gtcp)

```go
func LoadKeyCrt(crtFile, keyFile string) (*tls.Config, error)
func NewNetConn(addr string, timeout ...int) (net.Conn, error)
func NewNetConnKeyCrt(addr, crtFile, keyFile string) (net.Conn, error)
func NewNetConnTLS(addr string, tlsConfig *tls.Config) (net.Conn, error)
func Send(addr string, data []byte, retry ...Retry) error
func SendPkg(addr string, data []byte, option ...PkgOption) error
func SendPkgWithTimeout(addr string, data []byte, timeout time.Duration, option ...PkgOption) error
func SendRecv(addr string, data []byte, receive int, retry ...Retry) ([]byte, error)
func SendRecvPkg(addr string, data []byte, option ...PkgOption) ([]byte, error)
func SendRecvPkgWithTimeout(addr string, data []byte, timeout time.Duration, option ...PkgOption) ([]byte, error)
func SendRecvWithTimeout(addr string, data []byte, receive int, timeout time.Duration, retry ...Retry) ([]byte, error)
func SendWithTimeout(addr string, data []byte, timeout time.Duration, retry ...Retry) error
```

1. `NewNetConn` 用于简化标准库连接对象 `net.Conn` 的创建；
2. `NewNetConnTLS` 和 `NewNetConnKeyCrt` 用于创建支持TLS安全加密通信的TCP客户端；
3. `Send*` 系列方法直接通过给定地址进行数据发送，并获取该请求的返回结果，用于短链接请求的情况；

以下为一个简单的示例，我们使用工具方法来访问指定的Web站点：

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/net/gtcp"
)

func main() {
    data, err := gtcp.SendRecv("www.baidu.com:80", []byte("HEAD / HTTP/1.1\n\n"), -1)
    if err != nil {
        panic(err)
    }
    fmt.Println(string(data))
}
```

在这个示例中，我们通过TCP访问百度首页，模拟HTTP请求头信息，并获得返回结果。 执行后，输出结果如下：

```
HTTP/1.1 302 Found
Connection: Keep-Alive
Content-Length: 17931
Content-Type: text/html
Date: Tue, 04 Jun 2019 15:53:09 GMT
Etag: "54d9749e-460b"
Server: bfe/1.0.8.18
```