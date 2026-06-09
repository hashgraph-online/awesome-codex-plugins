`ORM` 组件目前支持常见的三种语法的子查询： `Where` 子查询、 `Having` 子查询及 `From` 子查询。

## `Where` 子查询

我们可以在 `Where` 条件中使用子查询语句，示例：

```go
g.Model("orders").Where("amount > ?", g.Model("orders").Fields("AVG(amount)")).Scan(&orders)
// SELECT * FROM "orders" WHERE amount > (SELECT AVG(amount) FROM "orders")
```

## `Having` 子查询

我们可以在 `Having` 条件中使用子查询语句，示例：

```go
subQuery := g.Model("users").Fields("AVG(age)").WhereLike("name", "name%")
g.Model("users").Fields("AVG(age) as avgage").Group("name").Having("AVG(age) > ?", subQuery).Scan(&results)
// SELECT AVG(age) as avgage FROM `users` GROUP BY `name` HAVING AVG(age) > (SELECT AVG(age) FROM `users` WHERE name LIKE "name%")
```

## `From` 子查询

我们可以在使用 `Model` 方法创建模型时使用子查询语句，示例：

```go
g.Model("? as u", g.Model("users").Fields("name", "age")).Where("age", 18).Scan(&users)
// SELECT * FROM (SELECT `name`,`age` FROM `users`) as u WHERE `age` = 18

subQuery1 := g.Model("users").Fields("name")
subQuery2 := g.Model("pets").Fields("name")
g.Model("? as u, ? as p", subQuery1, subQuery2).Scan(&users)
// SELECT * FROM (SELECT `name` FROM `users`) as u, (SELECT `name` FROM `pets`) as p
```