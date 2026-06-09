允许接口跨域往往是需要结合 [路由管理-中间件/拦截器](../%E8%B7%AF%E7%94%B1%E7%AE%A1%E7%90%86/%E8%B7%AF%E7%94%B1%E7%AE%A1%E7%90%86-%E4%B8%AD%E9%97%B4%E4%BB%B6%E6%8B%A6%E6%88%AA%E5%99%A8/%E4%B8%AD%E9%97%B4%E4%BB%B6%E6%8B%A6%E6%88%AA%E5%99%A8-%E5%9F%BA%E6%9C%AC%E4%BB%8B%E7%BB%8D.md) 一起使用，来统一设置某些路由规则下的接口可以跨域访问。同时，针对允许 `WebSocket` 的跨域请求访问，也是通过该方式来实现。

相关方法： [https://pkg.go.dev/github.com/gogf/gf/v2/net/ghttp#Response](https://pkg.go.dev/github.com/gogf/gf/v2/net/ghttp#Response)

```go
func (r *Response) CORS(options CORSOptions)
func (r *Response) CORSAllowedOrigin(options CORSOptions) bool
func (r *Response) CORSDefault()
func (r *Response) DefaultCORSOptions() CORSOptions
```

### `CORS` 对象

`CORS` 是 `W3` 互联网标准组织对HTTP跨域请求的标准，在 `ghttp` 模块中，我们可以通过 `CORSOptions` 对象来管理对应的跨域请求选项。定义如下：

```go
// See https://www.w3.org/TR/cors/ .
// 服务端允许跨域请求选项
type CORSOptions struct {
    AllowDomain      []string // Used for allowing requests from custom domains
    AllowOrigin      string   // Access-Control-Allow-Origin
    AllowCredentials string   // Access-Control-Allow-Credentials
    ExposeHeaders    string   // Access-Control-Expose-Headers
    MaxAge           int      // Access-Control-Max-Age
    AllowMethods     string   // Access-Control-Allow-Methods
    AllowHeaders     string   // Access-Control-Allow-Headers
}
```

具体参数的介绍请查看W3组织 [官网手册](https://www.w3.org/TR/cors/)。

### `CORS` 配置

#### 默认 `CORSOptions`

当然，为方便跨域设置，在 `ghttp` 模块中也提供了默认的跨域请求选项，通过 `DefaultCORSOptions` 方法获取。大多数情况下，我们在需要允许跨域请求的接口中（一般情况下使用中间件）可以直接使用 `CORSDefault()` 允许该接口跨域访问。

#### 限制 `Origin` 来源

大多数时候，我们需要限制请求来源为我们受信任的域名列表，我们可以使用 `AllowDomain` 配置，使用方式：

```go
// 允许跨域请求中间件
func Middleware(r *ghttp.Request) {
    corsOptions := r.Response.DefaultCORSOptions()
    corsOptions.AllowDomain = []string{"goframe.org", "johng.cn"}
    r.Response.CORS(corsOptions)
    r.Middleware.Next()
}
```

### `OPTIONS` 请求

有的客户端，部分浏览器在发送 `AJAX` 请求之前会首先发送 `OPTIONS` 预请求检测后续请求是否允许发送。 `GoFrame` 框架的 `Server` 完全遵守 `W3C` 关于 `OPTIONS` 请求方法的规范约定，因此只要服务端设置好 `CORS` 中间件， `OPTIONS` 请求也将会自动支持。

### 示例1，基本使用

我们来看一个简单的接口示例：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func Order(r *ghttp.Request) {
    r.Response.Write("GET")
}

func main() {
    s := g.Server()
    s.Group("/api.v1", func(group *ghttp.RouterGroup) {
        group.GET("/order", Order)
    })
    s.SetPort(8199)
    s.Run()
}
```

接口地址是 [http://localhost/api.v1/order](http://localhost/api.v1/order) ，当然这个接口是不允许跨域的。我们打开一个不同的域名，例如：百度首页(正好用了 `jQuery`，方便调试)，然后按 `F12` 打开开发者面板，在 `console` 下执行以下 `AJAX` 请求：

```
$.get("http://localhost:8199/api.v1/order", function(result){
    console.log(result)
});
```

结果如下：

返回了不允许跨域请求的提示错误，接着我们修改一下服务端接口的测试代码，如下：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func MiddlewareCORS(r *ghttp.Request) {
    r.Response.CORSDefault()
    r.Middleware.Next()
}

func Order(r *ghttp.Request) {
    r.Response.Write("GET")
}

func main() {
    s := g.Server()
    s.Group("/api.v1", func(group *ghttp.RouterGroup) {
        group.Middleware(MiddlewareCORS)
        group.GET("/order", Order)
    })
    s.SetPort(8199)
    s.Run()
}
```

我们增加了针对于路由 `/api.v1` 的前置中间件 `MiddlewareCORS`，该事件将会在所有服务执行之前调用。我们通过调用 `CORSDefault` 方法使用默认的跨域设置允许跨域请求。该绑定的事件路由规则使用了模糊匹配规则，表示所有 `/api.v1` 开头的接口地址都允许跨域请求。

返回刚才的百度首页，再次执行请求 `AJAX` 请求，这次便成功了：

当然我们也可以通过 `CORSOptions` 对象以及 `CORS` 方法对跨域请求做更多的设置。

### 示例2，授权跨域 `Origin`

在大多数场景中，我们是需要自定义授权跨域的 `Origin`，那么我们可以将以上的例子改进如下，在该示例中，我们仅允许 `goframe.org` 及 `baidu.com` 跨域请求访问。

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func MiddlewareCORS(r *ghttp.Request) {
    corsOptions := r.Response.DefaultCORSOptions()
    corsOptions.AllowDomain = []string{"goframe.org", "baidu.com"}
    r.Response.CORS(corsOptions)
    r.Middleware.Next()
}

func Order(r *ghttp.Request) {
    r.Response.Write("GET")
}

func main() {
    s := g.Server()
    s.Group("/api.v1", func(group *ghttp.RouterGroup) {
        group.Middleware(MiddlewareCORS)
        group.GET("/order", Order)
    })
    s.SetPort(8199)
    s.Run()
}
```

### 示例3，自定义检测授权

不知大家是否有注意，在以上的示例中有个细节，即使当前接口不允许跨域访问，但是只要接口被调用，接口完整逻辑仍会被执行，在服务端其实也已经走完了一次请求流程。针对于这个问题，我们可以通过自定义授权 `Origin` 并在中间件中通过 `CORSAllowedOrigin` 方法来做判断，如果当前请求的 `Origin` 在服务端是被允许执行的，那么才会执行后续流程，否则便会终止执行。

在以下示例中，仅允许来自 `goframe.org` 域名的跨域请求，而来自其他域名的请求将会失败并返回 `403`：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func MiddlewareCORS(r *ghttp.Request) {
    corsOptions := r.Response.DefaultCORSOptions()
    corsOptions.AllowDomain = []string{"goframe.org"}
    if !r.Response.CORSAllowedOrigin(corsOptions) {
        r.Response.WriteStatus(http.StatusForbidden)
        return
    }
    r.Response.CORS(corsOptions)
    r.Middleware.Next()
}

func Order(r *ghttp.Request) {
    r.Response.Write("GET")
}

func main() {
    s := g.Server()
    s.Group("/api.v1", func(group *ghttp.RouterGroup) {
        group.Middleware(MiddlewareCORS)
        group.GET("/order", Order)
    })
    s.SetPort(8199)
    s.Run()
}
```