## 基本介绍
进程管理以及进程间的通信是通过 `gproc` 模块实现的，其中进程间通信采用的是本地socket通信机制。

**使用方式**：

```go
import "github.com/gogf/gf/v2/os/gproc"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/os/gproc](https://pkg.go.dev/github.com/gogf/gf/v2/os/gproc)

**简要说明：**

1. `Manager` 对象为进程管理对象，可以同时管理多个子进程(当前执行进程为父进程)；
2. `Process` 为进程对象，表示特定执行或者获取的一个进程资源；
3. 我们可以通过 `Shell`、 `ShellExec`、 `ShellRun` 来执行Shell指令：
   - `Shell` 表示一个原生的Shell指令执行方式，带自定义的输入和输出控制；
   - `ShellExec` 执行命令后将会返回输出的结果内容；
   - `ShellRun` 执行命令后将会直接将返回内容输出到标准输出；
   - 我们可以使用 `goroutine` 来实现异步的执行，如： `go ShellRun(...)` 等等；

## 相关文档