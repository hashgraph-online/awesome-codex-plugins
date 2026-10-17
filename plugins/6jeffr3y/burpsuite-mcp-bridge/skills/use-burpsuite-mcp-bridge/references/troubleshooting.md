# Troubleshooting

## Bridge unavailable

1. Confirm the extension is loaded and enabled in Burp.
2. Confirm `http://127.0.0.1:9639/health` from the MCP host.
3. Check `BURP_MCP_BRIDGE_URL` and the configured bind address and port.
4. For WSL mirrored networking, prefer loopback. For WSL NAT, verify the configured Windows address and forwarding path.
5. Read the extension Output/Error tabs and the Overview last-error field.

## Pending intercept not visible

1. Confirm the rule is enabled, active, `apply_to="proxy"`, and has not reached `max_matches`.
2. Confirm direction, host, path, method, body, and response status matchers.
3. Confirm `intercept_mode="mcp"`; Burp mode appears in Proxy Intercept instead.
4. Trigger the browser request after creating the rule.
5. Poll before the configured timeout; timeout forwards the original message.

## Too many requests are held

Forward or drop existing pending messages, disable the intercept rule, and narrow host/path/method. Use `max_matches=1` for one-off tests.

## Large response is incomplete

List and detail tools return bounded previews. Use `burp_export_flow_bundle` for the complete raw request and response.
