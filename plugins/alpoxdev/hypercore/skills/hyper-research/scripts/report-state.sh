#!/usr/bin/env bash
# Track repair passes and write the run outcome manifest.
#
# State file: a JSON file in the run journal that records each repair pass
# (blocker/major/minor counts and defect codes) and the finished outcome.
# Pass its path with --state <path> or the REPORT_STATE_FILE environment
# variable. The default is `.hyper/research/report-state.json` relative to
# the current directory. outcome.json is written beside the state file.
set -euo pipefail

RS_USAGE='Usage: bash report-state.sh repair [--state <path>] --counts <blocker> <major> <minor> --codes <a,b>
       bash report-state.sh finish [--state <path>] --report <md> --ledger <md>
       bash report-state.sh briefing [--state <path>]
       bash report-state.sh --self-test
       bash report-state.sh --help'

RS_GATES='structure
citation
claim gate
number lineage
recency
read-back'

# rs_state_path <flag-value> prints the effective state path.
rs_state_path() {
  if [ -n "$1" ]; then
    printf '%s\n' "$1"
  elif [ -n "${REPORT_STATE_FILE:-}" ]; then
    printf '%s\n' "$REPORT_STATE_FILE"
  else
    printf '%s\n' '.hyper/research/report-state.json'
  fi
}

# rs_norm_codes <a,b> prints the sorted, de-duplicated code set as a,b.
rs_norm_codes() {
  printf '%s\n' "$1" | tr ',' '\n' | LC_ALL=C sort | uniq | paste -sd ',' - 2>/dev/null
}

# rs_new_state prints a fresh empty state document.
rs_new_state() {
  printf '%s\n' '{"version": 1, "passes": [], "outcome": null}'
}

# rs_load_state <path> prints the state JSON, creating a fresh one when the
# file does not exist yet.
rs_load_state() {
  local path=$1 loaded
  if [ -f "$path" ]; then
    loaded=$(cat "$path")
    printf '%s\n' "$loaded" | jq -e . >/dev/null 2>&1 || {
      printf '%s\n' '{"ok":false,"error":"state file is not valid JSON"}' >&2
      return 2
    }
    printf '%s\n' "$loaded"
  elif [ ! -e "$path" ]; then
    rs_new_state
  else
    printf '%s\n' '{"ok":false,"error":"not a file"}' >&2
    return 2
  fi
}

# rs_save_state <path> <json> writes the state document atomically.
rs_save_state() {
  local path=$1 json=$2 dir
  dir=$(dirname "$path")
  mkdir -p "$dir"
  printf '%s\n' "$json" >"$path.tmp"
  mv "$path.tmp" "$path"
}

