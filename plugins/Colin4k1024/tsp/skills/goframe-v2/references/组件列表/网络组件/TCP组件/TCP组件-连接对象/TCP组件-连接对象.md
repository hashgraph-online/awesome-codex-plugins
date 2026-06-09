`gtcp` 模块提供了简便易用的 `gtcp.Conn` 链接操作对象。

**使用方式**：

```go
import "github.com/gogf/gf/v2/net/gtcp"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/net/gtcp](https://pkg.go.dev/github.com/gogf/gf/v2/net/gtcp)

```go
type Conn
    func NewConn(addr string, timeout ...int) (*Conn, error)
    func NewConnByNetConn(conn net.Conn) *Conn
    func NewConnKeyCrt(addr, crtFile, keyFile string) (*Conn, error)
    func NewConnTLS(addr string, tlsConfig *tls.Config) (*Conn, error)
    func (c *Conn) Close() error
    func (c *Conn) LocalAddr() net.Addr
    func (c *Conn) Recv(length int, retry ...Retry) ([]byte, error)
    func (c *Conn) RecvLine(retry ...Retry) ([]byte, error)
    func (c *Conn) RecvWithTimeout(length int, timeout time.Duration, retry ...Retry) ([]byte, error)
    func (c *Conn) RemoteAddr() net.Addr
    func (c *Conn) Send(data []byte, retry ...Retry) error
    func (c *Conn) SendRecv(data []byte, receive int, retry ...Retry) ([]byte, error)
    func (c *Conn) SendRecvWithTimeout(data []byte, receive int, timeout time.Duration, retry ...Retry) ([]byte, error)
    func (c *Conn) SendWithTimeout(data []byte, timeout time.Duration, retry ...Retry) error
    func (c *Conn) SetDeadline(t time.Time) error
    func (c *Conn) SetRecvBufferWait(bufferWaitDuration time.Duration)
    func (c *Conn) SetRecvDeadline(t time.Time) error
    func (c *Conn) SetSendDeadline(t time.Time) error
```

## 写入操作

TCP通信写入操作由 `Send` 方法实现，并提供了错误重试的机制，由第二个非必需参数 `retry` 提供。需要注意的是 `Send` 方法不带任何的缓冲机制，也就是说每调用一次 `Send` 方法将会立即调用底层的TCP Write方法写入数据(缓冲机制依靠系统底层实现)。因此，如果想要进行输出缓冲控制，请在业务层进行处理。

在进行TCP写入时，可靠的通信场景下往往是一写一读，即 `Send` 成功之后接着便开始 `Recv` 获取目标的反馈结果。因此 `gtcp.Conn` 也提供了方便的 `SendRecv` 方法。

## 读取操作

TCP通信读取操作由 `Recv` 方法实现，同时也提供了错误重试的机制，由第二个非必需参数 `retry` 提供。 `Recv` 方法提供了内置的读取缓冲控制，读取数据时可以指定读取的长度（由 `length` 参数指定），当读取到指定长度的数据后将会立即返回。如果 `length < 0` 那么将会读取所有可读取的缓冲区数据并返回。当 `length = 0` 时表示获取一次缓冲区的数据后立即返回。

如果使用 `Recv(-1)` 可以读取所有缓冲区可读数据(长度不定，如果发送的数据包太长有可能会被截断)，但需要注意包的解析问题，容易产生非完整包的情况。这个时候，业务层需要根据既定的数据包结构自己负责包的完整性处理。推荐使用后续介绍的 `简单协议` 通过 `SendPkg`/ `RecvPkg` 来实现消息包的发送/接收，具体请查看后续章节。

## 超时处理

`gtcp.Conn` 对TCP通信时的数据写入和读取提供了超时处理，通过方法中的 `timeout` 参数指定，这块比较简单，不过多阐述。

* * *

我们接下来通过通过几个例子来看看如何使用 `gtcp.Conn` 对象。

## 使用示例

### 示例1，简单使用

```go
package main

