`gpage` 支持自定义 `URL` 模板，在模板中可以使用 `{.page}` 内置变量替换页码的内容，我们来看一个简单的示例：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/os/gview"
)

func main() {
    s := g.Server()
    s.BindHandler("/page/template/{page}.html", func(r *ghttp.Request) {
        page := r.GetPage(100, 10)
        page.UrlTemplate = "/order/list/{.page}.html"
        buffer, _ := gview.ParseContent(`
        <html>
            <head>
                <style>
                    a,span {padding:8px; font-size:16px;}
                    div{margin:5px 5px 20px 5px}
                </style>
            </head>
            <body>
                <div>{{.page1}}</div>
                <div>{{.page2}}</div>
                <div>{{.page3}}</div>
                <div>{{.page4}}</div>
            </body>
        </html>
        `, g.Map{
            "page1": page.GetContent(1),
            "page2": page.GetContent(2),
            "page3": page.GetContent(3),
            "page4": page.GetContent(4),
        })
        r.Response.Write(buffer)
    })
    s.SetPort(8199)
    s.Run()
}
```

在代码中，我们可以使用 `UrlTemplate` 属性设置 `URL` 模板，执行后，结果如下：