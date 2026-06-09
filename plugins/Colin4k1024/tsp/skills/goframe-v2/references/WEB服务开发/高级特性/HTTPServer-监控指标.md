`HTTP Server` 支持监控指标能力，默认是关闭的不影响性能，只有在 `metric` 特性全局开启时该组件才会默认开启监控指标计算和生成功能。

## 指标列表

| **指标名称** | **指标类型** | **指标单位** | **指标描述** |
| --- | --- | --- | --- |
| `http.server.request.duration` | `Histogram` | `ms` | 对 `Server` 端请求执行的时间开销分组。 |
| `http.server.request.duration_total` | `Counter` | `ms` | 每个请求的执行时间总开销。 |
| `http.server.request.total` | `Counter` |  | 已经执行完毕的请求总数，不包含正在执行的请求数。 |
| `http.server.request.active` | `Gauge` |  | 当前正在处理的请求数量。 |
| `http.server.request.body_size` | `Counter` | `bytes` | 请求的字节总大小。 |
| `http.server.response.body_size` | `Counter` | `bytes` | 返回的字节总大小。 |

## 属性列表

| **Label名称** | **Label描述** | **Label示例** |
| --- | --- | --- |
| `server.address` | 接受请求的请求地址。来源于 `Request.Host`，可能是域名也可能是IP地址。 | `goframe.org`<br />`10.0.1.132` |
| `server.port` | 接受请求的服务端口。同一服务可能有多个端口地址，当前请求连接的是哪个端口就记录哪个端口。 | `8000` |
| `http.route` | 请求的路由规则。 | `/api/v1/user/:id` |
| `url.schema` | 请求协议名称。 | `http`; `https` |
| `network.protocol.version` | 请求的协议版本。 | `1.0`; `1.1` |
| `http.request.method` | 请求的方法名称。 | `GET`; `POST`; `DELETE` |
| `error.code` | 请求返回的业务自定义错误码，字符串类型以提高兼容性。 | `-1`; `0`; `51` |
| `http.response.status_code` | 处理返回的 `HTTP` 状态码。 | `200` |