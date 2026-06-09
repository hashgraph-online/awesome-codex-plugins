## RedisHashTableStorage

与 `RedisKeyValueStorage` 不同的地方在于 `RedisHashTableStorage` 底层使用 `HashTable` 存储 `Session` 数据，每一次对 `Session` 的增删查改都是直接访问 `Redis` 服务实现（单条数据项操作），不存在像 `RedisKeyValueStorage` 那样初始化全量拉取一次，请求结束后如有修改再全量更新到 `Redis` 服务的操作。

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
    s.SetSessionStorage(gsession.NewStorageRedisHashTable(g.Redis()))
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