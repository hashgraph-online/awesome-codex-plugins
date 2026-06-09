`grand` 模块实现了对随机数操作的封装和改进，实现了极高的随机数生成性能，提供了丰富的随机数相关操作方法。

使用方式：

```go
import "github.com/gogf/gf/v2/util/grand"
```

接口文档：

[https://pkg.go.dev/github.com/gogf/gf/v2/util/grand](https://pkg.go.dev/github.com/gogf/gf/v2/util/grand)

常用方法：

```go
func N(min, max int) int
func B(n int) []byte
func S(n int, symbols ...bool) string
func Str(s string, n int) string
func Intn(max int) int
func Digits(n int) string
func Letters(n int) string
func Meet(num, total int) bool
func MeetProb(prob float32) bool
func Perm(n int) []int
func Symbols(n int) string
```

### 字符列表

```
字符类型  字符列表
数字字符  0123456789
英文字符  abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
特殊字符  !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~
```

### 随机整数

1. `Intn` 方法返回大于等 `0` 且不大于 `max` 的随机整数，即： `[0, max)`。
2. `N` 方法返回 `min` 到 `max` 之间的随机整数，支持负数，包含边界，即： `[min, max]`。

### 随机字符串

1. `B` 方法用于返回指定长度的二进制 `[]byte` 数据。
2. `S` 方法用于返回指定长度的数字、字符，第二个参数 `symbols` 用于指定知否返回的随机字符串中包含特殊字符。
3. `Str` 方法是一个比较高级的方法，用于从给定的字符列表中选择指定长度的随机字符串返回，并且支持 `unicode` 字符，例如中文。例如， `Str("中文123abc", 3)` 将可能会返回 `1a文` 的随机字符串。
4. `Digits` 方法用于返回指定长度的随机数字字符串。
5. `Letters` 方法用于返回指定长度的随机英文字符串。
6. `Symbols` 方法用于返回指定长度的随机特殊字符串。

### 概率性计算

1. `Meet` 用于指定一个数 `num` 和总数 `total`，往往 `num<=total`，并随机计算是否满足 `num/total` 的概率。例如， `Meet(1, 100)` 将会随机计算是否满足百分之一的概率。
2. `MeetProb` 用于给定一个概率浮点数 `prob`，往往 `prob<=1.0`，并随机计算是否满足该概率。例如， `MeetProb(0.005)` 将会随机计算是否满足千分之五的概率。