## SameSite 介绍

### 参考文档

[https://web.dev/samesite-cookies-explained/](https://web.dev/samesite-cookies-explained/)

[https://web.dev/samesite-cookie-recipes/](https://web.dev/samesite-cookie-recipes/)

[https://web.dev/schemeful-samesite/](https://web.dev/schemeful-samesite/)

### chrome89开始协议不同也属于跨站请求

[https://www.chromestatus.com/feature/5096179480133632](https://www.chromestatus.com/feature/5096179480133632)

## 如何设置？

```go
func main() {
    s := g.Server()
    s.BindHandler("/", func(r *ghttp.Request) {
        r.Cookie.SetHttpCookie(&http.Cookie{
            Name:     "test",
            Value:    "1234",
            Secure:   true,
            SameSite: http.SameSiteNoneMode,// 自定义samesite，配合secure一起使用
        })
    })
    s.SetAddr("127.0.0.1:8080")
    s.Run()
}
```