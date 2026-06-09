前面关于复杂类型的转换功能如果大家觉得还不够的话，那么您可以了解下 `Scan` 转换方法，该方法可以实现对任意参数到 `基础数据类型/struct/struct数组/map/map数组` 的转换，并且根据开发者输入的转换目标参数自动识别执行转换。

该方法定义如下：

```go
// Scan automatically checks the type of `pointer` and converts `params` to `pointer`.
// It supports various types of parameter conversions, including:
// 1. Basic types (int, string, float, etc.)
// 2. Pointer types
// 3. Slice types
// 4. Map types
// 5. Struct types
//
// The `paramKeyToAttrMap` parameter is used for mapping between attribute names and parameter keys.
func Scan(srcValue any, dstPointer any, paramKeyToAttrMap ...map[string]string) (err error)
```

## 基础数据类型转换

`Scan` 方法在`v2.9`版本中增强了对基础数据类型的转换支持，可以将各种类型的值转换为基础数据类型，如 `int`、`string`、`bool` 等。

### 整数类型转换

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    // 字符串转整数
    var num int
    if err := gconv.Scan("123", &num); err != nil {
        panic(err)
    }
    g.Dump(num) // 输出: 123
    
    // 浮点数转整数
    var num2 int
    if err := gconv.Scan(123.45, &num2); err != nil {
        panic(err)
    }
    g.Dump(num2) // 输出: 123
    
    // 布尔值转整数
    var num3 int
    if err := gconv.Scan(true, &num3); err != nil {
        panic(err)
    }
    g.Dump(num3) // 输出: 1
}
```

### 字符串类型转换

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    // 整数转字符串
    var str string
    if err := gconv.Scan(123, &str); err != nil {
        panic(err)
    }
    g.Dump(str) // 输出: "123"
    
    // 浮点数转字符串
    var str2 string
    if err := gconv.Scan(123.45, &str2); err != nil {
        panic(err)
    }
    g.Dump(str2) // 输出: "123.45"
    
    // 布尔值转字符串
    var str3 string
    if err := gconv.Scan(true, &str3); err != nil {
        panic(err)
    }
    g.Dump(str3) // 输出: "true"
}
```

### 布尔类型转换

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    // 整数转布尔值
    var b1 bool
    if err := gconv.Scan(1, &b1); err != nil {
        panic(err)
    }
    g.Dump(b1) // 输出: true
    
    // 字符串转布尔值
    var b2 bool
    if err := gconv.Scan("true", &b2); err != nil {
        panic(err)
    }
    g.Dump(b2) // 输出: true
    
    // 0值转布尔值
    var b3 bool
    if err := gconv.Scan(0, &b3); err != nil {
        panic(err)
    }
    g.Dump(b3) // 输出: false
}
```

### 指针类型转换

`Scan` 方法还支持指针类型的转换，可以将值转换为指针类型，或者将指针类型转换为另一个指针类型。

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    // 值转指针
    var numPtr *int
    if err := gconv.Scan(123, &numPtr); err != nil {
        panic(err)
    }
    g.Dump(numPtr)  // 输出: 123 (指针指向的值)
    
    // 指针转指针
    var num = 456
    var numPtr2 *int
    if err := gconv.Scan(&num, &numPtr2); err != nil {
        panic(err)
    }
    g.Dump(numPtr2) // 输出: 456 (指针指向的值)
}
```

## 自动识别转换 `Struct`

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
    if err := gconv.Scan(params, &user); err != nil {
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

## 自动识别转换 `Struct` 数组

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
    params := g.Slice{
        g.Map{
            "uid":  1,
            "name": "john",
        },
        g.Map{
            "uid":  2,
            "name": "smith",
        },
    }
    var users []*User
    if err := gconv.Scan(params, &users); err != nil {
        panic(err)
    }
    g.Dump(users)
}
```

执行后，终端输出：

```
[
    {
        Uid:  1,
        Name: "john",
    },
    {
        Uid:  2,
        Name: "smith",
    },
]
```

## 自动识别转换Map

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    var (
        user   map[string]string
        params = g.Map{
            "uid":  1,
            "name": "john",
        }
    )
    if err := gconv.Scan(params, &user); err != nil {
        panic(err)
    }
    g.Dump(user)
}
```

执行后，输出结果为：

```
{
    "uid":  "1",
    "name": "john",
}
```

