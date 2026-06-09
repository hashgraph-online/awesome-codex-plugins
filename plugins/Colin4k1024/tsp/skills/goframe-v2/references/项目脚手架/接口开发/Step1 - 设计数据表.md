## 设计数据表

我们先定义一个数据表，以下是本章节示例会用到的数据表`SQL`文件：

```sql
CREATE TABLE `user` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'user id',
  `name` varchar(45) DEFAULT NULL COMMENT 'user name',
  `status` tinyint DEFAULT NULL COMMENT 'user status',
  `age` tinyint unsigned DEFAULT NULL COMMENT 'user age',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

## 应用数据表

我们需要把这个数据表应用到`mysql`数据库中，便于后续的使用。如果你本地没有`mysql`数据库服务，那么这里使用`docker`运行一个吧：

```bash
docker run -d --name mysql \
 -p 3306:3306 \
 -e MYSQL_DATABASE=test \
 -e MYSQL_ROOT_PASSWORD=12345678 \
 loads/mysql:5.7
```

启动后，连接数据库，将数据表创建`sql`语句应用进去：
```text
$ mysql -h 127.0.0.1 -P 3306 -u root -p
mysql: [Warning] Using a password on the command line interface can be insecure.
Enter password: 
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 57
Server version: 9.0.1 Homebrew

Copyright (c) 2000, 2024, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> use test;
Database changed
mysql> CREATE TABLE `user` (
    ->   `id` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'user id',
    ->   `name` varchar(45) DEFAULT NULL COMMENT 'user name',
    ->   `status` tinyint DEFAULT NULL COMMENT 'user status',
    ->   `age` tinyint unsigned DEFAULT NULL COMMENT 'user age',
    ->   PRIMARY KEY (`id`)
    -> ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
Query OK, 0 rows affected, 2 warnings (0.02 sec)

mysql> 
```

## 学习小结

在接口开发之前先设计数据库表是比较好的开发习惯。这里我们使用的是`mysql`数据库，是需要先搭建/运行数据库服务。

在设计完成数据库表后，我们下一步可以使用脚手架工具自动去生成对应的数据库操作相关文件。