#!/bin/sh
# Repository-local verification for the optional Codex Agents Workflow extension.

set -eu

pass() { printf '%s\n' "PASS: $*"; }
fail() { printf '%s\n' "FAIL: $*" >&2; exit 1; }

run_tests=true
if [ "$#" -gt 0 ]; then
  [ "$#" -eq 1 ] && [ "$1" = --static-only ] \
    || { printf '%s\n' 'Usage: verify-control-plane.sh [--static-only]' >&2; exit 2; }
  run_tests=false
fi

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd) || exit 1
plugin_dir=$(CDPATH= cd "$script_dir/.." && pwd) || exit 1
repo_dir=$(CDPATH= cd "$plugin_dir/../.." && pwd) || exit 1
control=$plugin_dir/control-plane
manifest=$plugin_dir/.codex-plugin/plugin.json
mcp_manifest=$plugin_dir/.mcp.json
marketplace=$repo_dir/.agents/plugins/marketplace.json
config=$control/default-config.json
server=$control/server.mjs
web_app=$control/web/app.js
skill=$plugin_dir/skills/control-plane/SKILL.md
architecture=$plugin_dir/skills/control-plane/references/architecture.md
contracts=$plugin_dir/skills/control-plane/references/provider-contracts.md
ui=$plugin_dir/skills/control-plane/agents/openai.yaml
workflow=$repo_dir/.github/workflows/verify.yml
tutorial=$repo_dir/docs/TUTORIAL.zh-CN.md

for required in \
  "$manifest" "$mcp_manifest" "$marketplace" "$config" "$server" "$skill" "$architecture" \
  "$contracts" "$ui" "$workflow" "$tutorial" \
  "$control/package.json" \
  "$control/open-console.mjs" \
  "$control/connectors/cursor-cdp.mjs" \
  "$control/connectors/cursor-profile.mjs" \
  "$control/connectors/cdp-client.mjs" \
  "$control/connectors/websocket-client.mjs" \
  "$control/connectors/grok-acp.mjs" \
  "$control/connectors/registry.mjs" \
  "$control/connectors/scope-guard.mjs" \
  "$control/connectors/task-store.mjs" \
  "$control/lib/config.mjs" "$control/lib/control.mjs" \
  "$control/lib/providers.mjs" "$control/lib/templates.mjs" \
  "$control/lib/workbench-api.mjs" "$control/lib/mcp-app.mjs" \
  "$plugin_dir/assets/icon.svg" "$plugin_dir/assets/sidebar-icon.svg" \
  "$control/test/connector-integration.test.mjs" \
  "$control/test/open-console.test.mjs" \
  "$control/test/run-tests.mjs" \
  "$control/test/fixtures/fake-cursor.mjs" \
  "$control/test/fixtures/fake-grok.mjs" \
  "$control/web/index.html" "$control/web/app.js" "$control/web/styles.css" \
  "$control/web/app-client.js" "$control/web/workflows-app.html" "$control/web/settings-app.html" \
  "$plugin_dir/scripts/open-control-console.cmd" \
  "$plugin_dir/scripts/open-control-console.sh"; do
  test -f "$required" || fail "required control-plane file missing: $required"
done
pass "control-plane files present"

jq empty "$manifest"
jq empty "$mcp_manifest"
jq empty "$marketplace"
jq empty "$config"
jq empty "$control/package.json"
manifest_version=$(jq -er '.version | select(type == "string" and length > 0)' "$manifest")
package_version=$(jq -er '.version | select(type == "string" and length > 0)' "$control/package.json")
[ "$manifest_version" = "$package_version" ] || fail "plugin manifest and control-plane package versions differ: $manifest_version / $package_version"
[ "$(jq -r '.mcpServers' "$manifest")" = './.mcp.json' ] || fail "plugin manifest does not load control-plane MCP"
[ "$(jq -r '.mcpServers["codex-agents-workflow"].command' "$mcp_manifest")" = node ] || fail "control-plane MCP does not use node"
[ "$(jq -r '.mcpServers["codex-agents-workflow"].enabled' "$mcp_manifest")" = true ] || fail "control-plane MCP is disabled"
[ "$(jq -r '.mcpServers["codex-agents-workflow"].cwd' "$mcp_manifest")" = .. ] || fail "control-plane MCP must launch from its stable installation namespace"
# The suite below probes the packaged MCP with an isolated installation registry.
# check-mcp-startup.mjs remains the diagnostic for a real installed host.
jq -e '.name == "codex-agents-workflow" and (.plugins[] | select(.name == "codex-agents-workflow"))' "$marketplace" >/dev/null || fail "local marketplace still exposes the retired predecessor identity"
jq -e '.mcpServers["codex-agents-workflow"].env_vars | index("CODEX_HOME") and index("USERPROFILE")' "$mcp_manifest" >/dev/null || fail "control-plane MCP does not inherit the global Codex environment"
[ "$(jq -r '.mcpServers["codex-agents-workflow"].default_tools_approval_mode' "$mcp_manifest")" = approve ] || fail "control-plane MCP is not approval-gated"
pass "plugin and MCP manifests are valid"

