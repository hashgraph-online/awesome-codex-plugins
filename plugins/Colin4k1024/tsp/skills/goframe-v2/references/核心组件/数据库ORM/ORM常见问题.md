## `ORM`是否可以直接执行SQL文件

1. 首先，`ORM`底层依赖的数据库`driver`从安全性考虑，通常默认不支持同时执行多条`SQL`语句。你可以读取`SQL`文件内容，将内容拆分为单条`SQL`语句（通过`;`分隔符号分隔多条`SQL`语句），然后调用`ORM`的`Exec`方法来执行。
2. 其次，如果你想要允许底层`driver`一次性执行多条`SQL`语句，可以参考底层`driver`的配置，比如`mysql`的配置，可以设置`multiStatements=true`(参考[mysql-driver配置](https://github.com/go-sql-driver/mysql?tab=readme-ov-file#multistatements))，这样`ORM`的`Exec`方法就可以执行多条`SQL`语句了。配置项示例：
    ```yaml
    database:
        default:
            link: "mysql:root:123456@tcp(127.0.0.1:3306)/test?charset=utf8mb4&parseTime=True&loc=Local&multiStatements=true"
    ```

## `driver: bad connection`

如果数据库执行出现该错误，可能是由于本地数据库连接池的连接已经过期，可以检查一下客户端配置的 `MaxLifeTime` 配置是否超过数据库服务端设置的连接最大超时时间。更多客户端配置请参考章节： [ORM使用配置](./ORM使用配置/ORM使用配置.md)

## `update/insert` 操作不生效

使用 `orm` 时,配置文件中：

```toml
dryRun = "(可选)ORM空跑(只读不写)"
```

这行配置一定要删掉或者设置为0

否则出现 `update insert` 操作不生效的现象。

## `cannot find database driver for specified database type "xxx"， did you misspell type name "xxx" or forget importing the database driver?`

程序代码没有引入依赖的数据库驱动，需要注意从 `GoFrame v2.1` 版本开始，需要手动引入社区驱动，请参考：

- [https://github.com/gogf/gf/tree/master/contrib/drivers](https://github.com/gogf/gf/tree/master/contrib/drivers)

## 数据库打开 `DEBUG` 日志后，查询的 `SQL` 语句中发现出现 `WHERE 0=1` 的语句

出现 `WHERE 0=1` 的情况是由于查询条件中存在数组条件，并且数组的长度为 `0`。这种情况 `ORM` 无法自动过滤这种空数组条件（这种条件过滤可能会引起业务异常），需要开发者根据业务场景，显示调用 `OmitEmpty` 或者 `OmitEmptyWhere` 来告诉 `ORM` 可以过滤这些空数组的条件。

## MYSQL中的表情,用SQL查询后,乱码问题

解决办法:

`config.toml` 文件 数据库配置的 `charset` 设置为 `utf8mb4` 默认是 `utf8`

`MySQL` 存储表情时注意：

- 数据库编码 `utf8mb4`
- 表的编码是 `utf8mb4`
- 表中内容字段是 `utf8mb4`

## 怎么让有UUID类型的数据库支持UUID处理

由于ORM类型转换在底层是使用的gconv实现的，所以我们可以自己添加新的converter就可以了。如以下示例，在你的程序初始化时调用就可以了。
```golang
    gconv.RegisterTypeConverterFunc(func(src uuid.UUID) (val *string, err error) {
		v := src.String()
		return &v, nil
	})

	gconv.RegisterTypeConverterFunc(func(src uuid.UUIDs) (val *[]string, err error) {
		v := src.Strings()
		return &v, nil
	})

	gconv.RegisterTypeConverterFunc(func(src string) (val *uuid.UUID, err error) {
		var v uuid.UUID
		val = &v
		src = gstr.Trim(src)
		if src == "" {
			return
		}
		v, err = uuid.Parse(src)
		return
	})
```