`Struct`校验常使用以下链式操作方式：

```go
g.Validator().Data(object).Run(ctx)
```

## 校验 `tag` 规则介绍

在开始介绍 `Struct` 参数类型校验之前，我们来介绍一下常用的校验 `tag` 规则。规则如下：

```
[属性别名@]校验规则[#错误提示]
```

其中：

- `属性别名` 和 `错误提示` 为 **非必需字段**， `校验规则` 是 **必需字段。**
- `属性别名` 非必需字段，指定在校验中使用的对应 `struct` 属性的别名，同时校验后返回的 `error` 对象中的也将使用该别名返回。例如在处理请求表单时比较有用，因为表单的字段名称往往和 `struct` 的属性名称不一致。大部分场景下不需要设置属性别名，默认直接使用属性名称即可。
- `校验规则` 则为当前属性的校验规则，多个校验规则请使用 `|` 符号组合，例如： `required|between:1,100`。
- `错误提示` 非必需字段，表示自定义的错误提示信息，当规则校验时对默认的错误提示信息进行覆盖。

## 校验 `tag` 使用示例

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

type User struct {
    Uid   int    `v:"uid      @integer|min:1#|请输入用户ID"`
    Name  string `v:"name     @required|length:6,30#请输入用户名称|用户名称长度非法"`
    Pass1 string `v:"password1@required|password3"`
    Pass2 string `v:"password2@required|password3|same:Pass1#|密码格式不合法|两次密码不一致，请重新输入"`
}

func main() {
    var (
        ctx  = gctx.New()
        user = &User{
            Name:  "john",
            Pass1: "Abc123!@#",
            Pass2: "123",
        }
    )

    err := g.Validator().Data(user).Run(ctx)
    if err != nil {
        g.Dump(err.Items())
    }
}
```

可以看到，我们可以对在 `struct` 定义时使用了 `gvalid` 的 `gvalid tag` 来绑定校验的规则及错误提示信息。在此示例代码中， `same:password1` 规则同使用 `same:Pass1` 规则是一样的效果。 **也就是说，在数据校验中，可以同时使用原有的 `struct` 属性名称，也可以使用别名。但是，返回的结果中只会使用别名返回，这也是别名最大的用途。** 此外，在对 `struct` 对象进行校验时，也可以传递校验或者和错误提示参数，这个时候会覆盖 `struct` 在定义时绑定的对应参数。

以上示例执行后，输出结果为：

```
[
    {
        "uid": {
            "min": "请输入用户ID",
        },
    },
    {
        "name": {
            "length": "用户名称长度非法",
        },
    },
    {
        "password2": {
            "password3": "密码格式不合法",
        },
    },
]
```

## 使用 `map` 指定校验规则

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    type User struct {
        Age  int
        Name string
    }
    var (
        ctx   = gctx.New()
        user  = User{Name: "john"}
        rules = map[string]string{
            "Name": "required|length:6,16",
            "Age":  "between:18,30",
        }
        messages = map[string]interface{}{
            "Name": map[string]string{
                "required": "名称不能为空",
                "length":   "名称长度为{min}到{max}个字符",
            },
            "Age": "年龄为18到30周岁",
        }
    )

    err := g.Validator().Rules(rules).Messages(messages).Data(user).Run(ctx)
    if err != nil {
        g.Dump(err.Maps())
    }
}
```

在以上示例中， `Age` 属性由于默认值 `0` 的存在，因此会引起 `required` 规则的失效，因此这里没有使用 `required` 规则而是使用 `between` 规则来进行校验。示例代码执行后，终端输出：

```
{
    "Age": {
        "between": "年龄为18到30周岁"
    },
    "Name": {
        "length": "名称长度为6到16个字符"
    }
}
```

## 结构体递归校验（嵌套校验）

支持递归的结构体校验（嵌套校验），即如果属性也是结构体（也支持嵌套结构体（ `embedded`）），那么将会自动将该属性执行递归校验。使用示例：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    type Pass struct {
        Pass1 string `v:"password1@required|same:password2#请输入您的密码|您两次输入的密码不一致"`
        Pass2 string `v:"password2@required|same:password1#请再次输入您的密码|您两次输入的密码不一致"`
    }
    type User struct {
        Pass
        Id   int
        Name string `valid:"name@required#请输入您的姓名"`
    }
    var (
        ctx  = gctx.New()
        user = &User{
            Name: "john",
            Pass: Pass{
                Pass1: "1",
                Pass2: "2",
            },
        }
    )
    err := g.Validator().Data(user).Run(ctx)
    g.Dump(err.Maps())
}
```

或者属性为嵌套结构体（ `embedded`）的场景：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    type Pass struct {
        Pass1 string `v:"password1@required|same:password2#请输入您的密码|您两次输入的密码不一致"`
        Pass2 string `v:"password2@required|same:password1#请再次输入您的密码|您两次输入的密码不一致"`
    }
    type User struct {
        Id   int
        Name string `valid:"name@required#请输入您的姓名"`
        Pass Pass
    }
    var (
        ctx  = gctx.New()
        user = &User{
            Name: "john",
            Pass: Pass{
                Pass1: "1",
                Pass2: "2",
            },
        }
    )
    err := g.Validator().Data(user).Run(ctx)
    g.Dump(err.Maps())
}
```

执行后，终端输出：

```
{
    "password1": {
        "same": "您两次输入的密码不一致",
    },
    "password2": {
        "same": "您两次输入的密码不一致",
    },
}
```

更多递归校验的介绍，请参考章节： [数据校验-递归校验](../../数据校验-递归校验.md)