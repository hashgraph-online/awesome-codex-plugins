AES算法。

**使用方式**：

```go
import "github.com/gogf/gf/v2/crypto/gaes"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/crypto/gaes](https://pkg.go.dev/github.com/gogf/gf/v2/crypto/gaes)

**温馨提示：**

如果待解密数据经过其它编码，则要先解码再解密，如base64.decode

反过来也一样

如果希望加密完的数据编码，则将结果编码即可，如base64.encode