# rs_ledger_counts <ledger> prints two lines: source count, domain count.
rs_ledger_counts() {
  LC_ALL=C awk '
function trim(s) { sub(/^[ \t\r\n]+/, "", s); sub(/[ \t\r\n]+$/, "", s); return s }
function domain_of(u,   s, d) {
  s = trim(u)
  sub(/^</, "", s); sub(/>$/, "", s)
  if (match(s, /\]\([^)]*\)/)) {
    s = substr(s, RSTART + 2, RLENGTH - 3)
  }
  sub(/^https?:\/\//, "", s)
  sub(/^www\./, "", s)
  if (s ~ /^\//) {
    # A bare local path has no host; its first segment is its domain token.
    sub(/^\//, "", s)
    if (index(s, "/") > 0) s = substr(s, 1, index(s, "/") - 1)
    return s
  }
  if (index(s, "/") > 0) s = substr(s, 1, index(s, "/") - 1)
  if (index(s, ":") > 0) s = substr(s, 1, index(s, ":") - 1)
  sub(/\.$/, "", s)
  return s
}
{
  if (split($0, cells, "|") >= 3) {
    if (url_col == 0 && trim(cells[2]) == "#") {
      # Header row: find the URL/path column so a repeated source title is
      # never mistaken for the host.
      for (i = 3; i <= length(cells); i++) {
        label = trim(cells[i])
        if (label == "URL/path" || label == "URL" || label ~ /^URL\//) { url_col = i; break }
      }
      next
    }
    id = trim(cells[2])
    sub(/^\[/, "", id); sub(/\]$/, "", id)
    if (id ~ /^S[0-9]+$/) {
      n++
      col = url_col
      if (col == 0) col = (length(cells) >= 4 ? 4 : 3)
      d = domain_of(cells[col])
      if (d != "" && !(d in seen_dom)) { seen_dom[d] = 1; nd++ }
    }
  }
}
END { print n + 0; print nd + 0 }
' "$1"
}

# rs_gate_status <report> <gate> prints the stored status or empty when unset.
rs_gate_status() {
  LC_ALL=C awk -v gate="$2" '
function trim(s) { sub(/^[ \t\r\n]+/, "", s); sub(/[ \t\r\n]+$/, "", s); return s }
BEGIN { in_gates = 0 }
{
  if ($0 ~ /^## Report gates/) { in_gates = 1; next }
  if (in_gates && $0 ~ /^#{1,2}[ \t]/) in_gates = 0
}
in_gates && /^\|/ {
  if (split($0, cells, "|") >= 3) {
    name = trim(cells[2])
    if (name == gate) {
      print trim(cells[3])
      found = 1
      exit
    }
  }
}
END { if (!found) print "" }
' "$1"
}

# rs_command_repair <state> <b> <maj> <min> <codes> prints the verdict.
rs_command_repair() {
  local state=$1 blocker=$2 major=$3 minor=$4 codes=$5
  local norm current
  norm=$(rs_norm_codes "$codes")
  current=$(rs_load_state "$state") || return $?
  # Append this pass first, then judge: the verdict always describes the
  # newly recorded pass, and the pass is recorded even when the verdict stops.
  current=$(printf '%s' "$current" | jq -c --argjson b "$blocker" --argjson m "$major" --argjson k "$minor" --arg norm "$norm" \
    '.passes += [{counts: [$b, $m, $k], codes: $norm}]')
  rs_save_state "$state" "$current"
  # Oscillation: the same code set was recorded by an earlier pass.
  if printf '%s' "$current" | jq -e --arg norm "$norm" \
    '.passes | length >= 2 and (.[:-1] | any(.codes == $norm))' >/dev/null 2>&1; then
    printf '%s\n' 'stop:oscillation'
    return 0
  fi
  # Plateau: the total did not improve over the previous pass.
  if printf '%s' "$current" | jq -e \
    '(.passes | length >= 2) and ((.passes[-1].counts | add) >= (.passes[-2].counts | add))' >/dev/null 2>&1; then
    printf '%s\n' 'stop:plateau'
    return 0
  fi
  # Limit: two recorded passes is the package bound.
  if printf '%s' "$current" | jq -e '(.passes | length >= 2)' >/dev/null 2>&1; then
    printf '%s\n' 'stop:limit'
    return 0
  fi
  printf '%s\n' 'continue'
}

# rs_command_finish <state> <report> <ledger>; return 1 when delivery is blocked.
rs_command_finish() {
  local state=$1 report=$2 ledger=$3
  local current gate status counts total outcome
  if [ ! -f "$report" ]; then
    printf '%s\n' "$(jq -cn --arg e "ENOENT: no such file or directory, open '$report'" '{ok:false,error:$e}')" >&2
    return 1
  fi
  if [ ! -s "$report" ] || ! grep -q '[^[:space:]]' "$report" 2>/dev/null; then
    printf '%s\n' '{"ok":false,"error":"report is missing or empty"}' >&2
    return 1
  fi
  if [ ! -f "$ledger" ] || [ ! -s "$ledger" ]; then
    printf '%s\n' '{"ok":false,"error":"ledger is missing or empty"}' >&2
    return 1
  fi
  current=$(rs_load_state "$state") || return $?
  # Every gate must carry a stored status; an unset gate blocks finish.
  while IFS= read -r gate; do
    [ -n "$gate" ] || continue
    status=$(rs_gate_status "$report" "$gate")
    case "$status" in
      pass | fail | not_run) : ;;
      *) printf '%s\n' "$(jq -cn --arg g "$gate" '{ok:false,error:("unset gate: "+$g)}')" >&2; return 1 ;;
    esac
  done <<EOF
$RS_GATES
EOF
  total=$(printf '%s' "$current" | jq -r '.passes | length')
  counts=$(printf '%s' "$current" | jq -c 'if (.passes | length) == 0 then {blocker: 0, major: 0, minor: 0} else {blocker: .passes[-1].counts[0], major: .passes[-1].counts[1], minor: .passes[-1].counts[2]} end')
  counts=$(printf '%s' "$counts" | jq -c .)
  # A remaining blocker blocks finish: the last recorded pass or any failed gate.
  if printf '%s' "$counts" | jq -e '.blocker > 0' >/dev/null 2>&1; then
    printf '%s\n' '{"ok":false,"error":"a blocker defect remains"}' >&2
    return 1
  fi
  local failed_gates=0
  while IFS= read -r gate; do
    status=$(rs_gate_status "$report" "$gate")
    if [ "$status" = fail ]; then failed_gates=$((failed_gates + 1)); fi
  done <<EOF
$RS_GATES
EOF
  if [ "$failed_gates" -gt 0 ]; then
    printf '%s\n' '{"ok":false,"error":"a gate is failing with a blocker defect"}' >&2
    return 1
  fi
  counts=$(printf '%s' "$counts" | jq -c .)
  local srcdom
  srcdom=$(rs_ledger_counts "$ledger")
  local nsources ndomains
  nsources=$(printf '%s\n' "$srcdom" | sed -n '1p')
  ndomains=$(printf '%s\n' "$srcdom" | sed -n '2p')
  local gates_json passed=0 failed=0 notrun=0
  while IFS= read -r gate; do
    [ -n "$gate" ] || continue
    status=$(rs_gate_status "$report" "$gate")
    case "$status" in
      pass) passed=$((passed + 1)) ;;
      fail) failed=$((failed + 1)) ;;
      not_run) notrun=$((notrun + 1)) ;;
    esac
  done <<EOF
