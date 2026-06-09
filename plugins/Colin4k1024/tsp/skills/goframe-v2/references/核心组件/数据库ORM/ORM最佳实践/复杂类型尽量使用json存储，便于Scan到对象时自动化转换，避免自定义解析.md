举一个🌰。假如我们需要实现产品售卖规格列表，其中包含可选择的分片数量、分片容量以及副本数量，如下图（非现网代码，仅供示例学习）：

我们的表设计如下：

```sql
CREATE TABLE `sell_spec` (
    `id`            int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
    `product`       varchar(45) NOT NULL COMMENT '产品名称',
    `resources`     json NOT NULL COMMENT '资源规格(cpu:memory)，例如：["0:0.25", "0:1", "1:2"]',
    `disk_min`      int(10) DEFAULT NULL COMMENT '磁盘最小容量',
    `disk_max`      int(10) DEFAULT NULL COMMENT '磁盘最大容量',
    `disk_step`     int(10) DEFAULT NULL COMMENT '磁盘递增大小',
    `shards`        json NOT NULL COMMENT '分片规格，例如：[1,3,5,8,12,16,24,32,40,48,64,80,96,128]',
    `replicas`      json NOT NULL COMMENT '副本规格，例如：[1,2,3,4,5,6,7,8,9,12]',
    `created_at`    datetime DEFAULT NULL COMMENT '创建时间',
    `updated_at`    datetime DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='售卖规格配置';
```

其中的 `resources, shards, replicas` 我们定义为 `json` 格式，目的是可以存储自定义的资源、分片、副本规格列表（非顺序性）。那么我们的 `go struct` 定义如下：

```go
// SellSpec 是通过GoFrame工具自动生成的数据结构，由工具维护。
type SellSpec struct {
    Id        uint        `description:"主键"`
    Product   string      `description:"产品名称"`
    Resources string      `description:"资源规格(cpu:memory)，例如：[\"0:0.25\", \"0:1\", \"1:2\"]"`
    DiskMin   int         `description:"磁盘最小容量"`
    DiskMax   int         `description:"磁盘最大容量"`
    DiskStep  int         `description:"磁盘递增大小"`
    Shards    string      `description:"分片规格，例如：[1,3,5,8,12,16,24,32,40,48,64,80,96,128]"`
    Replicas  string      `description:"副本规格，例如：[1,2,3,4,5,6,7,8,9,12]"`
    CreatedAt *gtime.Time `description:"创建时间"`
    UpdatedAt *gtime.Time `description:"更新时间"`
}

// SellSpecItem 是扩展entity的自定义数据结构，
// 其中部分字段Resources/Shards/Replicas被覆盖为了数组类型，方便ORM操作时自动进行类型转换。
type SellSpecItem struct {
    entity.SellSpec
    Resources []string `dc:"资源规格"`
    Shards    []int    `dc:"分片规格"`
    Replicas  []int    `dc:"副本规格"`
}
```

那么在程序中我们可以这么来写入和查询数据记录。

数据写入：

```go
_, err = dao.SellSpec.Ctx(ctx).Data(v1.SellSpecItem{
    SellSpec: entity.SellSpec{
        Product:  "redis",
        DiskMin:  50,
        DiskMax:  1000,
        DiskStep: 10,
    },
    Resources: []string{"1:2", "2:4", "4:8"},
    Shards:    []int{1, 3, 5, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96, 128},
    Replicas:  []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 12},
}).Insert()
```

数据查询， `ORM` 组件将会自动地将数据表中的记录转换为 `go struct` 对应的数组类型属性：

```go
var items []v1.SellSpecItem
err = dao.SellSpec.Ctx(ctx).Scan(&items)
```