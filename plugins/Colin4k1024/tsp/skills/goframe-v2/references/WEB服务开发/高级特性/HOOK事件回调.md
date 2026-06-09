`ghttp.Server` 提供了事件回调注册功能，类似于其他框架的 `中间件` 功能，相比较于 `中间件`，事件回调的特性更加简单。

`ghttp.Server` 支持用户对于某一事件进行自定义监听处理，按照 `pattern` 方式进行绑定注册( `pattern` 格式与路由注册一致)。 **支持多个方法对同一事件进行监听**， `ghttp.Server` 将会按照 `路由优先级` 及 `回调注册顺序` 进行回调方法调用。同一事件时先注册的HOOK回调函数优先级越高。 相关方法如下：

```go
func (s *Server) BindHookHandler(pattern string, hook string, handler HandlerFunc) error
func (s *Server) BindHookHandlerByMap(pattern string, hookmap map[string]HandlerFunc) error
```

当然域名对象也支持事件回调注册：

```go
func (d *Domain) BindHookHandler(pattern string, hook string, handler HandlerFunc) error
func (d *Domain) BindHookHandlerByMap(pattern string, hookmap map[string]HandlerFunc) error
```

支持的 `Hook` 事件列表：

1. `ghttp.HookBeforeServe`

在进入/初始化服务对象之前，该事件是最常用的事件，特别是针对于权限控制、跨域请求等处理。

2. `ghttp.HookAfterServe`

在完成服务执行流程之后。

3. `ghttp.HookBeforeOutput`

向客户端输出返回内容之前。

4. `ghttp.HookAfterOutput`

向客户端输出返回内容之后。

具体调用时机请参考图例所示。

## 回调优先级

由于事件的绑定也是使用的路由规则，因此它的优先级和 [路由管理-路由规则](../路由管理/路由管理-路由规则.md) 章节介绍的优先级是一样的。

但是事件调用时和路由注册调用时的机制不一样， **同一个路由规则下允许绑定多个事件回调方法**，该路由下的事件调用会 `按照优先级进行调用`，假如优先级相等的路由规则，将会按照事件注册的顺序进行调用。

### 关于全局回调

我们往往使用绑定 `/*` 这样的 `HOOK` 路由来实现全局的回调处理，这样是可以的。但是 `HOOK` 执行的优先是最低的，路由注册的越精确，优先级越高，越模糊的路由优先级越低， `/*` 就属于最模糊的路由。

为降低不同的模块耦合性，所有的路由往往不是在同一个地方进行注册。例如用户模块注册的 `HOOK`( `/user/*`)，它将会被优先调用随后才可能是全局的 `HOOK`；如果仅仅依靠注册顺序来控制优先级，在模块多路由多的时候优先级便很难管理。

### 业务函数调用顺序

建议 相同的业务(同一业务模块) 的多个处理函数(例如: A、B、C)放到同一个 `HOOK` 回调函数中进行处理，在注册的回调函数中自行管理业务处理函数的调用顺序(函数调用顺序: A-B-C)。

虽然同样的需求，注册多个相同 `HOOK` 的回调函数也可以实现，功能上不会有问题，但从设计的角度来讲，内聚性降低了，不便于业务函数管理。

## `ExitHook` 方法

当路由匹配到多个 `HOOK` 方法时，默认是按照路由匹配优先级顺序执行 `HOOK` 方法。当在 `HOOK` 方法中调用 `Request.ExitHook` 方法后，后续的 `HOOK` 方法将不会被继续执行，作用类似 `HOOK` 方法覆盖。

## 接口鉴权控制

事件回调注册比较常见的应用是在对调用的接口进行鉴权控制/权限控制。该操作需要绑定 `ghttp.HookBeforeServe` 事件，在该事件中会对所有匹配的接口请求(例如绑定 `/*` 事件回调路由)服务执行前进行回调处理。当鉴权不通过时，需要调用 `r.ExitAll()` 方法退出后续的服务执行(包括后续的事件回调执行)。

