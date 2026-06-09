## 默认错误提示

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    var (
        ctx    = gctx.New()
        params = map[string]interface{}{
            "passport":  "",
            "password":  "123456",
            "password2": "1234567",
        }
        rules = map[string]string{
            "passport":  "required|length:6,16",
            "password":  "required|length:6,16|same:password2",
            "password2": "required|length:6,16",
        }
    )
    err := g.Validator().Rules(rules).Data(params).Run(ctx)
    if err != nil {
        g.Dump(err.Maps())
    }
}
```

执行后，终端输出：

```javascript
{
    "passport": {
        "required": "The passport field is required",
        "length":   "The passport value `` length must be between 6 and 16",
    },
    "password": {
        "same": "The password value `123456` must be the same as field password2",
    },
}
```

## 自定义错误提示

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    var (
        ctx    = gctx.New()
        params = map[string]interface{}{
            "passport":  "",
            "password":  "123456",
            "password2": "1234567",
        }
        rules = map[string]string{
            "passport":  "required|length:6,16",
            "password":  "required|length:6,16|same:password2",
            "password2": "required|length:6,16",
        }
        messages = map[string]interface{}{
            "passport": "账号不能为空|账号长度应当在{min}到{max}之间",
            "password": map[string]string{
                "required": "密码不能为空",
                "same":     "两次密码输入不相等",
            },
        }
    )

    err := g.Validator().Messages(messages).Rules(rules).Data(params).Run(ctx)
    if err != nil {
        g.Dump(err.Maps())
    }
}
```

该示例同时也展示了`messages`自定义错误信息传递的两种数据类型，`string`或者`map[string]string`。其中`map[string]string`类型参数需要指定对应字段、对应规则的错误提示信息，是一个二维的“关联数组”。该示例执行后，终端输出：

```javascript
{
    "passport": {
            "length": "账号长度应当在6到16之间",
            "required": "账号不能为空"
    },
    "password": {
            "same": "两次密码输入不相等"
    }
}
```