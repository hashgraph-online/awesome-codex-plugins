## 基本介绍

`grsa`组件提供了完整的`RSA`非对称加密算法实现，支持密钥对生成、数据加密解密等功能。该组件从`v2.10.0`版本开始提供。

### 主要特性

1. **密钥对生成**：支持生成`PKCS#1`和`PKCS#8`格式的密钥对
2. **多种加密模式**：支持`PKCS#1 v1.5`和`OAEP`两种填充模式
3. **灵活的密钥格式**：支持`PEM`、`DER`、`Base64`等多种格式
4. **自动格式检测**：能够自动识别和处理不同格式的密钥
5. **安全性考虑**：提供推荐的`OAEP`填充模式，同时保持向后兼容

### 安全建议

组件提供两种填充方案：

1. **PKCS#1 v1.5（传统）**：由`Encrypt*`、`DecryptPKCS1*`、`DecryptPKCS8*`等函数使用。该方案被认为安全性较低，容易受到填充预言攻击，但为了向后兼容仍然提供。

2. **OAEP（推荐）**：由`EncryptOAEP*`、`DecryptOAEP*`等函数使用。`OAEP`（最优非对称加密填充）是推荐用于新应用的填充方案，提供更好的安全保证。

**对于新项目，建议优先使用OAEP函数（`EncryptOAEP`、`DecryptOAEP`等）。**

## 使用方式

```go
import "github.com/gogf/gf/v2/crypto/grsa"
```

## 接口文档

[https://pkg.go.dev/github.com/gogf/gf/v2/crypto/grsa](https://pkg.go.dev/github.com/gogf/gf/v2/crypto/grsa)

## 基本使用

### 密钥对生成

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/grsa"
)

func main() {
    // 生成默认2048位的PKCS#1格式密钥对
    privateKey, publicKey, err := grsa.GenerateDefaultKeyPair()
    if err != nil {
        panic(err)
    }
    
    fmt.Println("Private Key:", string(privateKey))
    fmt.Println("Public Key:", string(publicKey))
    
    // 生成指定位数的PKCS#1格式密钥对
    privateKey, publicKey, err = grsa.GenerateKeyPair(4096)
    if err != nil {
        panic(err)
    }
    
    // 生成PKCS#8格式密钥对
    privateKey, publicKey, err = grsa.GenerateKeyPairPKCS8(2048)
    if err != nil {
        panic(err)
    }
}
```

### 基本加密解密（PKCS#1 v1.5）

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/grsa"
)

func main() {
    // 生成密钥对
    privateKey, publicKey, err := grsa.GenerateDefaultKeyPair()
    if err != nil {
        panic(err)
    }
    
    // 要加密的数据
    plainText := []byte("Hello, GoFrame!")
    
    // 使用公钥加密（自动检测密钥格式）
    cipherText, err := grsa.Encrypt(plainText, publicKey)
    if err != nil {
        panic(err)
    }
    fmt.Println("Encrypted:", cipherText)
    
    // 使用私钥解密（自动检测密钥格式）
    decrypted, err := grsa.Decrypt(cipherText, privateKey)
    if err != nil {
        panic(err)
    }
    fmt.Println("Decrypted:", string(decrypted))
}
```

### OAEP加密解密（推荐）

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/grsa"
)

func main() {
    // 生成密钥对
    privateKey, publicKey, err := grsa.GenerateDefaultKeyPair()
    if err != nil {
        panic(err)
    }
    
    // 要加密的数据
    plainText := []byte("Hello, GoFrame!")
    
    // 使用OAEP模式加密（推荐）
    cipherText, err := grsa.EncryptOAEP(plainText, publicKey)
    if err != nil {
        panic(err)
    }
    fmt.Println("Encrypted with OAEP:", cipherText)
    
    // 使用OAEP模式解密
    decrypted, err := grsa.DecryptOAEP(cipherText, privateKey)
    if err != nil {
        panic(err)
    }
    fmt.Println("Decrypted:", string(decrypted))
}
```

### Base64编码支持

```go
package main

import (
    "encoding/base64"
    "fmt"
    "github.com/gogf/gf/v2/crypto/grsa"
)

