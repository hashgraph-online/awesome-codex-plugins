## 基本介绍
`gtest` 模块提供了简便化的、轻量级的、常用的单元测试方法。是基于标准库 `testing` 的功能扩展封装，主要增加实现了以下特性：

- 单元测试用例多测试项的隔离。
- 增加常用的一系列测试断言方法。
- 断言方法支持多种常见格式断言。提高易用性。
- 测试失败时的错误信息格式统一。
:::tip
`gtest` 设计为比较简便易用，可以满足绝大部分的单元测试场景，如果涉及更复杂的测试场景，可以考虑第三方的 `testify`、 `goconvey` 等测试框架。
:::
**使用方式**：

```go
import "github.com/gogf/gf/v2/test/gtest"
```

**接口文档**：
本章节更新可能不及时，更全面的接口介绍请参考接口文档。
[https://pkg.go.dev/github.com/gogf/gf/v2/test/gtest](https://pkg.go.dev/github.com/gogf/gf/v2/test/gtest)

```go
func C(t *testing.T, f func(t *T))
func Assert(value, expect interface{})
func AssertEQ(value, expect interface{})
func AssertGE(value, expect interface{})
func AssertGT(value, expect interface{})
func AssertIN(value, expect interface{})
func AssertLE(value, expect interface{})
func AssertLT(value, expect interface{})
func AssertNE(value, expect interface{})
func AssertNI(value, expect interface{})
func AssertNil(value interface{})
func DataPath(names ...string) string
func DataContent(names ...string) string
func Error(message ...interface{})
func Fatal(message ...interface{})
```

**简要说明**：

1. 使用 `C` 方法创建一个 `Case`，表示一个单元测试用例。一个单元测试方法可以包含多个 `C`，每一个 `C` 包含的用例往往表示该方法的其中一种可能性测试。
2. 断言方法 `Assert` 支持任意类型的变量比较。 `AssertEQ` 进行断言比较时，会同时比较类型，即严格断言。
3. 使用大小比较断言方法如 `AssertGE` 时，参数支持字符串及数字比较，其中字符串比较为大小写敏感。
4. 包含断言方法 `AssertIN` 及 `AssertNI` 在 v2.9 版本中增强了对 `map` 类型参数的支持。

用于单元测试的包名既可以使用 `包名_test`，也可直接使用 `包名`（即与测试包同名）。两种使用方式都比较常见，且在 `Go` 官方标准库中也均有涉及。但需要注意的是，当需要测试包的私有方法/私有变量时，必须使用 `包名` 命名形式。且在使用 `包名` 命名方式时，注意仅用于单元测试的相关方法（非 `Test*` 测试方法）一般定义为私有，不要公开。

## 基本断言方法

### `Assert`

`Assert` 方法用于检查 `value` 和 `expect` 是否相等。它会将两个值转换为字符串进行比较，如果不相等则会触发 panic。

```go
func Assert(value, expect interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    t.Assert(1, 1)                  // 通过
    t.Assert("hello", "hello")      // 通过
    t.Assert(1, "1")                // 通过，会转换为字符串比较
    t.Assert(map[string]string{"name": "john"}, map[string]string{"name": "john"}) // 通过
})
```

### `AssertEQ`

`AssertEQ` 方法用于检查 `value` 和 `expect` 是否相等，包括它们的类型。这是一个严格的相等检查。

```go
func AssertEQ(value, expect interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    t.AssertEQ(1, 1)                // 通过
    t.AssertEQ("hello", "hello")    // 通过
    t.AssertEQ(1, "1")              // 失败，类型不同
    t.AssertEQ(float32(1.0), float32(1.0)) // 通过
    t.AssertEQ(float32(1.0), float64(1.0)) // 失败，类型不同
})
```

### `AssertNE`

`AssertNE` 方法用于检查 `value` 和 `expect` 是否不相等。

```go
func AssertNE(value, expect interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    t.AssertNE(1, 0)                // 通过
    t.AssertNE("hello", "world")    // 通过
    t.AssertNE(1, "0")              // 通过
})
```

### `AssertNQ`

`AssertNQ` 方法用于检查 `value` 和 `expect` 是否不相等，包括它们的类型。

```go
func AssertNQ(value, expect interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    t.AssertNQ(1, "1")              // 通过，类型不同
    t.AssertNQ(1.0, 1)              // 通过，类型不同
})
```

## 比较断言方法

### `AssertGT`

`AssertGT` 方法用于检查 `value` 是否大于 `expect`。仅支持字符串、整数和浮点数类型的比较。

```go
func AssertGT(value, expect interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    t.AssertGT(2, 1)                // 通过
    t.AssertGT("b", "a")            // 通过
    t.AssertGT(2.1, 2.0)            // 通过
})
```

### `AssertGE`

`AssertGE` 方法用于检查 `value` 是否大于等于 `expect`。仅支持字符串、整数和浮点数类型的比较。

```go
func AssertGE(value, expect interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    t.AssertGE(2, 1)                // 通过
    t.AssertGE(1, 1)                // 通过
    t.AssertGE("b", "a")            // 通过
    t.AssertGE("a", "a")            // 通过
})
```

### `AssertLT`

`AssertLT` 方法用于检查 `value` 是否小于 `expect`。仅支持字符串、整数和浮点数类型的比较。

```go
func AssertLT(value, expect interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    t.AssertLT(1, 2)                // 通过
    t.AssertLT("a", "b")            // 通过
    t.AssertLT(2.0, 2.1)            // 通过
})
```

### `AssertLE`

`AssertLE` 方法用于检查 `value` 是否小于等于 `expect`。仅支持字符串、整数和浮点数类型的比较。

```go
func AssertLE(value, expect interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    t.AssertLE(1, 2)                // 通过
    t.AssertLE(1, 1)                // 通过
    t.AssertLE("a", "b")            // 通过
    t.AssertLE("a", "a")            // 通过
})
```

## 包含断言方法

### `AssertIN`

`AssertIN` 方法用于检查 `value` 是否在 `expect` 中。`expect` 可以是切片、数组、字符串或映射类型。

```go
func AssertIN(value, expect interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    // 切片类型
    t.AssertIN("a", []string{"a", "b", "c"})  // 通过
    t.AssertIN(1, []int{1, 2, 3})            // 通过
    
    // 多个值检查
    t.AssertIN([]string{"a", "b"}, []string{"a", "b", "c"})  // 通过
    
    // 字符串类型
    t.AssertIN("a", "abc")                    // 通过
    
    // Map类型 (v2.9版本新增)
    t.AssertIN("k1", map[string]string{"k1": "v1", "k2": "v2"})  // 通过
    t.AssertIN(1, map[int]string{1: "v1", 2: "v2"})              // 通过
    t.AssertIN([]string{"k1", "k2"}, map[string]string{"k1": "v1", "k2": "v2"})  // 通过
})
```

### `AssertNI`

`AssertNI` 方法用于检查 `value` 是否不在 `expect` 中。`expect` 可以是切片、数组、字符串或映射类型。

```go
func AssertNI(value, expect interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    // 切片类型
    t.AssertNI("d", []string{"a", "b", "c"})  // 通过
    t.AssertNI(4, []int{1, 2, 3})            // 通过
    
    // 多个值检查
    t.AssertNI([]string{"d", "e"}, []string{"a", "b", "c"})  // 通过
    
    // 字符串类型
    t.AssertNI("d", "abc")                    // 通过
    
    // Map类型 (v2.9版本新增)
    t.AssertNI("k3", map[string]string{"k1": "v1", "k2": "v2"})  // 通过
    t.AssertNI(3, map[int]string{1: "v1", 2: "v2"})              // 通过
    t.AssertNI([]string{"k3", "k4"}, map[string]string{"k1": "v1", "k2": "v2"})  // 通过
})
```

### 对`Map`类型包含的断言支持

#### `AssertIN` 对 `Map` 的支持

```go
package main

import (
    "testing"
    "github.com/gogf/gf/v2/test/gtest"
)

func TestAssertIN_Map(t *testing.T) {
    gtest.C(t, func(t *gtest.T) {
        // 检查单个键是否存在于 Map 中
        t.AssertIN("k1", map[string]string{"k1": "v1", "k2": "v2"})
        
        // 支持不同类型的键
        t.AssertIN(1, map[int]string{1: "v1", 2: "v2"})
        
        // 检查多个键是否都存在于 Map 中
        t.AssertIN([]string{"k1", "k2"}, map[string]string{"k1": "v1", "k2": "v2"})
    })
}
```

#### `AssertNI` 对 `Map` 的支持

```go
package main

import (
    "testing"
    "github.com/gogf/gf/v2/test/gtest"
)

func TestAssertNI_Map(t *testing.T) {
    gtest.C(t, func(t *gtest.T) {
        // 检查单个键是否不存在于 Map 中
        t.AssertNI("k3", map[string]string{"k1": "v1", "k2": "v2"})
        
        // 支持不同类型的键
        t.AssertNI(3, map[int]string{1: "v1", 2: "v2"})
        
        // 检查多个键是否都不存在于 Map 中
        t.AssertNI([]string{"k3", "k4"}, map[string]string{"k1": "v1", "k2": "v2"})
    })
}
```

## 其他断言方法

### `AssertNil`

`AssertNil` 方法用于检查 `value` 是否为 nil。

```go
func AssertNil(value interface{})
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    var p *int = nil
    t.AssertNil(nil)                // 通过
    t.AssertNil(p)                  // 通过
})
```

## 辅助方法

### `DataPath`

`DataPath` 方法用于获取当前包的测试数据路径，仅用于单元测试用例。

```go
func DataPath(names ...string) string
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    path := gtest.DataPath("test.txt")  // 返回当前包testdata目录下的test.txt文件路径
})
```

### `DataContent`

`DataContent` 方法用于获取指定测试数据路径的文件内容。

```go
func DataContent(names ...string) string
```

示例：

```go
gtest.C(t, func(t *gtest.T) {
    content := gtest.DataContent("test.txt")  // 返回当前包testdata目录下的test.txt文件内容
})
```

## 使用示例

例如 `gstr` 模块其中一个单元测试用例：

```go
package gstr_test

import (
    "github.com/gogf/gf/v2/test/gtest"
    "github.com/gogf/gf/v2/text/gstr"
    "testing"
)

func Test_Trim(t *testing.T) {
    gtest.C(t, func(t *gtest.T) {
        t.Assert(gstr.Trim(" 123456\n "),      "123456")
        t.Assert(gstr.Trim("#123456#;", "#;"), "123456")
    })
}
```

也可以这样使用：

```go
package gstr_test

import (
    . "github.com/gogf/gf/v2/test/gtest"
    "github.com/gogf/gf/v2/text/gstr"
    "testing"
)

func Test_Trim(t *testing.T) {
    C(t, func(t *T) {
        Assert(gstr.Trim(" 123456\n "),      "123456")
        Assert(gstr.Trim("#123456#;", "#;"), "123456")
    })
}
```

一个单元测试用例可以包含多个 `C`，一个 `C` 也可以执行多个断言。 断言成功时直接PASS，但是如果断言失败，会输出如下类似的错误信息，并终止当前单元测试用例的继续执行（不会终止后续的其他单元测试用例）。

```text
=== RUN   Test_Trim
[ASSERT] EXPECT 123456#; == 123456
1. /Users/john/Workspace/Go/GOPATH/src/github.com/gogf/gf/v2/text/gstr/gstr_z_unit_trim_test.go:20
2. /Users/john/Workspace/Go/GOPATH/src/github.com/gogf/gf/v2/text/gstr/gstr_z_unit_trim_test.go:18
--- FAIL: Test_Trim (0.00s)
FAIL
```