$RS_GATES
EOF
  gates_json=$(jq -n --argjson p "$passed" --argjson f "$failed" --argjson n "$notrun" --argjson repairs "$total" --argjson src "$nsources" --argjson dom "$ndomains" \
    --argjson residual "$counts" --arg report "$report" \
    '{gates: {pass: $p, fail: $f, not_run: $n}, residual: $residual, repairs: $repairs, sources: $src, domains: $dom, report: $report}')
  outcome=$(jq -n --argjson g "$gates_json" '$g')
  current=$(printf '%s' "$current" | jq -c --argjson oc "$outcome" '.outcome = $oc')
  rs_save_state "$state" "$current"
  printf '%s\n' "$outcome" >"$(dirname "$state")/outcome.json"
  printf '%s\n' "$(jq -c '.' <<<"$outcome")"
}

# rs_command_briefing <state> prints the counted facts from outcome.json.
rs_command_briefing() {
  local state=$1 dir outcome
  dir=$(dirname "$state")
  if [ -f "$dir/outcome.json" ]; then
    outcome=$(cat "$dir/outcome.json")
  else
    outcome=$(rs_load_state "$state" | jq -c '.outcome // empty')
    [ -n "$outcome" ] || { printf '%s\n' '{"ok":false,"error":"no outcome yet"}' >&2; return 1; }
  fi
  printf 'Sources: %s\n' "$(printf '%s' "$outcome" | jq -r '.sources')"
  printf 'Domains: %s\n' "$(printf '%s' "$outcome" | jq -r '.domains')"
  printf 'Repairs: %s\n' "$(printf '%s' "$outcome" | jq -r '.repairs')"
  printf 'Gates: pass=%s fail=%s not_run=%s\n' \
    "$(printf '%s' "$outcome" | jq -r '.gates.pass')" \
    "$(printf '%s' "$outcome" | jq -r '.gates.fail')" \
    "$(printf '%s' "$outcome" | jq -r '.gates.not_run')"
  printf 'Residual: blocker=%s major=%s minor=%s\n' \
    "$(printf '%s' "$outcome" | jq -r '.residual.blocker')" \
    "$(printf '%s' "$outcome" | jq -r '.residual.major')" \
    "$(printf '%s' "$outcome" | jq -r '.residual.minor')"
  printf 'Report: %s\n' "$(printf '%s' "$outcome" | jq -r '.report')"
}

# rs_case <id> <want> <actual> <pass> appends one case; its pass flag decides ok.
rs_case() {
  local id=$1 want=$2 actual=$3 pass=$4
  cases=$(jq -cn --argjson c "$cases" --arg id "$id" --argjson e "$want" --argjson a "$actual" \
    '$c + [{id: $id, expected: $e, actual: $a}]')
  [ "$pass" = true ] || { ok=false; }
}

