:::warning
滚动切分目前属于实验性特性，如有问题请随时反馈。
:::
之前的章节中我们知道， `glog` 组件支持通过设置日志文件名称的方式，使得日志文件按照日期进行输出。从 `GoFrame v1.12` 版本开始， `glog` 组件也支持对日志文件进行滚动切分的特性，该特性涉及到日志对象配置属性中的以下几个配置项：

```go
RotateSize           int64          // Rotate the logging file if its size > 0 in bytes.
RotateExpire         time.Duration  // Rotate the logging file if its mtime exceeds this duration.
RotateBackupLimit    int            // Max backup for rotated files, default is 0, means no backups.
RotateBackupExpire   time.Duration  // Max expire for rotated files, which is 0 in default, means no expiration.
RotateBackupCompress int            // Compress level for rotated files using gzip algorithm. It's 0 in default, means no compression.
RotateCheckInterval  time.Duration  // Asynchronizely checks the backups and expiration at intervals. It's 1 hour in default.
```

简要说明：

1. `RotateSize` 用于设置滚动切分时按照文件大小进行切分，该属性的单位为字节。只有当该属性值大于0时才会开启滚动切分的特性。
2. `RotateExpire` 用于设置滚动切分时按照文件超过一定时间没有修改时进行切分。只有当该属性值大于0时才会开启滚动切分的特性。
3. `RotateBackupLimit` 用于设置滚动切分的保留文件数，默认为0表示不保留，往往该值需要设置大于0。超过该保留文件数的切分文件将会按照从旧到新进行删除。
4. `RotateBackupExpire` 用于设置按照过期时间进行清理。当切分文件超过指定的时间时将会被删除。
5. `RotateBackupCompress` 用于设置切分文件的压缩级别，默认为0表示不压缩。该压缩级别的取值范围为 `1-9`，其中 `9` 为最大压缩级别。
6. `RotateCheckInterval` 用于设置定时器的定时检测间隔，默认为1小时，往往不需要设置。

### 功能开启

从以上滚动切分的配置项可以看到，仅有当 `RotateSize` 或者 `RotateExpire` 配置项被设置时才会生效，默认情况下是关闭的。

### 文件格式

`glog` 组件的日志输出文件固定格式为 `*.log`，即使用 `.log` 作为日志文件名后缀。为方便统一规范管理，切分文件的格式也是固定的，开发者无法自定义。当日志文件被滚动切分时，当前被切分的日志文件将会按照” `*.切分时间.log`“的格式进行重命名。其中 `切分时间` 的格式为： `年月日时分秒毫秒微秒`，例如:

```html
access.log          -> access.20200326101301899002.log
access.20200326.log -> access.20200326.20200326101301899002.log
```

### 配置示例

1. 示例1，按照日志文件大小进行滚动切分：

```yaml
logger:
     Path:                  "/var/log"
     Level:                 "all"
     Stdout:                false
     RotateSize:            "100M"
     RotateBackupLimit:     2
     RotateBackupExpire:    "7d"
     RotateBackupCompress:  9
```

简要说明：

   - 可以看到 `RotateSize` 配置项在配置文件中支持使用字符串的形式进行设置，例如： `100M`, `200MB`, `500KB`, `1Gib` 等等，在该示例中，我们设置日志文件大小超过 `100M` 时进行切分。
   - 同时， `RotateBackupExpire` 的配置项也支持字符串配置，例如： `1h`, `30m`, `1d6h`, `7d` 等等，在该示例中，我们设置切分文件的过期时间为 `7d`，即七天后会自动删除该切分文件。
   - 这里通过设置 `RotateBackupCompress` 为 `9` 表示使用最大的压缩级别，使得切分后的文件最小化存储。但是需要注意，切分和压缩是两个不同的操作，文件压缩是一个异步操作，因此当文件被自动切分后，定时器通过一定的时间间隔定期检查后再自动将其压缩为 `*.gz` 文件。压缩级别设置得越高，会更多使用 `CPU` 资源。
2. 示例2，按照日志文件修改过期进行滚动切分：

```yaml
logger:
     Path:                  "/var/log"
     Level:                 "all"
     Stdout:                false
     RotateExpire:          "1d"
     RotateBackupLimit:     1
     RotateBackupExpire:    "7d"
     RotateBackupCompress:  9
```

在这里，我们设置 `RotateExpire` 为 `1d` 表示当某个日志文件超过一天都没有任何修改/写入时， `glog` 模块将会自动将其进行滚动切分。同时进行压缩存储。

### 注意事项

由于不同的日志对象可能有不同的滚动切分配置，假如多个日志对象的日志目录为同一个，并且都开启了滚动切分特性，那么多个日志对象的滚动切分配置项会冲突，会有意想不到的结果。因此，我们建议您两个选择：

1. 全局使用同一个默认的日志单例对象（ `g.Log()`），通过 `Cat` 或 `File` 方法设置输出日志文件到不同的目录或文件名。
2. 将不同日志对象（ `g.Log(名称)`）的输出目录（ `Path` 配置项）设置为不同的文件目录，并且多个日志对象的日志目录不存在相互的层级关系。

例如： 我们有两类业务日志文件 `order` 和 `promo`，分别对应订单业务和促销业务，我们先假定他们属于同一个服务程序中。

假如日志路径为 `/var/log`，我们可以：

1. 通过 `g.Log().Cat("order").Print(xxx)` 输出订单日志。生成的日志文件例如： `/var/log/order/2020-03-26.log`。
2. 通过 `g.Log().Cat("promo").Print(xxx)` 输出促销日志。生成的日志文件例如： `/var/log/promo/2020-03-26.log`。

也可以通过：

1. 通过 `g.Log("order").Print(xxx)` 输出订单日志。生成的日志文件例如： `/var/log/order.log`。
2. 通过 `g.Log("promo").Print(xxx)` 输出促销日志。生成的日志文件例如： `/var/log/promo.log`。