## 基本介绍

`gutil` 组件封装了一些开发中常用的工具方法。

使用方式：

```go
import "github.com/gogf/gf/v2/util/gutil"
```

接口文档：

[https://pkg.go.dev/github.com/gogf/gf/v2/util/gutil](https://pkg.go.dev/github.com/gogf/gf/v2/util/gutil)

## 常用方法

### `Dump`

- 说明： `Dump` 将 `values` 以更好的可读性的方式输出在标准输出中。

- 格式：

```go
Dump(values ...interface{})
```

- 示例：

```go
type User struct {
      Name string
      Age int
}

type Location struct {
      Province string
      City string
}

type UserInfo struct {
      U User
      L Location
}

func main() {
      userList := make([]UserInfo, 0)
      userList = append(userList, UserInfo{
          U: User{
              Name: "郭强",
              Age:  18,
          },
          L: Location{
              Province: "四川",
              City:     "成都",
          },
      })
      userList = append(userList, UserInfo{
          U: User{
              Name: "黄骞",
              Age:  18,
          },
          L: Location{
              Province: "江苏",
              City:     "南京",
          },
      })

      gutil.Dump(userList)
}

// Output:
[
      {
          U: {
              Name: "郭强",
              Age:  18,
          },
          L: {
              Province: "四川",
              City:     "成都",
          },
      },
      {
          U: {
              Name: "黄骞",
              Age:  18,
          },
          L: {
              Province: "江苏",
              City:     "南京",
          },
      },
]
```

### `DumpWithType`

- 说明： `DumpWithType` 和 `Dump` 类似，但是多了类型信息。

- 格式：

```go
DumpWithType(values ...interface{})
```

- 示例：

```go
type User struct {
      Name string
      Age int
}

type Location struct {
      Province string
      City string
}

type UserInfo struct {
      U User
      L Location
}

func main() {
      userList := make([]UserInfo, 0)
      userList = append(userList, UserInfo{
          U: User{
              Name: "郭强",
              Age:  18,
          },
          L: Location{
              Province: "四川",
              City:     "成都",
          },
      })
      userList = append(userList, UserInfo{
          U: User{
              Name: "黄骞",
              Age:  18,
          },
          L: Location{
              Province: "江苏",
              City:     "南京",
          },
      })

      gutil.DumpWithType(userList)
}

// Output:
[]main.UserInfo(2) [
      main.UserInfo(2) {
          U: main.User(2) {
              Name: string(6) "郭强",
              Age:  int(18),
          },
          L: main.Location(2) {
              Province: string(6) "四川",
              City:     string(6) "成都",
          },
      },
      main.UserInfo(2) {
          U: main.User(2) {
              Name: string(6) "黄骞",
              Age:  int(18),
          },
          L: main.Location(2) {
              Province: string(6) "江苏",
              City:     string(6) "南京",
          },
      },
]
```

### `DumpTo`

- 说明： `DumpTo` 将 `value` 以自定义的输出形式写入到 `write` 中。

- 格式：

```go
DumpTo(writer io.Writer, value interface{}, option DumpOption)
```

- 示例：
```go
package main

import (
      "bytes"
      "fmt"
      "github.com/gogf/gf/v2/util/gutil"
      "io"
)

type UserInfo struct {
      Name     string
      Age      int
      Province string
      City     string
}

type DumpWriter struct {
      Content string
}

func (d *DumpWriter) Write(p []byte) (n int, err error) {
      buffer := bytes.NewBuffer(nil)
      buffer.WriteString("I'm Start!\n")
      buffer.WriteString(string(p))
      buffer.WriteString("\nI'm End!\n")

      d.Content = buffer.String()

      return buffer.Len(), nil
}

func main() {
      u := UserInfo{
          "a", 18, "b", "c",
      }

      var dw io.Writer = &DumpWriter{}

      gutil.DumpTo(dw, u, gutil.DumpOption{})

      fmt.Println(dw.(*DumpWriter).Content)
}

// Output:
I'm Start!
{
      Name:     "a",
      Age:      18,
      Province: "b",
      City:     "c",
}
I'm End!
```