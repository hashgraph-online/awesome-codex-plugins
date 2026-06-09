:::tip
该命令从框架 `v2.3` 版本开始提供。
:::
## 使用方式

```text
$ gf up -h
USAGE
    gf up [OPTION]

OPTION
    -a, --all    upgrade both version and cli, auto fix codes
    -c, --cli    also upgrade CLI tool
    -f, --fix    auto fix codes(it only make sense if cli is to be upgraded)
    -h, --help   more information about this command

EXAMPLE
    gf up
    gf up -a
    gf up -c
    gf up -cf
```

用以实现版本更新，同时更新主框架版本、社区组件版本到最新版本。

选项说明：

| 名称 | 含义 |
| --- | --- |
| `all` | 同时更新 `cli` 工具版本，并且自动修复本地代码在升级中的不兼容变更 |
| `fix` | 升级时自动修复本地代码在升级中的不兼容变更 |
| `cli` | 升级时同时更新 `cli` 工具版本 |

## 使用示例

```text
$ gf up -a
start upgrading version...
upgrading "github.com/gogf/gf/contrib/drivers/mysql/v2" from "v2.2.4" to "latest"
go: upgraded github.com/BurntSushi/toml v1.1.0 => v1.2.1
go: upgraded github.com/cespare/xxhash/v2 v2.1.2 => v2.2.0
go: upgraded github.com/clbanning/mxj/v2 v2.5.6 => v2.5.7
go: upgraded github.com/fsnotify/fsnotify v1.5.4 => v1.6.0
go: upgraded github.com/go-sql-driver/mysql v1.6.0 => v1.7.0
go: upgraded github.com/gogf/gf/contrib/drivers/mysql/v2 v2.2.4 => v2.2.6
go: upgraded github.com/gogf/gf/v2 v2.2.4 => v2.2.6
go: upgraded github.com/magiconair/properties v1.8.6 => v1.8.7
go: upgraded github.com/mattn/go-colorable v0.1.12 => v0.1.13
go: upgraded github.com/mattn/go-isatty v0.0.14 => v0.0.17
go: upgraded github.com/mattn/go-runewidth v0.0.13 => v0.0.14
go: upgraded github.com/rivo/uniseg v0.2.0 => v0.4.3
go: upgraded go.opentelemetry.io/otel v1.7.0 => v1.11.2
go: upgraded go.opentelemetry.io/otel/sdk v1.7.0 => v1.11.2
go: upgraded golang.org/x/net v0.0.0-20220621193019-9d032be2e588 => v0.5.0
go: upgraded golang.org/x/sys v0.0.0-20220615213510-4f61da869c0c => v0.4.0
go: upgraded golang.org/x/text v0.3.8-0.20220509174342-b4bca84b0361 => v0.6.0
go: upgraded golang.org/x/tools v0.1.11-0.20220504162446-54c7ba520b92 => v0.1.12

upgrading "github.com/gogf/gf/v2" from "v2.2.4" to "latest"

auto fixing path "/Users/john/Workspace/Go/GOPATH/src/github.com/Khaos/eros"...
done!
```

## 注意事项

命令执行前请 `git` 提交本地修改内容或执行目录备份。