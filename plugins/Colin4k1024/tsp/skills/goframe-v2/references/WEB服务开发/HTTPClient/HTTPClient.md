## 基本介绍

`GoFrame` 框架提供了强大便捷易用的 `HTTP` 客户端，由 `gclient` 组件实现，对象创建可以通过 `gclient.New()` 包方法，也可以通过 `g.Client()` 方法调用。推荐使用 `g.Client()` 来便捷地创建 `HTTP` 客户端对象。由于 `gclient.Client` 内部封装扩展于标准库的 `http.Client` 对象，因此标准库 `http.Client` 有的特性， `gclient.Client` 也是支持的。

**方法列表**：[https://pkg.go.dev/github.com/gogf/gf/v2/net/gclient](https://pkg.go.dev/github.com/gogf/gf/v2/net/gclient)

**简要说明**：

1. 我们可以使用 `New` 创建一个自定义的HTTP客户端对象 `Client`，随后可以使用该对象执行请求，该对象底层使用了连接池设计，因此没有 `Close` 关闭方法。 `HTTP` 客户端对象也可以通过 `g.Client()` 快捷方法创建。
2. 客户端提供了一系列以 `HTTP Method` 命名的方法，调用这些方法将会发起对应的 `HTTP Method` 请求。常用的方法是 `Get` 和 `Post` 方法，同时 `DoRequest` 是核心的请求方法，用户可以调用该方法实现自定义的 `HTTP Method` 发送请求。
3. 请求返回结果为 `*ClientResponse` 对象，可以通过该结果对象获取对应的返回结果，通过 `ReadAll`/ `ReadAllString` 方法可以获得返回的内容，该对象在使用完毕后需要通过 `Close` 方法关闭，防止内存溢出。
4. `*Bytes` 方法用于获得服务端返回的二进制数据，如果请求失败返回 `nil`； `*Content` 方法用于请求获得字符串结果数据，如果请求失败返回空字符串； `Set*` 方法用于 `Client` 的参数设置。
5. `*Var` 方法直接请求并获取HTTP接口结果为泛型类型便于转换。如果请求失败或者请求结果为空，会返回一个空的 `g.Var` 泛型对象，不影响转换方法调用。
6. 可以看到，客户端的请求参数的数据参数 `data` 数据类型为 `interface{}` 类型，也就是说可以传递任意的数据类型，常见的参数数据类型为 `string`/ `map`，如果参数为 `map` 类型，参数值将会被自动 `urlencode` 编码。

:::warning
请使用给定的方法创建 `Client` 对象，而不要使用 `new(ghttp.Client)` 或者 `&ghttp.Client{}` 创建客户端对象，否则，哼哼。
:::
## 链式操作

`GoFrame` 框架的客户端支持便捷的链式操作，常用方法如下（文档方法列表可能滞后于源码，建议查看接口文档或源码 [https://pkg.go.dev/github.com/gogf/gf/v2/net/gclient](https://pkg.go.dev/github.com/gogf/gf/v2/net/gclient)）：

```go
func (c *Client) Timeout(t time.Duration) *Client
func (c *Client) Cookie(m map[string]string) *Client
func (c *Client) Header(m map[string]string) *Client
func (c *Client) HeaderRaw(headers string) *Client
func (c *Client) ContentType(contentType string) *Client
func (c *Client) ContentJson() *Client
func (c *Client) ContentXml() *Client
func (c *Client) BasicAuth(user, pass string) *Client
func (c *Client) Retry(retryCount int, retryInterval time.Duration) *Client
func (c *Client) Prefix(prefix string) *Client
func (c *Client) Proxy(proxyURL string) *Client
func (c *Client) RedirectLimit(redirectLimit int) *Client
func (c *Client) Dump(dump ...bool) *Client
func (c *Client) Use(handlers ...HandlerFunc) *Client
```

简要说明：

1. `Timeout` 方法用于设置当前请求超时时间。
2. `Cookie` 方法用于设置当前请求的自定义 `Cookie` 信息。
3. `Header*` 方法用于设置当前请求的自定义 `Header` 信息。
4. `Content*` 方法用于设置当前请求的 `Content-Type` 信息，并且支持根据该信息自动检查提交参数并自动编码。
5. `BasicAuth` 方法用于设置 `HTTP Basic Auth` 校验信息。
6. `Retry` 方法用于设置请求失败时重连次数和重连间隔。
7. `Proxy` 方法用于设置http访问代理。
8. `RedirectLimit` 方法用于限制重定向跳转次数。

## 返回对象

`gclient.Response` 为HTTP对应请求的返回结果对象，该对象继承于 `http.Response`，可以使用 `http.Response` 的所有方法。在此基础之上增加了以下几个方法：

```go
func (r *Response) GetCookie(key string) string
func (r *Response) GetCookieMap() map[string]string
func (r *Response) Raw() string
func (r *Response) RawDump()
func (r *Response) RawRequest() string
func (r *Response) RawResponse() string
func (r *Response) ReadAll() []byte
func (r *Response) ReadAllString() string
func (r *Response) Close() error
```

这里也要提醒的是， `Response` 需要手动调用 `Close` 方法关闭，也就是说，不管你使用不使用返回的 `Response` 对象，你都需要将该返回对象赋值给一个变量，并且手动调用其 `Close` 方法进行关闭（往往使用 `defer r.Close()`），否则会造成文件句柄溢出、内存溢出。

## 重要说明

1. `ghttp` 客户端默认关闭了 `KeepAlive` 功能以及对服务端 `TLS` 证书的校验功能，如果需要启用可自定义客户端的 `Transport` 属性。
2. **连接池参数设定**、 **连接代理设置** 等这些高级功能也可以通过自定义客户端的 `Transport` 属性实现，该数据继承于标准库的 `http.Transport` 对象。

## 相关文档