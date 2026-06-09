## 示例1，提交 `Json` 请求

```go
g.Client().ContentJson().PostContent(ctx, "http://order.svc/v1/order", g.Map{
    "uid"         : 1,
    "sku_id"      : 10000,
    "amount"      : 19.99,
    "create_time" : "2020-03-26 12:00:00",
})
```

通过调用 `ContentJson` 链式操作方法，该请求将会将 `Content-Type` 设置为 `application/json`，并且将提交参数自动编码为 `Json`:

```
{"uid":1,"sku_id":10000,"amount":19.99,"create_time":"2020-03-26 12:00:00"}
```

## 示例2，提交 `Xml` 请求

```go
g.Client().ContentXml().PostContent(ctx, "http://order.svc/v1/order", g.Map{
    "uid"         : 1,
    "sku_id"      : 10000,
    "amount"      : 19.99,
    "create_time" : "2020-03-26 12:00:00",
})
```

通过调用 `ContentXml` 链式操作方法，该请求将会将 `Content-Type` 设置为 `application/xml`，并且将提交参数自动编码为 `Xml`:

```
<doc><amount>19.99</amount><create_time>2020-03-26 12:00:00</create_time><sku_id>10000</sku_id><uid>1</uid></doc>
```

## 示例3，自定义 `ContentType`

我们可以通过 `ContentType` 方法自定义客户端请求的 `ContentType`。如果是给定的 `string/[]byte` 参数，客户端将会直接将参数提交给服务端；如果是其他数据类型将会自动对参数执行 `url encode` 再提交到服务端。

示例1：

```go
g.Client().ContentType("application/json").PostContent(
  ctx,
  "http://order.svc/v1/order",
  `{"uid":1,"sku_id":10000,"amount":19.99,"create_time":"2020-03-26 12:00:00"}`,
)
```

或

```go
g.Client().ContentType("application/json; charset=utf-8").PostContent(
  ctx,
  "http://order.svc/v1/order",
  `{"uid":1,"sku_id":10000,"amount":19.99,"create_time":"2020-03-26 12:00:00"}`,
)
```

提交的参数如下：

```
{"uid":1,"sku_id":10000,"amount":19.99,"create_time":"2020-03-26 12:00:00"}
```

示例2：

```go
g.Client().ContentType("application/x-www-form-urlencoded; charset=utf-8").GetContent(
  ctx,
  "http://order.svc/v1/order",
  g.Map{
    "category" : 1,
    "sku_id"   : 10000,
  },
)
```

提交的参数如下：

```
category=1&sku_id=10000
```