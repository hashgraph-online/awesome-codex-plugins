## 基本介绍

`gsha256`组件提供了`SHA-256`哈希算法的完整实现，用于生成数据的`256位（32字节）`哈希值。该组件从`v2.10.0`版本开始提供。

### 主要特性

1. **字符串哈希**：计算字符串的`SHA-256`哈希值
2. **字节数组哈希**：计算字节数组的`SHA-256`哈希值
3. **文件哈希**：计算文件内容的`SHA-256`哈希值
4. **HMAC签名**：支持`HMAC-SHA256`消息认证码
5. **多种输出格式**：支持十六进制字符串和原始字节输出

### 应用场景

1. **数据完整性校验**：验证数据在传输或存储过程中是否被篡改
2. **密码存储**：存储密码的哈希值而不是明文（建议配合盐值使用）
3. **文件校验**：生成和验证文件的数字指纹
4. **数字签名**：作为签名算法的哈希部分
5. **区块链应用**：计算区块哈希值
6. **API签名验证**：使用`HMAC-SHA256`验证`API`请求的真实性

## 使用方式

```go
import "github.com/gogf/gf/v2/crypto/gsha256"
```

## 接口文档

[https://pkg.go.dev/github.com/gogf/gf/v2/crypto/gsha256](https://pkg.go.dev/github.com/gogf/gf/v2/crypto/gsha256)

## 基本使用

### 字符串哈希

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/gsha256"
)

func main() {
    // 计算字符串的SHA-256哈希
    text := "Hello, GoFrame!"
    hash := gsha256.Encrypt(text)
    fmt.Println("SHA-256 Hash:", hash)
    // 输出: SHA-256 Hash: 8b3d9c5e1a2f4b8d... (64个十六进制字符)
}
```

### 字节数组哈希

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/gsha256"
)

func main() {
    // 计算字节数组的SHA-256哈希
    data := []byte("Hello, GoFrame!")
    hash := gsha256.EncryptBytes(data)
    fmt.Printf("SHA-256 Hash: %x\n", hash)
    // 输出32字节的哈希值
}
```

### 文件哈希

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/gsha256"
)

func main() {
    // 计算文件的SHA-256哈希
    filePath := "/path/to/file.txt"
    hash, err := gsha256.EncryptFile(filePath)
    if err != nil {
        panic(err)
    }
    fmt.Println("File SHA-256 Hash:", hash)
}
```

### HMAC-SHA256签名

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/gsha256"
)

func main() {
    // 使用密钥生成HMAC-SHA256签名
    data := "Hello, GoFrame!"
    key := "my-secret-key"
    
    // 生成HMAC签名
    signature := gsha256.MustEncryptHmac(data, key)
    fmt.Println("HMAC-SHA256 Signature:", signature)
    
    // 验证签名（比较哈希值是否相同）
    expectedSignature := gsha256.MustEncryptHmac(data, key)
    if signature == expectedSignature {
        fmt.Println("Signature is valid!")
    }
}
```

### 字节形式的HMAC签名

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/gsha256"
)

func main() {
    data := []byte("Hello, GoFrame!")
    key := []byte("my-secret-key")
    
    // 生成字节形式的HMAC签名
    signature := gsha256.MustEncryptHmacBytes(data, key)
    fmt.Printf("HMAC-SHA256 Signature: %x\n", signature)
    // 输出32字节的签名值
}
```

## 实际应用示例

### 密码哈希存储

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/gsha256"
    "github.com/gogf/gf/v2/util/grand"
)

func main() {
    // 用户密码
    password := "myPassword123"
    
    // 生成随机盐值
    salt := grand.S(16)
    
    // 计算密码+盐值的哈希
    passwordHash := gsha256.Encrypt(password + salt)
    
    fmt.Println("Salt:", salt)
    fmt.Println("Password Hash:", passwordHash)
    
    // 存储 salt 和 passwordHash 到数据库
    
    // 验证密码时
    inputPassword := "myPassword123"
    computedHash := gsha256.Encrypt(inputPassword + salt)
    
    if computedHash == passwordHash {
        fmt.Println("Password is correct!")
    } else {
        fmt.Println("Password is incorrect!")
    }
}
```

### 文件完整性校验

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/gsha256"
    "github.com/gogf/gf/v2/os/gfile"
)

