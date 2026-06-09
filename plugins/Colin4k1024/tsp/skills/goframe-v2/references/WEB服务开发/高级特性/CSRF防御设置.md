**跨站请求伪造**（英语： `Cross-Site Request Forgery`），也被称为**one-click attack**或者**session riding**，通常缩写为**CSRF** 或者**XSRF**， 是一种挟制用户在当前已登录的Web应用程序上执行非本意的操作的攻击方法。跟跨网站脚本（ `XSS`）相比， **XSS** 利用的是用户对指定网站的信任， `CSRF` 利用的是网站对用户网页浏览器的信任。

## 如何防御

这里我们选择通过 `token` 的方式对请求进行校验，通过中间件的方式实现， `CSRF` 跨站点防御插件由社区包提供。

开发者可以通过对接口添加中间件的方式，增加 `token` 校验功能。

感兴趣的朋友可以阅读插件源码 [https://github.com/gogf/csrf](https://github.com/gogf/csrf)

## 使用方式

### 引入插件包

```go
import "github.com/gogf/csrf"
```

### 配置接口中间件

`csrf` 插件支持自定义 `csrf.Config` 配置， `Config` 中的 `Cookie.Name` 是中间件设置到请求返回 `Cookie` **中** `token` 的名称， `ExpireTime` 是 `token` 超时时间， `TokenLength` 是 `token` 长度， `TokenRequestKey` 是后续请求需求带上的参数名。

```go
s := g.Server()
s.Group("/api.v2", func(group *ghttp.RouterGroup) {
    group.Middleware(csrf.NewWithCfg(csrf.Config{
        Cookie: &http.Cookie{
            Name: "_csrf",// token name in cookie
        },
        ExpireTime:      time.Hour * 24,
        TokenLength:     32,
        TokenRequestKey: "X-Token",// use this key to read token in request param
    }))
    group.ALL("/csrf", func(r *ghttp.Request) {
        r.Response.Writeln(r.Method + ": " + r.RequestURI)
    })
})
```

### 前端对接

通过配置后，前端在POST请求前从 `Cookie` 中读取 `_csrf` 的值（即 `token`），然后请求发出时将 `token` 以 `X-Token`（ `TokenRequestKey` 所设置）参数名置入请求中（可以是 `Header` 或者 `Form`）即可通过 `token` 校验。

## 代码示例

### 使用默认配置

```go
package main

import (
    "net/http"
    "time"

    "github.com/gogf/csrf"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

// default cfg
func main() {
    s := g.Server()
    s.Group("/api.v2", func(group *ghttp.RouterGroup) {
        group.Middleware(csrf.New())
        group.ALL("/csrf", func(r *ghttp.Request) {
            r.Response.Writeln(r.Method + ": " + r.RequestURI)
        })
    })
    s.SetPort(8199)
    s.Run()
}
```

### 使用自定义配置

```go
package main

import (
    "net/http"
    "time"

    "github.com/gogf/csrf"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

// set cfg
func main() {
    s := g.Server()
    s.Group("/api.v2", func(group *ghttp.RouterGroup) {
        group.Middleware(csrf.NewWithCfg(csrf.Config{
            Cookie: &http.Cookie{
                Name: "_csrf",// token name in cookie
                Secure:   true,
                SameSite: http.SameSiteNoneMode,// 自定义samesite
            },
            ExpireTime:      time.Hour * 24,
            TokenLength:     32,
            TokenRequestKey: "X-Token",// use this key to read token in request param
        }))
        group.ALL("/csrf", func(r *ghttp.Request) {
            r.Response.Writeln(r.Method + ": " + r.RequestURI)
        })
    })
    s.SetPort(8199)
    s.Run()
}
```

## 通过请求体验效果

[http://localhost:8199/api.v2/csrf](http://localhost:8199/api.v2/csrf)