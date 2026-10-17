---
name: goframe-v2
description: GoFrame development skill. TRIGGER when writing/modifying Go files, implementing services, creating APIs, or database operations. DO NOT TRIGGER for frontend/shell scripts.
license: Apache-2.0
---

# Critical Conventions

## Project Development Standards
- For complete projects (HTTP/microservices), install GoFrame CLI and use `gf init` to create project scaffolding. See [Project Creation - init](./references/开发工具/项目创建-init.md) for details.
- Auto-generated code files (dao, do, entity) MUST NOT be manually created or modified per GoFrame conventions.
- Unless explicitly requested, do NOT use the `logic/` directory for business logic. Implement business logic directly in the `service/` directory.
- Reference complete project examples:
  - HTTP service best practice: [user-http-service](./examples/practices/user-http-service)
  - gRPC service best practice: [user-grpc-service](./examples/practices/user-grpc-service)

## Component Usage Standards
- Before creating new methods or variables, check if they already exist elsewhere and reuse existing implementations.
- Use the `gerror` component for all error handling to ensure complete stack traces for traceability.
- When exploring new components, prioritize GoFrame built-in components and reference best practice code from examples.
- **Database Operations MUST use DO objects** (`internal/model/do/`), never `g.Map` or `map[string]interface{}`. DO struct fields are `interface{}`; unset fields remain `nil` and are automatically ignored by the ORM:
  ```go
  // Good - use DO object
  dao.Users.Ctx(ctx).Where(cols.Id, id).Data(do.User{Uid: uid}).Update()

  // Good - conditional fields, unset fields are nil and ignored
  data := do.User{}
  if password != "" { data.PasswordHash = hash }
  if isAdmin != nil { data.IsAdmin = *isAdmin }
  dao.Users.Ctx(ctx).Where(cols.Id, id).Data(data).Update()

  // Good - explicitly set a column to NULL using gdb.Raw
  dao.Instances.Ctx(ctx).Where(cols.Id, id).Data(do.Instance{IdleSince: gdb.Raw("NULL")}).Update()

  // Bad - never use g.Map for database operations
  dao.Users.Ctx(ctx).Data(g.Map{cols.Uid: uid}).Update()
  ```
## Code Style Standards
- **Variable Declarations**: When defining multiple variables, use a `var` block to group them for better alignment and readability:
  ```go
  // Good - aligned and clean
  var (
      authSvc       *auth.Service
      bizCtxSvc     *bizctx.Service
      k8sSvc        *svcK8s.Service
      notebookSvc   *notebook.Service
      middlewareSvc *middleware.Service
  )

  // Avoid - scattered declarations
  authSvc := auth.New()
  bizCtxSvc := bizctx.New()
  k8sSvc := svcK8s.New()
  ```
- Apply this pattern when you have 3 or more related variable declarations in the same scope.

## Soft Delete & Time Maintenance

GoFrame provides **automatic** soft delete and time maintenance features. When a table contains `created_at`, `updated_at`, or `deleted_at` fields, the ORM handles these automatically.

### Automatic Time Fields

| Field | Auto Behavior |
|-------|---------------|
| `created_at` | Auto-written on `Insert/InsertAndGetId`, never modified afterward |
| `updated_at` | Auto-written on `Insert/Update/Save` |
| `deleted_at` | Auto-written on `Delete` (soft delete), auto-filtered on queries |

### Critical Rules

**1. NEVER manually set time fields** - GoFrame handles these automatically:
```go
// WRONG - redundant manual time setting
dao.User.Ctx(ctx).Data(do.User{
    Name:      "john",
    CreatedAt: gtime.Now(),  // REDUNDANT! Framework handles this
    UpdatedAt: gtime.Now(),  // REDUNDANT! Framework handles this
}).Insert()

// CORRECT - let framework handle time fields
dao.User.Ctx(ctx).Data(do.User{
    Name: "john",
}).Insert()
```

**2. NEVER manually add `WhereNull(cols.DeletedAt)`** - GoFrame auto-adds soft delete filter:
```go
// WRONG - redundant soft delete condition
dao.User.Ctx(ctx).
    Where(do.User{Status: 1}).
    WhereNull(cols.DeletedAt).  // REDUNDANT! Framework auto-adds this
    Scan(&list)

// CORRECT - framework auto-adds deleted_at IS NULL
dao.User.Ctx(ctx).
    Where(do.User{Status: 1}).
    Scan(&list)
```

**3. Use `Delete()` for soft delete** - Framework converts to `UPDATE SET deleted_at = NOW()`:
```go
// CORRECT - use Delete(), framework handles soft delete
dao.User.Ctx(ctx).Where(do.User{Id: id}).Delete()
// Actual SQL: UPDATE `sys_user` SET `deleted_at`=NOW() WHERE `id`=?

// WRONG - manual Update with deleted_at
dao.User.Ctx(ctx).
    Where(do.User{Id: id}).
    Data(do.User{DeletedAt: gtime.Now()}).  // REDUNDANT!
    Update()
```

### Field Type Support

The `deleted_at` field supports multiple types:
- **DateTime/Timestamp**: Default, stores deletion time
- **Integer**: Stores Unix timestamp (seconds)
- **Boolean**: Stores 0/1 for deleted state

### Configuration (Optional)

Time field names can be customized in `config.yaml`:
```yaml
database:
  default:
    createdAt: "created_at"   # Custom field name
    updatedAt: "updated_at"
    deletedAt: "deleted_at"
    timeMaintainDisabled: false  # Set true to disable this feature
```

# GoFrame Documentation
Complete GoFrame development resources covering component design, usage, best practices, and considerations: [GoFrame Documentation](./references/README.MD)

# GoFrame Code Examples
Rich practical code examples covering HTTP services, gRPC services, and various project types: [GoFrame Examples](./examples/README.MD)