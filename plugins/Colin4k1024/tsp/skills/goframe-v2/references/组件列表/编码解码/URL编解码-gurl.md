`URL` 编码解析。

**使用方式**：

```go
import "github.com/gogf/gf/v2/encoding/gurl"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/encoding/gurl](https://pkg.go.dev/github.com/gogf/gf/v2/encoding/gurl)

## `URL` 参数构建

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/encoding/gurl"
    "net/url"
)

func main() {
    // 构建url参数
    values := url.Values{}
    values.Add("name", "gopher")
    values.Add("limit", "20")
    values.Add("page", "7")

    // 生成URL编码查询字符串 limit=20&name=gopher&page=7
    urlStr := gurl.BuildQuery(values)
    fmt.Println(urlStr)
}
```

执行后，输出结果为：

```
limit=20&name=gopher&page=7
```

## `URL` 参数编码与解码

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/encoding/gurl"
    "log"
)

func main() {
    // 编码对字符串进行转义，以便可以将其安全地放置在URL查询中。
    encodeStr := gurl.Encode("limit=20&name=gopher&page=7")
    fmt.Println(encodeStr)

    // 进行URL解码
    decodeStr, err := gurl.Decode("limit%3D20%26name%3Dgopher%26page%3D7")
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println(decodeStr)
}
```

执行后，输出结果为：

```
limit%3D20%26name%3Dgopher%26page%3D7
limit=20&name=gopher&page=7
```

## 解析 `URL`

`component` 参数值可选项:

| 参数值 | 说明 |
| --- | --- |
| -1 | all |
| 1 | scheme |
| 2 | host |
| 4 | port |
| 8 | user |
| 16 | pass |
| 32 | path |
| 64 | query |
| 128 | fragment |

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/encoding/gurl"
    "log"
)

func main() {
    // 解析URL并返回其组件
    data, err := gurl.ParseURL("http://127.0.0.1:8199/goods?limit=20&name=gopher&page=7", -1)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println(data)
    fmt.Println(data["host"])
    fmt.Println(data["query"])
    fmt.Println(data["path"])
    fmt.Println(data["scheme"])
    fmt.Println(data["fragment"])
}
```

执行后，输出结果为：

```
map[fragment: host:127.0.0.1 pass: path:/goods port:8199 query:limit=20&name=gopher&page=7 scheme:http user:]
127.0.0.1
limit=20&name=gopher&page=7
/goods
http
```