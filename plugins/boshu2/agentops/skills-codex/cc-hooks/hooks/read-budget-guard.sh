#!/usr/bin/env bash
# read-budget-guard (PreToolUse / Read|Bash) — policy core.context:unbounded-read
#
# Blocks an UNBOUNDED read of a text file over the line budget (default 350).
# The mistake-token: a Read without a numeric limit, or a Bash cat/head/tail
# whose EFFECTIVE line count exceeds the budget. Every such line lands in this
# context and is re-sent on every later turn; the same rule written into
# CLAUDE.md was advisory and ignored (the Spotify finding), so it lives here as
# a hook that can refuse. A LOOKUP predicate (wc -l on the exact argument), so
# this is a STANDALONE opt-in guard — never a policies.json registry entry
# (the dispatcher accepts pure regex predicates only). Ships INERT: nothing
# wires it until scripts/install-read-budget-guard.sh is run explicitly.
#
# Decision (deny-not-route: EVERY attempt blocks, the guard never self-relaxes):
#   FIRE  -> exit 2 + stderr. First fire in a session: the FULL message (both
#            correct moves — slice it, or delegate to a bulk-reader); later
#            fires in the same session: ONE short line (sentinel-gated).
#   PASS / WAIVED / DISABLED -> exit 0, ZERO stdout, ZERO stderr (stray stdout
#            on an exit-0 PreToolUse path is parsed as JSON by the harness).
#
# PASS by construction (zero false-positive surface): a Read with a numeric
# limit; a file at/below budget; a missing / non-regular / binary path; a Bash
# command containing | < > (a bounded consumer or a file sink); any command
# word other than cat/head/tail; unresolvable tokens ($VAR, globs, backticks);
# quoted text that merely mentions cat (the split is quote-aware).
#
# Env:
#   AOP_READ_BUDGET_LINES     line budget (positive integer; malformed -> 350)
#   AOP_WAIVE                 comma list of waived policy ids (env, or an inline
#                             AOP_WAIVE=<ids> prefix on the Bash command)
#   AOP_WAIVER_FILE           "<id> <expiry-unix-epoch>" lines, same semantics
#                             as policy-dispatch.sh
#   AGENTOPS_HOOKS_DISABLED=1 kill switch: exit 0, silent, no telemetry
#   AGENTOPS_GUARDRAIL_TELEMETRY / AGENTOPS_HOME  telemetry ledger location
#
# Telemetry: exactly one JSONL line per FIRE and per WAIVED call — never on
# pass / disabled / fail-open. The RESOLVED offending path is hashed (SHA-256);
# the raw path and the raw command are never stored. Telemetry failure never
# changes the exit decision.
#
# Fail OPEN: no jq -> exit 0; malformed JSON -> exit 0 silent; empty or unknown
# tool -> exit 0. Portable bash 3.2 + BSD tools: no GNU-only flags, no sed -i,
# no mapfile, no associative arrays; head/tail flags parsed with case.
set -uo pipefail
# Tokens are matched literally: a `*` / `?` / `[` in a command must never be
# expanded against the hook's own cwd.
set -f

# Kill switch: silent, no telemetry, before anything else is touched.
[ "${AGENTOPS_HOOKS_DISABLED:-}" = "1" ] && exit 0

# Fail OPEN if jq is unavailable: a guard that cannot parse its input must
# never brick a tool call.
command -v jq >/dev/null 2>&1 || exit 0

policy_id="core.context:unbounded-read"

input="$(cat)"
# 2>/dev/null: malformed stdin must be FULLY silent (fail open), never leak jq
# parse errors to stderr.
tool="$(printf '%s' "$input" | jq -r '.tool_name // ""' 2>/dev/null)"
[ -n "$tool" ] || exit 0
case "$tool" in Read|Bash) ;; *) exit 0 ;; esac
sid="$(printf '%s' "$input" | jq -r '.session_id // "nosession"' 2>/dev/null)"
[ -n "$sid" ] || sid="nosession"
cwd="$(printf '%s' "$input" | jq -r '.cwd // ""' 2>/dev/null)"
[ -n "$cwd" ] || cwd="$PWD"

