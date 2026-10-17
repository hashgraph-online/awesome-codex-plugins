# Tool recipes

## Logic-focused response intercept

```python
burp_target_overview(host="example.com", focus="logic", sources="all")

burp_rule_upsert(
    direction="response",
    action="intercept",
    intercept_mode="mcp",
    match_host_contains="example.com",
    match_path_contains="/api/decision",
    max_matches=1,
    ttl_seconds=120,
    auto_disable=True,
)

burp_intercept_poll(direction="response", include_bodies=True)

burp_intercept_decide(
    intercept_id="<id>",
    action="replace",
    body_replace_from='"success":false',
    body_replace_to='"success":true',
)
```

## Native Burp intercept

```python
burp_rule_upsert(
    direction="response",
    action="intercept",
    intercept_mode="burp",
    match_host_contains="example.com",
    match_path_contains="/api/login",
    max_matches=1,
    auto_disable=True,
)
```

Edit and forward the message in Proxy Intercept.

## Replay one variable

```python
burp_replay_flow(
    flow_id=123,
    source="history",
    body_replace_from='"documentId":1',
    body_replace_to='"documentId":2',
    include_bodies=True,
)
```

## Selection capture

In Burp, use **Burp MCP Bridge: Capture selection**, then:

```python
burp_selection_poll(limit=20, include_bodies=False)
burp_selection_get(flow_id=7, include_bodies=True, consume=False)
```

Consume the selection only after the workflow no longer needs it.
