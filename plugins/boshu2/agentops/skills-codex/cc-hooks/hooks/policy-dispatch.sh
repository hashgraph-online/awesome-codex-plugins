#!/usr/bin/env bash
# policy-dispatch.sh — ONE PreToolUse dispatcher over a policies-as-data registry
# (age-bhsz / epic age-4qw1: admission control — the membrane at tool-call altitude).
#
# Reads the PreToolUse JSON once from stdin, evaluates every applicable policy
# from the registry, and emits one decision:
#   deny  -> exit 2 + route message on stderr (blocks the tool call)
#   route -> exit 0 + permissionDecision:"ask" JSON on stdout (surfaces a dialog)
#   audit -> exit 0, silent; the fire is only recorded in telemetry
# Happy path: exit 0, ZERO output (stray stdout on exit-0 is parsed as JSON by
# the harness and breaks the tool call — see skills/cc-hooks/SKILL.md).
#
# Predicate discipline (the #511 anti-lesson, schema-enforced by
# scripts/lint-policies.sh + schemas/hooks-manifest.v2.schema.json): predicates
# are SYNTACTIC mistake-tokens only — pure regex over tool_input.command or
# tool_input.file_path. Policies with predicate_class other than "pure" are
# structurally barred from deny/route until promoted from audit.
#
# Registry resolution order: $AOP_POLICIES, then policies.json beside this
# script (installed layout), then ../policies/policies.json (repo layout).
#
# Waivers: AOP_WAIVE="id1,id2" env (one-shot), or a waiver file
# ($AGENTOPS_HOME/policy-waivers, default ~/.agents/ao/policy-waivers) with
# lines "<policy-id> <expiry-unix-epoch>".
#
# Telemetry: one JSONL line per fire (deny, route, audit, waived) appended to
# $AGENTOPS_GUARDRAIL_TELEMETRY (default $AGENTOPS_HOME/guardrail-telemetry.jsonl,
# AGENTOPS_HOME defaulting to ~/.agents/ao). Schema is a superset of the
# installed-skill-edit-guard line: {ts, session, token_class, path_sha256} plus
# {mode, decision}. The matched value is hashed, never stored raw. Telemetry
# failure never changes the exit decision.
set -uo pipefail

# shellcheck disable=SC1007  # CDPATH= scopes an empty CDPATH to the cd, intentionally
script_dir="$(CDPATH= cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

registry="${AOP_POLICIES:-}"
if [ -z "$registry" ]; then
  if [ -f "${script_dir}/policies.json" ]; then
    registry="${script_dir}/policies.json"
  else
    registry="${script_dir}/../policies/policies.json"
  fi
fi
# Fail OPEN if the registry or jq is unavailable: an admission layer that
# bricks every tool call on a missing file is worse than no layer (dcg
# precedent: fail-open on timeout).
command -v jq >/dev/null 2>&1 || exit 0
[ -f "$registry" ] || exit 0

input="$(cat)"
# 2>/dev/null: malformed stdin must be FULLY silent (fail open), not leak jq
# parse errors to stderr (validator finding F3, 2026-07-20).
tool="$(printf '%s' "$input" | jq -r '.tool_name // ""' 2>/dev/null)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""' 2>/dev/null)"
fpath="$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""' 2>/dev/null)"
sid="$(printf '%s' "$input" | jq -r '.session_id // "nosession"' 2>/dev/null)"
[ -n "$tool" ] || exit 0

hash_value() {
  # SHA-256 of $1 for telemetry privacy; empty string when no hasher exists.
  if command -v sha256sum >/dev/null 2>&1; then
    printf '%s' "$1" | sha256sum | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then
    printf '%s' "$1" | shasum -a 256 | cut -d' ' -f1
  elif command -v openssl >/dev/null 2>&1; then
    printf '%s' "$1" | openssl dgst -sha256 | sed 's/^.*= *//'
  fi
}

