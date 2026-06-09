:::tip
该功能特性从 `v2.4` 版本开始提供。
:::
## 基本介绍

该命令用于编译 `proto` 文件，生成对应的 `protobuf go` 文件以及对应的控制器文件。

## 命令使用

```text
$ gf gen pb -h
USAGE
    gf gen pb [OPTION]

OPTION
    -p, --path   protobuf file folder path
    -a, --api    output folder path storing generated go files of api
    -c, --ctrl   output folder path storing generated go files of controller
    -h, --help   more information about this command

EXAMPLE
    gf gen pb
    gf gen pb -p . -a . -p .
```
:::tip
如果使用框架推荐的项目工程脚手架，并且系统安装了 `make` 工具，也可以使用 `make pb` 快捷指令。
:::
参数说明：

| 名称 | 必须 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `path` | 否 | `manifest/protobuf` | 指向 `proto` 协议定义文件 |
| `api` | 否 | `api` | 指向生成的接口文件存放目录 |
| `ctrl` | 否 | `internal/controller` | 指向生成的控制器文件存放目录 |

## 注意事项

- 在生成控制器文件时，会自动识别是否已经存在对应的接口实现方法，如果已经存在则不再重复生成对应的接口方法，防止覆盖。
- 如果在 `proto` 目录执行该命令，并且指定的 `path` 目录不存在时，那么将会自动编译本地 `proto` 文件，且编译后的文件生成到当前目录，并自动关闭控制器文件的生成功能。