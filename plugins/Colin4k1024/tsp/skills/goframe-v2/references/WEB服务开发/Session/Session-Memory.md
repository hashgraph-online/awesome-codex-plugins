## 内存存储

内存存储比较简单，性能也很高效，但没有持久化存储 `Session` 数据，因此应用程序重启之后便会丢失 `Session` 数据，可用于特定的业务场景中。 `gsession` 的 `内存` 存储使用 `StorageMemory` 对象实现，

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
    s.SetSessionStorage(gsession.NewStorageMemory())
    s.Group("/", func(group *ghttp.RouterGroup) {
        group.ALL("/set", func(r *ghttp.Request) {
            r.Session.MustSet("time", gtime.Timestamp())
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
3. 接着，我们停止程序，并重新启动，再次访问 [http://127.0.0.1:8199/get](http://127.0.0.1:8199/get)，可以看到 `Session` 变量已经没有了；