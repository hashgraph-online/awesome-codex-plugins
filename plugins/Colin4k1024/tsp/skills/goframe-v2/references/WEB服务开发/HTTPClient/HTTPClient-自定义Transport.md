由于 `gclient.Client` 内部封装扩展于标准库的 `http.Client` 对象，因此标准库 `http.Client` 有的特性， `gclient.Client` 也是支持的。我们这里提到的例子是 `Transport` 使用。来看几个示例：

## 使用 `Unix Socket`

客户端和服务端使用 `Unix Socket` 通信，使用 `Transport` 来实现。以下代码为真实项目代码摘选，无法独立运行，仅做参考。

```go
func (*Guardian) ConvertContainerPathToHostPath(
    ctx context.Context, namespace, podName, containerName, containerPath string,
) (string, error) {
    var (
        client = g.Client()
        url    = "http://localhost/api/v1/pod/path"
        req    = webservice.HostPathInfoReq{
            Namespace:     namespace,
            PodName:       podName,
            ContainerName: containerName,
            ContainerPath: containerPath,
        }
        res *webservice.HostPathInfoRes
    )
    client.Transport = &http.Transport{
        DialContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
            return net.Dial("unix", serviceSocketPath)
        },
    }
    err := client.ContentJson().GetVar(ctx, url, req).Scan(&res)
    if err != nil {
        return "", gerror.Wrapf(
            err,
            `request guardian failed for url: %s, req: %s`,
            url, gjson.MustEncodeString(req),
        )
    }
    if res == nil {
        return "", gerror.Newf(
            `nil response from guardian request url: %s, req: %s`,
            url, gjson.MustEncodeString(req),
        )
    }
    return res.HostPath, nil
}
```

## 设置客户端连接池大小参数

```go
func ExampleNew_MultiConn_Recommend() {
    var (
        ctx    = gctx.New()
        client = g.Client()
    )

    // controls the maximum idle(keep-alive) connections to keep per-host
    client.Transport.(*http.Transport).MaxIdleConnsPerHost = 5

    for i := 0; i < 5; i++ {
        go func() {
            if r, err := client.Get(ctx, "http://127.0.0.1:8999/var/json"); err != nil {
                panic(err)
            } else {
                fmt.Println(r.ReadAllString())
                r.Close()
            }
        }()
    }

    time.Sleep(time.Second * 1)

    // Output:
    //{"id":1,"name":"john"}
    //{"id":1,"name":"john"}
    //{"id":1,"name":"john"}
    //{"id":1,"name":"john"}
    //{"id":1,"name":"john"}
}
```