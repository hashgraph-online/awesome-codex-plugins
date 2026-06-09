# 接口文档-扩展Response

## 一、概述

`RESTful API`设计中，不同的状态码表示不同的响应情况，例如 `200` 表示成功，`201` 表示创建成功，`400` 表示请求错误，`401` 表示未授权等。在`GoFrame`的`OpenAPIv3`接口文档中，默认情况下只会生成成功状态（通常是 `200`）的响应文档。

然而，在实际应用中，我们常常需要为一个`API`提供多种可能的响应状态，例如错误处理、权限验证失败等情况。为了满足这一需求，`GoFrame`在 `goai` 组件中提供了 `IEnhanceResponseStatus` 接口，开发者可以通过实现该接口来扩展响应结构体的信息，添加多种状态码的响应文档。

## 二、接口定义

`IEnhanceResponseStatus` 接口的相关定义如下：

``` go
type EnhancedStatusCode = int

type EnhancedStatusType struct {
    Response any
    Examples any
}

type IEnhanceResponseStatus interface {
    EnhanceResponseStatus() map[EnhancedStatusCode]EnhancedStatusType
}
```

## 三、接口字段说明

- `EnhancedStatusCode`：表示 HTTP 状态码，例如 `200`、`201`、`400`、`401`、`403`、`404`、`500` 等。

- `EnhancedStatusType`：包含两个字段：
  - `Response`：响应结构体，可以是任意类型（`any`）。你可以为它添加 `g.Meta` 标签来添加文档信息，如果设置了 `mime` 标签，该结构体会覆盖通用响应结构体的内容。
  - `Examples`：响应示例，可以是任意类型（`any`）。你可以使用错误码列表自动生成示例内容并显示在文档中，这样可以保证文档内容与实际业务内容的同步。

- `IEnhanceResponseStatus`：接口定义，包含一个方法 `EnhanceResponseStatus()`，该方法返回一个映射，将 HTTP 状态码映射到相应的 `EnhancedStatusType` 类型。

## 四、使用方法

要使用 `IEnhanceResponseStatus` 接口，需要在响应结构体中实现 `EnhanceResponseStatus()` 方法。该方法返回一个映射，将 HTTP 状态码映射到相应的响应结构体和示例。

### 1. 实现接口

在响应结构体中实现 `EnhanceResponseStatus()` 方法，返回不同状态码对应的响应结构体和示例。

### 2. 设置响应状态码

可以在响应结构体的 `g.Meta` 标签中使用 `status` 属性来设置默认的响应状态码，例如 `g.Meta `status:"201"`。

### 3. 使用示例数据

可以在 `EnhanceResponseStatus()` 方法中返回示例数据，这些数据将会显示在生成的 OpenAPIv3 文档中。

## 五、完整示例

下面是一个完整的示例，演示如何使用 `IEnhanceResponseStatus` 接口来扩展响应结构体的信息：

``` go
package main

import (
    "context"

    "github.com/gogf/gf/v2/errors/gcode"
    "github.com/gogf/gf/v2/errors/gerror"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "github.com/gogf/gf/v2/net/goai"
)

type StoreMessageReq struct {
    g.Meta  `path:"/messages" method:"post" summary:"Store a message"`
    Content string `json:"content"`
}
type StoreMessageRes struct {
    g.Meta `status:"201"`
    Id     string `json:"id"`
}
type EmptyRes struct {
    g.Meta `mime:"application/json"`
}

type CommonRes struct {
    Code    int         `json:"code"`
    Message string      `json:"message"`
    Data    interface{} `json:"data"`
}

var StoreMessageErr = map[int]gcode.Code{
    500: gcode.New(1, "Server Dead", nil),
}

func (r StoreMessageRes) EnhanceResponseStatus() (resList map[int]goai.EnhancedStatusType) {
    examples := []interface{}{}
    example500 := CommonRes{
        Code:    StoreMessageErr[500].Code(),
        Message: StoreMessageErr[500].Message(),
        Data:    nil,
    }
    examples = append(examples, example500)
    return map[int]goai.EnhancedStatusType{
        403: {
            Response: EmptyRes{},
        },
        500: {
            Response: struct{}{},
            Examples: examples,
        },
    }
}

type Controller struct{}

func (c *Controller) StoreMessage(ctx context.Context, req *StoreMessageReq) (res *StoreMessageRes, err error) {
    return nil, gerror.NewCode(gcode.CodeNotImplemented)
}

