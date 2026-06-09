项目中我们经常会遇到大量 `struct` 的使用，以及各种数据类型到 `struct` 的转换/赋值（特别是 `json`/ `xml`/各种协议编码转换）。为提高编码及项目维护效率， `gconv` 模块为各位开发者带来了极大的福利，为数据解析提供了更高的灵活度。

`gconv` 模块通过 `Struct` 转换方法执行 `struct` 类型转换，其定义如下：

```go
// Struct maps the params key-value pairs to the corresponding struct object's attributes.
// The third parameter `mapping` is unnecessary, indicating the mapping rules between the
// custom key name and the attribute name(case sensitive).
//
// Note:
// 1. The `params` can be any type of map/struct, usually a map.
// 2. The `pointer` should be type of *struct/**struct, which is a pointer to struct object
//    or struct pointer.
// 3. Only the public attributes of struct object can be mapped.
// 4. If `params` is a map, the key of the map `params` can be lowercase.
//    It will automatically convert the first letter of the key to uppercase
//    in mapping procedure to do the matching.
//    It ignores the map key, if it does not match.
func Struct(params interface{}, pointer interface{}, mapping ...map[string]string) (err error)
```

其中：

1. `params` 为需要转换到 `struct` 的变量参数，可以为任意数据类型，常见的数据类型为 `map`。
2. `pointer` 为需要执行转的目标 `struct` 对象，这个参数必须为该 `struct` 的对象指针，转换成功后该对象的属性将会更新。
3. `mapping` 为自定义的 `map键名` 到 `strcut属性` 之间的映射关系，此时 `params` 参数必须为 `map` 类型，否则该参数无意义。大部分场景下使用可以不用提供该参数，直接使用默认的转换规则即可。
:::tip
更多的 `struct` 相关转换方法请参考接口文档： [https://pkg.go.dev/github.com/gogf/gf/v2/util/gconv](https://pkg.go.dev/github.com/gogf/gf/v2/util/gconv)
:::
## 转换规则

`gconv` 模块的 `struct` 转换特性非常强大，支持任意数据类型到 `struct` 属性的映射转换。在没有提供自定义 `mapping` 转换规则的情况下，默认的转换规则如下：

1. `struct` 中需要匹配的属性必须为 **公开属性**(首字母大写)。
2. 根据 `params` 类型的不同，逻辑会有不同：
   - `params` 参数类型为 `map`：键名会自动按照 **不区分大小写** 且 **忽略特殊字符** 的形式与struct属性进行匹配。
   - `params` 参数为其他类型：将会把该变量值与 `struct` 的第一个属性进行匹配。
   -  此外，如果 `struct` 的属性为复杂数据类型如 `slice`, `map`, `strcut` 那么会进行递归匹配赋值。
3. 如果匹配成功，那么将键值赋值给属性，如果无法匹配，那么忽略该键值。

## 匹配规则优先级说明(只针对于map到struct的转换)

1.如果 `mapping` 参数不为空，将会按照 `mapping` 的 `key ` 到 `strcut字段名` 之间的映射关系。

2.如果设置了字段的 `tag`，会使用 `tag` 来匹配 `params` 参数的  `key`。

       如果没有设置 `tag`，gconv将会依次按照 `gconv, param, c, p, json` 这个顺序来查找字段是否有对应的 `tag`

3.按照 `字段名` 匹配。

4.如果以上都没有匹配到，gconv将会遍历 `params` 参数所有的 `key`，按照 以下规则来匹配

`字段名`:忽略大小写和下划线

`key`: 忽略大小写和下划线和特殊字符

提示

:::warning
没有特殊情况，请尽量满足前三条规则，第四条规则性能较差
:::

以下是几个 `map` 键名与 `struct` 属性名称的示例：

```
map键名    struct属性     是否匹配
name       Name           match
Email      Email          match
nickname   NickName       match
NICKNAME   NickName       match
Nick-Name  NickName       match
nick_name  NickName       match
nick name  NickName       match
NickName   Nick_Name      match
Nick-name  Nick_Name      match
nick_name  Nick_Name      match
nick name  Nick_Name      match
```

## 自动创建对象

当给定的 `pointer` 参数类型为 `**struct` 时， `Struct` 方法内部将会自动创建该 `struct` 对象，并修改传递变量指向的指针地址。

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    type User struct {
        Uid  int
        Name string
    }
    params := g.Map{
        "uid":  1,
        "name": "john",
    }
    var user *User
    if err := gconv.Struct(params, &user); err != nil {
        panic(err)
    }
    g.Dump(user)
}
```

执行后，输出结果为：

```
{
    Uid:  1,
    Name: "john",
}
```

## `Struct` 递归转换

递归转换是指当 `struct` 对象包含子对象时，并且子对象是 `embedded` 方式定义时，可以将 `params` 参数数据（第一个参数）同时递归地映射到其子对象上，常用于带有继承对象的 `struct` 上。

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    type Ids struct {
        Id         int    `json:"id"`
        Uid        int    `json:"uid"`
    }
    type Base struct {
        Ids
        CreateTime string `json:"create_time"`
    }
    type User struct {
        Base
        Passport   string `json:"passport"`
        Password   string `json:"password"`
        Nickname   string `json:"nickname"`
    }
    data := g.Map{
        "id"          : 1,
        "uid"         : 100,
        "passport"    : "john",
        "password"    : "123456",
        "nickname"    : "John",
        "create_time" : "2019",
    }
    user := new(User)
    gconv.Struct(data, user)
    g.Dump(user)
}
```