rs_help() {
  printf '%s\n' "$RS_USAGE"
}

rs_fail() {
  printf '%s\n' "$(jq -cn --arg e "$1" '{ok:false,error:$e}')" >&2
  exit 2
}

rs_self_ledger() {
  cat <<'RS_LEDGER'
# Sources

| # | Source | URL/path | Publisher |
|---|---|---|---|
| S1 | Example report | https://example.com/report | Example |
| S2 | Example registry | https://example.org/registry | Example |
RS_LEDGER
}

rs_self_report() {
  cat <<'RS_REPORT'
# Example Research Report

> As of: 2026-11-09

## Report gates

| Gate | Status (pass / fail / not_run) | Open-defect severity (blocker / major / minor) | Reason |
|---|---|---|---|
| structure | pass |  | ok |
| citation | pass |  | ok |
| claim gate | pass |  | ok |
| number lineage | pass |  | ok |
| recency | pass |  | ok |
| read-back | pass |  | ok |

## References

- [S1] [Example report](https://example.com/report), accessed 2026-11-09
RS_REPORT
}

rs_self_test() {
  local work verdict repeated
  work=$(mktemp -d "${TMPDIR:-/tmp}/report-state.XXXXXX")
  ok=true
  cases='[]'

  verdict=$(rs_command_repair "$work/a.json" 1 2 0 a)
  actual=$([ "$verdict" = continue ] && echo true || echo false)
  pass=$([ "$verdict" = continue ] && echo true || echo false)
  rs_case first-pass-continues true "$actual" "$pass"
  verdict=$(rs_command_repair "$work/a.json" 1 2 0 b)
  actual=$([ "$verdict" = "stop:plateau" ] && echo true || echo false)
  pass=$([ "$verdict" = "stop:plateau" ] && echo true || echo false)
  rs_case same-total-plateaus true "$actual" "$pass"

  verdict=$(rs_command_repair "$work/b.json" 3 1 0 a)
  actual=$([ "$verdict" = continue ] && echo true || echo false)
  pass=$([ "$verdict" = continue ] && echo true || echo false)
  rs_case improving-first-continues true "$actual" "$pass"
  verdict=$(rs_command_repair "$work/b.json" 1 0 0 b)
  actual=$([ "$verdict" = "stop:limit" ] && echo true || echo false)
  pass=$([ "$verdict" = "stop:limit" ] && echo true || echo false)
  rs_case two-passes-hit-limit true "$actual" "$pass"

  rs_command_repair "$work/c.json" 1 2 0 a >/dev/null 2>&1
  verdict=$(rs_command_repair "$work/c.json" 0 1 0 a)
  actual=$([ "$verdict" = "stop:oscillation" ] && echo true || echo false)
  pass=$([ "$verdict" = "stop:oscillation" ] && echo true || echo false)
  rs_case repeated-codes-oscillate-first true "$actual" "$pass"

  cat >"$work/repeated-title.md" <<'RS_REPEATED'
# Sources

| # | Source | URL/path | Publisher |
|---|---|---|---|
| S1 | Same title | https://example.org/a | Example |
| S2 | Same title | https://other.net/b | Example |
RS_REPEATED
  repeated=$(rs_ledger_counts "$work/repeated-title.md" | sed -n '2p')
  actual=$([ "$repeated" = 2 ] && echo true || echo false)
  pass=$([ "$repeated" = 2 ] && echo true || echo false)
  rs_case repeated-titles-count-distinct-hosts true "$actual" "$pass"

  rs_self_ledger >"$work/ledger.md"
  rs_self_report >"$work/report.md"
  printf '' >"$work/empty.md"
  rc=0
  rs_command_finish "$work/d.json" "$work/empty.md" "$work/ledger.md" >/dev/null 2>&1 || rc=$?
  actual=$([ "$rc" -eq 1 ] && [ ! -e "$work/outcome.json" ] && echo true || echo false)
  pass=$([ "$rc" -eq 1 ] && [ ! -e "$work/outcome.json" ] && echo true || echo false)
  rs_case empty-report-blocked true "$actual" "$pass"

  printf '%s' 'not json' >"$work/corrupt.json"
  rc=0
  rs_command_finish "$work/corrupt.json" "$work/report.md" "$work/ledger.md" >/dev/null 2>&1 || rc=$?
  actual=$([ "$rc" -eq 2 ] && echo true || echo false)
  pass=$([ "$rc" -eq 2 ] && echo true || echo false)
  rs_case corrupt-state-fails-loudly true "$actual" "$pass"

  rc=0
  rs_command_finish "$work/e.json" "$work/report.md" "$work/ledger.md" >/dev/null 2>&1 || rc=$?
  actual=$([ "$rc" -eq 0 ] && [ -f "$work/outcome.json" ] && echo true || echo false)
  pass=$([ "$rc" -eq 0 ] && [ -f "$work/outcome.json" ] && echo true || echo false)
  rs_case happy-finish-writes-outcome true "$actual" "$pass"

  local briefing src dom
  briefing=$(rs_command_briefing "$work/e.json")
  src=$(printf '%s' "$briefing" | sed -n 's/^Sources: //p')
  dom=$(printf '%s' "$briefing" | sed -n 's/^Domains: //p')
  actual=$([ "$src" = 2 ] && [ "$dom" = 2 ] && echo true || echo false)
  pass=$([ "$src" = 2 ] && [ "$dom" = 2 ] && echo true || echo false)
  rs_case briefing-counts-match-ledger true "$actual" "$pass"

  rm -rf "$work"
  printf '%s\n' "$(jq -n --argjson ok "$([ "$ok" = true ] && echo true || echo false)" --argjson cases "$cases" '{ok: $ok, cases: $cases}')"
  [ "$ok" = true ]
}

rs_main() {
  local state_flag='' command='' counts_vars='' report='' ledger=''
  if [ $# -eq 0 ]; then
    rs_help >&2
    exit 2
  fi
  counts_vars=''
  local do_repair=0 do_finish=0 do_briefing=0
  local b='' maj='' min='' codes_arg=''
  while [ $# -gt 0 ]; do
    case "$1" in
      repair) command=repair; do_repair=1; shift ;;
      finish) command=finish; do_finish=1; shift ;;
      briefing) command=briefing; do_briefing=1; shift ;;
      --state) shift; state_flag=${1-}; case "$state_flag" in '' | --*) rs_fail '--state requires a path' ;; esac; shift ;;
      --counts) shift; b=${1-}; shift; maj=${1-}; shift; min=${1-}; shift
        case "$b$maj$min" in ''|*[!0-9]*) rs_fail '--counts requires three non-negative integers' ;; esac ;;
      --codes) shift; codes_arg=${1-}; [ -n "$codes_arg" ] || rs_fail '--codes requires a value'; shift ;;
      --report) shift; report=${1-}; case "$report" in '' | --*) rs_fail '--report requires a path' ;; esac; shift ;;
      --ledger) shift; ledger=${1-}; case "$ledger" in '' | --*) rs_fail '--ledger requires a path' ;; esac; shift ;;
      --self-test) rs_self_test; return $? ;;
      --help | -h) rs_help; return 0 ;;
      *) printf '%s\n' "$(jq -cn --arg e "Unknown argument: $1" '{ok:false,error:$e}')" >&2; exit 2 ;;
    esac
  done
  local state
  state=$(rs_state_path "$state_flag")
  if [ "$do_repair" = 1 ]; then
    if [ -z "$b$maj$min" ] || [ -z "$codes_arg" ]; then
      rs_fail '--counts and --codes are required for repair'
    fi
    local v
    v=$(rs_command_repair "$state" "$b" "$maj" "$min" "$codes_arg")
    case "$v" in continue) printf 'continue\n' ;; stop:*) printf 'stop:%s\n' "${v#stop:}" ;; *) printf '%s\n' "$v" ;; esac
    return 0
  fi
  if [ "$do_finish" = 1 ]; then
    [ -n "$report" ] || rs_fail '--report is required for finish'
    [ -n "$ledger" ] || rs_fail '--ledger is required for finish'
    rs_command_finish "$state" "$report" "$ledger"
    return $?
  fi
  if [ "$do_briefing" = 1 ]; then
    rs_command_briefing "$state"
    return $?
  fi
  rs_fail 'a subcommand is required: repair, finish, or briefing'
}

rs_main "$@"