func main() {
    s := g.Server()
    s.Group("/", func(group *ghttp.RouterGroup) {
        group.Bind(new(Controller))
    })
    oai := s.GetOpenApi()
    oai.Config.CommonResponse = CommonRes{}
    oai.Config.CommonResponseDataField = `Data`
    s.SetOpenApiPath("/api.json")
    s.SetSwaggerPath("/swagger")
    s.SetPort(8199)
    s.Run()
}
```

执行后，访问地址 [http://127.0.0.1:8199/swagger](http://127.0.0.1:8199/swagger) 可以查看 `swagger ui`，访问 [http://127.0.0.1:8199/api.json](http://127.0.0.1:8199/api.json) 可以查看对应的 `OpenAPIv3` 接口文档。其中生成的 `OpenAPIv3` 接口文档如下：

``` json
{
    "openapi": "3.0.0",
    "components": {
        "schemas": {
            "main.StoreMessageReq": {
                "properties": {
                    "content": {
                        "format": "string",
                        "type": "string"
                    }
                },
                "type": "object"
            },
            "main.StoreMessageRes": {
                "properties": {
                    "id": {
                        "format": "string",
                        "type": "string"
                    }
                },
                "type": "object"
            },
            "interface": {
                "properties": {},
                "type": "object"
            },
            "main.EmptyRes": {
                "properties": {},
                "type": "object"
            },
            "struct": {
                "properties": {},
                "type": "object"
            }
        }
    },
    "info": {
        "title": "",
        "version": ""
    },
    "paths": {
        "/messages": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/main.StoreMessageReq"
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "properties": {
                                        "code": {
                                            "format": "int",
                                            "type": "integer"
                                        },
                                        "message": {
                                            "format": "string",
                                            "type": "string"
                                        },
                                        "data": {
                                            "properties": {
                                                "id": {
                                                    "format": "string",
                                                    "type": "string"
                                                }
                                            },
                                            "type": "object"
                                        }
                                    },
                                    "type": "object"
                                }
                            }
                        },
                        "description": ""
                    },
                    "403": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/main.EmptyRes"
                                }
                            }
                        },
                        "description": ""
                    },
                    "500": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "properties": {
                                        "code": {
                                            "format": "int",
                                            "type": "integer"
                                        },
                                        "message": {
                                            "format": "string",
                                            "type": "string"
                                        },
                                        "data": {
                                            "properties": {},
                                            "type": "object"
                                        }
                                    },
                                    "type": "object"
                                },
                                "examples": {
                                    "example 1": {
                                        "value": {
                                            "code": 1,
                                            "message": "Server Dead",
                                            "data": null
                                        }
                                    }
                                }
                            }
                        },
                        "description": ""
                    }
                },
                "summary": "Store a message"
            }
        }
    }
}
```
可以看到默认的响应状态码已经被更改为 `201`，并且响应示例也自动生成。

## 六、常见状态码使用场景

在实际应用中，不同的 HTTP 状态码用于表示不同的响应情况。以下是一些常见的状态码及其使用场景：

- `200 OK`：请求成功，返回请求的数据。
- `201 Created`：资源创建成功，通常用于 POST 请求。
- `204 No Content`：请求成功，但没有返回内容，通常用于 DELETE 请求。
- `400 Bad Request`：请求参数错误或格式不正确。
- `401 Unauthorized`：未授权，需要身份验证。
- `403 Forbidden`：已授权，但没有权限访问资源。
- `404 Not Found`：请求的资源不存在。
- `500 Internal Server Error`：服务器内部错误。

在实现 `IEnhanceResponseStatus` 接口时，可以根据实际业务需求，为这些不同的状态码提供相应的响应结构体和示例数据。

## 七、使用建议

1. **结构体复用**：对于类似的响应结构，可以定义公共的结构体进行复用，减少代码重复。

2. **错误码管理**：将错误码集中管理，例如使用 `map` 或常量来定义不同状态码对应的错误码，便于维护和扩展。

3. **示例数据的真实性**：提供的示例数据应尽量真实，反映实际业务场景，便于前端开发者理解和处理。

4. **文档同步更新**：当业务逻辑或错误码变更时，及时更新接口文档，保持文档与代码的一致性。

## 八、使用资源文件加载示例数据

在实际应用中，示例数据可能会比较大或复杂，直接在代码中编写可能会影响代码的可读性。`GoFrame`的`goai`组件提供了从外部文件加载示例数据的功能，支持从`gres`资源管理器或本地文件系统中读取示例数据，文件格式可以为`json/xml/yaml/ini`等`gjson`组件支持的格式。

### 1. 使用`g.Meta`标签指定示例文件

可以在响应结构体的`g.Meta`标签中使用`resEg`属性指定示例文件的路径：

```go
type MyResponse struct {
    g.Meta `status:"201" resEg:"testdata/examples/201.json"`
    // ...其他字段
}
```

其中`testdata/examples/201.json`是示例文件的路径，可以是相对路径或绝对路径。

### 2. 示例文件格式

示例文件可以是一个`JSON`对象或`JSON`数组：

- **JSON对象**：每个键将作为示例的名称，值作为示例的内容。

  ```json
  {
    "example1": {
      "code": 0,
      "message": "Success",
      "data": { "id": 1 }
    },
    "example2": {
      "code": 1,
      "message": "Failed",
      "data": null
    }
  }
  ```

- **JSON数组**：数组中的每个元素将作为一个示例，示例名称会自动生成为`example 1`、`example 2`等。

  ```json
  [
    {
      "code": 0,
      "message": "Success",
      "data": { "id": 1 }
    },
    {
      "code": 1,
      "message": "Failed",
      "data": null
    }
  ]
  ```

### 3. 使用`gres`资源管理器

`GoFrame`的`goai`组件会首先尝试从`gres`资源管理器中读取指定路径的文件，如果找不到，则会尝试从本地文件系统中读取。这使得可以将示例数据打包到程序中，方便分发和部署。

要使用`gres`资源管理器，需要先将示例文件打包到资源文件中：

```go
package main