python3 - "$manifest" "$ui" <<'PY'
import json
from pathlib import Path
import sys
manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for value in manifest["interface"]["defaultPrompt"]:
    if len(value) > 128:
        raise SystemExit(f"manifest defaultPrompt exceeds 128 characters: {len(value)}")
yaml_text = Path(sys.argv[2]).read_text(encoding="utf-8")
line = next(line for line in yaml_text.splitlines() if line.strip().startswith("default_prompt:"))
value = line.split(":", 1)[1].strip().strip('"')
if len(value) > 128:
    raise SystemExit(f"skill default_prompt exceeds 128 characters: {len(value)}")
print("default prompts fit the 128-character host cap")
PY
pass "plugin and skill prompt lengths"

jq -e '.version == 6 and .global.enabled == true and .global.allow_direct_api == false and (.scenarios | not)' "$config" >/dev/null || fail "default global switches or schema are unsafe"
jq -e '[.providers[] | select(.kind != "native_agent") | .enabled] | all(. == false)' "$config" >/dev/null || fail "a non-native provider is enabled by default"
jq -e '[.providers[] | select(.kind == "native_agent") | [.id, .config.model, .config.reasoning_effort]] | sort == ([["native-luna", "gpt-6-luna", "max"], ["native-sol", "gpt-6.1-sol", "high"], ["native-astra", "gpt-6-astra", "medium"]] | sort)' "$config" >/dev/null || fail "native Provider defaults do not match the three model connections"
jq -e '[.providers[] | select(.kind == "native_agent") | (.enabled == true and .config.agent_type == "default" and .config.role == "advisor")] | all' "$config" >/dev/null || fail "native Providers must use the generic Agent connection"
jq -e '.providers[] | select(.id == "cursor-local" and .kind == "builtin_connector" and .enabled == false and .requires_user_approval == false and .capabilities.write == true and .config.connector == "cursor_cdp" and .config.transport == "cdp_ui")' "$config" >/dev/null || fail "built-in Cursor default is missing or unsafe"
jq -e '.providers[] | select(.id == "grok-local" and .kind == "builtin_connector" and .enabled == false and .requires_user_approval == false and .capabilities.write == true and .config.connector == "grok_acp" and .config.transport == "leader_acp_stdio")' "$config" >/dev/null || fail "built-in Grok default is missing or unsafe"
jq -e '[.providers[].requires_user_approval, .task_types[].stages[].requires_user_approval] | all(. == false)' "$config" >/dev/null || fail "bundled approval gates must default off"
jq -e '[.task_types[] | select(.id != "hard-path-web-advice") | select((.id + " " + .name + " " + .description + " " + (.tags | join(" "))) | test("cursor|grok|chatgpt|luna|terra|openai"; "i"))] | length == 0' "$config" >/dev/null || fail "default Task Type metadata is Provider-specific"
jq -e '[.task_types[] | select(.id == "hard-path-web-advice")] | length == 1 and all(.[]; .enabled == false and .name == "GPT reviewer" and .route == "audit" and (.stages | length) == 1 and .stages[0].provider_id == "chatgpt-web-pro" and .stages[0].access == "read_only")' "$config" >/dev/null || fail "optional GPT reviewer must remain disabled and reuse its read-only packet Provider"
jq -e '.task_types[] | select(.id == "bounded-code-change" and .route == "delegate" and (.stages | length) == 1)' "$config" >/dev/null || fail "bounded change is not the delegate default"
jq -e '.task_types[] | select(.id == "judgment-heavy-change" and .route == "delegate" and (.stages | length) == 1)' "$config" >/dev/null || fail "judgment-heavy change must use its single implementation role"
jq -e 'all(.task_types[]; (.route == "solo" and (.stages|length)==0) or (.route == "delegate" and (.stages|length)==1 and .stages[0].id=="implementation" and .stages[0].role=="implementer") or (.route == "audit" and (.stages|length)==1 and .stages[0].id=="review" and .stages[0].role=="reviewer") or (.route == "full" and (.stages|length)==2 and .stages[0].id=="implementation" and .stages[1].id=="review"))' "$config" >/dev/null || fail "Task Type route topology is invalid"
if grep -Eqi '"sk-[A-Za-z0-9_-]{20,}"' "$config"; then fail "default config appears to contain a credential value"; fi
jq -e '.providers[] | select(.kind == "openai_compatible") | .config.api_key_env | test("^[A-Z_][A-Z0-9_]*$")' "$config" >/dev/null || fail "API provider does not use an environment-variable name"
pass "safe Provider defaults and model-independent Task Types"

