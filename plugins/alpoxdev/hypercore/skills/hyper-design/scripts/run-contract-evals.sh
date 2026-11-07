#!/usr/bin/env bash
# Run the report/waiver/rendered-evidence contract cases and report per-case exit-code agreement.
set -euo pipefail

RC_DEFAULT_CASES='skills/hyper-design/assets/evals/contract-cases.jsonl'
RC_USAGE='Usage: bash run-contract-evals.sh [--cases <cases.jsonl>] [--json]'

rc_fail() {
  printf '%s\n' "$(jq -cn --arg error "$1" '{ok: false, error: $error}')" >&2
  exit 2
}

# rc_command_script <command> prints the script that implements one contract command.
rc_command_script() {
  case "$1" in
    report) printf 'skills/hyper-design/scripts/validate-report.sh' ;;
    waiver) printf 'skills/hyper-design/scripts/validate-waivers.sh' ;;
    rendered) printf 'skills/hyper-design/scripts/collect-rendered-evidence.sh' ;;
    *) return 1 ;;
  esac
}

rc_main() {
  local cases=$RC_DEFAULT_CASES json=0 help=0 line index=0 total=0 results='' output ok
  local case_json case_status id command input expected case_script flag code out err work
  while [ $# -gt 0 ]; do
    case "$1" in
      --cases)
        shift
        cases=${1-}
        case "$cases" in ''|--*) rc_fail '--cases requires a path' ;; esac
        if [ $# -gt 0 ]; then shift; fi ;;
      --json) json=1; shift ;;
      --help|-h) help=1; shift; break ;;
      *) rc_fail "Unknown argument: $1" ;;
    esac
  done
  if [ "$help" = 1 ]; then
    printf '%s\n' "$RC_USAGE"
    return 0
  fi
  [ -f "$cases" ] || rc_fail "ENOENT: no such file or directory, open '$cases'"
  work=$(mktemp "${TMPDIR:-/tmp}/slop-contracts.XXXXXX")
  while IFS= read -r line || [ -n "$line" ]; do
    total=$((total + 1))
    index=$total
    line=${line%$'\r'}
    [ -n "$line" ] || continue
    if ! printf '%s' "$line" | jq . > /dev/null 2>&1; then
      rm -f -- "$work"
      rc_fail "Invalid JSONL at line $index: invalid JSON"
    fi
    case_json=$(printf '%s' "$line" | jq -c .)
    case_status=$(printf '%s' "$case_json" | jq -r '
      if type != "object" then "invalid"
      elif (.id | type) != "string" then "invalid"
      elif (.command | type) != "string" then "invalid"
      elif (.input | type) != "string" then "invalid"
      elif (.expectedExit | type) != "number" or ((.expectedExit | floor) != .expectedExit) then "invalid"
      else "ok" end')
    command=$(printf '%s' "$case_json" | jq -r '.command // ""')
    if [ "$case_status" != ok ] || ! case_script=$(rc_command_script "$command"); then
      rm -f -- "$work"
      rc_fail "Invalid case at line $index"
    fi
    id=$(printf '%s' "$case_json" | jq -r '.id')
    input=$(printf '%s' "$case_json" | jq -r '.input')
    expected=$(printf '%s' "$case_json" | jq -r '.expectedExit')
    if [ "$command" = report ]; then flag='--report'; else flag='--input'; fi
    set +e
    bash "$case_script" "$flag" "$input" --json > "$work.out" 2> "$work.err"
    code=$?
    set -e
    out=$(cat -- "$work.out")
    err=$(cat -- "$work.err")
    failures=''
    if [ "$code" != "$expected" ]; then
      failures="Expected exit $expected, received $code"
    fi
    local expected_error matches
    expected_error=$(printf '%s' "$case_json" | jq -r '.expectedError // ""')
    if [ -n "$expected_error" ]; then
      matches=$(printf '%s\n%s' "$out" "$err" | LC_ALL=C grep -c -F -- "$expected_error" || true)
      if [ "$matches" = 0 ]; then
        if [ -z "$failures" ]; then failures="Missing expected error: $expected_error"; else failures="$failures; Missing expected error: $expected_error"; fi
      fi
    fi
    if [ -z "$failures" ]; then
      results="$results$(jq -cn --arg id "$id" '{id: $id, ok: true, failures: []}')"$'\n'
    else
      results="$results$(jq -cn --arg id "$id" --arg failures "$failures" '{id: $id, ok: false, failures: [$failures]}')"$'\n'
    fi
  done < "$cases"
  rm -f -- "$work" "$work.out" "$work.err"
  output=$(printf '%s' "$results" | jq -s '.')
  ok=$(printf '%s' "$output" | jq '[.[] | select(.ok == false)] | length == 0')
  if [ "$json" = 1 ]; then
    jq -n --argjson ok "$ok" --argjson cases "$output" '{ok: $ok, cases: $cases}'
  else
    printf '%s' "$output" | jq -r '.[] | if .ok then "PASS \(.id)" else "FAIL \(.id): \(.failures | join("; "))" end'
  fi
  [ "$ok" = true ]
}

rc_main "$@"
