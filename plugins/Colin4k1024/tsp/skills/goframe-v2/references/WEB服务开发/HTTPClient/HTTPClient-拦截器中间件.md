## 基本介绍

`HTTPClient` 支持强大的拦截器/中间件特性，该特性使得对于客户端的全局请求拦截及注入成为了可能，例如修改/注入提交参数、修改/注入返回参数、基于客户端的参数校验等等。中间件的注入通过以下方法实现：

```go
func (c *Client) Use(handlers ...HandlerFunc) *Client
```

在中间件中通过 `Next` 方法执行下一步流程， `Next` 方法定义如下：

```go
func (c *Client) Next(req *http.Request) (*Response, error)
```

## 中间件类型

`HTTPClient` 中间件功能同 `HTTPServer` 的中间件功能类似，同样也是分为了前置中间件和后置中间件两种。

### 前置中间件

处理逻辑位于 `Next` 方法之前，格式形如：

```go
c := g.Client()
c.Use(func(c *gclient.Client, r *http.Request) (resp *gclient.Response, err error) {
    // 自定义处理逻辑
    resp, err = c.Next(r)
    return resp, err
})
```

### 后置中间件

处理逻辑位于 `Next` 方法之后，格式形如：

```go
c := g.Client()
c.Use(func(c *gclient.Client, r *http.Request) (resp *gclient.Response, err error) {
    resp, err = c.Next(r)
    // 自定义处理逻辑
    return resp, err
})
```

## 使用示例

我们来一个代码示例更好介绍使用，该示例通过给客户端增加拦截器，对提交的JSON数据注入自定义的额外参数，这些额外参数实现对提交参数的签名生成体积签名相关参数提交，也就是实现一版简单的接口参数安全校验。

### 服务端

服务端的逻辑很简单，就是把客户端提交的 `JSON` 参数按照 `map` 解析后再构造成 `JSON` 字符串返回给客户端。
:::note
往往服务端也需要通过中间件进行签名校验，我这里偷了一个懒，直接返回了客户端提交的数据。体谅一下文档维护作者😸。
:::
```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    s := g.Server()
    s.Group("/", func(group *ghttp.RouterGroup) {
        group.ALL("/", func(r *ghttp.Request) {
            r.Response.Write(r.GetMap())
        })
    })
    s.SetPort(8199)
    s.Run()
}
```

### 客户端

客户端的逻辑是实现基本的客户端参数提交、拦截器注入、签名相关参数注入以及签名参数生成。

```go
package main

import (
    "bytes"
    "fmt"
    "io/ioutil"
    "net/http"

    "github.com/gogf/gf/v2/container/garray"
    "github.com/gogf/gf/v2/crypto/gmd5"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/internal/json"
    "github.com/gogf/gf/v2/net/gclient"
    "github.com/gogf/gf/v2/os/gctx"
    "github.com/gogf/gf/v2/os/gtime"
    "github.com/gogf/gf/v2/util/gconv"
    "github.com/gogf/gf/v2/util/guid"
    "github.com/gogf/gf/v2/util/gutil"
)

const (
    appId     = "123"
    appSecret = "456"
)

// 注入统一的接口签名参数
func injectSignature(jsonContent []byte) []byte {
    var m map[string]interface{}
    _ = json.Unmarshal(jsonContent, &m)
    if len(m) > 0 {
        m["appid"] = appId
        m["nonce"] = guid.S()
        m["timestamp"] = gtime.Timestamp()
        var (
            keyArray   = garray.NewSortedStrArrayFrom(gutil.Keys(m))
            sigContent string
        )
        keyArray.Iterator(func(k int, v string) bool {
            sigContent += v
            sigContent += gconv.String(m[v])
            return true
        })
        m["signature"] = gmd5.MustEncryptString(gmd5.MustEncryptString(sigContent) + appSecret)
        jsonContent, _ = json.Marshal(m)
    }
    return jsonContent
}

func main() {
    c := g.Client()
    c.Use(func(c *gclient.Client, r *http.Request) (resp *gclient.Response, err error) {
        bodyBytes, _ := ioutil.ReadAll(r.Body)
        if len(bodyBytes) > 0 {
            // 注入签名相关参数，修改Request原有的提交参数
            bodyBytes = injectSignature(bodyBytes)
            r.Body = ioutil.NopCloser(bytes.NewBuffer(bodyBytes))
            r.ContentLength = int64(len(bodyBytes))
        }
        return c.Next(r)
    })
    content := c.ContentJson().PostContent(gctx.New(), "http://127.0.0.1:8199/", g.Map{
        "name": "goframe",
        "site": "https://goframe.org",
    })
    fmt.Println(content)
}
```

### 运行测试

先运行服务端：

```bash
$ go run server.go

  SERVER  | DOMAIN  | ADDRESS | METHOD | ROUTE |      HANDLER      | MIDDLEWARE
----------|---------|---------|--------|-------|-------------------|-------------
  default | default | :8199   | ALL    | /     | main.main.func1.1 |
----------|---------|---------|--------|-------|-------------------|-------------

2021-05-18 09:23:41.865 97906: http server started listening on [:8199]
```

再运行客户端：

```bash
$ go run client.go
{"appid":"123","name":"goframe","nonce":"12vd8tx23l6cbfz9k59xehk1002pixfo","signature":"578a90b67bdc63d551d6a18635307ba2","site":"https://goframe.org","timestamp":1621301076}
$
```

可以看到，服务端接受到的参数多了多了几项，包括 `appid/nonce/timestamp/signature`，这些参数往往都是签名校验算法所需要的参数。