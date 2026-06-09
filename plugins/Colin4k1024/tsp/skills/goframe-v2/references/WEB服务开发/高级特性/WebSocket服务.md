使用 `goframe` 框架进行 `websocket` 开发相当简单。我们以下通过实现一个简单的 `echo服务器` 来演示 `goframe` 框架的 `websocket` 的使用（客户端使用`HTML5`实现）。

示例代码：[Websocket Example](/examples/httpserver/websocket)

## HTML5客户端

先上 `H5` 客户端的代码

```html
<!DOCTYPE html>
<html lang="zh">
    <head>
        <title>goframe websocket echo server</title>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
        <link rel="stylesheet" href="//cdn.bootcss.com/bootstrap/3.3.5/css/bootstrap.min.css">
        <script src="//cdn.bootcss.com/jquery/1.11.3/jquery.min.js"></script>
    </head>
    <body>
        <div class="container">
            <div class="list-group" id="divShow"></div>
            <div>
                <div><input class="form-control" id="txtContent" autofocus placeholder="Content to send.."></div>
                <div><button class="btn btn-primary" id="btnSend" style="margin-top:15px">Send</button></div>
            </div>
        </div>
    </body>
</html>

<script type="application/javascript">
    function showInfo(content) {
        $("<div class=\"list-group-item list-group-item-info\">" + content + "</div>").appendTo("#divShow")
    }
    function showWaring(content) {
        $("<div class=\"list-group-item list-group-item-warning\">" + content + "</div>").appendTo("#divShow")
    }
    function showSuccess(content) {
        $("<div class=\"list-group-item list-group-item-success\">" + content + "</div>").appendTo("#divShow")
    }
    function showError(content) {
        $("<div class=\"list-group-item list-group-item-danger\">" + content + "</div>").appendTo("#divShow")
    }

    $(function () {
        const url = "ws://127.0.0.1:8000/ws";
        let ws  = new WebSocket(url);
        try {
            // ws connection succeeded
            ws.onopen = function () {
                showInfo("WebSocket Server [" + url +"] Connection Succeeded!");
            };
            // ws connection closed
            ws.onclose = function () {
                if (ws) {
                    ws.close();
                    ws = null;
                }
                showError("WebSocket Server [" + url +"] Connection Closed!");
            };
            // ws connection error
            ws.onerror = function () {
                if (ws) {
                    ws.close();
                    ws = null;
                }
                showError("WebSocket Server [" + url +"] Connection Error!");
            };
            // ws response message.
            ws.onmessage = function (result) {
                showWaring(" > " + result.data);
            };
        } catch (e) {
            alert(e.message);
        }

        // click to send message
        $("#btnSend").on("click", function () {
            if (ws == null) {
                showError("WebSocket Server [" + url +"] Connection Failed, Please Refresh Page!");
                return;
            }
            const content = $.trim($("#txtContent").val()).replace("/[\n]/g", "");
            if (content.length <= 0) {
                alert("Please input any content to send!");
                return;
            }
            $("#txtContent").val("")
            showSuccess(content);
            ws.send(content);
        });

        // enter to send message
        $("#txtContent").on("keydown", function (event) {
            if (event.keyCode === 13) {
                $("#btnSend").trigger("click");
            }
        });
    })
</script>
```

注意我们这里的服务端连接地址为： `ws://127.0.0.1:8199/ws`。

客户端的功能很简单，主要实现了这几个功能：

- 与服务端 `websocket` 连接状态保持及信息展示；
- 界面输入内容并发送信息到 `websocket` 服务端；
- 接收到 `websocket` 的返回信息后回显在界面上；

## WebSocket服务端

```go
package main

import (
    "net/http"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gorilla/websocket"
)

func main() {
    var (
        s          = g.Server()
        logger     = g.Log()
        wsUpGrader = websocket.Upgrader{
            // CheckOrigin allows any origin in development
            // In production, implement proper origin checking for security
            CheckOrigin: func(r *http.Request) bool {
                return true
            },
            // Error handler for upgrade failures
            Error: func(w http.ResponseWriter, r *http.Request, status int, reason error) {
                // Implement error handling logic here
            },
        }
    )

    // Bind WebSocket handler to /ws endpoint
    s.BindHandler("/ws", func(r *ghttp.Request) {
        // Upgrade HTTP connection to WebSocket
        ws, err := wsUpGrader.Upgrade(r.Response.Writer, r.Request, nil)
        if err != nil {
            r.Response.Write(err.Error())
            return
        }
        defer ws.Close()

        // Get request context for logging
        var ctx = r.Context()

        // Message handling loop
        for {
            // Read incoming WebSocket message
            msgType, msg, err := ws.ReadMessage()
            if err != nil {
                break // Connection closed or error occurred
            }
            // Log received message
            logger.Infof(ctx, "received message: %s", msg)
            // Echo the message back to client
            if err = ws.WriteMessage(msgType, msg); err != nil {
                break // Error writing message
            }
        }
        // Log connection closure
        logger.Info(ctx, "websocket connection closed")
    })

    // Configure static file serving
    s.SetServerRoot("static")
    // Set server port
    s.SetPort(8000)
    // Start the server
    s.Run()
}
```