emit_telemetry() {
  # $1 policy id, $2 mode, $3 decision, $4 matched value
  local h
  h="$(hash_value "$4")"
  [ -n "$h" ] || return 0
  local tdir="${AGENTOPS_HOME:-${HOME}/.agents/ao}"
  local tfile="${AGENTOPS_GUARDRAIL_TELEMETRY:-${tdir}/guardrail-telemetry.jsonl}"
  mkdir -p "$(dirname "$tfile")" 2>/dev/null || return 0
  local line
  line="$(jq -nc \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg session "$sid" \
    --arg token_class "$1" \
    --arg path_sha256 "$h" \
    --arg mode "$2" \
    --arg decision "$3" \
    '{ts:$ts, session:$session, token_class:$token_class, path_sha256:$path_sha256, mode:$mode, decision:$decision}' \
  )" || return 0
  printf '%s\n' "$line" >> "$tfile" 2>/dev/null || return 0
}

waived() {
  # $1 policy id -> 0 when a waiver applies.
  case ",${AOP_WAIVE:-}," in
    *",$1,"*) return 0 ;;
  esac
  local wfile="${AOP_WAIVER_FILE:-${AGENTOPS_HOME:-${HOME}/.agents/ao}/policy-waivers}"
  [ -f "$wfile" ] || return 1
  local now id expiry
  now="$(date +%s)"
  while read -r id expiry _; do
    [ "$id" = "$1" ] || continue
    case "$expiry" in (*[!0-9]*|'') continue ;; esac
    [ "$expiry" -gt "$now" ] && return 0
  done < "$wfile"
  return 1
}

deny_id=""; deny_msg=""; deny_val=""
route_id=""; route_msg=""; route_val=""

# Iterate matchers flattened as unit-separator-joined fields:
# id / mode / field / pattern / route_message. NOT @tsv — TSV escaping mangles
# backslashes inside regex patterns (\. arrives as \\.), silently breaking
# every pattern that escapes a metacharacter.
while IFS=$'\x1f' read -r pid pmode pfield ppattern pmsg; do
  [ -n "$pid" ] || continue
  case "$pfield" in
    command)   val="$cmd" ;;
    file_path) val="$fpath" ;;
    *) continue ;;
  esac
  [ -n "$val" ] || continue
  printf '%s' "$val" | grep -qE "$ppattern" || continue
  if waived "$pid"; then
    emit_telemetry "$pid" "$pmode" "waived" "$val"
    continue
  fi
  case "$pmode" in
    deny)
      if [ -z "$deny_id" ]; then deny_id="$pid"; deny_msg="$pmsg"; deny_val="$val"; fi
      ;;
    route)
      if [ -z "$route_id" ]; then route_id="$pid"; route_msg="$pmsg"; route_val="$val"; fi
      ;;
    audit)
      emit_telemetry "$pid" "audit" "audit" "$val"
      ;;
  esac
done < <(jq -r --arg tool "$tool" '
  .policies[]
  | . as $p
  | .matchers[]
  | select(.tools | index($tool))
  | [$p.id, $p.mode, .field, .pattern, ($p.route_message // "")]
  | join("")
' "$registry" 2>/dev/null)

if [ -n "$deny_id" ]; then
  emit_telemetry "$deny_id" "deny" "deny" "$deny_val"
  sdir="${TMPDIR:-/tmp}/aop-policy-dispatch"
  sentinel="${sdir}/${sid//\//_}-${deny_id//[^a-zA-Z0-9]/_}"
  if [ -f "$sentinel" ]; then
    printf '⛔ policy %s: blocked (reason shown earlier this session).\n' "$deny_id" >&2
  else
    mkdir -p "$sdir" 2>/dev/null || true
    : > "$sentinel" 2>/dev/null || true
    printf '⛔ policy %s\n%s\n' "$deny_id" "$deny_msg" >&2
  fi
  exit 2
fi

if [ -n "$route_id" ]; then
  emit_telemetry "$route_id" "route" "ask" "$route_val"
  jq -nc --arg reason "policy ${route_id}: ${route_msg}" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse", permissionDecision:"ask", permissionDecisionReason:$reason}}'
  exit 0
fi

exit 0
