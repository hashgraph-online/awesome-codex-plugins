## Redis KeyValue Storage

文件存储的方式在单节点的场景下非常不错，但是涉及到对应用进行多节点部署的场景下，各个节点的 `Session` 无法共享，因此需要将 `Session` 存储单独剥离出来管理， `Redis` 服务器是比较常见的一个选择。

`gsession` 的 `Redis` 存储使用 `StorageRedis` 对象实现，与文件存储比较类似，为了提高执行效率，也是采用了 `内存+Redis` 的方式。与文件存储唯一不同的是，在每一次请求中如果需要对 `Session` 进行操作时，将会从 `Redis` 中拉取一次最新的 `Session` 数据（而文件存储只会在 `Session` 不存在时读取一次文件）。在每一次请求结束之后，将全量的 `Session` 数据通过 `JSON` 序列化之后通过 `KeyValue` 方式更新到 `Redis` 服务中。
:::tip
如果单个用户下(以用户维度举例) `Session` 数据量不大的业务场景中，都推荐使用这种 `Storage` 方式。如果单个用户 `Session` 数据量较大（例如 `>10MB`），可以参考 `HashTable` 的 `Storage` 方式： [Session-Redis-HashTable](Session-Redis-HashTable.md)
:::
## 使用示例

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/os/gsession"
    "github.com/gogf/gf/v2/os/gtime"
    "time"
)

func main() {
    s := g.Server()
    s.SetSessionMaxAge(time.Minute)
    s.SetSessionStorage(gsession.NewStorageRedis(g.Redis()))
    s.Group("/", func(group *ghttp.RouterGroup) {
        group.ALL("/set", func(r *ghttp.Request) {
            r.Session.Set("time", gtime.Timestamp())
            r.Response.Write("ok")
        })
        group.ALL("/get", func(r *ghttp.Request) {
            r.Response.Write(r.Session.Data())
        })
        group.ALL("/del", func(r *ghttp.Request) {
            _ = r.Session.RemoveAll()
            r.Response.Write("ok")
        })
    })
    s.SetPort(8199)
    s.Run()
}
```

在该实例中，为了方便观察过期失效，我们将 `Session` 的过期时间设置为 `1分钟`。执行后，

1. 首先，访问 [http://127.0.0.1:8199/set](http://127.0.0.1:8199/set) 设置一个 `Session` 变量；
2. 随后，访问 [http://127.0.0.1:8199/get](http://127.0.0.1:8199/get) 可以看到该 `Session` 变量已经设置并成功获取；
3. 接着，我们停止程序，并重新启动，再次访问 [http://127.0.0.1:8199/get](http://127.0.0.1:8199/get)，可以看到 `Session` 变量已经从 `Redis` 存储中恢复；如果我们手动修改 `Redis` 中的对应键值数据，页面刷新时也会读取到最新的值；
4. 等待1分钟后，再次访问 [http://127.0.0.1:8199/get](http://127.0.0.1:8199/get) 可以看到已经无法获取该 `Session`，因为该 `Session` 已经过期；