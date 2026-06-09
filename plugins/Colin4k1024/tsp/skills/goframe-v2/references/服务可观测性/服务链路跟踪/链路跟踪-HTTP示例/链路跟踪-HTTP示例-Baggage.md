## `baggage` 链路数据传递

`baggage` 用户链路间（服务间）传递自定义的信息。

示例代码地址： [https://github.com/gogf/gf/tree/master/example/trace/http](https://github.com/gogf/gf/tree/master/example/trace/http)

## 客户端

```go
package main

import (
    "github.com/gogf/gf/contrib/trace/otlphttp/v2"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/gtrace"
    "github.com/gogf/gf/v2/os/gctx"
)

const (
     serviceName = "otlp-http-client"
    endpoint    = "tracing-analysis-dc-hz.aliyuncs.com"
    path        = "adapt_******_******/api/otlp/traces"
)

func main() {
    var ctx = gctx.New()
    shutdown, err := otlphttp.Init(serviceName, endpoint, path)
   if err != nil {
        g.Log().Fatal(ctx, err)
    }
    defer shutdown()

    StartRequests()
}

func StartRequests() {
    ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
    defer span.End()

    ctx = gtrace.SetBaggageValue(ctx, "name", "john")

    content := g.Client().GetContent(ctx, "http://127.0.0.1:8199/hello")
    g.Log().Print(ctx, content)
}
```

客户端代码简要说明：

1. 首先，客户端也是需要通过 `jaeger.Init` 方法初始化 `Jaeger`。
2. 随后，这里通过 `gtrace.SetBaggageValue(ctx, "name", "john")` 方法设置了一个 `baggage`，该 `baggage` 将会在该请求的所有链路中传递。不过我们该示例也有两个节点，因此该 `baggage` 数据只会传递到服务端。该方法会返回一个新的 `context.Context` 上下文变量，在随后的调用链中我们将需要传递这个新的上下文变量。
3. 其中，这里通过 `g.Client()` 创建一个HTTP客户端请求对象，该客户端会自动启用链路跟踪特性，无需开发者显示调用任何方法或者任何设置。
4. 最后，这里使用了 `g.Log().Print(ctx, content)` 方法打印服务端的返回内容，其中的 `ctx` 便是将链路信息传递给日志组件，如果 `ctx` 上下文对象中存在链路信息时，日志组件会同时自动将 `TraceId` 输出到日志内容中。

## 服务端

```go
package main

import (
    "github.com/gogf/gf/contrib/trace/otlphttp/v2"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/net/gtrace"
    "github.com/gogf/gf/v2/os/gctx"
)

const (
     serviceName = "otlp-http-server"
    endpoint    = "tracing-analysis-dc-hz.aliyuncs.com"
    path        = "adapt_******_******/api/otlp/traces" )

func main() {
    var ctx = gctx.New()
    shutdown, err := otlphttp.Init(serviceName, endpoint, path)
    if err != nil {
        g.Log().Fatal(ctx, err)
    }
    defer shutdown()

    s := g.Server()
    s.Group("/", func(group *ghttp.RouterGroup) {
        group.GET("/hello", HelloHandler)
    })
    s.SetPort(8199)
    s.Run()
}

func HelloHandler(r *ghttp.Request) {
    ctx, span := gtrace.NewSpan(r.Context(), "HelloHandler")
    defer span.End()

    value := gtrace.GetBaggageVar(ctx, "name").String()

    r.Response.Write("hello:", value)
}
```

服务端代码简要说明：

1. 当然，服务端也是需要通过 `jaeger.Init` 方法初始化 `Jaeger`。
2. 服务端启动启用链路跟踪特性，开发者无需显示调用任何方法或任何设置。
3. 服务端通过 `gtrace.GetBaggageVar(ctx, "name").String()` 方法获取客户端提交的 `baggage` 信息，并转换为字符串返回。

## 效果查看

**启动服务端：**

**启动客户端：**

可以看到，客户端提交的 `baggage` 已经被服务端成功接收到并打印返回。并且客户端在输出日志内容的时候也同时输出的 `TraceId` 信息。 `TraceId` 是一条链路的唯一ID，可以通过该ID检索该链路的所有日志信息，并且也可以通过该 `TraceId` 在 `Jaeger` 系统上查询该调用链路详情。

在 `Jaeger` 上查看链路信息：

可以看到在这里出现了两个服务名称： `tracing-http-client` 和 `tracing-http-server`，表示我们这次请求涉及到两个服务，分别是HTTP请求的客户端和服务端，并且每个服务中分别涉及到 `2` 个 `span` 链路节点。

我们点击这个 `trace` 的详情，可以看得到调用链的层级关系。并且可以看得到客户端请求的地址、服务端接收的路由以及服务端路由函数名称。我们这里来介绍一下客户端的 `Atttributes` 信息和 `Events` 信息，也就是 `Jaeger` 中展示的 `Tags` 信息和 `Process` 信息。

### HTTP Client Attributes

| Attribute/Tag | 说明 |
| --- | --- |
| `otel.instrumentation_library.name` | 当前仪表器名称，往往是当前 `span` 操作的组件名称 |
| `otel.instrumentation_library.version` | 当前仪表器组件版本 |
| `span.kind` | 当前 `span` 的类型，一般由组件自动写入。常见 `span` 类型为：

| 类型 | 说明 |
| --- | --- |
| `client ` | 客户端 |
| `server` | 服务端 |
| `producer` | 生产者，常用于MQ |
| `consumer` | 消费者，常用于MQ |
| `internal` | 内部方法，一般业务使用 |
| `undefined` | 未定义，较少使用 | |
| `status.code` | 当前 `span` 状态， `0` 为正常， `非0` 表示失败 |
| `status.message` | 当前 `span` 状态信息，往往在失败时会带有错误信息 |
| `hostname` | 当前节点的主机名称 |
| `ip.intranet` | 当前节点的主机内网地址列表 |
| `http.address.local` | HTTP通信的本地地址和端口 |
| `http.address.remote` | HTTP通信的目标地址和端口 |
| `http.dns.start` | 当请求的目标地址带有域名时，开始解析的域名地址 |
| `http.dns.done` | 当请求的目标地址带有域名时，解析结束之后的IP地址 |
| `http.connect.start` | 开始创建连接的类型和地址 |
| `http.connect.done` | 创建连接成功后的类型和地址 |

### HTTP Client Events

| Event/Log | 说明 |
| --- | --- |
| `http.request.headers` | HTTP客户端请求提交的 `Header` 信息，可能会比较大。 |
| `http.request.baggage` | HTTP客户端请求提交的 `Baggage` 信息，用于服务间链路信息传递。 |
| `http.request.body` | HTTP客户端请求提交的 `Body` 数据，可能会比较大，最大只记录 `512KB`，如果超过该大小则忽略。 |
| `http.response.headers` | HTTP客户端请求接收返回的的 `Header` 信息，可能会比较大。 |
| `http.response.body` | HTTP客户端请求接收返回的 `Body` 数据，可能会比较大，最大只记录 `512KB`，如果超过该大小则忽略。 |

### HTTP Server Attributes

`HTTP Server` 端的 `Attributes` 含义同 `HTTP Client`，在同一请求中，打印的数据基本一致。

### HTTP Server Events

`HTTP Server` 端的 `Events` 含义同 `HTTP Client`，在同一请求中，打印的数据基本一致。