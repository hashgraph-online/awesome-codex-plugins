该命令仅针对于预编译二进制下载安装。如果通过 `go install` 命名安装的工具的话，不需要手动再使用 `install` 命令安装 `gf` 工具。

## 下载安装

### 最新版下载

#### `Mac`&`Linux`  快捷下载命令

```bash
wget -O gf https://github.com/gogf/gf/releases/latest/download/gf_$(go env GOOS)_$(go env GOARCH) && chmod +x gf && ./gf install -y && rm ./gf
```

#### Windows 需手动下载

确定自己当前项目的 `goframe` 依赖版本，查看自己的系统信息：

```bash
go env GOOS
go env GOARCH
```

下载地址： [releases](https://github.com/gogf/gf/releases)

### 通过 `go install` 安装

注意：需要将 `$GOPATH/bin` 加入到系统环境变量中，通过 `go env GOPATH` 查看。

#### 最新版本

```bash
go install github.com/gogf/gf/cmd/gf/v2@latest
```

#### 指定版本(版本需要 >= v2.5.5)

```bash
go install github.com/gogf/gf/cmd/gf/v2@v2.5.5
```

### 其它版本下载

#### v2 版本

预编译二进制下载： [releases](https://github.com/gogf/gf/releases)

源码：[gf/cmd/gf](https://github.com/gogf/gf/tree/master/cmd/gf)

#### v1 版本

预编译二进制下载： [releases](https://github.com/gogf/gf-cli/releases)

源码： [gogf/gf-cli](https://github.com/gogf/gf-cli)

## 使用方式

项目地址： [https://github.com/gogf/gf/tree/master/cmd/gf](https://github.com/gogf/gf/tree/master/cmd/gf)

使用方式： `./gf install`

该命令往往是在 `gf` 命令行工具下载到本地后执行（注意执行权限），用于将 `gf` 命令安装到系统环境变量默认支持的目录路径中，以便于在系统任何的地方直接可以使用 `gf` 工具。

:::note
部分系统需要管理员权限支持。

如果是 `MacOS` 下使用 `zsh` 的小伙伴可能会遇到别名冲突问题，可以通过 `alias gf=gf` 来解决，运行一次之后 `gf` 工具会自动修改 `profile` 中的别名设置，用户重新登录（或者重开终端）就好了。
:::

## 使用示例

```bash
$ ./gf_darwin_amd64 install
I found some installable paths for you(from $PATH):
  Id | Writable | Installed | Path
   0 |     true |      true | /usr/local/bin
   1 |     true |     false | /Users/john/Workspace/Go/GOPATH/bin
   2 |     true |     false | /Users/john/.gvm/bin
   4 |     true |     false | /Users/john/.ft
please choose one installation destination [default 0]:
gf binary is successfully installed to: /usr/local/bin
```