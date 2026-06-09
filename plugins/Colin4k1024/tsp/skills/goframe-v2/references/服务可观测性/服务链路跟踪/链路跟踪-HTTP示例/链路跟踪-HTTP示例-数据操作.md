## `HTTP+DB+Redis+Logging`

我们再来看一个相对完整一点的例子，包含几个常用核心组件的链路跟踪示例，示例代码地址： [https://github.com/gogf/gf/tree/master/example/trace/http\_with\_db](https://github.com/gogf/gf/tree/master/example/trace/http_with_db)

## 客户端

```go
package main

import (
    "github.com/gogf/gf/contrib/trace/otlphttp/v2"
    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/net/gtrace"
    "github.com/gogf/gf/v2/os/gctx"
)

const (
    serviceName = "otlp-http-client"
    endpoint    = "tracing-analysis-dc-hz.aliyuncs.com"
    path        = "adapt_******_******/api/otlp/traces" )

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

    var (
        err    error
        client = g.Client()
    )
    // Add user info.
    var insertRes = struct {
        ghttp.DefaultHandlerResponse
        Data struct{ Id int64 } `json:"data"`
    }{}
    err = client.PostVar(ctx, "http://127.0.0.1:8199/user/insert", g.Map{
        "name": "john",
    }).Scan(&insertRes)
    if err != nil {
        panic(err)
    }
    g.Log().Info(ctx, "insert result:", insertRes)
    if insertRes.Data.Id == 0 {
        g.Log().Error(ctx, "retrieve empty id string")
        return
    }

    // Query user info.
    var queryRes = struct {
        ghttp.DefaultHandlerResponse
        Data struct{ User gdb.Record } `json:"data"`
    }{}
    err = client.GetVar(ctx, "http://127.0.0.1:8199/user/query", g.Map{
        "id": insertRes.Data.Id,
    }).Scan(&queryRes)
    if err != nil {
        panic(err)
    }
    g.Log().Info(ctx, "query result:", queryRes)

    // Delete user info.
    var deleteRes = struct {
        ghttp.DefaultHandlerResponse
    }{}
    err = client.PostVar(ctx, "http://127.0.0.1:8199/user/delete", g.Map{
        "id": insertRes.Data.Id,
    }).Scan(&deleteRes)
    if err != nil {
        panic(err)
    }
    g.Log().Info(ctx, "delete result:", deleteRes)
}
```

客户端代码简要说明：

1. 首先，客户端也是需要通过 `jaeger.Init` 方法初始化 `Jaeger`。
2. 在本示例中，我们通过HTTP客户端向服务端发起了 `3` 次请求：
1. `/user/insert` 用于新增一个用户信息，成功后返回用户的ID。
2. `/user/query` 用于查询用户，使用前一个接口返回的用户ID。
3. `/user/delete` 用于删除用户，使用之前接口返回的用户ID。

## 服务端

```go
package main

import (
    "context"
    "fmt"
    "time"

    "github.com/gogf/gf/contrib/trace/otlphttp/v2"
    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/os/gcache"
    "github.com/gogf/gf/v2/os/gctx"
)

type cTrace struct{}

const (
    serviceName = "otlp-http-client"
    endpoint    = "tracing-analysis-dc-hz.aliyuncs.com"
    path        = "adapt_******_******/api/otlp/traces" )

func main() {
    var ctx = gctx.New()
    shutdown, err := otlphttp.Init(serviceName, endpoint, path)
    if err != nil {
        g.Log().Fatal(ctx, err)
    }
    defer shutdown()

    // Set ORM cache adapter with redis.
    g.DB().GetCache().SetAdapter(gcache.NewAdapterRedis(g.Redis()))

    // Start HTTP server.
    s := g.Server()
    s.Use(ghttp.MiddlewareHandlerResponse)
    s.Group("/", func(group *ghttp.RouterGroup) {
        group.ALL("/user", new(cTrace))
    })
    s.SetPort(8199)
    s.Run()
}

type InsertReq struct {
    Name string `v:"required#Please input user name."`
}
type InsertRes struct {
    Id int64
}

// Insert is a route handler for inserting user info into database.
func (c *cTrace) Insert(ctx context.Context, req *InsertReq) (res *InsertRes, err error) {
    result, err := g.Model("user").Ctx(ctx).Insert(req)
    if err != nil {
        return nil, err
    }
    id, _ := result.LastInsertId()
    res = &InsertRes{
        Id: id,
    }
    return
}

type QueryReq struct {
    Id int `v:"min:1#User id is required for querying"`
}
type QueryRes struct {
    User gdb.Record
}

// Query is a route handler for querying user info. It firstly retrieves the info from redis,
// if there's nothing in the redis, it then does db select.
func (c *cTrace) Query(ctx context.Context, req *QueryReq) (res *QueryRes, err error) {
    one, err := g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
        Duration: 5 * time.Second,
        Name:     c.userCacheKey(req.Id),
        Force:    false,
    }).WherePri(req.Id).One()
    if err != nil {
        return nil, err
    }
    res = &QueryRes{
        User: one,
    }
    return
}

type DeleteReq struct {
    Id int `v:"min:1#User id is required for deleting."`
}
type DeleteRes struct{}

// Delete is a route handler for deleting specified user info.
func (c *cTrace) Delete(ctx context.Context, req *DeleteReq) (res *DeleteRes, err error) {
    _, err = g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
        Duration: -1,
        Name:     c.userCacheKey(req.Id),
        Force:    false,
    }).WherePri(req.Id).Delete()
    if err != nil {
        return nil, err
    }
    return
}

func (c *cTrace) userCacheKey(id int) string {
    return fmt.Sprintf(`userInfo:%d`, id)
}
```

服务端代码简要说明：

1. 首先，客户端也是需要通过 `jaeger.Init` 方法初始化 `Jaeger`。
2. 在本示例中，我们使用到了数据库和数据库缓存功能，以便于同时演示 `ORM` 和 `Redis` 的链路跟踪记录。
3. 我们在程序启动时通过以下方法设置当前数据库缓存管理的适配器为 `redis`。关于缓存适配器的介绍感兴趣可以参考 [缓存管理-接口设计](../../../核心组件/缓存管理/缓存管理-接口设计.md) 章节。

```go
g.DB().GetCache().SetAdapter(gcache.NewAdapterRedis(g.Redis()))
```

4. 在 `ORM` 的操作中，需要通过 `Ctx` 方法将上下文变量传递到组件中， `orm` 组件会自动识别当前上下文中是否包含Tracing链路信息，如果包含则自动启用链路跟踪特性。
5. 在 `ORM` 的操作中，这里使用 `Cache` 方法缓存查询结果到 `redis` 中，并在删除操作中也使用 `Cache` 方法清除 `redis` 中的缓存结果。关于 `ORM` 的缓存管理介绍请参考 [ORM链式操作-查询缓存](../../../核心组件/数据库ORM/ORM链式操作/ORM链式操作-查询缓存.md) 章节。

## 效果查看

**启动服务端：**

**启动客户端：**

在 `Jaeger` 上查看链路信息：

可以看到，这次请求总共产生了 `14` 个 `span`，其中客户端有 `4` 个 `span`，服务端有 `10` 个 `span`，每一个 `span` 代表一个链路节点。不过，我们注意到，这里产生了 `3` 个 `errors`。我们点击详情查看什么原因呢。

我们看到好像所有的 `redis` 操作都报错了，随便点击一个 `redis` 的相关 `span`，查看一下详情呢：

原来是 `redis` 连接不上报错了，这样的话所有的 `orm` 缓存功能都失效了，但是可以看到并没有影响接口逻辑，只是所有的查询都走了数据库。这个报错是因为我本地忘了打开 `redis server`，我赶紧启动一下本地的 `redis server`，再看看效果：

再把上面的客户端运行一下，查看 `jaeger`：

现在就没有报错了。

`HTTP Client&Server`、 `Logging` 组件在之前已经介绍过，因此这里我们主要关注 `orm` 和 `redis` 组件的链路跟踪信息。

### ORM链路信息

#### Attributes/Tags

我们随便点开一个 `ORM` 链路 `Span`，看看 `Attributes/Tags` 信息：

可以看到这里的 `span.kind` 是 `internal`，也就是之前介绍过的方法内部 `span` 类型。这里很多 `Tags` 在之前已经介绍过，因此这里主要介绍关于数据库相关的 `Tags`：

| Attribute/Tag | 说明 |
| --- | --- |
| `<br />                db.type<br />              ` | 数据库连接类型。如 `mysql`, `mssql`, `pgsql` 等等。 |
| `db.link` | 数据库连接信息。其中密码字段被自动隐藏。 |
| `db.group` | 在配置文件中的数据库分组名称。 |

#### Events/Process

| Event/Log | 说明 |
| --- | --- |
| `db.execution.sql` | 执行的具体 `SQL` 语句。由于ORM底层是预处理，该语句为方便查看自动拼接而成，仅供参考。 |
| `db.execution.type` | 执行的 `SQL` 语句类型。常见为 `DB.ExecContext` 和 `DB.QueryContext`，分别代表写操作和读操作。 |
| `db.execution.cost` | 当前 `SQL` 语句执行耗时，单位为 `ms` 毫秒。 |

### Redis链路信息

#### Attributes/Tags

| Attribute/Tag | 说明 |
| --- | --- |
| `<br />                redis.host<br />              ` | `Redis` 连接地址。 |
| `redis.port` | `Redis` 连接端口。 |
| `redis.db` | `Redis` 操作 `db`。 |

#### Events/Process

| Event/Log | 说明 |
| --- | --- |
| `redis.execution.command` | `Redis` 执行指令。 |
| `redis.execution.arguments` | `Redis` 执行指令参数。 |
| `redis.execution.cost` | `Redis` 执行指令执行耗时，单位为 `ms` 毫秒。 |