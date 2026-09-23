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
# PASS cases: a Read with a numeric
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
# no mapfile, no associative arrays; head/tail flags parsed with case. Bash
# judging also fails open without awk or uname.
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

# Normalize decimal strings before arithmetic. Bash wraps overflowing integers;
# saturate budgets at its signed 64-bit maximum and reject out-of-range
# command counts. Leading zeroes do not invoke octal arithmetic.
max_integer=9223372036854775807
normalize_uint() {
  local value="$1"
  case "$value" in ''|*[!0-9]*) return 1 ;; esac
  value="${value#"${value%%[!0]*}"}"
  [ -n "$value" ] || value=0
  # Equal-width decimals compare lexically before entering machine arithmetic.
  # shellcheck disable=SC2071
  if [ "${#value}" -gt 19 ] || { [ "${#value}" -eq 19 ] && [[ "$value" > "$max_integer" ]]; }; then
    [ "${2:-}" = exact ] && return 1
    value="$max_integer"
  fi
  printf '%s' "$value"
}
budget="$(normalize_uint "${AOP_READ_BUDGET_LINES:-350}")" || budget=350
[ "$budget" -gt 0 ] || budget=350

# Set when a leading AOP_WAIVE=<ids> assignment on the Bash command names this
# policy: the WHOLE call is waived.
inline_waived=0

# resolve_path P → absolute path: relative paths resolve against the JSON cwd.
resolve_path() {
  case "$1" in
    /*) printf '%s' "$1" ;;
    \~|\~/*)
      # Bash tokens already have their unquoted tilde expanded by the lexer.
      # Read paths keep the existing HOME shorthand; otherwise retain it literally.
      if [ "${2:-}" != literal ] && [ -n "${HOME:-}" ]; then printf '%s%s' "$HOME" "${1#\~}"; else printf '%s/%s' "$cwd" "$1"; fi ;;
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
    printf '⛔ policy %s: %s is %s lines (budget %s) — slice it (offset+limit / sed -n) or delegate to agentops:bulk-reader (full reason shown earlier this session).\n' \
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
    Agent tool: subagent_type "agentops:bulk-reader", prompt "<question>\nfiles: $1"
    Workflow: agentops:bulk-read { question: "<question>", files: ["$1"] }
    These names require the AgentOps plugin. Use bare names only when the runtime lists standalone definitions or links under those names.
Waive once: AOP_WAIVE=${policy_id} (hook env, or a prefix on the Bash command). Raise the budget: AOP_READ_BUDGET_LINES=$2 in the hook env (an operator setting, not a command prefix).
MSG
  exit 2
}

# ---------------------------------------------------------------- Read ------

check_read() {
  local fpath ltype abs lines
  fpath="$(printf '%s' "$input" | jq -r '.tool_input.file_path | select(type == "string")' 2>/dev/null)"
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

# Resolve an executable without invoking it. Bare names use the command's
# literal PATH assignments and cwd; paths containing / resolve against cwd.
resolve_command() {
  case "$1" in
    */*) resolve_path "$1" literal ;;
    *) (cd "$cwd" 2>/dev/null && PATH="$2" type -P -- "$1" 2>/dev/null) ;;
  esac
}

