## 注意事项

由于 `Go` 是不支持热编译特性的，每一次代码变更后都要重新手动停止、编译、运行代码文件。 `run` 命令也不是实现热编译功能，而是提供了自动编译功能，当开发者修改了项目中的 `go` 文件时，该命令将会自动编译当前程序，并停止原有程序，运行新版的程序。
:::tip
`run` 命令会递归监控 **当前运行目录** 的所有 `go` 文件变化来实现自动编译。
:::
## 使用帮助

```text
$ gf run -h
USAGE
    gf run FILE [OPTION]

ARGUMENT
    FILE    building file path.

OPTION
    -p, --path         output directory path for built binary file. it's "./" in default
    -e, --extra        the same options as "go run"/"go build" except some options as follows defined
    -a, --args         custom arguments for your process
    -w, --watchPaths   watch additional paths for live reload, separated by ",". i.e. "manifest/config/*.yaml"
    -h, --help         more information about this command

EXAMPLE
    gf run main.go
    gf run main.go --args "server -p 8080"
    gf run main.go -mod=vendor
    gf run main.go -w "manifest/config/*.yaml"

DESCRIPTION
    The "run" command is used for running go codes with hot-compiled-like feature,
    which compiles and runs the go codes asynchronously when codes change.

```

配置文件格式示例：

```yaml
gfcli:
  run:
    path:  "./bin"
    extra: ""
    args:  "all"
    watchPaths:
    - api/*.go
    - internal/controller/*.go
```

参数介绍：

| 名称 | 默认值 | 含义 | 示例 |
| --- | --- | --- | --- |
| `path` | `./` | 指定编译后生成的二进制文件存放目录。 |  |
| `extra` |  | 指定用于底层 `go build` 的命令参数 |  |
| `args` |  | 指定启动运行二进制文件的命令行参数 |  |
| `watchPath` |  | 指定本地项目文件监听的文件路径格式，支持多个路径使用 `,` 覆盖分隔。该参数的格式同标准库的 `filepath.Match` 方法参数 | `internal/*.go` |

## 使用示例

一般 `gf run main.go` 即可

```text
$ gf run main.go --swagger
2020-12-31 00:40:16.948 build: main.go
2020-12-31 00:40:16.994 producing swagger files...
2020-12-31 00:40:17.145 done!
2020-12-31 00:40:17.216 gf pack swagger packed/swagger.go -n packed -y
2020-12-31 00:40:17.279 done!
2020-12-31 00:40:17.282 go build -o bin/main  main.go
2020-12-31 00:40:18.696 go file changes: "/Users/john/Workspace/Go/GOPATH/src/github.com/gogf/gf-demos/packed/swagger.go": WRITE
2020-12-31 00:40:18.696 build: main.go
2020-12-31 00:40:18.775 producing swagger files...
2020-12-31 00:40:18.911 done!
2020-12-31 00:40:19.045 gf pack swagger packed/swagger.go -n packed -y
2020-12-31 00:40:19.136 done!
2020-12-31 00:40:19.144 go build -o bin/main  main.go
2020-12-31 00:40:21.367 bin/main
2020-12-31 00:40:21.372 build running pid: 40954
2020-12-31 00:40:21.437 [DEBU] [ghttp] SetServerRoot path: /Users/john/Workspace/Go/GOPATH/src/github.com/gogf/gf-demos/public
2020-12-31 00:40:21.440 40954: http server started listening on [:8199]
...
```

## 常见问题

[too many open files on macOS](https://github.com/fsnotify/fsnotify/issues/129)