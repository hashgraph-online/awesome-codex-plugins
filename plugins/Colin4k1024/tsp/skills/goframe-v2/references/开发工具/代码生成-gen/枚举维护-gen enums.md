:::tip
该功能特性为 **实验性特性**，从 `v2.4` 版本开始提供。
:::
## 基本介绍

该命令用于分析指定代码目录源码，按照规范生成枚举值信息以及 `Go` 代码文件， **主要用以完善 `OpenAPIv3` 文档中的枚举值维护**。

## 解决痛点

### 痛点描述

- `API` 文档中枚举值类型参数不展示枚举值可选项的问题。
- `API` 文档中的枚举值维护困难的问题，代码与文档脱离维护的问题。降低了与调用端，特别是前后端的协作效率

> 例如，以下接口定义中，任务包含多种状态，这些状态都是枚举值，如果后端来维护成本比较高，并且容易遗漏状态的维护，造成状态枚举值不完整。

### 痛点解决

通过工具解析源码，将枚举值解析生成到启动包 `Go` 文件中，在服务运行时自动加载枚举值，降低手工维护成本，避免枚举值遗漏维护问题。

> 例如，在以下接口定义中，通过工具来维护枚举值，提高了开发效率。

## 命令使用

```text
$ gf gen enums -h
USAGE
    gf gen enums [OPTION]

OPTION
    -s, --src        source folder path to be parsed
    -p, --path       output go file path storing enums content
    -x, --prefixes   only exports packages that starts with specified prefixes
    -h, --help       more information about this command

EXAMPLE
    gf gen enums
    gf gen enums -p internal/boot/boot_enums.go
    gf gen enums -p internal/boot/boot_enums.go -s .
    gf gen enums -x github.com/gogf
```

参数说明：

| 名称 | 必须 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `src` | 否 | `.` | 指定分析的源码目录路径，默认为当前项目根目录 |
| `path` | 否 | `internal/boot/boot_enums.go` | 指定生成的枚举值注册Go代码文件路径 |
| `prefixes` | 否 | - | 只会生成包名称前缀的带有指定关键字的枚举值，支持多个前缀配置 |

:::info
该命令底层使用了`AST`解析实现，将会递归分析所有依赖包的`enums`定义。如果业务项目依赖较复杂，生成`enums`可能会比较多，但绝大部分时候我们只关心自身项目或者个别依赖包的`enums`定义，那么这个时候可以使用`prefixes`参数来控制只生成特定包名前缀的`enums`。
:::

工具配置项`yaml`格式示例：
```yaml title="hack/config.yaml"
gfcli:
  gen:
    enums:
      src:  "api"
      path: "internal/boot/boot_enums.go"
      prefixes: 
      - github.com/gogf
      - myexample/project
```

## 生成文件的使用

执行 `gf gen enums` 命令生成枚举分析文件 `internal/boot/boot_enums.go`，生成文件之后，需要在项目入口文件匿名引入：

```go
import (
    _ "项目模块名/internal/boot"
)
```

## 扩展阅读

### 如何规范定义枚举值

请参考章节： [Golang枚举值管理](../../框架设计/Golang枚举值管理.md)

### 如何对枚举值进行校验

如果规范化定义了枚举值，并且通过命令生成了枚举值维护文件，那么在参数校验中可以使用 `enums` 规则对枚举值字段进行校验，具体规则介绍请参考章节： [数据校验-校验规则](../../核心组件/数据校验/数据校验-校验规则.md)