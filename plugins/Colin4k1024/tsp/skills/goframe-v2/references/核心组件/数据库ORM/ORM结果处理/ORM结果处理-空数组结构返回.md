## 痛点描述

经过前面的章节介绍，如果给定一个未初始化的数组（值为 `nil`），在 `ORM` 根据给定条件未查询到数据时，并不会自动初始化该数组。因此该未初始化的数组结果如果通过 `JSON` 进行编码后，会被转换为 `null` 值。

```go
package main

import (
    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"

    "fmt"

    "github.com/gogf/gf/v2/encoding/gjson"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gtime"
)

func main() {
    type User struct {
        Id        uint64      // 主键
        Passport  string      // 账号
        Password  string      // 密码
        NickName  string      // 昵称
        CreatedAt *gtime.Time // 创建时间
        UpdatedAt *gtime.Time // 更新时间
    }
    type Response struct {
        Users []User
    }
    var res = &Response{}
    err := g.Model("user").WhereGT("id", 10).Scan(&res.Users)
    fmt.Println(err)
    fmt.Println(gjson.MustEncodeString(res))
}
```

执行后，终端展示结果为：

```html
<nil>
{"Users":null}
```

在大部分场景下， `ORM` 查询的数据需要渲染展示在浏览器页面上，也就意味着返回的数据需要给前端 `JS` 进行处理。为了对前端 `JS` 处理后端返回数据时更加友好，如果在后端查询不到数据时，期望返回一个空的数组结构，而不是返回一个 `null` 属性值。

## 改进方案

针对这种场景，可以给 `ORM` 的 `Scan` 方法一个初始化的空数组即可。当 `ORM` 查询不到数据时，该数组属性仍然是一个空数组，而不是 `nil`，返回 `JSON` 编码后也不会是 `null` 值。

```go
package main

import (
    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"

    "fmt"

    "github.com/gogf/gf/v2/encoding/gjson"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gtime"
)

func main() {
    type User struct {
        Id        uint64      // 主键
        Passport  string      // 账号
        Password  string      // 密码
        NickName  string      // 昵称
        CreatedAt *gtime.Time // 创建时间
        UpdatedAt *gtime.Time // 更新时间
    }
    type Response struct {
        Users []User
    }
    var res = &Response{
        Users: make([]User, 0),
    }
    err := g.Model("user").WhereGT("id", 10).Scan(&res.Users)
    fmt.Println(err)
    fmt.Println(gjson.MustEncodeString(res))
}
```

执行后，终端展示结果为：

```html
<nil>
{"Users":[]}
```