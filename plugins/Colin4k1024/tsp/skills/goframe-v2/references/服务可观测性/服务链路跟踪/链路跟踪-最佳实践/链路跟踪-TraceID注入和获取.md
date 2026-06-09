## 一、基本介绍

在链路跟踪中，`TraceID`作为在各个服务间传递的唯一标识，用于串联服务间请求关联关系，是非常重要的一项数据。`TraceID`是通过`Context`参数传递的，如果使用框架的`glog`日志组件，那么在日志打印中将会自动读取`TraceID`记录到日志内容中。因此也建议大家使用框架的`glog`日志组件来打印日志，便于完美地支持链路跟踪特性。

## 二、TraceID的注入

### 1、客户端

如果使用 `GoFrame` 框架的 `Client`，那么所有的请求将会自带 `TraceID` 的注入。 `GoFrame` 的 `TraceID` 使用的是 `OpenTelemetry` 规范，是由十六进制字符组成的的 `32` 字节字符串。
:::tip
强烈建议大家统一使用 `gclient` 组件，不仅功能全面而且自带链路跟踪能力。
:::
### 2、服务端

如果使用 `GoFrame` 框架的 `Server`，如果请求带有 `TraceID`，那么将会自动承接到 `Context` 中；否则，将会自动注入标准的 `TraceID`，并传递给后续逻辑。

## 三、TraceID的获取

### 1、客户端

如果使用 `GoFrame` 框架的 `Client`，这里有三种方式。

#### 1）自动生成TraceID（推荐）

通过 `gctx.New/WithCtx` 方法创建一个带有 `TraceID` 的 `Context`，该 `Context` 参数用于传递给请求方法。随后可以通过 `gctx.CtxId` 方法获取整个链路的 `TraceID`。相关方法：

```go
// New creates and returns a context which contains context id.
func New() context.Context

// WithCtx creates and returns a context containing context id upon given parent context `ctx`.
func WithCtx(ctx context.Context) context.Context
```

使用 `WithCtx` 方法时，如果给定的 `ctx` 参数本身已经带有 `TraceID`，那么它将会直接使用该 `TraceID`，并不会新建。

#### 2）客户端自定义TraceID

这里还有个高级的用法，客户端可以自定义 `TraceID`，使用 `gtrace.WithTraceID` 方法。方法定义如下：

```go
// WithTraceID injects custom trace id into context to propagate.
func WithTraceID(ctx context.Context, traceID string) (context.Context, error)
```

#### 3）读取Response Header

如果是请求 `GoFrame` 框架的 `Server`，那么在返回请求的 `Header` 中将会增加 `Trace-Id` 字段，供客户端读取。

### 2、服务端

如果使用 `GoFrame` 框架的 `Server`，直接通过 `gctx.CtxId` 方法即可获取 `TraceID`。相关方法：

```go
// CtxId retrieves and returns the context id from context.
func CtxId(ctx context.Context) string
```

## 四、使用示例

### 1、HTTP Response Header TraceID

```go
package main

import (
    "context"
    "time"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    s := g.Server()
    s.BindHandler("/", func(r *ghttp.Request) {
        traceID := gctx.CtxId(r.Context())
        g.Log().Info(r.Context(), "handler")
        r.Response.Write(traceID)
    })
    s.SetPort(8199)
    go s.Start()

    time.Sleep(time.Second)

    req, err := g.Client().Get(context.Background(), "http://127.0.0.1:8199/")
    if err != nil {
        panic(err)
    }
    defer req.Close()
    req.RawDump()
}
```

执行后，终端输出：

```
  ADDRESS | METHOD | ROUTE |                             HANDLER                             |    MIDDLEWARE
----------|--------|-------|-----------------------------------------------------------------|--------------------
  :8199   | ALL    | /     | main.main.func1                                                 |
----------|--------|-------|-----------------------------------------------------------------|--------------------
  :8199   | ALL    | /*    | github.com/gogf/gf/v2/net/ghttp.internalMiddlewareServerTracing | GLOBAL MIDDLEWARE
----------|--------|-------|-----------------------------------------------------------------|--------------------

2022-06-06 21:14:37.245 [INFO] pid[55899]: http server started listening on [:8199]
2022-06-06 21:14:38.247 [INFO] {908d2027560af616e218e912d2ac3972} handler
+---------------------------------------------+
|                   REQUEST                   |
+---------------------------------------------+
GET / HTTP/1.1
Host: 127.0.0.1:8199
User-Agent: GClient v2.1.0-rc4 at TXQIANGGUO-MB0
Traceparent: 00-908d2027560af616e218e912d2ac3972-1e291041b9afa718-01
Accept-Encoding: gzip

+---------------------------------------------+
|                   RESPONSE                  |
+---------------------------------------------+
HTTP/1.1 200 OK
Connection: close
Content-Length: 32
Content-Type: text/plain; charset=utf-8
Date: Mon, 06 Jun 2022 13:14:38 GMT
Server: GoFrame HTTP Server
Trace-Id: 908d2027560af616e218e912d2ac3972

908d2027560af616e218e912d2ac3972
```

