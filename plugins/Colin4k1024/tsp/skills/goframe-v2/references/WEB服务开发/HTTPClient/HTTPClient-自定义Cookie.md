HTTP客户端发起请求时可以自定义发送给服务端的 `Cookie` 内容，该特性使用 `SetCookie*` 相关方法实现。

方法列表：

```go
func (c *Client) SetCookie(key, value string) *Client
func (c *Client) SetCookieMap(m map[string]string) *Client
```

我们来看一个客户端自定义 `Cookie` 的示例。

### 服务端

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    s := g.Server()
    s.BindHandler("/", func(r *ghttp.Request){
        r.Response.Write(r.Cookie.Map())
    })
    s.SetPort(8199)
    s.Run()
}
```

由于是作为示例，服务端的逻辑很简单，直接将接收到的 `Cookie` 参数全部返回给客户端。

### 客户端

1. 使用 `SetCookie` 方法

```go
package main

import (
       "fmt"

       "github.com/gogf/gf/v2/frame/g"
       "github.com/gogf/gf/v2/os/gctx"
)

func main() {
       c := g.Client()
       c.SetCookie("name", "john")
       c.SetCookie("score", "100")
       if r, e := c.Get(gctx.New(), "http://127.0.0.1:8199/"); e != nil {
           panic(e)
       } else {
           fmt.Println(r.ReadAllString())
       }
}
```

通过 `g.Client()` 创建一个自定义的HTTP请求客户端对象，并通过 `c.SetCookie` 方法设置自定义的 `Cookie`，这里我们设置了两个示例用的 `Cookie` 参数，一个 `name`，一个 `score`。

2. 使用 `SetCookieMap` 方法

这个方法更加简单，可以批量设置 `Cookie` 键值对。

```go
package main

import (
       "fmt"

       "github.com/gogf/gf/v2/frame/g"
       "github.com/gogf/gf/v2/os/gctx"
)

func main() {
       c := g.Client()
       c.SetCookieMap(g.MapStrStr{
           "name":  "john",
           "score": "100",
       })
       if r, e := c.Get(gctx.New(), "http://127.0.0.1:8199/"); e != nil {
           panic(e)
       } else {
           fmt.Println(r.ReadAllString())
       }
}
```

3. 执行结果

客户端代码执行后，终端将会打印出服务端的返回结果，如下：

```
map[name:john score:100]
```

可以看到，服务端已经接收到了客户端自定义的 `Cookie` 参数。