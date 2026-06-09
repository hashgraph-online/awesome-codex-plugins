## 基本介绍

如果将之前的示例代码多执行几次之后会发现，返回的结果是没有排序的，而且字段及规则输出的先后顺序完全是随机的。即使我们使用`FirstItem`、`FirstString()`等其他方法获取校验结果也是一样，返回的校验结果不固定。那是因为校验的规则我们传递的是`map`类型，而`golang`的`map`类型并不具有有序性，因此校验的结果和规则一样是随机的，同一个校验结果的同一个校验方法多次获取结果值返回的可能也不一样了。

## 顺序校验

我们来改进一下以上的示例：校验结果中如果不满足 `required` 那么返回对应的错误信息，否则才是后续的校验错误信息；也就是说，返回的错误信息应当和我设定规则时的顺序一致。如下：

```go
package main

import (
    "fmt"
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
        rules = []string{
            "passport@required|length:6,16#账号不能为空|账号长度应当在{min}到{max}之间",
            "password@required|length:6,16|same:password2#密码不能为空|密码长度应当在{min}到{max}之间|两次密码输入不相等",
            "password2@required|length:6,16#",
        }
    )
    err := g.Validator().Rules(rules).Data(params).Run(ctx)
    if err != nil {
        fmt.Println(err.Map())
        fmt.Println(err.FirstItem())
        fmt.Println(err.FirstError())
    }
}
```

执行后，终端输出：

```
map[length:账号长度应当在6到16之间 required:账号不能为空]
passport map[length:账号长度应当在6到16之间 required:账号不能为空]
账号不能为空
```

可以看到，我们想要校验结果满足顺序性，只需要将`rules`参数的类型修改为`[]string`，按照一定的规则设定即可，并且`messages`参数既可以定义到`rules`参数中，也可以分开传入（使用第三个参数）。`rules`的中的校验规则编写请参考章节[Struct校验-基本使用](../数据校验-Struct校验/Struct校验-基本使用.md)。