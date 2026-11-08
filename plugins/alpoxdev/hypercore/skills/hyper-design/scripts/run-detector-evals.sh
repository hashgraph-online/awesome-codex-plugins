#!/usr/bin/env bash
# Run the detector eval cases against the static detector and report per-case agreement.
set -euo pipefail

RD_DEFAULT_CASES='skills/hyper-design/assets/evals/detector-cases.jsonl'
RD_DETECTOR='skills/hyper-design/scripts/detect-slop.sh'
RD_USAGE='Usage: bash run-detector-evals.sh [--cases <cases.jsonl>] [--json]'

rd_fail() {
  printf '%s\n' "$(jq -cn --arg error "$1" '{ok: false, error: $error}')" >&2
  exit 2
}

rd_main() {
  local cases=$RD_DEFAULT_CASES json=0 help=0 line index=0 total=0 failures='' results='' output ok
  local id target expect_error case_json case_status code out err work
  while [ $# -gt 0 ]; do
    case "$1" in
      --cases)
        shift
        cases=${1-}
        case "$cases" in ''|--*) rd_fail '--cases requires a path' ;; esac
        if [ $# -gt 0 ]; then shift; fi ;;
      --json) json=1; shift ;;
      --help|-h) help=1; shift; break ;;
      *) rd_fail "Unknown argument: $1" ;;
    esac
  done
  if [ "$help" = 1 ]; then
    printf '%s\n' "$RD_USAGE"
    return 0
  fi
  [ -f "$cases" ] || rd_fail "ENOENT: no such file or directory, open '$cases'"
  work=$(mktemp "${TMPDIR:-/tmp}/slop-evals.XXXXXX")
  while IFS= read -r line || [ -n "$line" ]; do
    total=$((total + 1))
    index=$total
    line=${line%$'\r'}
    [ -n "$line" ] || continue
    if ! printf '%s' "$line" | jq . > /dev/null 2>&1; then
      rm -f -- "$work"
      rd_fail "Invalid JSONL at line $index: invalid JSON"
    fi
    case_json=$(printf '%s' "$line" | jq -c .)
    case_status=$(printf '%s' "$case_json" | jq -r '
      if type != "object" then "row must be an object"
      elif (.id | type) != "string" or (.target | type) != "string" then "id and target are required strings"
      else "ok" end')
    if [ "$case_status" != ok ]; then
      rm -f -- "$work"
      rd_fail "Invalid JSONL at line $index: $case_status"
    fi
    id=$(printf '%s' "$case_json" | jq -r '.id')
    target=$(printf '%s' "$case_json" | jq -r '.target')
    expect_error=$(printf '%s' "$case_json" | jq -r 'if has("expectError") and .expectError == true then "1" else "0" end')
    set +e
    bash "$RD_DETECTOR" --target "$target" --json > "$work.out" 2> "$work.err"
    code=$?
    set -e
    out=$(cat -- "$work.out")
    err=$(cat -- "$work.err")
    failures=''
    if [ "$expect_error" = 1 ]; then
      [ "$code" = 2 ] || failures="Expected error exit 2, received $code"
    elif [ "$code" != 0 ]; then
      failures="Detector exited $code: $(printf '%s' "$err" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
    elif ! printf '%s' "$out" | jq . > /dev/null 2>&1; then
      failures='Detector did not emit JSON'
    else
      failures=$(printf '%s' "$out" | jq -r --argjson case "$case_json" '
        . as $o
        | [ ($o.findings // [])[] | .id ] as $ids
        | [ (if ($case | has("expectedDetectorVersion")) and (($o.detectorVersion // "undefined") != $case.expectedDetectorVersion)
               then "Expected detectorVersion \($case.expectedDetectorVersion), received \(if ($o | has("detectorVersion")) then ($o.detectorVersion | tostring) else "undefined" end)"
               else empty end),
            (($case.expectedContains // [])[] as $rid
              | if ($ids | index($rid)) == null then "Missing finding: \($rid)" else empty end),
            (($case.expectedAbsent // [])[] as $rid
              | if ($ids | index($rid)) != null then "Unexpected finding: \($rid)" else empty end),
            ((($case.expectedSummary // {}) | to_entries[]) as $entry
              | "\($entry.key)" as $sev
              | (if (($o.summary | type) == "object") and ($o.summary | has($sev))
                   then ($o.summary[$sev] | tostring) else "undefined" end) as $actual
              | if $actual != ($entry.value | tostring) then "Expected \($sev)=\($entry.value), received \($actual)" else empty end),
            ((($case.expectedExceptions // {}) | to_entries[]) as $entry
              | (($o.findings // []) | map(select(.id == $entry.key)) | first) as $finding
              | if $finding == null then "Missing exception finding: \($entry.key)"
                elif ($finding.exceptionStatus // "undefined") != $entry.value
                  then "Expected \($entry.key) exceptionStatus=\($entry.value), received \($finding.exceptionStatus // "undefined")"
                else empty end)
          ] | join("; ")')
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

rd_main "$@"
