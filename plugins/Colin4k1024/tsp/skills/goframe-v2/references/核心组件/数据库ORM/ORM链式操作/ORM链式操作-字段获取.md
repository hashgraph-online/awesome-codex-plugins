## `GetFieldsStr/GetFieldsExStr` 字段获取

1. `GetFieldsStr` 用于获取指定表的字段，并可给定字段前缀，字段之间使用" `,`"符号连接成字符串返回；
2. `GetFieldsExStr` 用于获取指定表中例外的字段，并可给定字段前缀，字段之间使用" `,`"符号连接成字符串返回；

### `GetFieldsStr` 示例

1. 假如 `user` 表有4个字段 `uid`, `nickname`, `passport`, `password`。
2. 查询字段
    ```go
    // uid,nickname,passport,password
    g.Model("user").GetFieldsStr()
    ```

3. 查询字段给指定前缀
    ```go
    // gf_uid,gf_nickname,gf_passport,gf_password
    g.Model("user").GetFieldsStr("gf_")
    ```

### `GetFieldsExStr` 示例

1. 假如 `user` 表有4个字段 `uid`, `nickname`, `passport`, `password`。
2. 查询字段排除
    ```go
    // uid,nickname
    g.Model("user").GetFieldsExStr("passport, password")
    ```

3. 查询字段排除并给定前缀
    ```go
    // gf_uid,gf_nickname
    g.Model("user").GetFieldsExStr("passport, password", "gf_")
    ```