DES算法。

**使用方式**：

```go
import "github.com/gogf/gf/v2/crypto/gdes"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/crypto/gdes](https://pkg.go.dev/github.com/gogf/gf/v2/crypto/gdes)

**关于 `gdes` 包中的补位说明：**

**`gdes` 包中补位方式支持： `PKCS5PADDING`、 `NOPADDING` 两种方式，当使用 `NOPADDING` 方式时需要自定义补位方法。**

**关于gdes包中的密钥的说明：**

**当使用三倍长的DES算法时，密钥为16字节时，key3等于key1。**