# check_segment receives literal words from the lexer, prefixed with "a" for
# syntactic assignments or "w" for ordinary words. Never eval command input.
check_segment() {
  local -a toks files
  toks=("$@"); files=()
  local n i t cmdw command_literal command_path utility_family platform v n_raw want_next sign num options
  local lookup_path="${PATH:-}"
  n=${#toks[@]}
  [ "$n" -gt 0 ] || return 0
  i=0
  while [ "$i" -lt "$n" ]; do
    t="${toks[$i]}"
    case "$t" in
      aPATH=*) lookup_path="${t#aPATH=}" ;;
      aAOP_WAIVE=*)
        v="${t#aAOP_WAIVE=}"
        case ",${v}," in *",${policy_id},"*) inline_waived=1 ;; esac ;;
      a*) ;;
      *) break ;;
    esac
    i=$((i + 1))
  done
  [ "$i" -lt "$n" ] || return 0
  command_literal="${toks[$i]#w}"
  cmdw="${command_literal##*/}"
  case "$cmdw" in cat|head|tail) ;; *) return 0 ;; esac
  command_path="$(resolve_command "$command_literal" "$lookup_path")" || return 0
  [ -n "$command_path" ] || return 0
  command_path="$(resolve_path "$command_path" literal)"
  [ -f "$command_path" ] && [ -x "$command_path" ] || return 0
  # Darwin system utilities reject some GNU forms without reading. Follow
  # executable identity, including symlinks: basename alone is insufficient.
  # uname is a guard dependency; never probe a caller-selected executable.
  utility_family=generic
  platform="$(uname -s 2>/dev/null)" || return 0
  if [ "$platform" = Darwin ]; then
    case "$cmdw" in
      cat) [ "$command_path" -ef /bin/cat ] && utility_family=bsd-cat ;;
      head) [ "$command_path" -ef /usr/bin/head ] && utility_family=bsd-head ;;
      tail) [ "$command_path" -ef /usr/bin/tail ] && utility_family=bsd-tail ;;
    esac
  fi
  i=$((i + 1))

  n_raw=10; want_next=""; options=1
  while [ "$i" -lt "$n" ]; do
    t="${toks[$i]:1}"
    i=$((i + 1))
    if [ -n "$want_next" ]; then
      n_raw="$t"; want_next=""; continue
    fi
    if [ "$options" -eq 1 ]; then
      case "$t" in
        --) options=0; continue ;;
        --help|--version) return 0 ;;
        -) continue ;; # stdin, including after -- (handled below too)
      esac
      if [ "$cmdw" = cat ]; then
        # Only known output-format flags are non-bounding. Unknown options
        # may terminate without reading any file, so fail open.
        if [ "$utility_family" = bsd-cat ]; then
          case "$t" in --*|-*[AET]*) return 0 ;; esac
        fi
        case "$t" in
          --number|--number-nonblank|--squeeze-blank|--show-all|--show-ends|--show-nonprinting|--show-tabs) continue ;;
          -*) v="${t#-}"; case "$v" in *[!AbensTtuvE]*) return 0 ;; *) continue ;; esac ;;
        esac
      else
        case "$t" in
          -c*|--bytes|--bytes=*|-f|-F|--follow|--follow=*) return 0 ;;
          -n|--lines) want_next=1; continue ;;
          -n*) n_raw="${t#-n}"; continue ;;
          --lines=*) n_raw="${t#--lines=}"; continue ;;
          -[0-9]*) n_raw="${t#-}"; continue ;;
          --quiet|--silent|--verbose) [ "$utility_family" = bsd-head ] && return 0; continue ;;
          -*)
            v="${t#-}"
            case "$v" in *[!qv]*) return 0 ;; esac
            [ "$utility_family" = bsd-head ] && return 0
            continue ;;
        esac
      fi
    fi
    [ "$t" = - ] && continue
    files[${#files[@]}]="$t"
  done
  [ -z "$want_next" ] || return 0
  [ "${#files[@]}" -gt 0 ] || return 0

  local abs lines eff total maxlines maxpath
  if [ "$cmdw" = cat ]; then
    total=0; maxlines=0; maxpath=""
    for t in "${files[@]}"; do
      abs="$(resolve_path "$t" literal)"
      is_text_file "$abs" || continue
      lines="$(line_count "$abs")"
      case "$lines" in ''|*[!0-9]*) continue ;; esac
      if [ "$lines" -gt "$((max_integer - total))" ]; then
        total="$max_integer"
      else
        total=$((total + lines))
      fi
      if [ "$lines" -gt "$maxlines" ] || [ -z "$maxpath" ]; then
        maxlines="$lines"; maxpath="$abs"
      fi
    done
    [ -n "$maxpath" ] || return 0
    [ "$total" -gt "$budget" ] || return 0
    fire "$maxpath" "$total" Bash
  fi

  # head -K means all but the last K; tail +K starts at line K (0 and 1
  # both start at the first line). Out-of-range counts fail open: the utility
  # may reject them instead of reading. Never let them wrap in arithmetic.
  sign=""; num="$n_raw"
  case "$n_raw" in
    +*) sign="+"; num="${n_raw#+}" ;;
    -*) sign="-"; num="${n_raw#-}" ;;
  esac
  [ "$utility_family" = bsd-head ] && [ "$sign" = - ] && return 0
  num="$(normalize_uint "$num" exact)" || return 0
  for t in "${files[@]}"; do
    abs="$(resolve_path "$t" literal)"
    is_text_file "$abs" || continue
    lines="$(line_count "$abs")"
    case "$lines" in ''|*[!0-9]*) continue ;; esac
    if [ "$cmdw" = head ] && [ "$sign" = - ]; then
      eff=$((lines - num))
      [ "$eff" -lt 0 ] && eff=0
    elif [ "$cmdw" = tail ] && [ "$sign" = + ]; then
      if [ "$num" -le 1 ]; then eff="$lines"; else eff=$((lines - num + 1)); fi
      [ "$eff" -lt 0 ] && eff=0
    else
      eff="$num"
      [ "$eff" -gt "$lines" ] && eff="$lines"
    fi
    [ "$eff" -gt "$budget" ] || continue
    fire "$abs" "$eff" Bash
  done
  return 0
}