### 2、客户端注入 `TraceID`

```go
package main

import (
    "time"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    s := g.Server()
    s.BindHandler("/", func(r *ghttp.Request) {
        traceID := gctx.CtxId(r.Context())
        g.Log().Info(r.Context(), "handler")
        r.Response.Write(traceID)
    })
    s.SetPort(8199)
    go s.Start()

    time.Sleep(time.Second)

    ctx := gctx.New()
    g.Log().Info(ctx, "request starts")
    content := g.Client().GetContent(ctx, "http://127.0.0.1:8199/")
    g.Log().Infof(ctx, "response: %s", content)
}
```

执行后，终端输出：

```html
2022-06-06 21:17:17.447 [INFO] pid[56070]: http server started listening on [:8199]

  ADDRESS | METHOD | ROUTE |                             HANDLER                             |    MIDDLEWARE
----------|--------|-------|-----------------------------------------------------------------|--------------------
  :8199   | ALL    | /     | main.main.func1                                                 |
----------|--------|-------|-----------------------------------------------------------------|--------------------
  :8199   | ALL    | /*    | github.com/gogf/gf/v2/net/ghttp.internalMiddlewareServerTracing | GLOBAL MIDDLEWARE
----------|--------|-------|-----------------------------------------------------------------|--------------------

2022-06-06 21:17:18.450 [INFO] {e843f0737b0af616d8ed185d46ba65c5} request starts
2022-06-06 21:17:18.451 [INFO] {e843f0737b0af616d8ed185d46ba65c5} handler
2022-06-06 21:17:18.451 [INFO] {e843f0737b0af616d8ed185d46ba65c5} response: e843f0737b0af616d8ed185d46ba65c5
```

### 3、客户端自定义 `TraceID`

```go
package main

import (
    "context"
    "time"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/net/gtrace"
    "github.com/gogf/gf/v2/os/gctx"
    "github.com/gogf/gf/v2/text/gstr"
)

func main() {
    s := g.Server()
    s.BindHandler("/", func(r *ghttp.Request) {
        traceID := gctx.CtxId(r.Context())
        g.Log().Info(r.Context(), "handler")
        r.Response.Write(traceID)
    })
    s.SetPort(8199)
    go s.Start()

    time.Sleep(time.Second)

    ctx, _ := gtrace.WithTraceID(context.Background(), gstr.Repeat("a", 32))
    g.Log().Info(ctx, "request starts")
    content := g.Client().GetContent(ctx, "http://127.0.0.1:8199/")
    g.Log().Infof(ctx, "response: %s", content)
}
```

执行后，终端输出：

```
  ADDRESS | METHOD | ROUTE |                             HANDLER                             |    MIDDLEWARE
----------|--------|-------|-----------------------------------------------------------------|--------------------
  :8199   | ALL    | /     | main.main.func1                                                 |
----------|--------|-------|-----------------------------------------------------------------|--------------------
  :8199   | ALL    | /*    | github.com/gogf/gf/v2/net/ghttp.internalMiddlewareServerTracing | GLOBAL MIDDLEWARE
----------|--------|-------|-----------------------------------------------------------------|--------------------

2022-06-06 21:40:03.897 [INFO] pid[58435]: http server started listening on [:8199]
2022-06-06 21:40:04.900 [INFO] {aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa} request starts
2022-06-06 21:40:04.901 [INFO] {aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa} handler
2022-06-06 21:40:04.901 [INFO] {aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa} response: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

## 五、常见问题

### 1、如果没有使用 `GoFrame` 框架的 `Client/Server`，如何获取链路的 `TraceID`？

可以参考 `GoFrame` 框架的 `Client/Server` 的链路跟踪实现，并自行实现一遍，这块可能需要一定成本。

如果使用的第三方 `Client/Server` 组件，请参考第三方组件相关介绍。

### 2、企业内部服务没有使用标准的 `OpenTelemetry` 规范，但是每个请求都带 `RequestID` 参数，形如 `33612a70-990a-11ea-87fe-fd68517e7a2d`，如何和 `TraceID` 结合起来？

根据我的分析，你这个 `RequestID` 的格式和 `TraceID` 规范非常切合，使用的是 `UUID` 字符串，而 `UUID` 可直接转换为 `TraceID`。建议在自己的 `Server` 内部第一层中间件中将 `RequestID` 转换为 `TraceID`，通过自定义 `TraceID` 的方式注入到 `Context` 中，并将该 `Context` 传递给后续业务逻辑。

我来给你写个例子吧：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/net/gtrace"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    // 内部服务
    internalServer := g.Server("internalServer")
    internalServer.BindHandler("/", func(r *ghttp.Request) {
        traceID := gctx.CtxId(r.Context())
        g.Log().Info(r.Context(), "internalServer handler")
        r.Response.Write(traceID)
    })
    internalServer.SetPort(8199)
    go internalServer.Start()

    // 外部服务，访问以测试
    // http://127.0.0.1:8299/?RequestID=33612a70-990a-11ea-87fe-fd68517e7a2d
    userSideServer := g.Server("userSideServer")
    userSideServer.Use(func(r *ghttp.Request) {
        requestID := r.Get("RequestID").String()
        if requestID != "" {
            newCtx, err := gtrace.WithUUID(r.Context(), requestID)
            if err != nil {
                panic(err)
            }
            r.SetCtx(newCtx)
        }
        r.Middleware.Next()
    })
    userSideServer.BindHandler("/", func(r *ghttp.Request) {
        ctx := r.Context()
        g.Log().Info(ctx, "request internalServer starts")
        content := g.Client().GetContent(ctx, "http://127.0.0.1:8199/")
        g.Log().Infof(ctx, "internalServer response: %s", content)
        r.Response.Write(content)
    })
    userSideServer.SetPort(8299)
    userSideServer.Run()
}
```

