## `AdapterContent`

`AdapterContent` 是基于配置内容的实现，用户可以给定具体的配置内容，生成 `Adapter` 接口对象。配置内容支持多种格式，格式列表同配置管理组件。

## 使用示例

大部分场景下，我们可以通过框架已经封装好的g.Cfg单例对象来便捷使用基于文件的配置管理实现。例如：

```go
package main

import (
    "fmt"

    "github.com/gogf/gf/v2/os/gcfg"
    "github.com/gogf/gf/v2/os/gctx"
)

const content = `
server:
  address:     ":8888"
  openapiPath: "/api.json"
  swaggerPath: "/swagger"
  dumpRouterMap: false

database:
  default:
    link:  "mysql:root:12345678@tcp(127.0.0.1:3306)/test"
    debug:  true
`

func main() {
    var ctx = gctx.New()
    adapter, err := gcfg.NewAdapterContent(content)
    if err != nil {
        panic(err)
    }
    config := gcfg.NewWithAdapter(adapter)
    fmt.Println(config.MustGet(ctx, "server.address").String())
    fmt.Println(config.MustGet(ctx, "database.default").Map())
}
```

运行后，终端输出：

```html
:8888
map[debug:true link:mysql:root:12345678@tcp(127.0.0.1:3306)/test]
```