check_bash() {
  local cmd token
  local -a words
  words=()
  cmd="$(printf '%s' "$input" | jq -r '.tool_input.command | select(type == "string")' 2>/dev/null)"
  [ -n "$cmd" ] || return 0
  # Pipes and redirects are explicitly outside this guard, even in quotes.
  case "$cmd" in *'|'*|*'<'*|*'>'*) return 0 ;; esac
  command -v awk >/dev/null 2>&1 || return 0
  # The lexer keeps literal word boundaries (including spaces/newlines),
  # strips shell quotes, and removes escaped newlines outside single quotes.
  # It emits NOTHING until the whole command is known to use this subset.
  # Expansions, ANSI-C quotes, control syntax, directory changes and persistent
  # assignments before later segments fail open for the whole call. This avoids both stale-cwd attribution and
  # prematurely blocking text before an unmatched/unsupported later quote.
  while IFS= read -r -d '' token; do
    if [ "$token" = s ]; then
      if [ "${#words[@]}" -gt 0 ]; then check_segment "${words[@]}"; fi
      words=()
    else
      words[${#words[@]}]="$token"
    fi
  done < <(printf '%s\n' "$cmd" | awk '
    function word_done(    value, kind) {
      if (!active) return
      if (persistent_assignment) bad = 1
      value = word
      if (tilde && ENVIRON["HOME"] != "") value = ENVIRON["HOME"] substr(value, 2)
      kind = assignment ? "a" : "w"
      records[++count] = kind value
      segment_words++; pending_and = 0
      if (!command_seen && !assignment) {
        command_seen = 1
        # Builtins/wrappers may change cwd or shell evaluation for later
        # segments; reserved words require a real shell grammar.
        if (value ~ /^(cd|pushd|popd|builtin|command|eval|source|\.|if|then|else|elif|fi|while|until|do|done|for|case|esac|select|function|!|time|coproc|exec)$/) bad = 1
      }
      word = ""; active = 0; assignment = 0; quoted = 0; tilde = 0
    }
    function segment_done() {
      word_done()
      # Assignment-only commands persist shell state for later segments.
      # Do not judge those later words using the original hook environment.
      if (segment_words && !command_seen) persistent_assignment = 1
      records[++count] = "s"
      command_seen = 0; segment_words = 0
    }
    BEGIN { q = ""; word = ""; count = 0 }
    {
      line = $0; n = length(line); continuation = 0
      for (i = 1; i <= n; i++) {
        c = substr(line, i, 1); nextc = substr(line, i + 1, 1)
        if (q == "\047") {
          if (c == "\047") q = ""; else word = word c
          continue
        }
        if (c == "\\") {
          if (i == n) { continuation = 1; break }
          active = 1; quoted = 1
          if (q == "\"" && nextc !~ /[\\"$`]/) word = word "\\"
          word = word nextc; i++; continue
        }
        if (q == "\"") {
          if (c == "\"") q = ""
          else if (c == "$" || c == "`") bad = 1
          else word = word c
          continue
        }
        if (c == "#" && !active) break
        if (c == "\"" || c == "\047") { q = c; active = 1; quoted = 1; continue }
        if (c == " " || c == "\t") { word_done(); continue }
        if (c == ";") {
          word_done(); if (!segment_words || pending_and) bad = 1
          segment_done(); continue
        }
        if (c == "&" && nextc == "&") {
          word_done(); if (!segment_words || pending_and) bad = 1
          segment_done(); pending_and = 1; i++; continue
        }
        if (c ~ /[$`*?\[(){}&]/) { bad = 1; continue }
        if (c == "~") {
          if (!active && (nextc == "/" || nextc == "" || nextc ~ /[ \t;]/)) tilde = 1
          else { bad = 1; continue }
        }
        if (c == "=" && !quoted && word ~ /^[A-Za-z_][A-Za-z0-9_]*$/) assignment = 1
        active = 1; word = word c
      }
      if (!continuation) {
        if (q != "") word = word "\n"; else segment_done()
      }
    }
    END {
      if (q != "" || continuation || pending_and || bad) exit
      for (j = 1; j <= count; j++) printf "%s%c", records[j], 0
    }
  ')
  return 0
}

case "$tool" in
  Read) check_read ;;
  Bash) check_bash ;;
esac
exit 0