## 自动识别转换 `Map` 数组

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    var (
        users  []map[string]string
        params = g.Slice{
            g.Map{
                "uid":  1,
                "name": "john",
            },
            g.Map{
                "uid":  2,
                "name": "smith",
            },
        }
    )
    if err := gconv.Scan(params, &users); err != nil {
        panic(err)
    }
    g.Dump(users)
}
```

执行后，输出结果为：

```
[
    {
        "uid":  "1",
        "name": "john",
    },
    {
        "uid":  "2",
        "name": "smith",
    },
]
```

## Scan 高级选项（v2.10+）

从 `v2.10.0` 版本开始，`gconv` 包新增了 `ScanWithOptions` 函数，支持更灵活的转换控制选项，特别是 `OmitEmpty` 和 `OmitNil` 选项。

### 方法定义

```go
// ScanWithOptions 自动检查 dstPointer 的类型并将 srcValue 转换为 dstPointer。
// 它与 Scan 函数相同，但接受一个或多个 ScanOption 值以进行额外的转换控制。
//
// 使用 ScanWithOptions 时，"忽略"（omit）意味着跳过从源到目标的赋值，
// 从而保留目标字段中的现有值。
//
//   - option.OmitEmpty，当设置为 true 时，跳过空源值的赋值（例如：空字符串、
//     零数值、零时间值、空切片或映射），保留目标中任何现有的非空值。
//
//   - option.OmitNil，当设置为 true 时，跳过 nil 源值的赋值，
//     当源包含 nil 时保留目标中的现有值。
//
func ScanWithOptions(srcValue any, dstPointer any, option ...ScanOption) (err error)
```

### OmitEmpty 选项

`OmitEmpty` 选项用于在转换时跳过空值字段的赋值，保留目标结构体中已有的非空值。

**什么是空值？**

- 空字符串（`""`）
- 零数值（`0`、`0.0`）
- 零时间值
- 空切片或空映射（`nil` 或长度为`0`）

**使用场景：** 当你需要将源数据合并到目标数据中，但不希望源数据中的空值覆盖目标数据中已有的值时，可以使用此选项。

**示例：**

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    type User struct {
        Name  string
        Age   int
        Email string
    }

    // 目标结构体包含初始值
    person := User{
        Name:  "张三",
        Age:   30,
        Email: "zhangsan@example.com",
    }

    // 源数据包含一些空值
    sourceData := g.Map{
        "Name":  "",     // 空字符串
        "Age":   25,     // 非空值
        "Email": "",     // 空字符串
    }

    // 使用 OmitEmpty 选项进行转换
    err := gconv.ScanWithOptions(sourceData, &person, gconv.ScanOption{
        OmitEmpty: true,
    })
    if err != nil {
        panic(err)
    }

    g.Dump(person)
}
```

执行后，输出结果为：

```js
{
    Name:  "张三",      // 保持原值，因为源值为空字符串
    Age:   25,          // 更新为源值
    Email: "zhangsan@example.com", // 保持原值，因为源值为空字符串
}
```

### OmitNil 选项

`OmitNil` 选项用于在转换时跳过 `nil` 值字段的赋值，保留目标结构体中已有的值。

**使用场景：** 当你的源数据是 `map[string]any` 类型，其中可能包含 `nil` 值，而你不希望这些 `nil` 值覆盖目标结构体中已有的值时，可以使用此选项。

**示例：**

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    type Person struct {
        Name  string
        Age   int
        Email string
    }

    // 目标结构体包含初始值
    person := Person{
        Name:  "李四",
        Age:   0,
        Email: "lisi@example.com",
    }

    // 源数据包含 nil 值
    sourceData := map[string]any{
        "Name":  nil,  // nil 值
        "Age":   30,   // 非 nil 值
        "Email": nil,  // nil 值
    }

    // 使用 OmitNil 选项进行转换
    err := gconv.ScanWithOptions(sourceData, &person, gconv.ScanOption{
        OmitNil: true,
    })
    if err != nil {
        panic(err)
    }

    g.Dump(person)
}
```

执行后，输出结果为：

```js
{
    Name:  "李四",      // 保持原值，因为源值为 nil
    Age:   30,          // 更新为源值
    Email: "lisi@example.com", // 保持原值，因为源值为 nil
}
```

### 同时使用 OmitEmpty 和 OmitNil

你可以同时使用这两个选项来实现更灵活的转换控制：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/util/gconv"
)

func main() {
    type User struct {
        Name  string
        Age   int
        Email string
    }

    // 目标结构体包含初始值
    user := User{
        Name:  "王五",
        Age:   0,
        Email: "wangwu@example.com",
    }

    // 源数据同时包含空值和 nil 值
    sourceData := map[string]any{
        "Name":  "",    // 空字符串
        "Age":   25,    // 非空值
        "Email": nil,   // nil 值
    }

    // 同时使用 OmitEmpty 和 OmitNil 选项
    err := gconv.ScanWithOptions(sourceData, &user, gconv.ScanOption{
        OmitEmpty: true,
        OmitNil:   true,
    })
    if err != nil {
        panic(err)
    }

    g.Dump(user)
}
```

执行后，输出结果为：

```js
{
    Name:  "王五",      // 保持原值，因为源值为空字符串
    Age:   25,          // 更新为源值
    Email: "wangwu@example.com", // 保持原值，因为源值为 nil
}
```