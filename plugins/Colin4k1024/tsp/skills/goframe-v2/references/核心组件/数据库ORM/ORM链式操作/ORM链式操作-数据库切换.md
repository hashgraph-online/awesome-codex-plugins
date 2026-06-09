我们知道数据库的配置中有支持对默认数据库的配置，因此 `DB` 对象及 `Model` 对象在初始化的时候已经绑定到了特定的数据库上。运行时切换数据库有几种方案（假如我们的数据库有 `user` 用户数据库和 `order` 订单数据库）：

1. 通过不同的配置分组来实现。这需要在配置文件中配置不同的分组配置，随后在程序中可以通过 `g.DB("分组名称")` 来获取特定数据库的单例对象。
2. 通过运行时 `DB.SetSchema` 方法切换单例对象的数据库，需要注意的是由于修改的是单例对象的数据库配置，因此影响是全局的：
   ```go
   g.DB().SetSchema("user-schema")
   g.DB().SetSchema("order-schema")
   ```

3. 通过链式操作 `Schema` 方法创建 `Schema` 数据库对象，并通过该数据库对象创建模型对象并执行后续链式操作：
   ```go
   g.DB().Schema("user-schema").Model("user").All()
   g.DB().Schema("order-schema").Model("order").All()
   ```

4. 也可以通过链式操作 `Model.Schema` 方法设置当前链式操作对应的数据库，没有设置的情况下使用的是其 `DB` 或者 `TX` 默认连接的数据库：
   ```go
   g.Model("user").Schema("user-schema").All()
   g.Model("order").Schema("order-schema").All()
   ```
   :::tip
   注意两种使用方式的差别，前一种方式来自于 `Schema` 对象创建 `Model` 对象后执行操作；后一种方式是通过修改当前 `Model` 对象操作的数据库名称达到切换数据库的目的。
   :::
5. 此外，假如当前数据库操作配置的用户有权限，那么可以直接通过表名中带数据库名称实现跨域操作，甚至跨域关联查询：
   ```go
   // SELECT * FROM `order`.`order` o LEFT JOIN `user`.`user` u ON (o.uid=u.id) WHERE u.id=1 LIMIT 1
   g.Model("order.order o").LeftJoin("user.user u", "o.uid=u.id").Where("u.id", 1).One()
   ```