为了演示服务间的链路跟踪能力，这个示例代码中运行了两个HTTP服务，一个内部服务，提供功能逻辑；一个外部服务，供外部的接口调用，它的功能是调用内部服务来实现的。执行后，我们访问： [http://127.0.0.1:8299/?RequestID=33612a70-990a-11ea-87fe-fd68517e7a2d](http://127.0.0.1:8299/?RequestID=33612a70-990a-11ea-87fe-fd68517e7a2d)

随后查看终端输出：

```html
2022-06-07 14:51:21.957 [INFO] openapi specification is disabled
2022-06-07 14:51:21.958 [INTE] ghttp_server.go:78 78198: graceful reload feature is disabled

      SERVER     | DOMAIN  | ADDRESS | METHOD | ROUTE |                             HANDLER                             |    MIDDLEWARE
-----------------|---------|---------|--------|-------|-----------------------------------------------------------------|--------------------
  internalServer | default | :8199   | ALL    | /     | main.main.func1                                                 |
-----------------|---------|---------|--------|-------|-----------------------------------------------------------------|--------------------
  internalServer | default | :8199   | ALL    | /*    | github.com/gogf/gf/v2/net/ghttp.internalMiddlewareServerTracing | GLOBAL MIDDLEWARE
-----------------|---------|---------|--------|-------|-----------------------------------------------------------------|--------------------

2022-06-07 14:51:21.959 [INFO] pid[78198]: http server started listening on [:8199]
2022-06-07 14:51:21.965 [INFO] openapi specification is disabled

      SERVER     | DOMAIN  | ADDRESS | METHOD | ROUTE |                             HANDLER                             |    MIDDLEWARE
-----------------|---------|---------|--------|-------|-----------------------------------------------------------------|--------------------
  userSideServer | default | :8299   | ALL    | /     | main.main.func3                                                 |
-----------------|---------|---------|--------|-------|-----------------------------------------------------------------|--------------------
  userSideServer | default | :8299   | ALL    | /*    | github.com/gogf/gf/v2/net/ghttp.internalMiddlewareServerTracing | GLOBAL MIDDLEWARE
-----------------|---------|---------|--------|-------|-----------------------------------------------------------------|--------------------
  userSideServer | default | :8299   | ALL    | /*    | main.main.func2                                                 | GLOBAL MIDDLEWARE
-----------------|---------|---------|--------|-------|-----------------------------------------------------------------|--------------------

2022-06-07 14:51:21.965 [INFO] pid[78198]: http server started listening on [:8299]
2022-06-07 14:53:05.322 [INFO] {33612a70990a11ea87fefd68517e7a2d} request internalServer starts
2022-06-07 14:53:05.323 [INFO] {33612a70990a11ea87fefd68517e7a2d} internalServer handler
2022-06-07 14:53:05.323 [INFO] {33612a70990a11ea87fefd68517e7a2d} internalServer response: 33612a70990a11ea87fefd68517e7a2d
```

我们发现， `RequestID` 作为 `TraceID` 贯通了整个服务间的链路了呢！