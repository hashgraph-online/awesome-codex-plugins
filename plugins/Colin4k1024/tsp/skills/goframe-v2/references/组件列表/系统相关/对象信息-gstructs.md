## 基本介绍

`gstructs` 组件用于方便获取结构体的相关信息。

这是一个偏底层组件，一般业务上很少会用到，在框架、基础库、中间件编写中用到。

使用方式：

```go
import "github.com/gogf/gf/v2/os/gstructs"
```

接口文档：

[https://pkg.go.dev/github.com/gogf/gf/v2/os/gstructs](https://pkg.go.dev/github.com/gogf/gf/v2/os/gstructs)

## 常用方法

### `Fields`

- 说明：`Fields ` 将输入参数 `in` 的 `Pointer ` 属性的字段以 `Field` 切片的形式返回。

- 格式：

```go
Fields(in FieldsInput) ([]Field, error)
```

- 示例：

```go
func main() {
      type User struct {
          Id   int
          Name string `params:"name"`
          Pass string `my-tag1:"pass1" my-tag2:"pass2" params:"pass"`
      }
      var user *User
      fields, _ := gstructs.Fields(gstructs.FieldsInput{
          Pointer:         user,
          RecursiveOption: 0,
      })

      g.Dump(fields)
}

// Output:
[
      {
          Value:    "<int Value>",
          Field:    {
              Name:      "Id",
              PkgPath:   "",
              Type:      "int",
              Tag:       "",
              Offset:    0,
              Index:     [
                  0,
              ],
              Anonymous: false,
          },
          TagValue: "",
      },
      {
          Value:    {},
          Field:    {
              Name:      "Name",
              PkgPath:   "",
              Type:      "string",
              Tag:       "params:\"name\"",
              Offset:    8,
              Index:     [
                  1,
              ],
              Anonymous: false,
          },
          TagValue: "",
      },
      {
          Value:    {},
          Field:    {
              Name:      "Pass",
              PkgPath:   "",
              Type:      "string",
              Tag:       "my-tag1:\"pass1\" my-tag2:\"pass2\" params:\"pass\"",
              Offset:    24,
              Index:     [
                  2,
              ],
              Anonymous: false,
          },
          TagValue: "",
      },
]
```

### `TagMapName`

- 说明：`TagMapName` 从参数 `pointer` 中检索 `tag`，并以 `map[string]string` 的形式返回。

- 注意：
  - 参数 `pointer` 的类型应该是 `struct/*struct`。
  - 只会返回可导出的字段(首字母大写的字段)。
- 格式：

```go
TagMapName(pointer interface{}, priority []string) (map[string]string, error)
```

- 示例：

```go
func main() {
      type User struct {
          Id   int
          Name string `params:"name"`
          Pass string `my-tag1:"pass1" my-tag2:"pass2" params:"pass"`
      }
      var user User
      m, _ := gstructs.TagMapName(user, []string{"params"})

      g.Dump(m)
}

// Output:
{
      "name": "Name",
      "pass": "Pass",
}
```