# Budget: a positive integer, else the default. Normalized through base-10
# arithmetic so a leading zero can never reach --argjson as invalid JSON.
budget="${AOP_READ_BUDGET_LINES:-350}"
case "$budget" in ''|*[!0-9]*) budget=350 ;; esac
budget=$((10#$budget))
[ "$budget" -gt 0 ] || budget=350

# Set when a leading AOP_WAIVE=<ids> assignment on the Bash command names this
# policy: the WHOLE call is waived.
inline_waived=0

# resolve_path P → absolute path: relative paths resolve against the JSON cwd.
resolve_path() {
  case "$1" in
    /*) printf '%s' "$1" ;;
    \~|\~/*)
      # The shell would expand a leading tilde against HOME; mirror it. With no
      # HOME the token stays literal, is never found, and the read passes.
      if [ -n "${HOME:-}" ]; then printf '%s%s' "$HOME" "${1#\~}"; else printf '%s/%s' "$cwd" "$1"; fi ;;
    *)  printf '%s/%s' "$cwd" "$1" ;;
  esac
}

# is_text_file P → 0 when P is an existing, readable, regular file with no NUL
# byte in its first 8 KiB (the portable binary test: compare the byte count
# with and without NULs stripped).
is_text_file() {
  [ -f "$1" ] && [ -r "$1" ] || return 1
  local all stripped
  all="$(head -c 8192 "$1" 2>/dev/null | wc -c | tr -d ' ')"
  stripped="$(head -c 8192 "$1" 2>/dev/null | tr -d '\000' | wc -c | tr -d ' ')"
  [ "$all" = "$stripped" ]
}

# line_count P → number of newline characters in P (trimmed).
line_count() {
  wc -l < "$1" 2>/dev/null | tr -d ' '
}

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
  # $1 decision (deny|waived), $2 resolved path, $3 effective lines, $4 tool.
  # Best-effort: no hasher -> no line (never leak the raw path); any failure
  # returns 0 so the exit decision is unchanged.
  # No ledger location at all (no HOME, no AGENTOPS_* override) -> no line;
  # never anchor the default at the filesystem root.
  [ -n "${AGENTOPS_GUARDRAIL_TELEMETRY:-}${AGENTOPS_HOME:-}${HOME:-}" ] || return 0
  local h
  h="$(hash_value "$2")"
  [ -n "$h" ] || return 0
  local tdir="${AGENTOPS_HOME:-${HOME:-}/.agents/ao}"
  local tfile="${AGENTOPS_GUARDRAIL_TELEMETRY:-${tdir}/guardrail-telemetry.jsonl}"
  mkdir -p "$(dirname "$tfile")" 2>/dev/null || return 0
  local line
  line="$(jq -nc \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg session "$sid" \
    --arg token_class "$policy_id" \
    --arg path_sha256 "$h" \
    --arg mode "deny" \
    --arg decision "$1" \
    --arg tool "$4" \
    --argjson lines "$3" \
    --argjson budget "$budget" \
    '{ts:$ts, session:$session, token_class:$token_class, path_sha256:$path_sha256, mode:$mode, decision:$decision, tool:$tool, lines:$lines, budget:$budget}' \
    2>/dev/null)" || return 0
  # Braces: a failed redirect is reported by bash BEFORE a trailing 2>/dev/null
  # applies, and an exit-0 path must stay silent.
  { printf '%s\n' "$line" >> "$tfile"; } 2>/dev/null || return 0
}

waived() {
  # 0 when a waiver applies: inline prefix, AOP_WAIVE env, or an unexpired
  # waiver-file entry (same semantics as policy-dispatch.sh).
  [ "$inline_waived" -eq 1 ] && return 0
  case ",${AOP_WAIVE:-}," in
    *",${policy_id},"*) return 0 ;;
  esac
  local wfile="${AOP_WAIVER_FILE:-${AGENTOPS_HOME:-${HOME:-}/.agents/ao}/policy-waivers}"
  [ -f "$wfile" ] || return 1
  local now id expiry
  now="$(date +%s)"
  while read -r id expiry _; do
    [ "$id" = "$policy_id" ] || continue
    case "$expiry" in (*[!0-9]*|'') continue ;; esac
    [ "$expiry" -gt "$now" ] && return 0
  done < "$wfile"
  return 1
}

fire() {
  # $1 resolved path, $2 effective lines, $3 tool. Never returns.
  if waived; then
    emit_telemetry "waived" "$1" "$2" "$3"
    exit 0
  fi
  emit_telemetry "deny" "$1" "$2" "$3"
  local sdir="${TMPDIR:-/tmp}/aop-read-budget-guard"
  local sentinel="${sdir}/${sid//\//_}"
  if [ -f "$sentinel" ]; then
    printf '⛔ policy %s: %s is %s lines (budget %s) — slice it (offset+limit / sed -n) or delegate to bulk-reader (full reason shown earlier this session).\n' \
      "$policy_id" "$1" "$2" "$budget" >&2
    exit 2
  fi
  mkdir -p "$sdir" 2>/dev/null || true
  { : > "$sentinel"; } 2>/dev/null || true
  cat >&2 <<MSG
⛔ policy ${policy_id}
$1 is $2 lines (budget ${budget}). An unbounded read puts every line into this context and re-sends it on every later turn.
→ Read a slice: Read(file_path, offset, limit) with limit ≤ ${budget}, or Bash: sed -n '1,${budget}p' $1 / grep -n <pattern> $1.
→ Or delegate the whole file to a cheap reader that returns line-referenced bullets and keeps the bytes out of this context:
    Agent tool: subagent_type "bulk-reader", prompt "<question>\nfiles: $1"
    Workflow: bulk-read { question: "<question>", files: ["$1"] }
Waive once: AOP_WAIVE=${policy_id} (hook env, or a prefix on the Bash command). Raise the budget: AOP_READ_BUDGET_LINES=$2 in the hook env (an operator setting, not a command prefix).
MSG
  exit 2
}

# ---------------------------------------------------------------- Read ------

check_read() {
  local fpath ltype abs lines
  fpath="$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""' 2>/dev/null)"
  [ -n "$fpath" ] || return 0
  # A bounded slice always passes; offset alone does NOT bound.
  ltype="$(printf '%s' "$input" | jq -r '.tool_input.limit | type' 2>/dev/null)"
  [ "$ltype" = "number" ] && return 0
  abs="$(resolve_path "$fpath")"
  is_text_file "$abs" || return 0
  lines="$(line_count "$abs")"
  case "$lines" in ''|*[!0-9]*) return 0 ;; esac
  [ "$lines" -gt "$budget" ] || return 0
  fire "$abs" "$lines" "Read"
}

# ---------------------------------------------------------------- Bash ------

# strip_quotes T → T with ONE layer of surrounding single or double quotes removed.
strip_quotes() {
  local t="$1"
  case "$t" in
    \"*\") t="${t#\"}"; t="${t%\"}" ;;
    \'*\') t="${t#\'}"; t="${t%\'}" ;;
  esac
  printf '%s' "$t"
}

# check_segment SEG — judge one `;` / `&&` segment. Calls fire (never returns)
# when the segment's effective read exceeds the budget; returns 0 otherwise.
check_segment() {
  local -a toks
  local -a files
  local n i t cmdw name v n_raw want_next sign num
  read -r -a toks <<< "$1" || true
  n=${#toks[@]}
  [ "$n" -gt 0 ] || return 0

  # Segments arrive from the quote-aware split in check_bash, so every quote
  # here belongs to a word of ONE real command. A `#` word starts a comment:
  # nothing after it is a command. A word is judgeable only when its quotes
  # are a matched pair around the whole word (or around the value of a
  # NAME=value assignment); anything else — a quoted path with a space, a
  # stray quote, foo"bar" — is unparseable here: skip the segment, silent.
  local -a words
  local q
  words=()
  for t in "${toks[@]}"; do
    case "$t" in \#*) break ;; esac
    words[${#words[@]}]="$t"
  done
  n=${#words[@]}
  [ "$n" -gt 0 ] || return 0
  for t in "${words[@]}"; do
    case "$t" in *\"*|*\'*) ;; *) continue ;; esac
    v="$t"
    name="${t%%=*}"
    case "$name" in
      [A-Za-z_]*) case "$name" in *[!A-Za-z0-9_]*) ;; *) v="${t#*=}" ;; esac ;;
      --[A-Za-z]*) case "$name" in *[!A-Za-z0-9-]*) ;; *) v="${t#*=}" ;; esac ;;
    esac
    case "$v" in
      \"\"|\'\') ;;
      \"?*\") q="${v//[!\"]/}"; [ "${#q}" -eq 2 ] || return 0 ;;
      \'?*\') q="${v//[!\']/}"; [ "${#q}" -eq 2 ] || return 0 ;;
      *) return 0 ;;
    esac
  done
  toks=("${words[@]}")

  # Leading VAR=value assignments: skip them; an AOP_WAIVE naming this policy
  # waives the whole call.
  i=0
  while [ "$i" -lt "$n" ]; do
    t="${toks[$i]}"
    case "$t" in
      *=*)
        name="${t%%=*}"
        case "$name" in ''|[0-9]*|*[!A-Za-z0-9_]*) break ;; esac
        if [ "$name" = "AOP_WAIVE" ]; then
          v="$(strip_quotes "${t#*=}")"
          case ",${v}," in *",${policy_id},"*) inline_waived=1 ;; esac
        fi
        i=$((i + 1))
        ;;
      *) break ;;
    esac
  done
  [ "$i" -lt "$n" ] || return 0

  cmdw="$(strip_quotes "${toks[$i]}")"
  cmdw="${cmdw##*/}"
  case "$cmdw" in cat|head|tail) ;; *) return 0 ;; esac
  i=$((i + 1))

  n_raw="10"
  want_next=""
  files=()
  while [ "$i" -lt "$n" ]; do
    t="$(strip_quotes "${toks[$i]}")"
    i=$((i + 1))
    if [ -n "$want_next" ]; then
      n_raw="$t"
      want_next=""
      continue
    fi
    # Unresolvable tokens: variables, command substitution, globs.
    case "$t" in \$*|*\`*|*\**|*\?*|*\[*) continue ;; esac
    if [ "$cmdw" = "cat" ]; then
      # cat flags (-n, -A, ...) never bound the read; everything else is a file.
      case "$t" in -*) continue ;; esac
      files[${#files[@]}]="$t"
      continue
    fi
    # head / tail flag forms. A byte-mode or follow form makes the segment
    # unjudgeable by line count -> skip the whole segment.
    case "$t" in
      -c|-c*|--bytes|--bytes=*) return 0 ;;
      -f|-F|--follow|--follow=*)
        [ "$cmdw" = "tail" ] && return 0
        continue
        ;;
      -n|--lines) want_next=1; continue ;;
      -n*) n_raw="${t#-n}"; continue ;;
      --lines=*) n_raw="$(strip_quotes "${t#--lines=}")"; continue ;;
      -[0-9]*) n_raw="${t#-}"; continue ;;
      -*) continue ;;
    esac
    files[${#files[@]}]="$t"
  done
  [ "${#files[@]}" -gt 0 ] || return 0

  local abs lines eff total maxlines maxpath
  if [ "$cmdw" = "cat" ]; then
    # Effective = the SUM over the resolved files; report the largest file.
    total=0; maxlines=0; maxpath=""
    for t in "${files[@]}"; do
      abs="$(resolve_path "$t")"
      is_text_file "$abs" || continue
      lines="$(line_count "$abs")"
      case "$lines" in ''|*[!0-9]*) continue ;; esac
      total=$((total + lines))
      if [ "$lines" -gt "$maxlines" ] || [ -z "$maxpath" ]; then
        maxlines="$lines"; maxpath="$abs"
      fi
    done
    [ -n "$maxpath" ] || return 0
    [ "$total" -gt "$budget" ] || return 0
    fire "$maxpath" "$total" "Bash"
  fi

  # head / tail: parse the count. head: N -> min(N, lines); -K -> the whole
  # file. tail: N or -K -> min(K, lines); +K -> lines - K + 1 (min 0).
  sign=""; num="$n_raw"
  case "$n_raw" in
    +*) sign="+"; num="${n_raw#+}" ;;
    -*) sign="-"; num="${n_raw#-}" ;;
  esac
  case "$num" in ''|*[!0-9]*) return 0 ;; esac
  [ "$cmdw" = "head" ] && [ "$sign" = "+" ] && return 0
  num=$((10#$num))
  for t in "${files[@]}"; do
    abs="$(resolve_path "$t")"
    is_text_file "$abs" || continue
    lines="$(line_count "$abs")"
    case "$lines" in ''|*[!0-9]*) continue ;; esac
    if [ "$cmdw" = "head" ] && [ "$sign" = "-" ]; then
      eff="$lines"
    elif [ "$cmdw" = "tail" ] && [ "$sign" = "+" ]; then
      eff=$((lines - num + 1))
      [ "$eff" -lt 0 ] && eff=0
    else
      eff="$num"
      [ "$eff" -gt "$lines" ] && eff="$lines"
    fi
    [ "$eff" -gt "$budget" ] || continue
    fire "$abs" "$eff" "Bash"
  done
  return 0
}

check_bash() {
  local cmd seg
  cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""' 2>/dev/null)"
  [ -n "$cmd" ] || return 0
  # Pipes and redirects are out of scope by design: a bounded consumer or a
  # file sink, never an unbounded read into this context.
  case "$cmd" in *'|'*|*'<'*|*'>'*) return 0 ;; esac
  # Quote-aware split: `;`, `&&` and a newline end a segment only OUTSIDE
  # single/double quotes (backslash escapes honored outside single quotes), so
  # quoted text that merely mentions `cat` — a commit message, an echo — stays
  # inside its own command's segment and is never judged as an invocation. A
  # newline inside quotes becomes a space (segments are only ever tokenized).
  # A `#` comment (at a word start) runs to end of line and is dropped, so a
  # separator or a quote inside a comment never splits or swallows anything;
  # a backslash-newline is deleted, joining the segment exactly as the shell
  # does (`cat big\` + newline + `.txt` is `cat big.txt`). awk (POSIX, BSD and GNU) keeps
  # this a single linear pass in bash 3.2; no awk -> fail open, silent.
  command -v awk >/dev/null 2>&1 || return 0
  while IFS= read -r seg; do
    [ -n "$seg" ] || continue
    check_segment "$seg"
  done < <(printf '%s\n' "$cmd" | awk '
    BEGIN { q = ""; seg = ""; cont = 0 }
    {
      line = $0; n = length(line)
      for (i = 1; i <= n; i++) {
        c = substr(line, i, 1)
        if (q == "") {
          if (c == "\\") {
            if (i == n) { cont = 1; break }
            seg = seg c substr(line, i + 1, 1); i++; continue
          }
          if (c == "#" && (i == 1 || substr(line, i - 1, 1) ~ /[ \t;&()]/)) break
          if (c == "\"" || c == "\047") { q = c; seg = seg c; continue }
          if (c == ";") { print seg; seg = ""; continue }
          if (c == "&" && substr(line, i + 1, 1) == "&") { print seg; seg = ""; i++; continue }
          seg = seg c
        } else if (q == "\"") {
          if (c == "\\") { seg = seg c substr(line, i + 1, 1); i++; continue }
          if (c == "\"") q = ""
          seg = seg c
        } else {
          if (c == "\047") q = ""
          seg = seg c
        }
      }
      if (cont) { cont = 0 }
      else if (q == "") { print seg; seg = "" }
      else { seg = seg " " }
    }
    END { if (seg != "") print seg }
  ')
  return 0
}

case "$tool" in
  Read) check_read ;;
  Bash) check_bash ;;
esac
exit 0
