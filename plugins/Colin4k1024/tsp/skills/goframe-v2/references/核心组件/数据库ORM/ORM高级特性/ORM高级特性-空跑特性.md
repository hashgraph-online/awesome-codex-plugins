`ORM` 空跑可以通过 `DryRun` 配置项来启用，默认关闭。当 `ORM` 的空跑特性开启时，读取操作将会提交，而写入、更新、删除操作将会被忽略。该特性往往结合调试模式和日志输出一起使用，用于校验当前的程序（特别是脚本）执行的 `SQL` 是否符合预期。以下是一个开启了空跑特性的配置示例：

```yaml
database:
  default:
  - link:   "mysql:root:12345678@tcp(127.0.0.1:3306)/user"
    debug:  true
    dryRun: true
```

空跑特性也可以通过命令行参数或者环境变量全局修改：

1. 命令行启动参数 \- `gf.gdb.dryrun=true`。
2. 指定的环境变量 \- `GF_GDB_DRYRUN=true`。

例如：

```bash
$ ./app --gf.gdb.dryrun=true
```

```bash
$ ./app --gf.gdb.dryrun true
```