默认情况下，模板引擎对所有的变量输出并没有使用 `HTML` 转码处理，也就是说，如果开发者处理不好，可能会存在XSS漏洞。

不用担心， `GoFrame` 框架当然已经充分考虑到这点，并且为开发者提供了比较灵活的配置参数来控制是否默认转义变量输出的 `HTML` 内容。该特性可以通过 `AutoEncode` 配置项，或者 `SetAutoEncode` 方法来开启/关闭。
:::tip
需要注意的是，该特性并不会影响 `include` 模板的内置函数。
:::
使用示例：

1、配置文件

```toml
[viewer]
    delimiters  =  ["${", "}"]
    autoencode  =  true
```

2、示例代码

```go
package main

import (
    "context"
    "fmt"
    "github.com/gogf/gf/v2/frame/g"
)

func main() {
    result, _ := g.View().ParseContent(context.TODO(), "姓名: ${.name}", g.Map{
        "name": "<script>alert('john');</script>",
    })
    fmt.Println(result)
}
```

3、执行输出

```html
姓名: &lt;script&gt;alert(&#39;john&#39;);&lt;/script&gt;
```