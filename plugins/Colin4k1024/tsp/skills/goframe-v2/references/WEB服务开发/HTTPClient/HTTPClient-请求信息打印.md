## 基本介绍

`http` 客户端支持对HTTP请求的输入与输出原始信息获取与打印，方便调试，相关方法如下：

```go
func (r *Response) Raw() string
func (r *Response) RawDump()
func (r *Response) RawRequest() string
func (r *Response) RawResponse() string
```

可以看到，所有的方法均绑定在 `Response` 对象上，也就是说必须要请求结束后才能打印。

## 使用示例

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    response, err := g.Client().Post(
        gctx.New(),
        "https://goframe.org",
        g.Map{
            "name": "john",
        },
    )
    if err != nil {
        panic(err)
    }
    response.RawDump()
}
```

执行后，终端输出为：

```
+---------------------------------------------+
|                   REQUEST                   |
+---------------------------------------------+
POST / HTTP/1.1
Host: goframe.org
User-Agent: GoFrameHTTPClient v2.0.0-beta
Content-Length: 9
Content-Type: application/x-www-form-urlencoded
Accept-Encoding: gzip

name=john

+---------------------------------------------+
|                   RESPONSE                  |
+---------------------------------------------+
HTTP/1.1 405 Method Not Allowed
Connection: close
Transfer-Encoding: chunked
Allow: GET
Cache-Control: no-store
Content-Security-Policy: frame-ancestors 'self'
Content-Type: text/html;charset=UTF-8
Date: Fri, 03 Dec 2021 09:43:29 GMT
Expires: Thu, 01 Jan 1970 00:00:00 GMT
Server: nginx
...
```