此外，在权限校验的事件回调函数中执行 `r.Redirect*` 方法，又没有调用 `r.ExitAll()` 方法退出业务执行，往往会产生 `http multiple response writeheader calls` 错误提示。因为 `r.Redirect*` 方法会往返回的header中写入 `Location` 头；而随后的业务服务接口往往会往header写入 `Content-Type`/ `Content-Length` 头，这两者有冲突造成的。

## 中间件与事件回调

中间件（ `Middleware`）与事件回调（ `HOOK`）是 `GoFrame` 框架的两大流程控制特性，两者都可用于控制请求流程，并且也都支持绑定特定的路由规则。但两者区别也是非常明显的。

1. 首先，中间件侧重于应用级的流程控制，而事件回调侧重于服务级流程控制；也就是说中间件的作用域仅限于应用，而事件回调的“权限”更强大，属于 `Server` 级别，并可处理静态文件的请求回调。
2. 其次，中间件设计采用了“洋葱”设计模型；而事件回调采用的是特定事件的钩子触发设计。
3. 最后，中间件相对来说灵活性更高，也是比较推荐的流程控制方式；而事件回调比较简单，但灵活性较差。

### `Request.URL` 与 `Request.Router`

`Request.Router` 是匹配到的路由对象，包含路由注册信息，一般来说开发者不会用到。 `Request.URL` 是底层请求的URL对象（继承自标准库 `http.Request`），包含请求的URL地址信息，特别是 `Request.URL.Path` 表示请求的URI地址。

因此，假如在服务回调函数中使用的话， `Request.Router` 是有值的，因为只有匹配到了路由才会调用服务回调方法。但是在事件回调函数中，该对象可能为 `nil`（表示没有匹配到服务回调函数路由）。特别是在使用事件回调对请求接口鉴权的时候，应当使用 `Request.URL` 对象获取请求的URL信息，而不是 `Request.Router`。

## 静态文件事件
:::tip
如果仅仅是提供API接口服务（包括前置静态文件服务代理如 `nginx`），不涉及到静态文件服务，那么可以忽略该小节。
:::
需要注意的是，事件回调同样能够匹配到符合路由规则的静态文件访问（ [静态文件](静态文件服务.md) 特性在 `gf` 框架中是默认关闭的，我们可以使用 `WebServer` 相关配置来手动开启，具体查看 [服务配置](../服务配置/服务配置.md) 章节）。

例如，我们注册了一个 `/*` 的全局匹配事件回调路由，那么 `/static/js/index.js` 或者 `/upload/images/thumb.jpg` 等等静态文件访问也会被匹配到，会进入到注册的事件回调函数中进行处理。

我们可以在事件回调函数中使用 `Request.IsFileRequest()` 方法来判断该请求是否是静态文件请求，如果业务逻辑不需要静态文件的请求事件回调，那么在事件回调函数中直接忽略即可，以便进行选择性地处理。

## 事件回调示例

### 示例1，基本使用

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/os/glog"
)

func main() {
    // 基本事件回调使用
    p := "/:name/info/{uid}"
    s := g.Server()
    s.BindHookHandlerByMap(p, map[string]ghttp.HandlerFunc{
        ghttp.HookBeforeServe:  func(r *ghttp.Request) { glog.Println(ghttp.HookBeforeServe) },
        ghttp.HookAfterServe:   func(r *ghttp.Request) { glog.Println(ghttp.HookAfterServe) },
        ghttp.HookBeforeOutput: func(r *ghttp.Request) { glog.Println(ghttp.HookBeforeOutput) },
        ghttp.HookAfterOutput:  func(r *ghttp.Request) { glog.Println(ghttp.HookAfterOutput) },
    })
    s.BindHandler(p, func(r *ghttp.Request) {
        r.Response.Write("用户:", r.Get("name"), ", uid:", r.Get("uid"))
    })
    s.SetPort(8199)
    s.Run()
}

