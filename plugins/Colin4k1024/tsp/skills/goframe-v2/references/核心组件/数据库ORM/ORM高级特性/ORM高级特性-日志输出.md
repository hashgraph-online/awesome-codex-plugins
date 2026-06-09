:::danger
`ORM` 日志的输出，是在提交底层数据库 `driver` 之前， `ORM` 将链式操作或者 `SQL` 构成的模板与执行参数进行格式化打印展示，供人工阅读调试。由于底层 `driver` 可能会对提交参数进行二次的转换，所以这里的日志输出仅供参考，并不完全是底层真正执行的 `SQL` 语句。
:::
日志输出往往是打印一些调试或者 `SQL` 语句，日志对象可以通过 `SetLogger/GetLogger` 方法来设置，也可以通过配置文件来做配置，日志的配置请查看 `ORM` 的 [ORM使用配置](../ORM使用配置/ORM使用配置.md) 章节。以下是一个开启了日志输出的配置示例：

```yaml
database:
  logger:
  - path:   "/var/log/gf-app/sql"
    level:  "all"
    stdout: true
  default:
  - link:  "mysql:root:12345678@tcp(127.0.0.1:3306)/user"
    debug: true
```
:::warning
需要注意这里使用关键字 `logger` 作为 `ORM` 的日志配置项名称，因此您无法使用该名字作为数据库配置分组。
:::
`ORM` 组件输出的日志相当详尽，我们来看一个示例：

```html
2021-05-22 21:12:10.776 [DEBU] {38d45cbf2743db16f1062074f7473e5c} [  4 ms] [default] [rows:0  ] [txid:1] BEGIN
2021-05-22 21:12:10.776 [DEBU] {38d45cbf2743db16f1062074f7473e5c} [  0 ms] [default] [rows:0  ] [txid:1] SAVEPOINT `transaction0`
2021-05-22 21:12:10.789 [DEBU] {38d45cbf2743db16f1062074f7473e5c} [ 13 ms] [default] [rows:8  ] [txid:1] SHOW FULL COLUMNS FROM `user`
2021-05-22 21:12:10.790 [DEBU] {38d45cbf2743db16f1062074f7473e5c} [  1 ms] [default] [rows:1  ] [txid:1] INSERT INTO `user`(`id`,`name`) VALUES(1,'john')
2021-05-22 21:12:10.791 [DEBU] {38d45cbf2743db16f1062074f7473e5c} [  1 ms] [default] [rows:0  ] [txid:1] ROLLBACK TO SAVEPOINT `transaction0`
2021-05-22 21:12:10.791 [DEBU] {38d45cbf2743db16f1062074f7473e5c} [  0 ms] [default] [rows:1  ] [txid:1] INSERT INTO `user`(`id`,`name`) VALUES(2,'smith')
2021-05-22 21:12:10.792 [DEBU] {38d45cbf2743db16f1062074f7473e5c} [  1 ms] [default] [rows:0  ] [txid:1] COMMIT
```

可以看到，日志包含以下几部分信息：

1. 日期及时间，精确到毫秒。
2. 日志级别。因为 `SQL` 日志主要用于功能调试/问题排查，生产环境往往需要关闭掉，因此日志级别固定为 `DEBUG` 级别。
3. 当前 `SQL` 执行耗时。从客户端发起请求到接收到数据的时间，单位为毫秒。当执行时间不足 `1` 毫秒时，展示为 `0` 毫秒。
4. 当前 `SQL` 所处的数据库配置分组，默认为 `default`。关于配置分组的介绍具体请参考章节： [ORM使用配置](../ORM使用配置/ORM使用配置.md)。
5. 当前 `SQL` 所属的 **事务ID**。如果当前 `SQL` 不属于事务操作时，不存在该字段。关于事务ID的介绍请参考章节： [ORM事务处理](../ORM事务处理/ORM事务处理.md)。
6. 具体执行的 `SQL` 语句。需要注意的是，由于底层使用的是 `SQL` 预处理，这里的 `SQL` 语句是通过组件自动拼接的结果，仅供参考。