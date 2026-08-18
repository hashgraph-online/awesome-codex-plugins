#!/usr/bin/env bats

setup() {
    SKILL_DIR="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
    HELPER="$SKILL_DIR/scripts/mcp-search.py"
    TMP_DIR="$(mktemp -d)"
    MOCK="$TMP_DIR/ms"
    export MOCK_REQUEST_LOG="$TMP_DIR/requests.jsonl"
    export MOCK_PID_LOG="$TMP_DIR/server.pid"

    cat >"$MOCK" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
[[ "${1:-}" == "mcp" && "${2:-}" == "serve" ]]
cat >"$MOCK_REQUEST_LOG"
case "${MOCK_MODE:-success}" in
  success)
    printf '%s\n' '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}'
    printf '%s\n' '{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"{\"query\":\"mock\",\"count\":1,\"results\":[{\"id\":\"cass\",\"score\":9.5}]}"}]}}'
    ;;
  rpc-error)
    printf '%s\n' '{"jsonrpc":"2.0","id":1,"result":{}}'
    printf '%s\n' '{"jsonrpc":"2.0","id":2,"error":{"code":-32603,"message":"search failed"}}'
    ;;
  malformed-outer)
    printf '%s\n' 'not-json'
    ;;
  malformed-inner)
    printf '%s\n' '{"jsonrpc":"2.0","id":1,"result":{}}'
    printf '%s\n' '{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"{not-json"}]}}'
    ;;
  timeout)
    printf '%s\n' "$$" >"$MOCK_PID_LOG"
    trap 'exit 0' TERM INT
    while :; do sleep 1; done
    ;;
esac
EOF
    chmod +x "$MOCK"
}

teardown() {
    rm -rf "$TMP_DIR"
}

@test "prints only the structured MCP search payload" {
    run env MS_BIN="$MOCK" python3 "$HELPER" "find session archaeology"
    [ "$status" -eq 0 ]
    printf '%s' "$output" | jq -e '.count == 1 and .results[0].id == "cass"' >/dev/null
    [[ "$output" != *'"jsonrpc"'* ]]
}

@test "JSON-escapes quotes backslashes and newlines in the query" {
    local query
    query=$'quote " and slash \\ and\nnewline'
    run env MS_BIN="$MOCK" python3 "$HELPER" "$query"
    [ "$status" -eq 0 ]
    run jq -e --arg query "$query" 'select(.id == 2) | .params.arguments.query == $query' "$MOCK_REQUEST_LOG"
    [ "$status" -eq 0 ]
}

@test "fails cleanly on a JSON-RPC error response" {
    run env MS_BIN="$MOCK" MOCK_MODE=rpc-error python3 "$HELPER" "anything"
    [ "$status" -ne 0 ]
    [[ "$output" == *"JSON-RPC error -32603: search failed"* ]]
}

@test "fails cleanly on malformed outer JSON" {
    run env MS_BIN="$MOCK" MOCK_MODE=malformed-outer python3 "$HELPER" "anything"
    [ "$status" -ne 0 ]
    [[ "$output" == *"malformed JSON-RPC line 1"* ]]
}

@test "fails cleanly on malformed nested search JSON" {
    run env MS_BIN="$MOCK" MOCK_MODE=malformed-inner python3 "$HELPER" "anything"
    [ "$status" -ne 0 ]
    [[ "$output" == *"search text is not valid JSON"* ]]
}

@test "timeout kills and reaps the disposable server" {
    run env MS_BIN="$MOCK" MOCK_MODE=timeout python3 "$HELPER" --timeout 0.5 "anything"
    [ "$status" -ne 0 ]
    [[ "$output" == *"server timed out after 0.5s"* ]]
    [ -s "$MOCK_PID_LOG" ]
    run kill -0 "$(cat "$MOCK_PID_LOG")"
    [ "$status" -ne 0 ]
}
