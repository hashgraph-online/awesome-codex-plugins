大部分场景下，通过 `gsession` 组件内置提供的常见 `Storage` 实现已经能够满足需求。如果有特殊的场景需要制定不易开发 `Storage` 当然也是支持的，因为 `gsession` 的功能都采用了接口化设计。

## Storage定义

[https://github.com/gogf/gf/blob/master/os/gsession/gsession\_storage.go](https://github.com/gogf/gf/blob/master/os/gsession/gsession_storage.go)

```go
// Storage is the interface definition for session storage.
type Storage interface {
    // New creates a custom session id.
    // This function can be used for custom session creation.
    New(ctx context.Context, ttl time.Duration) (id string, err error)

    // Get retrieves and returns session value with given key.
    // It returns nil if the key does not exist in the session.
    Get(ctx context.Context, id string, key string) (value interface{}, err error)

    // GetMap retrieves all key-value pairs as map from storage.
    GetMap(ctx context.Context, id string) (data map[string]interface{}, err error)

    // GetSize retrieves and returns the size of key-value pairs from storage.
    GetSize(ctx context.Context, id string) (size int, err error)

    // Set sets one key-value session pair to the storage.
    // The parameter `ttl` specifies the TTL for the session id.
    Set(ctx context.Context, id string, key string, value interface{}, ttl time.Duration) error

    // SetMap batch sets key-value session pairs as map to the storage.
    // The parameter `ttl` specifies the TTL for the session id.
    SetMap(ctx context.Context, id string, data map[string]interface{}, ttl time.Duration) error

    // Remove deletes key with its value from storage.
    Remove(ctx context.Context, id string, key string) error

    // RemoveAll deletes all key-value pairs from storage.
    RemoveAll(ctx context.Context, id string) error

    // GetSession returns the session data as `*gmap.StrAnyMap` for given session id from storage.
    //
    // The parameter `ttl` specifies the TTL for this session.
    // The parameter `data` is the current old session data stored in memory,
    // and for some storage it might be nil if memory storage is disabled.
    //
    // This function is called ever when session starts. It returns nil if the TTL is exceeded.
    GetSession(ctx context.Context, id string, ttl time.Duration, data *gmap.StrAnyMap) (*gmap.StrAnyMap, error)

    // SetSession updates the data for specified session id.
    // This function is called ever after session, which is changed dirty, is closed.
    // This copy all session data map from memory to storage.
    SetSession(ctx context.Context, id string, data *gmap.StrAnyMap, ttl time.Duration) error

    // UpdateTTL updates the TTL for specified session id.
    // This function is called ever after session, which is not dirty, is closed.
    UpdateTTL(ctx context.Context, id string, ttl time.Duration) error
}
```

每一个方法的调用时机都在注释中详细介绍了，开发者在实现自定义的 `Storage` 时，可以充分参考内置的几种 `Storage` 实现。

## 注意事项

- `Storage` 接口中，并不是所有的接口方法都需要实现，开发者仅需要根据业务需要，实现特定调用时机的一些接口即可。
- 为了提高 `Session` 的执行性能，接口有 `gmap.StrAnyMap` 容器类型的使用，开发时可以参考一下章节： [字典类型-gmap](../../组件列表/数据结构/字典类型-gmap/字典类型-gmap.md)