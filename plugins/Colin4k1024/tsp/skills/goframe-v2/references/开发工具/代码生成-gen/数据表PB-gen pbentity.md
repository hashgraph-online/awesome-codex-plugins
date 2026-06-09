:::tip
该功能特性从 `v2.4` 版本开始提供。
:::
## 基本介绍

该命令用于读取配置的数据库，根据数据表生成对应的 `proto` 数据结构文件。

## 命令使用

```text
$ gf gen pbentity -h
USAGE
    gf gen pbentity [OPTION]

OPTION
    -p, --path                 directory path for generated files storing
    -k, --package              package path for all entity proto files
    -l, --link                 database configuration, the same as the ORM configuration of GoFrame
    -t, --tables               generate models only for given tables, multiple table names separated with ','
    -f, --prefix               add specified prefix for all entity names and entity proto files
    -r, --removePrefix         remove specified prefix of the table, multiple prefix separated with ','
    -rf, --removeFieldPrefix   remove specified prefix of the field, multiple prefix separated with ','
    -n, --nameCase             case for message attribute names, default is "Camel":
                               | Case            | Example            |
                               |---------------- |--------------------|
                               | Camel           | AnyKindOfString    |
                               | CamelLower      | anyKindOfString    | default
                               | Snake           | any_kind_of_string |
                               | SnakeScreaming  | ANY_KIND_OF_STRING |
                               | SnakeFirstUpper | rgb_code_md5       |
                               | Kebab           | any-kind-of-string |
                               | KebabScreaming  | ANY-KIND-OF-STRING |
    -j, --jsonCase             case for message json tag, cases are the same as "nameCase", default "CamelLower".
                               set it to "none" to ignore json tag generating.
    -o, --option               extra protobuf options
    -h, --help                 more information about this command

EXAMPLE
    gf gen pbentity
    gf gen pbentity -l "mysql:root:12345678@tcp(127.0.0.1:3306)/test"
    gf gen pbentity -p ./protocol/demos/entity -t user,user_detail,user_login
    gf gen pbentity -r user_ -k github.com/gogf/gf/example/protobuf
    gf gen pbentity -r user_

CONFIGURATION SUPPORT
    Options are also supported by configuration file.
    It's suggested using configuration file instead of command line arguments making producing.
    The configuration node name is "gf.gen.pbentity", which also supports multiple databases, for example(config.yaml):
    gfcli:
      gen:
      - pbentity:
            link:    "mysql:root:12345678@tcp(127.0.0.1:3306)/test"
            path:    "protocol/demos/entity"
            tables:  "order,products"
            package: "demos"
      - pbentity:
            link:    "mysql:root:12345678@tcp(127.0.0.1:3306)/primary"
            path:    "protocol/demos/entity"
            prefix:  "primary_"
            tables:  "user, userDetail"
            package: "demos"
            option:  |
              option go_package    = "protobuf/demos";
              option java_package  = "protobuf/demos";
              option php_namespace = "protobuf/demos";
            typeMapping:
              json:
                type: google.protobuf.Value
                import: google/protobuf/struct.proto
              jsonb:
                type: google.protobuf.Value
                import: google/protobuf/struct.proto
```
:::tip
如果使用框架推荐的项目工程脚手架，并且系统安装了 `make` 工具，也可以使用 `make pbentity` 快捷指令。
:::
参数说明：

