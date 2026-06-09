可以看到，通过项目脚手架工具，很多与项目业务逻辑无关的代码都已经预先生成好，我们只需要关注业务逻辑实现即可。我们接下来看看如何实现`CRUD`具体逻辑吧。

## 创建接口

### 创建逻辑实现
```go title="internal/controller/user/user_v1_create.go"
package user

import (
    "context"

    "demo/api/user/v1"
    "demo/internal/dao"
    "demo/internal/model/do"
)

func (c *ControllerV1) Create(ctx context.Context, req *v1.CreateReq) (res *v1.CreateRes, err error) {
    insertId, err := dao.User.Ctx(ctx).Data(do.User{
        Name:   req.Name,
        Status: v1.StatusOK,
        Age:    req.Age,
    }).InsertAndGetId()
    if err != nil {
        return nil, err
    }
    res = &v1.CreateRes{
        Id: insertId,
    }
    return
}
```
在`Create`实现方法中：
- 我们通过`dao.User`通过`dao`组件操作`user`表。
- 每个`dao`操作都需要传递`ctx`参数，因此我们通过`Ctx(ctx)`方法创建一个`gdb.Model`对象，该对象是框架的模型对象，用于操作特定的数据表。
- 通过`Data`传递需要写入数据表的数据，我们这里使用`do`转换模型对象输入我们的数据。`do`转换模型会自动过滤`nil`数据，并在底层自动转换为对应的数据表字段类型。在绝大部分时候，我们都使用`do`转换模型来给数据库操作对象传递写入/更新参数、查询条件等数据。
- 通过`InsertAndGetId`方法将`Data`的参数写入数据库，并返回新创建的记录主键`id`。

### 参数校验实现

等等，大家可能会问，为什么这里没有校验逻辑呢？因为校验逻辑都已经配置到请求参数对象`CreateReq`上了。还记得前面介绍的`v`标签吗？我们再来看看这个请求参数对象：
```go title="api/user/v1/user.go"
type CreateReq struct {
    g.Meta `path:"/user" method:"put" tags:"User" summary:"Create user"`
    Name   string `v:"required|length:3,10" dc:"user name"`
    Age    uint   `v:"required|between:18,200" dc:"user age"`
}
type CreateRes struct {
    Id int64 `json:"id" dc:"user id"`
}
```
这里的`required/length/between`校验规则在调用路由函数`Create`之前就已经由`GoFrame`框架的`Server`自动执行了。
如果请求参数校验失败，会立即返回错误，不会进入到路由函数。`GoFrame`框架的这种机制极大地简便了开发流程，
开发者在这个路由函数中，仅需要关注业务逻辑实现即可。
:::info
当然，如果有一些额外的、定制化的业务逻辑校验，是需要在路由函数中自行实现的哟。
:::
## 删除接口

```go title="internal/controller/user/user_v1_delete.go"
package user

import (
    "context"

    "demo/api/user/v1"
    "demo/internal/dao"
)

func (c *ControllerV1) Delete(ctx context.Context, req *v1.DeleteReq) (res *v1.DeleteRes, err error) {
    _, err = dao.User.Ctx(ctx).WherePri(req.Id).Delete()
    return
}
```
删除逻辑比较简单，我们这里用到一个`WherePri`方法，该方法会将给定的参数`req.Id`作为主键进行`Where`条件限制。

## 更新接口

```go title="internal/controller/user/user_v1_update.go"
package user

import (
    "context"

    "demo/api/user/v1"
    "demo/internal/dao"
    "demo/internal/model/do"
)

func (c *ControllerV1) Update(ctx context.Context, req *v1.UpdateReq) (res *v1.UpdateRes, err error) {
    _, err = dao.User.Ctx(ctx).Data(do.User{
        Name:   req.Name,
        Status: req.Status,
        Age:    req.Age,
    }).WherePri(req.Id).Update()
    return
}
```
更新接口也比较简单，除了已经介绍过的`WherePri`方法，在更新数据时也需要通过`Data`方法传递更新的数据。

## 查询接口（单个）

```go title="internal/controller/user/user_v1_get_one.go"
package user

import (
    "context"

    "demo/api/user/v1"
    "demo/internal/dao"
)

func (c *ControllerV1) GetOne(ctx context.Context, req *v1.GetOneReq) (res *v1.GetOneRes, err error) {
    res = &v1.GetOneRes{}
    err = dao.User.Ctx(ctx).WherePri(req.Id).Scan(&res.User)
    return
}
```
数据查询接口中，我们使用了`Scan`方法，该方法可以将查询到的单条数据表记录智能地映射到结构体对象上。大家需要注意这里的`&res.User`中的`User`属性对象其实是没有初始化的，其值为`nil`。如果查询到了数据，`Scan`方法会对其做初始化并赋值，如果查询不到数据，那么`Scan`方法什么都不会做，其值还是`nil`。

## 查询接口（列表）

```go title="internal/controller/user/user_v1_get_list.go"
package user

import (
    "context"

    "demo/api/user/v1"
    "demo/internal/dao"
    "demo/internal/model/do"
)

func (c *ControllerV1) GetList(ctx context.Context, req *v1.GetListReq) (res *v1.GetListRes, err error) {
    res = &v1.GetListRes{}
    err = dao.User.Ctx(ctx).Where(do.User{
        Age:    req.Age,
        Status: req.Status,
    }).Scan(&res.List)
    return
}
```
查询列表数据我们同样使用到了`Scan`方法，这个方法是非常强大的。同查询单条数据的逻辑一样，它仅会在查询的数据时才会初始化这里的`&res.List`。

## 学习小结

本章节的示例源码：https://github.com/gogf/quick-demo/tree/main/internal/controller/user

可以看到，使用`GoFrame`数据库`ORM`组件可以非常快速、高效地完成接口开发工作。整个`CRUD`接口开发下来，开发者需要实现的业务逻辑仅需要几行代码😼。

开发效率的提升，除了归功于脚手架工具自动生成的`dao`和`controller`代码之外，强大的数据库`ORM`组件也是功不可没。可以看到，我们在对数据库表进行操作时，代码量非常简洁优雅，但在数据库`ORM`组件的内部设计中，涉及很多精细的设计、严格的代码测试、年复一年的功能迭代的沉淀结果。

接口逻辑开发完了，在下一步，我们需要做一些数据库配置和路由注册的操作，同样也是非常简便，一起看看吧。