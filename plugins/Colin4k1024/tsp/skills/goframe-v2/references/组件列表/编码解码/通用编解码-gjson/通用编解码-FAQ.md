## JSON中的大数字精度丢失问题

### 问题描述

```go
package main

import (
    "github.com/gogf/gf/v2/encoding/gjson"
    "github.com/gogf/gf/v2/frame/g"
)

func main() {
    str := `{"Id":1492404095703580672,"Name":"Jason"}`
    strJson := gjson.New(str)
    g.Dump(strJson)
}
```

执行后输出为：

```
"{\"Id\":1492404095703580700,\"Name\":\"Jason\"}"
```

### 解决方案

```go
package main

import (
    "github.com/gogf/gf/v2/encoding/gjson"
    "github.com/gogf/gf/v2/frame/g"
)

func main() {
    str := `{"Id":1492404095703580672,"Name":"Jason"}`
    strJson := gjson.NewWithOptions(str, gjson.Options{
        StrNumber: true,
    })
    g.Dump(strJson)
}
```

执行后输出为：

```
"{\"Id\":1492404095703580672,\"Name\":\"Jason\"}"
```

### 相关连接

- [https://github.com/gogf/gf/issues/1603](https://github.com/gogf/gf/issues/1603)