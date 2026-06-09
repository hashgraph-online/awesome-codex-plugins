相关方法：

```go
func (r *Response) WriteJson(content interface{}) error
func (r *Response) WriteJsonExit(content interface{}) error
func (r *Response) WriteJsonP(content interface{}) error
func (r *Response) WriteJsonPExit(content interface{}) error
func (r *Response) WriteXml(content interface{}, rootTag ...string) error
func (r *Response) WriteXmlExit(content interface{}, rootTag ...string) error
```

`Response` 提供了对 `JSON/XML` 数据格式输出的原生支持，通过以下方法实现：

1. `WriteJson*` 方法用于返回 `JSON` 数据格式，参数为任意类型，可以为 `string`、 `map`、 `struct` 等等。返回的 `Content-Type` 为 `application/json`。
2. `WriteXml*` 方法用于返回 `XML` 数据格式，参数为任意类型，可以为 `string`、 `map`、 `struct` 等等。返回的 `Content-Type` 为 `application/xml`。
:::tip
对 `JSON` 数据格式支持的同时，同时也支持 `JSONP` 协议。
:::
## `JSON`

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    s := g.Server()
    s.Group("/", func(group *ghttp.RouterGroup) {
        group.ALL("/json", func(r *ghttp.Request) {
            r.Response.WriteJson(g.Map{
                "id":   1,
                "name": "john",
            })
        })
    })
    s.SetPort(8199)
    s.Run()
}
```

执行后，我们通过 `curl` 工具测试下：

```bash
$ curl -i http://127.0.0.1:8199/json
HTTP/1.1 200 OK
Content-Type: application/json
Server: GoFrame HTTP Server
Date: Sun, 05 Jan 2020 02:49:31 GMT
Content-Length: 22

{"id":1,"name":"john"}
```

## `JSONP`

需要注意使用 `JSONP` 协议时必须通过 `Query` 方式提供 `callback` 参数。

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    s := g.Server()
    s.Group("/", func(group *ghttp.RouterGroup) {
        group.ALL("/jsonp", func(r *ghttp.Request) {
            r.Response.WriteJsonP(g.Map{
                "id":   1,
                "name": "john",
            })
        })
    })
    s.SetPort(8199)
    s.Run()
}
```

执行后，我们通过 `curl` 工具测试下：

```bash
$ curl -i "http://127.0.0.1:8199/jsonp?callback=MyCallback"
HTTP/1.1 200 OK
Server: GoFrame HTTP Server
Date: Sun, 05 Jan 2020 02:50:42 GMT
Content-Length: 34
Content-Type: text/plain; charset=utf-8

MyCallback({"id":1,"name":"john"})
```

## `XML`

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    s := g.Server()
    s.Group("/", func(group *ghttp.RouterGroup) {
        group.ALL("/xml", func(r *ghttp.Request) {
            r.Response.Write(`<?xml version="1.0" encoding="UTF-8"?>`)
            r.Response.WriteXml(g.Map{
                "id":   1,
                "name": "john",
            })
        })
    })
    s.SetPort(8199)
    s.Run()
}
```

执行后，我们通过 `curl` 工具测试下：

```bash
$ curl -i http://127.0.0.1:8199/xml
HTTP/1.1 200 OK
Content-Type: application/xml
Server: GoFrame HTTP Server
Date: Sun, 05 Jan 2020 03:00:55 GMT
Content-Length: 76

<?xml version="1.0" encoding="UTF-8"?><doc><id>1</id><name>john</name></doc>
```