import (
    "fmt"
    "time"
    "github.com/gogf/gf/v2/net/gtcp"
    "github.com/gogf/gf/v2/os/glog"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    // Server
    go gtcp.NewServer("127.0.0.1:8999", func(conn *gtcp.Conn) {
        defer conn.Close()
        for {
            data, err := conn.Recv(-1)
            if len(data) > 0 {
                  fmt.Println(string(data))
            }
            if err != nil {
                break
            }
        }
    }).Run()

    time.Sleep(time.Second)

    // Client
    conn, err := gtcp.NewConn("127.0.0.1:8999")
    if err != nil {
        panic(err)
    }
    for i := 0; i < 10000; i++ {
        if err := conn.Send([]byte(gconv.String(i))); err != nil {
            glog.Error(err)
        }
        time.Sleep(time.Second)
    }
}
```

1. `Server` 端，接收到客户端的数据后立即打印到终端上。
2. `Client` 端，使用同一个连接对象，在循环中每隔1秒向服务端发送当前递增的数字。同时，该功能也可以演示出底层 `Socket` 通信并没有使用缓冲实现，也就是说，执行一次 `Send` 即立刻向服务端发送数据。因此，客户端需要在本地自行管理好需要发送的缓冲数据。
3. 执行结果 执行后，可以看到Server在终端上输出以下信息：

```shell
    2018-07-11 22:11:08.650 0
    2018-07-11 22:11:09.651 1
    2018-07-11 22:11:10.651 2
    2018-07-11 22:11:11.651 3
    2018-07-11 22:11:12.651 4
    2018-07-11 22:11:13.651 5
    2018-07-11 22:11:14.652 6
    2018-07-11 22:11:15.652 7
    2018-07-11 22:11:16.652 8
    2018-07-11 22:11:17.652 9
    2018-07-11 22:11:18.652 10
    2018-07-11 22:11:19.653 11
    ...
```

### 示例2，回显服务

我们将之前的回显服务改进一下：

```go
package main

import (
    "fmt"
    "time"
    "github.com/gogf/gf/v2/net/gtcp"
    "github.com/gogf/gf/v2/os/glog"
    "github.com/gogf/gf/v2/os/gtime"
)

func main() {
    // Server
    go gtcp.NewServer("127.0.0.1:8999", func(conn *gtcp.Conn) {
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

    time.Sleep(time.Second)

    // Client
    for {
       if conn, err := gtcp.NewConn("127.0.0.1:8999"); err == nil {
           if b, err := conn.SendRecv([]byte(gtime.Datetime()), -1); err == nil {
               fmt.Println(string(b), conn.LocalAddr(), conn.RemoteAddr())
           } else {
               fmt.Println(err)
           }
           conn.Close()
       } else {
           glog.Error(err)
       }
       time.Sleep(time.Second)
    }
}
```

该示例程序中， `Client` 每隔1秒钟向 `Server` 发送当前的时间信息， `Server` 接收到之后返回原数据信息， `Client` 接收到 `Server` 端返回信息后立即打印到终端。

执行后，输出结果为：

```
> 2018-07-19 23:25:43 127.0.0.1:34306 127.0.0.1:8999
> 2018-07-19 23:25:44 127.0.0.1:34308 127.0.0.1:8999
> 2018-07-19 23:25:45 127.0.0.1:34312 127.0.0.1:8999
> 2018-07-19 23:25:46 127.0.0.1:34314 127.0.0.1:8999
```

### 示例3，HTTP客户端

我们在这个示例中使用gtcp包来实现一个简单的HTTP客户端，读取并打印出百度首页的 `header` 和 `content` 内容。

```go
package main

import (
    "fmt"
    "bytes"
    "github.com/gogf/gf/v2/net/gtcp"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    conn, err := gtcp.NewConn("www.baidu.com:80")
    if err != nil {
        panic(err)
    }
    defer conn.Close()

    if err := conn.Send([]byte("GET / HTTP/1.1\r\n\r\n")); err != nil {
        panic(err)
    }

    header        := make([]byte, 0)
    content       := make([]byte, 0)
    contentLength := 0
    for {
        data, err := conn.RecvLine()
        // header读取，解析文本长度
        if len(data) > 0 {
            array := bytes.Split(data, []byte(": "))
            // 获得页面内容长度
            if contentLength == 0 && len(array) == 2 && bytes.EqualFold([]byte("Content-Length"), array[0]) {
                contentLength = gconv.Int(string(array[1][:len(array[1])-1]))           }
            header = append(header, data...)
            header = append(header, '\n')
        }
        // header读取完毕，读取文本内容
        if contentLength > 0 && len(data) == 1 {
            content, _ = conn.Recv(contentLength)
            break
        }
        if err != nil {
            fmt.Errorf("ERROR: %s\n", err.Error())
            break
        }
    }

    if len(header) > 0 {
        fmt.Println(string(header))
    }
    if len(content) > 0 {
        fmt.Println(string(content))
    }
}
```

执行后，输出结果为：

```
HTTP/1.1 200 OK
Accept-Ranges: bytes
Cache-Control: no-cache
Connection: Keep-Alive
Content-Length: 14615
Content-Type: text/html
Date: Sat, 21 Jul 2018 04:21:03 GMT
Etag: "5b3c3650-3917"
Last-Modified: Wed, 04 Jul 2018 02:52:00 GMT
P3p: CP=" OTI DSP COR IVA OUR IND COM "
Pragma: no-cache
Server: BWS/1.1
...
(略)
```