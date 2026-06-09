使用 `GoFrame ORM` 查询数据时，由于字段值是一个泛型对象，返回的数据类型将会被自动识别映射到 `Go` 变量类型，作为泛型的具体值。

例如：

- 当字段类型为 `int(xx)` 时，查询到的字段值类型将会被识别会 `int` 类型
- 当字段类型为 `varchar(xxx)`/ `char(xxx)`/ `text` 等类型时将会被自动识别为 `string` 类型
- ……

以下以 `mysql` 类型为例，介绍数据库类型与 `Go` 变量类型的自动识别映射关系:
:::tip
版本可能随时迭代更新，具体可查看源码 [https://github.com/gogf/gf/blob/master/database/gdb/gdb\_core\_structure.go](https://github.com/gogf/gf/blob/master/database/gdb/gdb_core_structure.go)
:::
| 数据库类型 | Go变量类型 |
| --- | --- |
| `*char` | `string` |
| `*text` | `string` |
| `*binary` | `bytes` |
| `*blob` | `bytes` |
| `*int` | `int` |
| `*money` | `float64` |
| `bit` | `int` |
| `big_int` | `int64` |
| `float` | `float64` |
| `double` | `float64` |
| `decimal` | `float64` |
| `bool` | `bool` |
| `year` | `time.Time` |
| `date` | `time.Time` |
| `datetime` | `time.Time` |
| `time` | `time.Time` |
| `timestamp` | `time.Time` |
| `其他` | `string` |

这一特性对于需要将查询结果进行编码，并通过例如 `JSON` 方式直接返回给客户端来说将会非常友好。