## 文件存储

在默认情况下， `ghttp.Server` 的 `Session` 存储使用了 `内存+文件` 的方式，使用 `StorageFile` 对象实现。具体原理为：

1. `Session` 的数据操作完全基于内存；
2. 使用 `gcache` 进程缓存模块控制数据过期；
3. 使用文件存储持久化存储管理 `Session` 数据；
4. 当且仅有当 `Session` 被标记为 `dirty` 时（数据有更新）才会执行 `Session` 序列化并执行文件持久化存储；
5. 当且仅当内存中的 `Session` 不存在时，才会从文件存储中反序列化恢复 `Session` 数据到内存中，降低 `IO` 调用；
6. 序列化/反序列化使用的是标准库的 `json.Marshal/UnMarshal` 方法；

从原理可知，当 `Session` 为读多写少的场景中， `Session` 的数据操作非常高效。
:::tip
有个注意的细节，由于文件存储涉及到文件操作，为便于降低 `IO` 开销并提高 `Session` 操作性能，并不是每一次 `Session` 请求结束后都会立即刷新对应 `Session` 的 `TTL` 时间。而只有当涉及到更新操作（被标记为 `dirty`）时才会立即刷新其 `TTL`；针对于读取请求，将会每隔 `一分钟` 更新前一分钟内读取操作对应的 `Session` 文件 `TTL` 时间，以便于 `Session` 自动续活。
:::
## 使用示例

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/os/gtime"
    "time"
)

func main() {
    s := g.Server()
    s.SetSessionMaxAge(time.Minute)
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
3. 接着，我们停止程序，并重新启动，再次访问 [http://127.0.0.1:8199/get](http://127.0.0.1:8199/get)，可以看到 `Session` 变量已经从文件存储中恢复；
4. 等待1分钟后，再次访问 [http://127.0.0.1:8199/get](http://127.0.0.1:8199/get) 可以看到已经无法获取该 `Session`，因为该 `Session` 已经过期；