func main() {
    // 生成密钥对
    privateKey, publicKey, err := grsa.GenerateDefaultKeyPair()
    if err != nil {
        panic(err)
    }
    
    // 将密钥转换为Base64格式（方便存储和传输）
    privateKeyBase64 := base64.StdEncoding.EncodeToString(privateKey)
    publicKeyBase64 := base64.StdEncoding.EncodeToString(publicKey)
    
    // 要加密的数据
    plainText := []byte("Hello, GoFrame!")
    
    // 使用Base64格式的公钥加密，返回Base64格式的密文
    cipherTextBase64, err := grsa.EncryptBase64(plainText, publicKeyBase64)
    if err != nil {
        panic(err)
    }
    fmt.Println("Encrypted (Base64):", cipherTextBase64)
    
    // 使用Base64格式的私钥解密Base64格式的密文
    decrypted, err := grsa.DecryptBase64(cipherTextBase64, privateKeyBase64)
    if err != nil {
        panic(err)
    }
    fmt.Println("Decrypted:", string(decrypted))
}
```

### 指定密钥格式加密

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/grsa"
)

func main() {
    // 生成PKCS#1格式密钥对
    privateKeyPKCS1, publicKeyPKCS1, _ := grsa.GenerateKeyPair(2048)
    
    // 生成PKCS#8格式密钥对
    privateKeyPKCS8, publicKeyPKCS8, _ := grsa.GenerateKeyPairPKCS8(2048)
    
    plainText := []byte("Hello, GoFrame!")
    
    // 使用PKCS#1格式公钥加密
    cipherText1, _ := grsa.EncryptPKCS1(plainText, publicKeyPKCS1)
    decrypted1, _ := grsa.DecryptPKCS1(cipherText1, privateKeyPKCS1)
    fmt.Println("PKCS#1:", string(decrypted1))
    
    // 使用PKCS#8格式公钥加密
    cipherText2, _ := grsa.EncryptPKCS8(plainText, publicKeyPKCS8)
    decrypted2, _ := grsa.DecryptPKCS8(cipherText2, privateKeyPKCS8)
    fmt.Println("PKCS#8:", string(decrypted2))
    
    // 使用PKIX格式公钥加密（标准格式）
    cipherText3, _ := grsa.EncryptPKIX(plainText, publicKeyPKCS8)
    decrypted3, _ := grsa.DecryptPKCS8(cipherText3, privateKeyPKCS8)
    fmt.Println("PKIX:", string(decrypted3))
}
```

### 密钥类型检测

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/grsa"
)

func main() {
    // 生成不同格式的密钥
    privateKeyPKCS1, _, _ := grsa.GenerateKeyPair(2048)
    privateKeyPKCS8, _, _ := grsa.GenerateKeyPairPKCS8(2048)
    
    // 检测密钥类型
    keyType1, _ := grsa.GetPrivateKeyType(privateKeyPKCS1)
    fmt.Println("Key Type 1:", keyType1) // 输出: PKCS#1
    
    keyType2, _ := grsa.GetPrivateKeyType(privateKeyPKCS8)
    fmt.Println("Key Type 2:", keyType2) // 输出: PKCS#8
}
```

## 注意事项

### 加密数据大小限制

`RSA`加密对明文大小有限制，具体取决于密钥长度和填充模式：

- **PKCS#1 v1.5填充**：`最大明文长度 = 密钥字节数 - 11`
  - 例如：`2048位`密钥可以加密最多`245字节`
- **OAEP填充**：`最大明文长度 = 密钥字节数 - 2 * 哈希长度 - 2`
  - 例如：`2048位`密钥使用`SHA-256`可以加密最多`190字节`

如需加密大量数据，建议使用混合加密方案：用`RSA`加密对称密钥，用对称密钥（如`AES`）加密实际数据。

### 密钥格式说明

- **PKCS#1**：传统的`RSA`密钥格式，`PEM`头为`RSA PRIVATE KEY`和`RSA PUBLIC KEY`
- **PKCS#8**：通用的私钥格式，`PEM`头为`PRIVATE KEY`，公钥格式为`PKIX`（`PEM`头为`PUBLIC KEY`）
- 组件的`Encrypt`和`Decrypt`方法可以自动识别和处理这两种格式

### 安全性建议

1. **密钥长度**：建议使用至少2048位的密钥，4096位更安全
2. **填充模式**：新项目使用`EncryptOAEP`和`DecryptOAEP`
3. **密钥保护**：私钥必须妥善保管，不要硬编码在代码中
4. **密钥轮换**：定期更换密钥对以提高安全性
5. **证书验证**：在实际应用中，建议结合数字证书进行身份验证