| 名称 | 默认值 | 含义 | 示例 |
| --- | --- | --- | --- |
| `gfcli.gen.pbentity` |  | 代码生成配置项，可以有多个配置项构成数组，支持多个数据库生成。不同的数据库可以设置不同的生成规则，例如可以生成到不同的位置或者文件。 | - |
| `path` | `manifest/protobuf/pbentity` | 生成 `proto` 文件的存储 **目录** 地址。 | `protobuf/pbentity` |
| `package` | 自动识别 `go.mod` | 生成的 `proto` 文件中的 `go_package` 路径，并自动识别 `package` 名称 | - |
| `link` |  | 分为两部分，第一部分表示你连接的数据库类型 `mysql`, `postgresql` 等, 第二部分就是连接数据库的 `dsn` 信息。具体请参考 [ORM使用配置](../../核心组件/数据库ORM/ORM使用配置/ORM使用配置.md) 章节。 | - |
| `prefix` |  | 生成数据库对象及文件的前缀，以便区分不同数据库或者不同数据库中的相同表名，防止数据表同名覆盖。 | `order_`<br />`user_` |
| `removePrefix` |  | 删除数据表的指定前缀名称。多个前缀以 `,` 号分隔。 | `gf_` |
| `removeFieldPrefix` |  | 删除字段名称的指定前缀名称。多个前缀以 `,` 号分隔。 | `f_` |
| `tables` |  | 指定当前数据库中需要执行代码生成的数据表。如果为空，表示数据库的所有表都会生成。 | `user, user_detail` |
| `nameCase` | `CamelLower` | 生成的 `message` 属性字段名称格式。参数可选为： `Camel`、 `CamelLower`、 `Snake`、 `SnakeScreaming`、 `SnakeFirstUpper`、 `Kebab`、 `KebabScreaming`。具体介绍请参考命名行帮助示例。 | `Snake` |
| `option` |  | 额外的 `proto option` 配置列表 |  |
| `typeMapping` |  | 用于自定义数据表字段类型到生成的Go文件中对应属性类型映射 |  |
| `fieldMapping` |  | 用于自定义数据表具体字段到生成的Go文件中对应属性类型映射 |  |

### 参数：`typeMapping`

参数`typeMapping`支持配置数据库字段类型对应的`Go`数据类型，默认值为：
```yaml
decimal:
  type: float64
money:
  type: float64
numeric:
  type: float64
smallmoney:
  type: float64
```
该配置支持通过`import`配置项引入第三方包，例如：
```yaml
decimal:
  type:   decimal.Decimal
  import: github.com/shopspring/decimal
```

### 参数：`fieldMapping`

参数`fieldMapping`提供细粒度的字段类型映射配置，支持配置指定数据库字段生成的`Go`数据类型。除了配置名称不一样外，配置内容与`typeMapping`一致。配置示例：
```yaml
paid_orders.amount:
  type:   decimal.Decimal
  import: github.com/shopspring/decimal
```
示例中，`paid_orders`为表名称，`amount`为字段名称，`type`表示生成的`Go`代码中对应的数据类型名称，`import`表示生成的代码中需要引入第三方包。

## 与 `gen dao` 中的 `entity` 差别

### 相同之处

- 两者生成的内容都是 `entity` 内容，即从数据集合（数据库表）中生成对应的 `Golang` 实体对象供程序方便使用。并且都是单向生成，即只能从数据集合生成实体对象代码，以保证实体对象数据结构的同步。
- `gen dao` 生成的 `entity` 数据实体对象是对于 `Golang` 语言来说是通用的，但目前主要为 `HTTP` 协议服务。在 `HTTP` 服务中， `gen dao` 中生成的 `entity` 虽然是在 `internal` 目录下，但最终也会作为 `HTTP API` 返回的一部分服务客户端。

### 不同之处

- 在 `GRPC` 服务中， `gen dao` 生成的 `entity` 数据结构无法提供给 `GRPC` 接口使用，因为 `GRPC` 的数据结构需要使用 `proto` 文件来定义。因此，在 `GRPC` 服务中就需要使用到 `gen pbentity` 中生成的 `pbentity proto` 文件。同时，在 `GRPC` 微服务开发中， `gen dao` 生成的 `entity` 已经没有具体作用。
- 取名 `pbentity` 而不是 `entity` 的名称，是为了防止和 `gen dao` 中的 `entity` 含义冲突。