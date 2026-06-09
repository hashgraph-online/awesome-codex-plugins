## 基本介绍
`gtcp` 模块实现简便易用、轻量级的 `TCPServer` 服务端。

**使用方式**：

```go
import "github.com/gogf/gf/v2/net/gtcp"
```

**接口文档**： [https://pkg.go.dev/github.com/gogf/gf/v2/net/gtcp](https://pkg.go.dev/github.com/gogf/gf/v2/net/gtcp)

```go
type Server
    func GetServer(name ...interface{}) *Server
    func NewServer(address string, handler func(*Conn), name ...string) *Server
    func NewServerKeyCrt(address, crtFile, keyFile string, handler func(*Conn), name ...string) *Server
    func NewServerTLS(address string, tlsConfig *tls.Config, handler func(*Conn), name ...string) *Server
    func (s *Server) Close() error
    func (s *Server) Run() (err error)
    func (s *Server) SetAddress(address string)
    func (s *Server) SetHandler(handler func(*Conn))
    func (s *Server) SetTLSConfig(tlsConfig *tls.Config)
    func (s *Server) SetTLSKeyCrt(crtFile, keyFile string) error
```

其中， `GetServer` 使用单例模式通过给定一个唯一的名称获取/创建一个单例 `Server`，后续可通过 `SetAddress` 和 `SetHandler` 方法动态修改Server属性； `NewServer` 则直接根据给定参数创建一个Server对象，并可指定名称。

我们通过实现一个简单的 `echo服务器` 来演示 `TCPServer` 的使用：

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/net/gtcp"
)

func main() {
    gtcp.NewServer("127.0.0.1:8999", func(conn *gtcp.Conn) {
        defer conn.Close()
        for {
            data, err := conn.Recv(-1)
            if len(data) > 0 {
                if err := conn.Send(append([]byte("> "), data...)); err != nil {
                  fmt.Println(err)
                }
            }
            if err != nil {
                break
            }
        }
    }).Run()
}
```

在这个示例中我们使用了 `Send` 和 `Recv` 来发送和接收数据。其中 `Recv` 方法会通过阻塞方式接收数据，直到客户端”发送完毕一条数据”(执行一次 `Send`，底层Socket通信不带缓冲实现)，或者关闭链接。关于其中的链接对象 `gtcp.Conn` 的介绍，请继续阅读后续章节。

执行之后我们使用 `telnet` 工具来进行测试：

```bash
john@home:~$ telnet 127.0.0.1 8999
Trying 127.0.0.1...
Connected to 127.0.0.1.
Escape character is '^]'.
hello
> hello
hi there
> hi there
```

每一个客户端发起的TCP链接，TCPServer都会创建一个 `goroutine` 进行处理，直至TCP链接断开。由于goroutine比较轻量级，因此可以支撑很高的并发量。

## 相关文档