执行后，终端输出结果为：

```
{
    Id:         1,
    Uid:        100,
    CreateTime: "2019",
    Passport:   "john",
    Password:   "123456",
    Nickname:   "John",
}
```

## 示例1，基本使用

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

type User struct {
    Uid      int
    Name     string
    SiteUrl  string
    NickName string
    Pass1    string `c:"password1"`
    Pass2    string `c:"password2"`
}

func main() {
    var user *User

    // 使用默认映射规则绑定属性值到对象
    user = new(User)
    params1 := g.Map{
        "uid":       1,
        "Name":      "john",
        "site_url":  "https://goframe.org",
        "nick_name": "johng",
        "PASS1":     "123",
        "PASS2":     "456",
    }
    if err := gconv.Struct(params1, user); err == nil {
        g.Dump(user)
    }

    // 使用struct tag映射绑定属性值到对象
    user = new(User)
    params2 := g.Map{
        "uid":       2,
        "name":      "smith",
        "site-url":  "https://goframe.org",
        "nick name": "johng",
        "password1": "111",
        "password2": "222",
    }
    if err := gconv.Struct(params2, user); err == nil {
        g.Dump(user)
    }
}
```

可以看到，我们可以直接通过 `Struct` 方法将 `map` 按照默认规则绑定到 `struct` 上，也可以使用 `struct tag` 的方式进行灵活的设置。此外， `Struct` 方法有第三个 `map` 参数，用于指定自定义的参数名称到属性名称的映射关系。

执行后，输出结果为：

```
{
    Uid:      1,
    Name:     "john",
    SiteUrl:  "https://goframe.org",
    NickName: "johng",
    Pass1:    "123",
    Pass2:    "456",
}
{
    Uid:      2,
    Name:     "smith",
    SiteUrl:  "https://goframe.org",
    NickName: "johng",
    Pass1:    "111",
    Pass2:    "222",
}
```

## 示例2，复杂属性类型

属性支持 `struct` 对象或者 `struct` 对象指针（目标为指针且为 `nil` 时，转换时会自动初始化）转换。

```go
package main

import (
    "github.com/gogf/gf/v2/util/gconv"
    "github.com/gogf/gf/v2/frame/g"
    "fmt"
)

func main() {
    type Score struct {
        Name   string
        Result int
    }
    type User1 struct {
        Scores Score
    }
    type User2 struct {
        Scores *Score
    }

    user1  := new(User1)
    user2  := new(User2)
    scores := g.Map{
        "Scores": g.Map{
            "Name":   "john",
            "Result": 100,
        },
    }

    if err := gconv.Struct(scores, user1); err != nil {
        fmt.Println(err)
    } else {
        g.Dump(user1)
    }
    if err := gconv.Struct(scores, user2); err != nil {
        fmt.Println(err)
    } else {
        g.Dump(user2)
    }
}
```

执行后，输出结果为：

```
{
    Scores: {
        Name:   "john",
        Result: 100,
    },
}
{
    Scores: {
        Name:   "john",
        Result: 100,
    },
}
```