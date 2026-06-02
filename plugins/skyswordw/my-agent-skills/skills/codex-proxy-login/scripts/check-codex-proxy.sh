#!/bin/sh
# Verify the local Codex proxy-login setup WITHOUT printing any secret values.
# Reports presence/absence of the keys that `codex login` tends to wipe.
#
# Usage: sh check-codex-proxy.sh [codex-home]
#   codex-home defaults to ~/.codex

set -eu

CODEX_HOME=${1:-"$HOME/.codex"}
CONFIG="$CODEX_HOME/config.toml"
AUTH="$CODEX_HOME/auth.json"

problems=0

note_ok()   { printf '  ok   %s\n' "$1"; }
note_miss() { printf '  MISS %s\n' "$1"; problems=$((problems + 1)); }

has_key() {
  # has_key <file> <ERE>  -> presence only, never echoes the matched line/value
  grep -Eq "$2" "$1"
}

printf 'config.toml: %s\n' "$CONFIG"
if [ -f "$CONFIG" ]; then
  has_key "$CONFIG" '^[[:space:]]*model_provider[[:space:]]*=' \
    && note_ok 'model_provider set' || note_miss 'model_provider'
  has_key "$CONFIG" '^[[:space:]]*\[model_providers\.' \
    && note_ok 'model_providers block present' || note_miss '[model_providers.*] block'
  has_key "$CONFIG" '^[[:space:]]*experimental_bearer_token[[:space:]]*=[[:space:]]*"..*"' \
    && note_ok 'experimental_bearer_token set (non-empty)' || note_miss 'experimental_bearer_token'
  has_key "$CONFIG" '^[[:space:]]*requires_openai_auth[[:space:]]*=[[:space:]]*true' \
    && note_ok 'requires_openai_auth = true' || note_miss 'requires_openai_auth = true'
  has_key "$CONFIG" '^[[:space:]]*base_url[[:space:]]*=.*v1' \
    && note_ok 'base_url contains /v1' || note_miss 'base_url ending in /v1'
  has_key "$CONFIG" '^[[:space:]]*remote_connections[[:space:]]*=[[:space:]]*true' \
    && note_ok 'remote_connections = true' || note_miss 'remote_connections = true'
  has_key "$CONFIG" '^[[:space:]]*remote_control[[:space:]]*=[[:space:]]*true' \
    && note_ok 'remote_control = true' || note_miss 'remote_control = true'
else
  note_miss 'config.toml not found'
fi

printf 'auth.json:   %s\n' "$AUTH"
if [ -f "$AUTH" ]; then
  has_key "$AUTH" '"auth_mode"[[:space:]]*:[[:space:]]*"chatgpt"' \
    && note_ok 'auth_mode = chatgpt' || note_miss 'auth_mode = chatgpt'
  has_key "$AUTH" '"OPENAI_API_KEY"[[:space:]]*:[[:space:]]*null' \
    && note_ok 'OPENAI_API_KEY = null' || note_miss 'OPENAI_API_KEY = null'
  has_key "$AUTH" '"tokens"[[:space:]]*:[[:space:]]*\{' \
    && note_ok 'tokens object present' || note_miss 'tokens object (run: codex login)'
else
  note_miss 'auth.json not found (run: codex login)'
fi

if [ "$problems" -eq 0 ]; then
  printf '\nAll checks passed. Restart Codex and test one turn.\n'
else
  printf '\n%d issue(s) found. See gotchas in SKILL.md (login rewrites config.toml).\n' "$problems"
  exit 1
fi
