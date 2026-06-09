在本章节中，我们将之前介绍 `HTTP Client&Server` 的示例修改为 `GRPC` 微服务，并演示如何使用 `GoFrame` 框架开发一个简单的 `GRPC` 服务端和客户端，并且为 `GRPC` 微服务增加链路跟踪特性。

本章节的示例代码位于： [https://github.com/gogf/gf/tree/master/example/trace/grpc\_with\_db](https://github.com/gogf/gf/tree/master/example/trace/grpc_with_db)

## 目录结构

## Protobuf

```
syntax = "proto3";

package user;

option go_package = "protobuf/user";

// User service for tracing demo.
service User {
  rpc Insert(InsertReq) returns (InsertRes) {}
  rpc Query(QueryReq) returns (QueryRes) {}
  rpc Delete(DeleteReq) returns (DeleteRes) {}
}

message InsertReq {
  string Name = 1; // v: required#Please input user name.
}
message InsertRes {
  int32 Id = 1;
}

message QueryReq {
  int32 Id = 1; // v: min:1#User id is required for querying.
}
message QueryRes {
  int32  Id = 1;
  string Name = 2;
}

message DeleteReq {
  int32 Id = 1; // v:min:1#User id is required for deleting.
}
message DeleteRes {}
```

使用 `gf gen pb` 命令编译该 `proto` 文件，将会生成对应的 `grpc` 接口文件和数据结构文件。

## GRPC Server

```go
package main

import (
    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"
    _ "github.com/gogf/gf/contrib/nosql/redis/v2"
    "github.com/gogf/gf/contrib/registry/etcd/v2"
    "github.com/gogf/gf/example/trace/grpc_with_db/protobuf/user"

    "context"
    "fmt"
    "time"

    "github.com/gogf/gf/contrib/rpc/grpcx/v2"
    "github.com/gogf/gf/contrib/trace/otlpgrpc/v2"
    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gcache"
    "github.com/gogf/gf/v2/os/gctx"
)

type Controller struct {
    user.UnimplementedUserServer
}

const (
    serviceName = "otlp-grpc-server"
    endpoint    = "tracing-analysis-dc-bj.aliyuncs.com:8090"
    traceToken  = "******_******"
)

func main() {
    grpcx.Resolver.Register(etcd.New("127.0.0.1:2379"))

    var ctx = gctx.New()
    shutdown, err := otlpgrpc.Init(serviceName, endpoint, traceToken)
    if err != nil {
        g.Log().Fatal(ctx, err)
    }
    defer shutdown()

    // Set ORM cache adapter with redis.
    g.DB().GetCache().SetAdapter(gcache.NewAdapterRedis(g.Redis()))

    s := grpcx.Server.New()
    user.RegisterUserServer(s.Server, &Controller{})
    s.Run()
}

// Insert is a route handler for inserting user info into database.
func (s *Controller) Insert(ctx context.Context, req *user.InsertReq) (res *user.InsertRes, err error) {
    result, err := g.Model("user").Ctx(ctx).Insert(g.Map{
        "name": req.Name,
    })
    if err != nil {
        return nil, err
    }
    id, _ := result.LastInsertId()
    res = &user.InsertRes{
        Id: int32(id),
    }
    return
}

// Query is a route handler for querying user info. It firstly retrieves the info from redis,
// if there's nothing in the redis, it then does db select.
func (s *Controller) Query(ctx context.Context, req *user.QueryReq) (res *user.QueryRes, err error) {
    err = g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
        Duration: 5 * time.Second,
        Name:     s.userCacheKey(req.Id),
        Force:    false,
    }).WherePri(req.Id).Scan(&res)
    if err != nil {
        return nil, err
    }
    return
}

// Delete is a route handler for deleting specified user info.
func (s *Controller) Delete(ctx context.Context, req *user.DeleteReq) (res *user.DeleteRes, err error) {
    err = g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
        Duration: -1,
        Name:     s.userCacheKey(req.Id),
        Force:    false,
    }).WherePri(req.Id).Scan(&res)
    return
}

func (s *Controller) userCacheKey(id int32) string {
    return fmt.Sprintf(`userInfo:%d`, id)
}
```

服务端代码简要说明：

1、首先，服务端需要通过 `jaeger.Init` 方法初始化 `Jaeger`。

2、可以看到，业务逻辑和之前HTTP示例项目完全一致，只是接入层修改为了GRPC协议。

3、我们仍然通过缓存适配器的方式注入Redis缓存：

```go
g.DB().GetCache().SetAdapter(gcache.NewAdapterRedis(g.Redis()))
```

5、这里也是通过 `Cache` 方法启用 `ORM` 的缓存特性，之前已经做过介绍，这里不再赘述。

## GRPC Client

```go
package main

import (
    "github.com/gogf/gf/contrib/registry/etcd/v2"
    "github.com/gogf/gf/contrib/rpc/grpcx/v2"
    "github.com/gogf/gf/contrib/trace/otlpgrpc/v2"
    "github.com/gogf/gf/example/trace/grpc_with_db/protobuf/user"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/gtrace"
    "github.com/gogf/gf/v2/os/gctx"
)

const (
     serviceName = "otlp-grpc-client"
    endpoint    = "tracing-analysis-dc-bj.aliyuncs.com:8090"
    traceToken  = "******_******"
)

func main() {
    grpcx.Resolver.Register(etcd.New("127.0.0.1:2379"))

    var ctx = gctx.New()
    shutdown, err := otlpgrpc.Init(serviceName, endpoint, traceToken)
    if err != nil {
        g.Log().Fatal(ctx, err)
    }
    defer shutdown()

    StartRequests()
}

func StartRequests() {
    ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
    defer span.End()

    client := user.NewUserClient(grpcx.Client.MustNewGrpcClientConn("demo"))

    // Baggage.
    ctx = gtrace.SetBaggageValue(ctx, "uid", 100)

    // Insert.
    insertRes, err := client.Insert(ctx, &user.InsertReq{
        Name: "john",
    })
    if err != nil {
        g.Log().Fatalf(ctx, `%+v`, err)
    }
    g.Log().Info(ctx, "insert id:", insertRes.Id)

    // Query.
    queryRes, err := client.Query(ctx, &user.QueryReq{
        Id: insertRes.Id,
    })
    if err != nil {
        g.Log().Errorf(ctx, `%+v`, err)
        return
    }
    g.Log().Info(ctx, "query result:", queryRes)

    // Delete.
    _, err = client.Delete(ctx, &user.DeleteReq{
        Id: insertRes.Id,
    })
    if err != nil {
        g.Log().Errorf(ctx, `%+v`, err)
        return
    }
    g.Log().Info(ctx, "delete id:", insertRes.Id)

    // Delete with error.
    _, err = client.Delete(ctx, &user.DeleteReq{
        Id: -1,
    })
    if err != nil {
        g.Log().Errorf(ctx, `%+v`, err)
        return
    }
    g.Log().Info(ctx, "delete id:", -1)
}
```

客户端代码简要说明：

1、首先，客户端也是需要通过 `jaeger.Init` 方法初始化 `Jaeger`。

2、客户端非常简单，内部初始化以及默认拦截器的设置已经由 `Katyusha` 框架封装好了，开发者只需要关心业务逻辑实现即可，

## 效果查看

**启动服务端：**

**启动客户端：**

这里客户端的执行最后报了一个错误，那是我们 **故意为之**，目的是演示 `GRPC` 报错时的链路信息展示。我们打开 `jaeger` 查看一下链路跟踪信息：

可以看到本次请求涉及到两个服务： `tracing-grpc-client` 和 `tracing-grpc-server`，即客户端和服务端。整个请求链路涉及到 `17` 个 `span`，客户端 `5` 个 `span`，服务端 `12` 个 `span`，并且产生了 `2` 个错误。我们点击查看详情：

我们点击查看一下最后接口调用错误的 `span` 情况：

看起来像个参数校验错误，点击查看 `Events/Logs` 中的请求参数：

查看 `Process` 中的 `Log` 信息可以看到，是由于传递的参数为 `-1`，不满足校验规则，因此在数据校验的时候报错返回了。

### GRPC Client

由于 `orm`、 `redis`、 `logging` 组件在之前的章节中已经介绍过链路信息，因此我们这里主要介绍 `GRPC Client&Server` 的链路信息。

#### Attributes

| Attribute/Tag | 说明 |
| --- | --- |
| `net.peer.ip` | 请求的目标IP。 |
| `net.peer.port` | 请求的目标端口。 |
| `rpc.grpc.status_code` | `GRPC` 的内部状态码， `0` 表示成功， `非0` 表示失败。 |
| `rpc.service` | `RPC` 的服务名称，注意这里是 `RPC` 而不是 `GRPC`，因为这里是通用定义，客户端支持多种 `RPC` 通信协议， `GRPC` 只是其中一种。 |
| `rpc.method` | `RPC` 的方法名称。 |
| `rpc.system` | `RPC` 协议类型，如： `grpc`, `thrift` 等。 |

#### Events/Logs

| Event/Log | 说明 |
| --- | --- |
| `grpc.metadata.outgoing` | `GRPC` 客户端请求提交的 `Metadata` 信息，可能会比较大。 |
| `grpc.request.baggage` | `GRPC` 客户端请求提交的 `Baggage` 信息，用于服务间链路信息传递。 |
| `grpc.request.message` | `GRPC` 客户端请求提交的 `Message` 数据，可能会比较大，最大只记录 `512KB`，如果超过该大小则忽略。仅对 `Unary` 请求类型有效。 |
| `grpc.response.message` | `GRPC` 客户端请求接收返回的的 `Message` 信息，可能会比较大。仅对 `Unary` 请求类型有效。 |

### GRPC Server

#### Attributes

`GRPC Server` 端的 `Attributes` 含义同 `GRPC Client`，在同一请求中，打印的数据基本一致。

#### Events

`GRPC Server` 端的 `Events` 与 `GRPC Client` 不同的是，在同一请求中，服务端接收到的 `metadata` 为 `grpc.metadata.incoming`，其他同 `GRPC Client`。