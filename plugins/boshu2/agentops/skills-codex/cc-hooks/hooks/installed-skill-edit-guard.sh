#!/usr/bin/env bash
# installed-skill-edit-guard (PreToolUse / Edit|Write)
# age-workflow-guardrail-hooks-j39.1 — route Edit/Write of an INSTALLED skill copy
# back to the repo source of truth.
#
# The mistake-token: an Edit/Write whose target path is under */.claude/skills/**
# (or .codex/skills, .gemini/skills) has NO legitimate form — those are the
# installed / symlinked copies (overwritten on install; symlinks through to the
# factory checkout). The source of truth is skills/<name>/ in the agentops repo.
#
# Reversible footgun -> ROUTE, not hard-block: exit 2 + a one-line stderr redirect.
#
# Context-budget discipline (hooks are powerful but pollute context — use sparingly):
#   - SILENT on the happy path: any other file_path -> exit 0, zero stdout/stderr.
#   - Fires its one redirect ONLY on an installed-skill-copy edit, at most ONCE
#     per session (sentinel-gated) so it never repeats.
#   - NEVER emits stray stdout on an exit-0 PreToolUse path (stdout there is
#     parsed as JSON). Block via exit 2 + stderr only.
set -uo pipefail

input="$(cat)"
path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""')"
sid="$(printf '%s' "$input" | jq -r '.session_id // "nosession"')"

# Match ONLY the file_path: an Edit/Write target under an installed skills dir.
# We match the path segment `.claude/skills/` (or .codex/.gemini) anywhere in the
# path so ~, $HOME, and absolute /Users/*/.claude/skills/** all hit. We match the
# file_path field only — a repo doc whose BODY mentions "claude/skills" lands in
# tool_input.content, never file_path, so prose can never fire this guard.
case "$path" in
  */.claude/skills/*|*/.codex/skills/*|*/.gemini/skills/*)
    : # installed skill copy -> fire
    ;;
  *)
    exit 0  # repo skills/**, any other path -> SILENT happy path
    ;;
esac

dir="${TMPDIR:-/tmp}/claude-installed-skill-edit-guard"
sentinel="$dir/${sid//\//_}"
[ -f "$sentinel" ] && exit 0   # already redirected this session

mkdir -p "$dir" 2>/dev/null || true
: > "$sentinel" 2>/dev/null || true

# Derive the repo-relative target so the redirect is actionable.
name="$(printf '%s' "$path" | sed -n 's#.*/\.\(claude\|codex\|gemini\)/skills/\([^/]*\)/.*#\2#p')"
[ -n "$name" ] || name="$(printf '%s' "$path" | sed -n 's#.*/\.\(claude\|codex\|gemini\)/skills/\([^/]*\)$#\2#p')"
hint="skills/<name>/"
[ -n "$name" ] && hint="skills/${name}/"

# --- value-proof telemetry (age-workflow-guardrail-hooks-j39.2) -------------
# Emit EXACTLY one gate-BLIND JSONL line per FIRE. The metric is the
# fire-ATTEMPT rate over time (a learning signal the redirect itself cannot
# fake) — see references/GUARDRAIL-VALUE-PROOF.md. PRIVACY: never the raw
# command/path — only a SHA-256 hash of the path. Inert until the guard is
# installed (this code only runs when the guard fires). Best-effort: telemetry
# failure must NEVER change the guard's exit behavior.
emit_telemetry() {
  command -v jq >/dev/null 2>&1 || return 0
  # Hash the path (privacy): sha256sum / shasum -a 256 / openssl, first available.
  local h=""
  if command -v sha256sum >/dev/null 2>&1; then
    h="$(printf '%s' "$path" | sha256sum | cut -d' ' -f1)"
  elif command -v shasum >/dev/null 2>&1; then
    h="$(printf '%s' "$path" | shasum -a 256 | cut -d' ' -f1)"
  elif command -v openssl >/dev/null 2>&1; then
    h="$(printf '%s' "$path" | openssl dgst -sha256 | sed 's/^.*= *//')"
  else
    return 0  # no hasher -> emit nothing rather than risk leaking the raw path
  fi
  [ -n "$h" ] || return 0
  local tdir="${AGENTOPS_HOME:-${HOME}/.agentops}"
  local tfile="${AGENTOPS_GUARDRAIL_TELEMETRY:-${tdir}/guardrail-telemetry.jsonl}"
  mkdir -p "$(dirname "$tfile")" 2>/dev/null || return 0
  local line
  line="$(jq -nc \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg session "$sid" \
    --arg token_class "installed-skill-edit" \
    --arg path_sha256 "$h" \
    '{ts:$ts, session:$session, token_class:$token_class, path_sha256:$path_sha256}' \
  )" || return 0
  printf '%s\n' "$line" >> "$tfile" 2>/dev/null || return 0
}
emit_telemetry

cat >&2 <<MSG
⛔ INSTALLED-SKILL EDIT: do not edit installed skill copies.
  ${path}
  is an INSTALLED / symlinked copy — overwritten on install, or symlinked through
  to the factory checkout. Editing it is lost work.
  → Edit ${hint} in the agentops repo (the source of truth) instead.
Fires once per session. Re-run your edit against the repo skills/ path.
MSG
exit 2
