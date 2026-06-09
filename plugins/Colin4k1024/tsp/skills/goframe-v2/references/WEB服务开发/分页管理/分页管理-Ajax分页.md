`Ajax` 分页与其他分页方式的区别在于，分页链接会使用 `Javascript` 方法来实现，该 `Javascript` 方法是分页方法，参数固定为该分页对应的分页 `URL` 地址。该 `Javascript` 方法通过 `Ajax` 获取到 `URL` 连接对应的分页内容后渲染到页面。

完整示例如下：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/os/gview"
)

func main() {
    s := g.Server()
    s.BindHandler("/page/ajax", func(r *ghttp.Request) {
        page := r.GetPage(100, 10)
        page.AjaxActionName = "DoAjax"
        buffer, _ := gview.ParseContent(`
        <html>
            <head>
                <style>
                    a,span {padding:8px; font-size:16px;}
                    div{margin:5px 5px 20px 5px}
                </style>
                <script src="https://cdn.bootcss.com/jquery/2.0.3/jquery.min.js"></script>
                <script>
                function DoAjax(url) {
                     $.get(url, function(data,status) {
                         $("body").html(data);
                     });
                }
                </script>
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

在该示例中，我们定义了一个 `DoAjax(url)` 方法用来执行分页操作，为演示需要它逻辑很简单，会加载指定分页页面的内容并覆盖掉当前页面的分页内容。

```
function DoAjax(url) {
     $.get(url, function(data,status) {
         $("body").html(data);
     });
}
```