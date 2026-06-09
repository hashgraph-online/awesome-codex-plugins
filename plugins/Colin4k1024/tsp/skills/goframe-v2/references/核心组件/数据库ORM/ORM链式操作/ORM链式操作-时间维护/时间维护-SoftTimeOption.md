在前面的[整型字段](./时间维护-整型字段.md)的示例中，时间字段写入的都是秒级时间戳，但如果我们想要控制时间写入的粒度，写入毫秒级时间戳怎么做呢？
我们可以使用`SoftTimeOption`来控制写入的时间数值粒度。

## 示例SQL
这是后续示例代码中用到的`MySQL`表结构。由于需要写入比秒级更细粒度的数值，因此字段类型使用`big int`来存储。

```sql
CREATE TABLE `user` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  `status` tinyint DEFAULT 0,
  `created_at` bigint unsigned DEFAULT NULL,
  `updated_at` bigint unsigned DEFAULT NULL,
  `deleted_at` bigint unsigned DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

:::tip
如果您尝试测试查看`ORM`操作执行的`SQL`语句，建议您打开`debug`模式（相关文档：[调试模式](../../ORM高级特性/ORM高级特性-调试模式.md)），`SQL`语句将会自动打印到日志输出。
:::

## `created_at` 写入时间

```go
// INSERT INTO `user`(`name`,`created_at`,`updated_at`,`deleted_at`) VALUES('john',1731484186556,1731484186556,0)
g.Model("user").SoftTime(gdb.SoftTimeOption{
  SoftTimeType: gdb.SoftTimeTypeTimestampMilli,
}).Data(g.Map{"name": "john"}).Insert()
```

其中`SoftTimeType`控制时间粒度，粒度选项如下：
```go
const (
    SoftTimeTypeAuto           SoftTimeType = 0 // (Default)Auto detect the field type by table field type.
    SoftTimeTypeTime           SoftTimeType = 1 // Using datetime as the field value.
    SoftTimeTypeTimestamp      SoftTimeType = 2 // In unix seconds.
    SoftTimeTypeTimestampMilli SoftTimeType = 3 // In unix milliseconds.
    SoftTimeTypeTimestampMicro SoftTimeType = 4 // In unix microseconds.
    SoftTimeTypeTimestampNano  SoftTimeType = 5 // In unix nanoseconds.
)
```