import (
    "github.com/gogf/gf/v2/os/gres"
    "github.com/gogf/gf/v2/frame/g"
)

func main() {
    // 打包资源文件
    gres.Dump()
    
    // 初始化服务器
    s := g.Server()
    // ...其他配置
    s.Run()
}
```

### 4. 完整示例

下面是一个使用资源文件加载示例数据的完整示例：

```go
package main

import (
    "context"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

type CreateUserReq struct {
    g.Meta  `path:"/users" method:"post" summary:"创建用户"`
    Name    string `json:"name" v:"required" dc:"用户名"`
    Email   string `json:"email" v:"required|email" dc:"电子邮箱"`
}

type CreateUserRes struct {
    g.Meta `status:"201" resEg:"testdata/examples/user/create_success.json"`
    Id     int    `json:"id" dc:"用户ID"`
}

func (r CreateUserRes) EnhanceResponseStatus() map[int]goai.EnhancedStatusType {
    return map[int]goai.EnhancedStatusType{
        400: {
            Response: struct{}{},
            // 从文件中加载错误示例
        },
        500: {
            Response: struct{}{},
            // 从文件中加载错误示例
        },
    }
}

type Controller struct{}

func (c *Controller) CreateUser(ctx context.Context, req *CreateUserReq) (res *CreateUserRes, err error) {
    // 实际业务逻辑
    return &CreateUserRes{Id: 1}, nil
}

func main() {
    s := g.Server()
    s.Group("/", func(group *ghttp.RouterGroup) {
        group.Bind(new(Controller))
    })
    s.SetOpenApiPath("/api.json")
    s.SetSwaggerPath("/swagger")
    s.Run()
}
```

其中`testdata/examples/user/create_success.json`文件内容可能是：

```json
{
  "成功示例": {
    "code": 0,
    "message": "创建成功",
    "data": {
      "id": 1
    }
  }
}
```

这种方式可以使示例数据与代码分离，更容易维护和管理。

## 九、总结

`GoFrame`的 `IEnhanceResponseStatus` 接口提供了一种灵活、强大的方式来扩展 `OpenAPIv3`接口文档中的响应信息。通过实现该接口，开发者可以：

1. 为`API`提供多种响应状态的文档，使文档更符合`RESTful API`设计规范。
2. 自定义不同状态码的响应结构体，提供更精确的接口定义。
3. 通过示例数据展示不同状态的响应格式，便于前端开发者理解和处理。
4. 保持文档与代码的一致性，提高开发效率和协作质量。

通过合理使用 `IEnhanceResponseStatus` 接口，可以显著提升`API`文档的质量和完整性，为前后端开发者提供更好的开发体验。