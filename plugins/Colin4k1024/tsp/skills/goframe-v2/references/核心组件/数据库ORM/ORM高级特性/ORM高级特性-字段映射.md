## 基本介绍

在对数据进行写入、更新使用诸如 `Fields/Data/Scan` 方法时，如果给定的参数为 `map/struct` 类型，给定参数的键名/属性名称将会自动按照忽略大小写及特殊字符的方式与数据表的字段进行自动识别映射。
:::tip
这也是为什么使用数据库组件执行数据库操作时会出现 ``SHOW FULL COLUMNS FROM `xxx` `` 语句的原因，该语句每张表只会执行一次，随后缓存结果到内存。
:::
匹配规则的示例：

```html
Map键名     字段名称     是否匹配
nickname   nickname      match
NICKNAME   nickname      match
Nick-Name  nickname      match
nick_name  nickname      match
nick name  nickname      match
NickName   nickname      match
Nick-name  nickname      match
nick_name  nickname      match
nick name  nickname      match
```

## 重要说明

### 接口设计

该特性需要依靠 `DB` 中定义的 `TableFields` 接口实现来支持的。如果不实现该接口，那么上层业务需要维护属性/键名到数据表字段的映射关系，维护这种非业务逻辑的工作成本是比较大的。框架的目标是尽可能让业务开发同学的精力聚焦于业务，因此框架组件中能够自动化的地方均采用自动化设计。目前对接到框架的 `driver` 实现均支持该接口。

```go
// TableFields retrieves and returns the fields' information of specified table of current
// schema.
//
// The parameter `link` is optional, if given nil it automatically retrieves a raw sql connection
// as its link to proceed necessary sql query.
//
// Note that it returns a map containing the field name and its corresponding fields.
// As a map is unsorted, the TableField struct has an "Index" field marks its sequence in
// the fields.
//
// It's using cache feature to enhance the performance, which is never expired util the
// process restarts.
func (db DB) TableFields(ctx context.Context, table string, schema ...string) (fields map[string]*TableField, err error)
```

### 字段缓存

每个数据表的字段信息，将在数据表的第一次操作时执行查询并缓存到内存中。如果需要手动刷新字段缓存，那么可以依靠以下方法实现：

```go
// ClearTableFields removes certain cached table fields of current configuration group.
func (c *Core) ClearTableFields(ctx context.Context, table string, schema ...string) (err error)

// ClearTableFieldsAll removes all cached table fields of current configuration group.
func (c *Core) ClearTableFieldsAll(ctx context.Context) (err error)
```

方法介绍如注释。可以看到这两个方法是挂载 `Core` 对象上的，而底层的 `Core` 对象已经通过 `DB` 接口暴露，因此我们这么来获取 `Core` 对象：

```go
g.DB().GetCore()
```

## 使用示例

我们来看一个例子，我们实现一个查询用户基本信息的一个接口，这个用户是一个医生。

1、我们有两张表，一张 `user` 表，大概有 `30` 个字段；一张 `doctor_user` 表，大概有 `80` 多个字段。

2、 `user` 是用户基础表，包含用户的最基础信息； `doctor_user` 是基于 `user` 表的业务扩展表，特定用户角色的表，与 `user` 表是一对一关系。

3、我们有一个 `GRPC` 的接口，接口定义是这样的（为方便演示，这里做了一些简化）：

1） `GetDoctorInfoRes`

```go
// 查询接口返回数据结构
type GetDoctorInfoRes struct {
    UserInfo             *UserInfo   `protobuf:"bytes,1,opt,name=UserInfo,proto3" json:"UserInfo,omitempty"`
    DoctorInfo           *DoctorInfo `protobuf:"bytes,2,opt,name=DoctorInfo,proto3" json:"DoctorInfo,omitempty"`
    XXX_NoUnkeyedLiteral struct{}    `json:"-"`
    XXX_unrecognized     []byte      `json:"-"`
    XXX_sizecache        int32       `json:"-"`
}
```

2） `UserInfo`

```go
// 用户基础信息
type UserInfo struct {
    Id                   uint32   `protobuf:"varint,1,opt,name=id,proto3" json:"id,omitempty"`
    Avatar               string   `protobuf:"bytes,2,opt,name=avatar,proto3" json:"avatar,omitempty"`
    Name                 string   `protobuf:"bytes,3,opt,name=name,proto3" json:"name,omitempty"`
    Sex                  int32    `protobuf:"varint,4,opt,name=sex,proto3" json:"sex,omitempty"`
    XXX_NoUnkeyedLiteral struct{} `json:"-"`
    XXX_unrecognized     []byte   `json:"-"`
    XXX_sizecache        int32    `json:"-"`
}
```

3） `DoctorInfo`

```go
// 医生信息
type DoctorInfo struct {
    Id                   uint32   `protobuf:"varint,1,opt,name=id,proto3" json:"id,omitempty"`
    Name                 string   `protobuf:"bytes,3,opt,name=name,proto3" json:"name,omitempty"`
    Hospital             string   `protobuf:"bytes,4,opt,name=hospital,proto3" json:"hospital,omitempty"`
    Section              string   `protobuf:"bytes,6,opt,name=section,proto3" json:"section,omitempty"`
    Title                string   `protobuf:"bytes,8,opt,name=title,proto3" json:"title,omitempty"`
    XXX_NoUnkeyedLiteral struct{} `json:"-"`
    XXX_unrecognized     []byte   `json:"-"`
    XXX_sizecache        int32    `json:"-"`
}
```

4、查询接口实现代码

```go
// 查询医生信息
func (s *Service) GetDoctorInfo(ctx context.Context, req *pb.GetDoctorInfoReq) (res *pb.GetDoctorInfoRes, err error) {
    // Protobuf返回数据结构
    res = &pb.GetDoctorInfoRes{}
    // 查询医生信息
    // SELECT `id`,`avatar`,`name`,`sex` FROM `user` WHERE `user_id`=xxx
    err = dao.PrimaryDoctorUser.
        Ctx(ctx).
        Fields(res.DoctorInfo).
        Where(dao.PrimaryDoctorUser.Columns.UserId, req.Id).
        Scan(&res.DoctorInfo)
    if err != nil {
        return
    }
    // 查询基础用户信息
    // SELECT `id`,`name`,`hospital`,`section`,`title` FROM `doctor_user` WHERE `id`=xxx
    err = dao.PrimaryUser.
        Ctx(ctx).
        Fields(res.DoctorInfo).
        Where(dao.PrimaryUser.Columns.Id, req.Id).
        Scan(&res.UserInfo)
    return res, err
}
```

当我们调用 `GetDoctorInfo` 执行查询时，将会向数据库发起两条 `SQL` 查询，例如：

```
SELECT `id`,`avatar`,`name`,`sex` FROM `user` WHERE `user_id`=1
SELECT `id`,`name`,`hospital`,`section`,`title` FROM `doctor_user` WHERE `id`=1
```

可以看到：

- 使用 `Fields` 方法时，参数类型为 `struct` 或者 `*struct`， `ORM` 将会自动将 `struct` 的属性名称与数据表的字段名称做自动映射匹配，当映射匹配成功时只会查询特定字段数据，而不存在的属性字段将会被自动过滤。
- 使用 `Scan` 方法时（也可以用 `Struct`/ `Structs`），参数类型为 `*struct` 或者 `**struct`，查询结果将会自动与 `struct` 的属性做自动映射匹配，当映射匹配成功时会自动做转换赋值，否则不会对参数的属性做任何处理。