```

当访问 [http://127.0.0.1:8199/john/info/10000](http://127.0.0.1:8199/john/info/10000) 时，运行WebServer进程的终端将会按照事件的执行流程打印出对应的事件名称。

### 示例2，相同事件注册

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

// 优先调用的HOOK
func beforeServeHook1(r *ghttp.Request) {
    r.SetParam("name", "GoFrame")
    r.Response.Writeln("set name")
}

// 随后调用的HOOK
func beforeServeHook2(r *ghttp.Request) {
    r.SetParam("site", "https://goframe.org")
    r.Response.Writeln("set site")
}

// 允许对同一个路由同一个事件注册多个回调函数，按照注册顺序进行优先级调用。
// 为便于在路由表中对比查看优先级，这里讲HOOK回调函数单独定义为了两个函数。
func main() {
    s := g.Server()
    s.BindHandler("/", func(r *ghttp.Request) {
        r.Response.Writeln(r.Get("name"))
        r.Response.Writeln(r.Get("site"))
    })
    s.BindHookHandler("/", ghttp.HookBeforeServe, beforeServeHook1)
    s.BindHookHandler("/", ghttp.HookBeforeServe, beforeServeHook2)
    s.SetPort(8199)
    s.Run()
}
```

执行后，终端输出的路由表信息如下：

```text
SERVER | ADDRESS | DOMAIN  | METHOD | P | ROUTE |        HANDLER        |    MIDDLEWARE
|---------|---------|---------|--------|---|-------|-----------------------|-------------------|
  default |  :8199  | default | ALL    | 1 | /     | main.main.func1       |
|---------|---------|---------|--------|---|-------|-----------------------|-------------------|
  default |  :8199  | default | ALL    | 2 | /     | main.beforeServeHook1 | HOOK_BEFORE_SERVE
|---------|---------|---------|--------|---|-------|-----------------------|-------------------|
  default |  :8199  | default | ALL    | 1 | /     | main.beforeServeHook2 | HOOK_BEFORE_SERVE
|---------|---------|---------|--------|---|-------|-----------------------|-------------------|
```

手动访问 [http://127.0.0.1:8199/](http://127.0.0.1:8199/) 后，页面输出内容为：

```
set name
set site
GoFrame
https://goframe.org
```

### 示例3，改变业务逻辑

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    s := g.Server()
    // 多事件回调示例，事件1
    pattern1 := "/:name/info"
    s.BindHookHandlerByMap(pattern1, map[string]ghttp.HandlerFunc{
        ghttp.HookBeforeServe: func(r *ghttp.Request) {
            r.SetParam("uid", 1000)
        },
    })
    s.BindHandler(pattern1, func(r *ghttp.Request) {
        r.Response.Write("用户:", r.Get("name"), ", uid:", r.Get("uid"))
    })

    // 多事件回调示例，事件2
    pattern2 := "/{object}/list/{page}.java"
    s.BindHookHandlerByMap(pattern2, map[string]ghttp.HandlerFunc{
        ghttp.HookBeforeOutput: func(r *ghttp.Request) {
            r.Response.SetBuffer([]byte(
                fmt.Sprintf("通过事件修改输出内容, object:%s, page:%s", r.Get("object"), r.GetRouterString("page"))),
            )
        },
    })
    s.BindHandler(pattern2, func(r *ghttp.Request) {
        r.Response.Write(r.Router.Uri)
    })
    s.SetPort(8199)
    s.Run()
}
```

通过事件1设置了访问 `/:name/info` 路由规则时的GET参数；通过事件2，改变了当访问的路径匹配路由 `/{object}/list/{page}.java` 时的输出结果。执行之后，访问以下URL查看效果：

- [http://127.0.0.1:8199/user/info](http://127.0.0.1:8199/user/info)
- [http://127.0.0.1:8199/user/list/1.java](http://127.0.0.1:8199/user/list/1.java)
- [http://127.0.0.1:8199/user/list/2.java](http://127.0.0.1:8199/user/list/2.java)

### 示例4，回调执行优先级

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    s := g.Server()
    s.BindHandler("/priority/show", func(r *ghttp.Request) {
        r.Response.Writeln("priority service")
    })

    s.BindHookHandlerByMap("/priority/:name", map[string]ghttp.HandlerFunc{
        ghttp.HookBeforeServe: func(r *ghttp.Request) {
            r.Response.Writeln("/priority/:name")
        },
    })
    s.BindHookHandlerByMap("/priority/*any", map[string]ghttp.HandlerFunc{
        ghttp.HookBeforeServe: func(r *ghttp.Request) {
            r.Response.Writeln("/priority/*any")
        },
    })
    s.BindHookHandlerByMap("/priority/show", map[string]ghttp.HandlerFunc{
        ghttp.HookBeforeServe: func(r *ghttp.Request) {
            r.Response.Writeln("/priority/show")
        },
    })
    s.SetPort(8199)
    s.Run()
}
```

