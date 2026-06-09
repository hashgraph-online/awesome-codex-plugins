## 基本介绍
:::warning
需要注意，该特性仅对链式操作有效。
:::
`gdb` 模块支持对数据记录的写入、更新、删除时间自动填充，提高开发维护效率。为了便于时间字段名称、类型的统一维护，如果使用该特性，我们约定：

- 字段的类型可以为时间类型、数字整型或者布尔型，如: `date`, `datetime`, `timestamp`, `int`, `uint`, `big int`, `bool`等。
- 字段的名称支持自定义设置，默认名称约定为：
  - `created_at` 用于记录创建时更新，仅会写入一次。
  - `updated_at` 用于记录修改时更新，每次记录变更时更新。
  - `deleted_at` 用于记录的软删除特性，只有当记录删除时会写入一次。
字段名称不区分大小写，也会忽略特殊字符，例如 `CreatedAt`, `UpdatedAt`, `DeletedAt` 也是支持的。

## 特性配置

时间字段名称可以通过配置文件进行自定义修改，并可使用 `timeMaintainDisabled` 配置在数据库实例上完整关闭该特性。

在配置文件中对应配置项：

```yaml
database:
  default:                      # 分组名称，可自定义，默认为default
    createdAt: "created_at"     # (可选)自动创建时间字段名称
    updatedAt: "updated_time"   # (可选)自动更新时间字段名称
    deletedAt: "is_deleted"     # (可选)软删除时间字段名称
    timeMaintainDisabled: false # (可选)是否完全关闭时间更新特性，为true时CreatedAt/UpdatedAt/DeletedAt都将失效
```

:::tip
特别是针对历史项目，本身已经存在不一样的时间字段名称时，可以通过配置项灵活配置时间字段名称。
:::

完整的数据库配置请参考 [ORM使用配置](../../ORM使用配置/ORM使用配置.md) 章节。

## 特性启用

当数据表包含 `created_at`、 `updated_at`、 `deleted_at` 任意一个或多个字段时，或者包含配置文件中对应的配置字段时，该特性自动启用。

## 相关文档