func main() {
    filePath := "/path/to/important/file.dat"
    
    // 计算原始文件的哈希值
    originalHash, err := gsha256.EncryptFile(filePath)
    if err != nil {
        panic(err)
    }
    fmt.Println("Original Hash:", originalHash)
    
    // 保存哈希值用于后续验证
    gfile.PutContents(filePath+".sha256", originalHash)
    
    // 稍后验证文件完整性
    currentHash, err := gsha256.EncryptFile(filePath)
    if err != nil {
        panic(err)
    }
    
    savedHash := gfile.GetContents(filePath + ".sha256")
    
    if currentHash == savedHash {
        fmt.Println("File integrity verified!")
    } else {
        fmt.Println("File has been modified!")
    }
}
```

### API请求签名

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/gsha256"
    "github.com/gogf/gf/v2/encoding/gjson"
    "github.com/gogf/gf/v2/util/gconv"
    "sort"
    "strings"
)

func main() {
    // API请求参数
    params := map[string]interface{}{
        "user_id":   "12345",
        "timestamp": "1609459200",
        "action":    "get_user_info",
    }
    
    // API密钥
    apiSecret := "my-api-secret-key"
    
    // 生成签名
    signature := generateSignature(params, apiSecret)
    fmt.Println("API Signature:", signature)
    
    // 验证签名
    receivedSignature := signature // 从请求中获取
    computedSignature := generateSignature(params, apiSecret)
    
    if receivedSignature == computedSignature {
        fmt.Println("Signature is valid!")
    } else {
        fmt.Println("Signature is invalid!")
    }
}

// generateSignature 生成API签名
func generateSignature(params map[string]interface{}, secret string) string {
    // 1. 将参数按键名排序
    keys := make([]string, 0, len(params))
    for k := range params {
        keys = append(keys, k)
    }
    sort.Strings(keys)
    
    // 2. 拼接参数字符串
    var parts []string
    for _, k := range keys {
        parts = append(parts, fmt.Sprintf("%s=%s", k, gconv.String(params[k])))
    }
    signString := strings.Join(parts, "&")
    
    // 3. 使用HMAC-SHA256生成签名
    return gsha256.MustEncryptHmac(signString, secret)
}
```

### 数据去重（使用哈希作为唯一标识）

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/crypto/gsha256"
)

func main() {
    // 使用哈希值去重大量数据
    seen := make(map[string]bool)
    
    data := []string{
        "data1",
        "data2",
        "data1", // 重复
        "data3",
        "data2", // 重复
    }
    
    var uniqueData []string
    
    for _, item := range data {
        // 计算数据的哈希值
        hash := gsha256.Encrypt(item)
        
        // 检查是否已经存在
        if !seen[hash] {
            seen[hash] = true
            uniqueData = append(uniqueData, item)
        }
    }
    
    fmt.Println("Unique Data:", uniqueData)
    // 输出: Unique Data: [data1 data2 data3]
}
```

## 注意事项

### SHA-256的不可逆性

`SHA-256`是一种单向哈希函数，**无法从哈希值还原出原始数据**。这使其适合存储敏感信息（如密码）的哈希值，但不适合需要恢复原始数据的场景。

### 密码存储建议

对于密码存储，建议：

1. **使用盐值**：为每个密码生成随机盐值，防止彩虹表攻击
2. **使用专用算法**：考虑使用`bcrypt`、`scrypt`或`Argon2`等专为密码设计的算法
3. **多次哈希**：可以对哈希结果再次哈希（如`PBKDF2`），增加破解难度

### 碰撞抵抗性

虽然`SHA-256`具有很强的碰撞抵抗性（找到两个不同输入产生相同哈希值的难度极大），但在某些对安全性要求极高的场景，可以考虑使用`SHA-384`或`SHA-512`。

### 性能考虑

- 文件哈希计算的时间与文件大小成正比
- 对于大文件，考虑分块计算或异步处理
- `HMAC`操作比普通哈希略慢，因为需要进行额外的密钥处理

## 与其他哈希算法对比

| 算法 | 输出长度 | 安全性 | 速度 | 适用场景 |
|------|---------|--------|------|---------|
| `MD5` | `128位` | 已破解 | 快 | 仅用于非安全场景的校验 |
| `SHA-1` | `160位` | 理论破解 | 较快 | 不推荐用于安全场景 |
| **`SHA-256`** | **`256位`** | **安全** | **中等** | **推荐用于大多数场景** |
| `SHA-512` | `512位` | 非常安全 | 稍慢 | 高安全性要求场景 |