在这个示例中，我们往注册了3个路由规则的事件回调，并且都能够匹配到路由注册的地址 `/priority/show`，这样我们便可以通过访问这个地址来看看路由执行的顺序是怎么样的。

执行后我们访问 [http://127.0.0.1:8199/priority/show](http://127.0.0.1:8199/priority/show) ，随后我们看到页面输出以下信息：

```
/priority/show
/priority/:name
/priority/*any
priority service
```

### 示例5，允许跨域请求

在 [路由管理-中间件/拦截器](../%E8%B7%AF%E7%94%B1%E7%AE%A1%E7%90%86/%E8%B7%AF%E7%94%B1%E7%AE%A1%E7%90%86-%E4%B8%AD%E9%97%B4%E4%BB%B6%E6%8B%A6%E6%88%AA%E5%99%A8/%E4%B8%AD%E9%97%B4%E4%BB%B6%E6%8B%A6%E6%88%AA%E5%99%A8-%E5%9F%BA%E6%9C%AC%E4%BB%8B%E7%BB%8D.md) 和 [CORS跨域处理](CORS跨域处理.md) 章节也有介绍跨域处理的示例，大多数情况下，我们使用中间件来处理跨域请求的实现居多。

`HOOK` 和中间件都能实现跨域请求处理，我们这里使用HOOK来实现简单的跨域处理。 首先我们来看一个简单的接口示例：

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

接口地址是 [http://localhost:8199/api.v1/order](http://localhost:8199/api.v1/order) ，当然这个接口是不允许跨域的。我们打开一个不同的域名，例如：百度首页(正好用了 `jQuery`，方便调试)，然后按 `F12` 打开开发者面板，在 `console` 下执行以下 `AJAX` 请求：

```
$.get("http://localhost:8199/api.v1/order", function(result){
    console.log(result)
});
```

结果如下：

返回了不允许跨域的错误，接着我们修改一下测试代码，如下：

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
        group.Hook("/*any", ghttp.HookBeforeServe, func(r *ghttp.Request) {
            r.Response.CORSDefault()
        })
        group.GET("/order", Order)
    })
    s.SetPort(8199)
    s.Run()
}
```

我们增加了针对于路由 `/api.v1/*any` 的绑定事件 `ghttp.HookBeforeServe`，该事件将会在所有服务执行之前调用，该事件的回调方法中，我们通过调用 `CORSDefault` 方法使用默认的跨域设置允许跨域请求。该绑定的事件路由规则使用了模糊匹配规则，表示所有 `/api.v1` 开头的接口地址都允许跨域请求。

返回刚才的百度首页，再次执行请求 `AJAX` 请求，这次便成功了：