可以看到，服务端的代码相当简单，这里需要着重说明的是这几个地方：

1. **WebSocket方法**

    `websocket` 服务端的路由注册方式和普通的 `http` 回调函数注册方式一样，但是在接口处理中我们需要通过 `ghttp.Request.WebSocket` 方法（这里直接使用指针对象 `r.WebSocket()`）将请求转换为 `websocket` 操作，并返回一个 `WebSocket对象`，该对象用于后续的 `websocket` 通信操作。当然，如果客户端请求并非为 `websocket` 操作时，转换将会失败，该方法会返回错误信息，使用时请注意判断方法的 `error` 返回值。

1. **ReadMessage & WriteMessage**

    读取消息以及写入消息对应的是 `websocket` 的数据读取以及写入操作( `ReadMessage & WriteMessage`)，需要注意的是这两个方法都有一个 `msgType` 的变量，表示请求读取及写入数据的类型，常见的两种数据类型为：字符串数据或者二进制数据。在使用过程中，由于接口双方都会约定统一的数据格式，因此读取和写入的 `msgType` 几乎都是一致的，所以在本示例中的返回消息时，数据类型参数直接使用的是读取到的 `msgType`。

## HTTPS的WebSocket

如果需要支持 `HTTPS` 的 `WebSocket` 服务，只需要依赖的 `WebServer` 支持 `HTTPS` 即可，访问的 `WebSocket` 地址需要使用 `wss://` 协议访问。以上客户端 `HTML5` 页面中的 `WebSocket` 访问地址需要修改为： `wss://127.0.0.1:8199/ws`。服务端示例代码：

```go
package main

import (
    "net/http"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gorilla/websocket"
)

func main() {
    var (
        s          = g.Server()
        logger     = g.Log()
        wsUpGrader = websocket.Upgrader{
            CheckOrigin: func(r *http.Request) bool {
                // In production, you should implement proper origin checking
                return true
            },
            Error: func(w http.ResponseWriter, r *http.Request, status int, reason error) {
                // Error callback function.
            },
        }
    )

    s.BindHandler("/ws", func(r *ghttp.Request) {
        ws, err := wsUpGrader.Upgrade(r.Response.Writer, r.Request, nil)
        if err != nil {
            r.Response.Write(err.Error())
            return
        }
        defer ws.Close()

        var ctx = r.Context()
        for {
            msgType, msg, err := ws.ReadMessage()
            if err != nil {
                break
            }
            logger.Infof(ctx, "received message: %s", msg)
            if err = ws.WriteMessage(msgType, msg); err != nil {
                break
            }
        }
        logger.Info(ctx, "websocket connection closed")
    })
    s.EnableHTTPS("certs/server.crt", "certs/server.key")
    s.SetServerRoot("static")
    s.SetPort(8000)
    s.Run()
}
```

## 示例结果展示

我们首先执行示例代码 `main.go`，随后访问页面 [http://127.0.0.1:8199/](http://127.0.0.1:8199/)，随意输入请求内容并提交，随后在服务端关闭程序。可以看到，页面会回显提交的内容信息，并且即时展示 `websocket` 的连接状态的改变，当服务端关闭时，客户端也会即时地打印出关闭信息。

## Websocket安全校验

`GoFrame` 框架的 `websocket` 模块并不会做同源检查( `origin`)，也就是说，这种条件下的`websocket`允许完全跨域。

安全的校验需要由业务层来处理，安全校验主要包含以下几个方面：

1. `origin` 的校验: 业务层在执行 `r.WebSocket()` 之前需要进行 `origin` 同源请求的校验；或者按照自定义的处理对请求进行校验(如果请求提交参数)；如果未通过校验，那么调用 `r.Exit()` 终止请求。
2. `websocket` 通信数据校验: 数据通信往往都有一些自定义的数据结构，在这些通信数据中加上鉴权处理逻辑；

## WebSocket Client 客户端

```go
package main

import (
    "context"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gorilla/websocket"
)

func main() {
    var (
        ctx    = context.Background()
        logger = g.Log()
    )

    // Connect to WebSocket server using default dialer
    ws, _, err := websocket.DefaultDialer.Dial("ws://127.0.0.1:8000/ws", nil)
    if err != nil {
        logger.Fatalf(ctx, "dial failed: %+v", err)
    }
    // Ensure connection is closed when function returns
    defer ws.Close()

    // Send a test message to the server
    err = ws.WriteMessage(websocket.TextMessage, []byte("hello"))
    if err != nil {
        logger.Fatalf(ctx, "ws.WriteMessage failed: %+v", err)
    }

    // Read the server's response
    _, msg, err := ws.ReadMessage()
    if err != nil {
        logger.Fatalf(ctx, "ws.ReadMessage failed: %+v", err)
        return
    }

    logger.Infof(ctx, `received message: %s`, msg)

    // Cleanly close the connection by sending a close message
    // This is important for proper connection cleanup
    err = ws.WriteMessage(websocket.CloseMessage, []byte("going to close"))
    if err != nil {
        logger.Fatalf(ctx, "ws.WriteMessage failed: %+v", err)
    }
}
```