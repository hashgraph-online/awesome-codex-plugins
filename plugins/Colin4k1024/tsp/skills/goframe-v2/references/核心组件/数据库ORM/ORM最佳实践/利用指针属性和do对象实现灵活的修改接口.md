大家都知道框架自带的开发工具可以生成 `do` 对象代码，该 `do` 对象主要用于查询、修改、写入等操作时对操作字段的自动 `nil` 过滤。

今天教给大家一个新的玩法，通过指针结合 `do` 对象快速实现灵活、便捷的修改操作 `API` 实现。

## 数据结构

以下是我们使用的用户表数据结构：

```sql
CREATE TABLE `user`(
    `id`        int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `passport`  varchar(32) NOT NULL COMMENT '账号',
    `password`  varchar(32) NOT NULL COMMENT '密码',
    `nickname`  varchar(32) NOT NULL COMMENT '昵称',
    `status`    varchar(32) NOT NULL COMMENT '状态',
    `brief`     varchar(512) NOT NULL COMMENT '备注信息',
    `create_at` datetime DEFAULT NULL COMMENT '创建时间',
    `update_at` datetime DEFAULT NULL COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_passport` (`passport`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

其中的用户状态，我们使用了单独的类型定义，用以实现枚举值：

```go
type Status string

const (
    StatusEnabled  Status = "enabled"
    StatusDisabled Status = "disabled"
)
```

通过 `gf gen dao` 命令，我们自动生成的 `do` 对象如下：

```go
type User struct {
    g.Meta    `table:"user" orm:"do:true"`
    Id        interface{}
    Passport  interface{}
    Password  interface{}
    Nickname  interface{}
    Status    interface{}
    Brief     interface{}
    CreatedAt interface{}
    UpdatedAt interface{}
}
```

## 请求API定义

我们来实现一个用户信息修改的 `API` 接口，这是一个运维管理接口，可以通过用户账号名称来修改用户信息。该 `API` 的定义如下：

```go
type UpdateReq struct {
    g.Meta   `path:"/user/{Id}" method:"post" summary:"修改用户信息"`
    Passport string  `v:"required" dc:"用户账号"`
    Password *string `dc:"修改用户密码"`
    Nickname *string `dc:"修改用户昵称"`
    Status   *Status `dc:"修改用户状态"`
    Brief    *string `dc:"修改用户描述"`
}
```

其中，用户的可修改信息为密码、昵称、状态和描述，可能同时修改一项或者多项。这里使用了 **指针类型** 的属性参数， **用于实现：当传递该参数时执行修改，不传递时不修改。**

## 业务逻辑实现

为了简化实例，我们这里直接在控制器中将指针参数传递给 `do` 对象。我们知道当调用端没有传递该参数时，该参数为 `nil`，那么传递给 `do` 对象的字段时，仍然是 `nil`，这个时候执行数据库更新操作时， `do` 对象中的 `nil` 字段将会被自动过滤掉。

```go
func (c *Controller) Update(ctx context.Context, req *v1.UpdateReq) (res *v1.UpdateRes, err error) {
    _, err = dao.User.Ctx(ctx).Data(do.User{
        Password: req.Password,
        Nickname: req.Nickname,
        Status:   req.Status,
        Brief:    req.Brief,
    }).Where(do.User{
        Passport: req.Passport,
    }).Update()
    return
}
```