for phrase in \
  'codex_agents_workflow_status' \
  'codex_agents_workflow_console' \
  'codex_agents_workflow_resolve' \
  'codex_agents_workflow_connector_probe' \
  'codex_agents_workflow_connector_start' \
  'codex_agents_workflow_connector_status' \
  'codex_agents_workflow_connector_control' \
  'codex_agents_workflow_invoke' \
  'Prompt templates, provider endpoints, credential variable names, and console tokens are never returned'; do
  grep -Fq "$phrase" "$server" || fail "server omits required contract: $phrase"
done
grep -Fq 'workflow-review' "$web_app" || fail "console omits the independent review workflow switch"
if grep -Fq 'task-type-route' "$web_app"; then fail "console still exposes an independent route selector"; fi
grep -Fq 'Report the observed error' "$skill" || fail "control-plane skill hides activation failure"
grep -Fq 'workflow_role_templates' "$plugin_dir/skills/orchestration/SKILL.md" || fail "orchestration skill does not read the Workbench Role catalog"
grep -Fq 'Never inject Role instructions into a Workflow node' "$plugin_dir/skills/orchestration/SKILL.md" || fail "orchestration skill overlaps Workflow node prompts"
for phrase in \
  'This is minimization, not a hostile-model secrecy sandbox' \
  'Minimal Cursor connection' \
  'Minimal Grok connection' \
  'unknown_after_restart' \
  'prevented_attempts'; do
  grep -Fq "$phrase" "$architecture" || fail "architecture omits: $phrase"
done
for phrase in \
  'builtin_connector`: Cursor CDP' \
  'builtin_connector`: Grok ACP' \
  'expected_agent_id' \
  'expected_session_id' \
  'outside_paths'; do
  grep -Fq "$phrase" "$contracts" || fail "provider contracts omit: $phrase"
done
grep -Fq 'windows-latest' "$workflow" || fail "CI does not cover Windows"
grep -Fq 'ubuntu-latest' "$workflow" || fail "CI does not cover Linux"
grep -Fq 'connector-protocol-' "$workflow" || fail "CI does not expose connector protocol matrix"
grep -Fq 'macos-latest' "$workflow" || fail "CI does not cover macOS"
for operation in workflow_start workflow_native_next workflow_native_spawned_batch workflow_native_followed_up workflow_reattach_connector; do
  grep -Fq "$operation" "$skill" "$plugin_dir/skills/control-plane/references/native-execution.md" "$plugin_dir/skills/control-plane/references/recovery.md" || fail "execution instructions omit $operation"
done
pass "v7 execution, v6 compatibility, connector contracts, and three-platform CI documented"

node "$script_dir/rebind-workflow-packages.mjs" --check
pass "shipped packages use current built-in Host implementations"

node --check "$server"
node --check "$control/open-console.mjs"
for file in "$control"/lib/*.mjs "$control"/connectors/*.mjs "$control"/web/app.js; do
  node --check "$file"
done
pass "Node syntax"
if [ "$run_tests" = true ]; then
  node "$control/test/run-tests.mjs"
  pass "control-plane tests"
else
  printf '%s\n' 'Static verification requested; control-plane test manifest not run.'
fi

sh -n "$script_dir/verify-control-plane.sh"
pass "verification script syntax"

printf '%s\n' "VERIFY PASSED: Codex Agents Workflow extension checks completed"
