## 使用方式

`gf build` 命令用于 Go 项目的交叉编译，是 `go build` 的强大封装。

使用 `gf build -h` 查看完整帮助信息。支持为多种操作系统和架构编译可执行文件。

## 内置编译变量

`gf build` 命令在编译时会自动嵌入一组内置变量到二进制文件中，开发者也可以自定义这些变量。运行时可通过 `gbuild` 组件读取这些变量。

默认嵌入的变量包括（可通过 `gf -v` 查看）：

- 当前 `Go` 版本
- 当前 `GoFrame` 版本
- 当前 `Git Commit`（如果存在）
- 当前编译时间

这些信息有助于版本管理和问题追溯。

## 编译配置文件

`gf build` 支持从命令行参数和配置文件两种方式指定编译选项。GoFrame 的配置管理采用统一的配置组件，默认配置文件及使用方法请参考 [配置管理](../核心组件/配置管理/配置管理.md)。

以下是一个配置文件示例：

```yaml
gfcli:
  build:
    name:     "gf"
    arch:     "all"
    system:   "all"
    mod:      "none"
    packSrc:  "resource,manifest"
    version:  "v1.0.0"
    output:   "./bin"
    extra:    ""
```

配置选项与命令行同名参数含义一致。各配置项说明如下：

| 名称 | 默认值 | 含义 | 示例 |
| --- | --- | --- | --- |
| `name` | 与程序入口 `go` 文件同名 | 生成的可执行文件名称。如果是 `windows` 平台，那么默认会加上 `.exe` 后缀 | `gf` |
| `arch` | 当前系统架构 | 编译架构，多个以 `,` 号分隔，如果是 `all` 表示编译所有支持架构 | `386,amd64,arm` [更多](https://golang.google.cn/doc/install/source#environment) |
| `system` | `当前系统平台` | 编译平台，多个以 `,` 号分隔，如果是 `all` 表示编译所有支持平台 | `linux,darwin,windows` [更多](https://golang.google.cn/doc/install/source#environment) |
| `path` | `./bin` | 编译可执行文件存储的 **目录地址** | `./bin` |
| `mod` |  | 同 `go build -mod` 编译选项，不常用 | `none` |
| `cgo` | `false` | 是否开启 `CGO`，默认是关闭的。如果开启，那么交叉编译可能会有问题。 |  |
| `packSrc` |  | 需要打包的目录，多个以 `,` 号分隔，生成到 `internal/packed/build_pack_data.go` | `public,template,manifest` |
| `packDst` | `internal/packed/build_pack_data.go` | 打包后生成的 `Go` 文件路径，一般使用相对路径指定到本项目目录中 |  |
| `version` |  | 程序版本，如果指定版本信息，那么程序生成的路径中会多一层以版本名称的目录 | `v1.0.0` |
| `output` |  | 输出的可执行文件路径，当该参数指定时， `name` 和 `path` 参数失效，常用于编译单个可执行文件。 | `./bin/gf.exe` |
| `extra` |  | 额外自定义的编译参数，会直接传递给 `go build` 命令 |  |
| `varMap` |  | 自定义的内置变量键值对，构建的二进制中可以通过 `gbuild` 包获取编译信息。 | ```<br />gfcli:<br />  build:<br />    name:     "gf"<br />    arch:     "all"<br />    system:   "all"<br />    mod:      "none"<br />    cgo:      0<br />    varMap:<br />      k1: v1<br />      k2: v2<br />``` |
| `exitWhenError` | `false` | 当编译发生错误时，立即停止后续执行，并退出编译流程（使用 `os.Exit(1)`） |  |
| `dumpEnv` | `false` | 每次编译之前在终端打印当前编译环境的环境变量信息 |  |
:::tip
编译时的内置变量可以在运行时通过 `gbuild` 包 [构建信息-gbuild](../组件列表/系统相关/构建信息-gbuild.md) 获取。
:::

## 使用示例

```text
$ gf build
2020-12-31 00:35:25.562 start building...
2020-12-31 00:35:25.562 go build -o ./bin/darwin_amd64/gf main.go
2020-12-31 00:35:28.381 go build -o ./bin/freebsd_386/gf main.go
2020-12-31 00:35:30.650 go build -o ./bin/freebsd_amd64/gf main.go
2020-12-31 00:35:32.957 go build -o ./bin/freebsd_arm/gf main.go
2020-12-31 00:35:35.824 go build -o ./bin/linux_386/gf main.go
2020-12-31 00:35:38.082 go build -o ./bin/linux_amd64/gf main.go
2020-12-31 00:35:41.076 go build -o ./bin/linux_arm/gf main.go
2020-12-31 00:35:44.369 go build -o ./bin/linux_arm64/gf main.go
2020-12-31 00:35:47.352 go build -o ./bin/linux_ppc64/gf main.go
2020-12-31 00:35:50.293 go build -o ./bin/linux_ppc64le/gf main.go
2020-12-31 00:35:53.166 go build -o ./bin/linux_mips/gf main.go
2020-12-31 00:35:55.840 go build -o ./bin/linux_mipsle/gf main.go
2020-12-31 00:35:58.423 go build -o ./bin/linux_mips64/gf main.go
2020-12-31 00:36:01.062 go build -o ./bin/linux_mips64le/gf main.go
2020-12-31 00:36:03.502 go build -o ./bin/netbsd_386/gf main.go
2020-12-31 00:36:06.280 go build -o ./bin/netbsd_amd64/gf main.go
2020-12-31 00:36:09.332 go build -o ./bin/netbsd_arm/gf main.go
2020-12-31 00:36:11.811 go build -o ./bin/openbsd_386/gf main.go
2020-12-31 00:36:14.140 go build -o ./bin/openbsd_amd64/gf main.go
2020-12-31 00:36:17.859 go build -o ./bin/openbsd_arm/gf main.go
2020-12-31 00:36:20.327 go build -o ./bin/windows_386/gf.exe main.go
2020-12-31 00:36:22.994 go build -o ./bin/windows_amd64/gf.exe main.go
2020-12-31 00:36:25.795 done!
```