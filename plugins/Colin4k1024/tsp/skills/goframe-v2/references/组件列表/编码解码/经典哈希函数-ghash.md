## 基本介绍

常用经典哈希函数Go语言实现，提供 `uint32` 及 `uint64` 类型的哈希函数。

**使用方式**：

```go
import "github.com/gogf/gf/v2/encoding/ghash"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/encoding/ghash](https://pkg.go.dev/github.com/gogf/gf/v2/encoding/ghash)

## 基准测试

```
goos: darwin
goarch: amd64
pkg: github.com/gogf/gf/v2/encoding/ghash
cpu: Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz
Benchmark_BKDR
Benchmark_BKDR-12          39315165            26.88 ns/op
Benchmark_BKDR64
Benchmark_BKDR64-12        62891215            22.61 ns/op
Benchmark_SDBM
Benchmark_SDBM-12          49689925            25.40 ns/op
Benchmark_SDBM64
Benchmark_SDBM64-12        48860472            24.38 ns/op
Benchmark_RS
Benchmark_RS-12            39463418            25.52 ns/op
Benchmark_RS64
Benchmark_RS64-12         53318370            19.45 ns/op
Benchmark_JS
Benchmark_JS-12            53751033            23.20 ns/op
Benchmark_JS64
Benchmark_JS64-12          62440287            19.25 ns/op
Benchmark_PJW
Benchmark_PJW-12           42439626            27.85 ns/op
Benchmark_PJW64
Benchmark_PJW64-12         37491696            33.28 ns/op
Benchmark_ELF
Benchmark_ELF-12           38034584            31.74 ns/op
Benchmark_ELF64
Benchmark_ELF64-12         44047201            27.58 ns/op
Benchmark_DJB
Benchmark_DJB-12           46994352            22.60 ns/op
Benchmark_DJB64
Benchmark_DJB64-12         61980186            19.19 ns/op
Benchmark_AP
Benchmark_AP-12            29544234            40.58 ns/op
Benchmark_AP64
Benchmark_AP64-12          28123783            42.48 ns/op
```

## 重复测试

测试结果与测试内容有关联性和随机性，我这里通过 `uint64` 数值的范围遍历来进行简单的重复性测试，本身不够严谨，因此仅供趣味性参考。

```go
package main

import (
    "encoding/binary"
    "fmt"
    "math"

    "github.com/gogf/gf/v2/encoding/ghash"
)

func main() {
    var (
        m    = make(map[uint64]struct{})
        b    = make([]byte, 8)
        ok   bool
        hash uint64
    )
    for i := uint64(0); i < math.MaxUint64; i++ {
        binary.LittleEndian.PutUint64(b, i)
        hash = ghash.PJW64(b)
        if _, ok = m[hash]; ok {
            fmt.Println("repeated found:", i)
            break
        }
        m[hash] = struct{}{}
    }
}
```

测试结果如下：

| 哈希函数 | 重复位置 | 备注 |
| --- | --- | --- |
| `AP64` | `8388640` |  |
| `BKDR64` | `33536` |  |
| `DJB64` | `8448` |  |
| `ELF64` | `4096` |  |
| `JS64` | `734` |  |
| `PJW64` | `2` |  |
| `RS64` | - | 32G Memory OOM |
| `SDBM64` | - | 32G Memory OOM |