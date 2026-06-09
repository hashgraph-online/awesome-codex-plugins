## `*Join`系列方法

1. `LeftJoin` 左关联查询。
2. `RightJoin` 右关联查询。
3. `InnerJoin` 内关联查询。
:::note
其实我们并不推荐使用 `Join` 进行联表查询，特别是在数据量比较大、并发请求量比较高的场景中，容易产生性能问题，也容易提高维护的复杂度。建议您在确定有此必要的场景下使用。
此外，您也可以参考 
[ORM链式操作-模型关联](../ORM%E9%93%BE%E5%BC%8F%E6%93%8D%E4%BD%9C-%E6%A8%A1%E5%9E%8B%E5%85%B3%E8%81%94/%E6%A8%A1%E5%9E%8B%E5%85%B3%E8%81%94-%E5%8A%A8%E6%80%81%E5%85%B3%E8%81%94-ScanList.md) 
章节，数据库只负责存储数据和简单的单表操作，通过 `ORM` 提供的功能在代码层面实现数据聚合。
:::
使用示例：

```go
// 查询符合条件的单条记录(第一条)
// SELECT u.*,ud.site FROM user u LEFT JOIN user_detail ud ON u.uid=ud.uid WHERE u.uid=1 LIMIT 1
g.Model("user u").LeftJoin("user_detail ud", "u.uid=ud.uid").Fields("u.*,ud.site").Where("u.uid", 1).One()

// 查询指定字段值
// SELECT ud.site FROM user u RIGHT JOIN user_detail ud ON u.uid=ud.uid WHERE u.uid=1 LIMIT 1
g.Model("user u").RightJoin("user_detail ud", "u.uid=ud.uid").Fields("ud.site").Where("u.uid", 1).Value()

// 分组及排序
// SELECT u.*,ud.city FROM user u INNER JOIN user_detail ud ON u.uid=ud.uid GROUP BY city ORDER BY register_time asc
g.Model("user u").InnerJoin("user_detail ud", "u.uid=ud.uid").Fields("u.*,ud.city").Group("city").Order("register_time asc").All()

// 不使用join的联表查询
// SELECT u.*,ud.city FROM user u,user_detail ud WHERE u.uid=ud.uid
g.Model("user u,user_detail ud").Where("u.uid=ud.uid").Fields("u.*,ud.city").All()
```

## 自定义数据表别名

```go
// SELECT * FROM `user` AS u LEFT JOIN `user_detail` as ud ON(ud.id=u.id) WHERE u.id=1 LIMIT 1
g.Model("user", "u").LeftJoin("user_detail", "ud", "ud.id=u.id").Where("u.id", 1).One()
g.Model("user").As("u").LeftJoin("user_detail", "ud", "ud.id=u.id").Where("u.id", 1).One()
```

## `*JoinOnFields`系列方法

`LeftJoinOnFields/RightJoinOnFields/InnerJoinOnFields`这三个方法可以指定字段和操作符进行`join`查询，使用示例：

```go
// 查询符合条件的单条记录(第一条)
// SELECT user.*,user_detail.address FROM user LEFT JOIN user_detail ON (user.id = user_detail.uid) WHERE user.id=1 LIMIT 1
g.Model("user").LeftJoinOnFields("user_detail", "id", "=", "uid").Fields("user.*,user_detail.address").Where("id", 1).One()

// 查询多条记录
// SELECT user.*,user_detail.address FROM user RIGHT JOIN user_detail ON (user.id = user_detail.uid)
g.Model("user").RightJoinOnFields("user_detail", "id", "=", "uid").Fields("user.*,user_detail.address").All()
```

## 结合 `dao` 使用示例

```go
// SELECT resource_task_schedule.id,...,time_window.time_window
// FROM `resource_task_schedule`
// LEFT JOIN `time_window` ON (`resource_task_schedule`.`resource_id`=`time_window`.`resource_id`)
// WHERE (time_window.`status`="valid") AND (`time_window`.`start_time` <= 3600)
var (
    orm                = dao.ResourceTaskSchedule.Ctx(ctx)
    tsTable            = dao.ResourceTaskSchedule.Table()
    tsCls              = dao.ResourceTaskSchedule.Columns()
    twTable            = dao.TimeWindow.Table()
    twCls              = dao.TimeWindow.Columns()
    scheduleItems      []scheduleItem
)
orm = orm.FieldsPrefix(tsTable, tsCls)
orm = orm.FieldsPrefix(twTable, twCls.TimeWindow)
orm = orm.LeftJoinOnField(twTable, twCls.ResourceId)
orm = orm.WherePrefix(twTable, twCls.Status, "valid")
orm = orm.WherePrefixLTE(twTable, twCls.StartTime, 3600)
err = orm.Scan(&scheduleItems)
```

```go
// SELECT DISTINCT resource_info.* FROM `resource_info`
// LEFT JOIN `resource_network` ON (`resource_info`.`resource_id`=`resource_network`.`resource_id`)
// WHERE (`resource_info`.`resource_id` like '%10.0.1.3%')
// or (`resource_info`.`resource_name` like '%10.0.1.3%')
// or (`resource_network`.`vip`like '%10.0.1.3%')
// ORDER BY `id` Desc LIMIT 0,2
var (
    orm    = dao.ResourceInfo.Ctx(ctx).OmitEmpty()
    rTable = dao.ResourceInfo.Table()
    rCls   = dao.ResourceInfo.Columns()
    nTable = dao.ResourceNetwork.Table()
    nCls   = dao.ResourceNetwork.Columns()
)
orm = orm.LeftJoinOnField(nTable, rCls.ResourceId)
orm = orm.WherePrefix(rTable, do.ResourceInfo{
    AppId:        req.AppIds,
    ResourceId:   req.ResourceIds,
    Region:       req.Regions,
    Zone:         req.Zones,
    ResourceName: req.ResourceNames,
    Status:       req.Statuses,
    BusinessType: req.Products,
    Engine:       req.Engines,
    Version:      req.Versions,
})
orm = orm.WherePrefix(nTable, do.ResourceNetwork{
    Vip:      req.Vips,
    VpcId:    req.VpcIds,
    SubnetId: req.SubnetIds,
})
// Fuzzy like querying.
if req.Key != "" {
    var (
        keyLike = "%" + req.Key + "%"
    )
    whereFormat := fmt.Sprintf(
        "(`%s`.`%s` like ?) or (`%s`.`%s` like ?) or (`%s`.`%s`like ?) ",
        rTable, rCls.ResourceId,
        rTable, rCls.ResourceName,
        nTable, nCls.Vip,
    )
    orm = orm.Where(whereFormat, keyLike, keyLike, keyLike)
}
// Resource items.
err = orm.Distinct().FieldsPrefix(rTable, "*").Order(req.Order, req.OrderDirection).Limit(req.Offset, req.Limit).Scan(&res.Items)
```