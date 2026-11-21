#!/usr/bin/env bash
# Validate a saved slop-removal report against the bilingual section and evidence contract.
set -euo pipefail

VR_USAGE='Usage: bash validate-report.sh --report <report.md> [--json]
       bash validate-report.sh  # run self-tests'
VR_KOREAN=('# AI Design Slop 정리 결과' '## 처리 요약' '## Brief inference' '## 발견 사항' '## 적용한 변경' '## 검증' '## 남은 위험')
VR_ENGLISH=('# AI Design Slop Cleanup Result' '## Processing summary' '## Brief inference' '## Findings' '## Applied changes' '## Verification' '## Residual risk')

vr_awk_prog() {
  cat <<'VR_AWK'
function isspace(ch) { return index(" \t\n\r\f\v", ch) > 0 }
function trim(s) {
  sub(/^[ \t\r\n\f\v]+/, "", s)
  sub(/[ \t\r\n\f\v]+$/, "", s)
  return s
}
function label_value(t, pos,   i, ch, cap) {
  i = pos
  while (i <= tlen && isspace(substr(t, i, 1))) i++
  if (substr(t, i, 1) != ":") return 0
  i++
  while (i <= tlen && isspace(substr(t, i, 1))) i++
  cap = ""
  while (i <= tlen) {
    ch = substr(t, i, 1)
    if (ch == "\n") break
    cap = cap ch
    i++
  }
  if (cap == "") return 0
  g_val = trim(cap)
  return 1
}
function first_valid(tlower, torig, lab,   from, q, after) {
  from = 1
  while (1) {
    q = index(substr(tlower, from), lab)
    if (q == 0) return 0
    q = from + q - 1
    if (label_value(torig, q + length(lab))) return q
    from = q + 1
  }
}
function match_field(tlower, torig, l1, l2,   p1, p2, v1, v2) {
  p1 = first_valid(tlower, torig, l1)
  v1 = g_val
  p2 = 0; v2 = ""
  if (l2 != "") { p2 = first_valid(tlower, torig, l2); v2 = g_val }
  if (p1 == 0) return v2
  if (p2 == 0) return v1
  return (p1 <= p2) ? v1 : v2
}
function section_body(t, idx,   start, pos, i, rel, cand, endpos) {
  start = index(t, H[idx])
  if (start == 0) { sb_missing = 1; return "" }
  sb_missing = 0
  pos = start + length(H[idx])
  endpos = tlen + 1
  for (i = 1; i <= 7; i++) {
    rel = index(substr(t, pos), H[i])
    if (rel > 0) {
      cand = pos + rel - 1
      if (cand < endpos) endpos = cand
    }
  }
  return trim(substr(t, pos, endpos - pos))
}
function emit(code, heading, message) {
  if (heading != "") printf "%s\tH\t%s\n", code, heading
  else printf "%s\tM\t%s\n", code, message
}
function line_has(text, re,   lines, n, i) {
  n = split(text, lines, "\n")
  for (i = 1; i <= n; i++) if (lines[i] ~ re) return 1
  return 0
}
function waiver_conflict(text,   lines, n, i, line, q, rest, pos) {
  n = split(text, lines, "\n")
  for (i = 1; i <= n; i++) {
    line = lines[i]
    q = match(line, /candidate 또는 persisted waiver|candidate or persisted waivers/)
    if (q == 0) continue
    rest = substr(line, q + RLENGTH)
    pos = 1
    while (pos <= length(rest) && isspace(substr(rest, pos, 1))) pos++
    if (substr(rest, pos, 1) != ":") continue
    pos++
    while (pos <= length(rest) && isspace(substr(rest, pos, 1))) pos++
    if (substr(rest, pos, 1) == "`") pos++
    if (substr(rest, pos, 4) == "none") continue
    if (substr(rest, pos, 6) == "없음") continue
    return 1
  }
  return 0
}
BEGIN {
  FS = "\t"
  text = ""
  textfile = ENVIRON["VR_TEXTFILE"]
  while ((getline line < textfile) > 0) text = text line "\n"
  if (ENVIRON["VR_NOEOL"] == "1") sub(/\n$/, "", text)
  tlen = length(text)
  lower = tolower(text)
  split("", H)
  for (i = 1; i <= 7; i++) H[i] = ENVIRON["VR_H" i]
  korean = index(text, H[1]) > 0
  for (i = 1; i <= 7; i++) {
    body = section_body(text, i)
    if (sb_missing) emit("SECTION_MISSING", H[i], "")
    else if (i > 1 && body == "") emit("SECTION_EMPTY", H[i], "")
  }
  status = match_field(lower, text, tolower(ENVIRON["VR_STATUS1"]), tolower(ENVIRON["VR_STATUS2"]))
  if (!((status == "pass") || (status == "review_required") || (status == "blocked")))
    emit("STATUS_MISSING", "", "Final status must be pass, review_required, or blocked.")
  detector = match_field(lower, text, "detector", "")
  engines = match_field(lower, text, tolower(ENVIRON["VR_ENGINES1"]), "engines run")
  risk = match_field(lower, text, "generic-output risk", "")
  rendered = match_field(lower, text, tolower(ENVIRON["VR_RENDERED1"]), "render verification")
  baselinefield = match_field(lower, text, "baseline delta", "")
  if (detector == "") emit("DETECTOR_MISSING", "", "Processing summary must state detector status.")
  if (engines == "") emit("ENGINES_MISSING", "", "Processing summary must state engines run.")
  if (!((risk == "low") || (risk == "medium") || (risk == "high") || (risk == "unassessed")))
    emit("GENERIC_RISK_MISSING", "", "Generic-output risk must be low, medium, high, or unassessed.")
  if (!((rendered == "complete") || (rendered == "static_only") || (rendered == "unavailable")))
    emit("RENDER_STATUS_MISSING", "", "Render verification must be complete, static_only, or unavailable.")
  if (baselinefield == "") emit("BASELINE_MISSING", "", "Processing summary must state baseline delta.")
  if ((rendered == "static_only" || rendered == "unavailable") &&
      line_has(lower, "(visual|시각|accessibility|접근성).*(pass|통과)"))
    emit("RENDER_CLAIM_CONFLICT", "", "Unavailable/static-only rendering conflicts with a visual or accessibility pass.")
  if (line_has(lower, "ai[- ]?(authorship|작성|저작).*(confirmed|확정|pass|통과)"))
    emit("AUTHORSHIP_CLAIM", "", "Reports must not claim AI authorship.")
  if (waiver_conflict(lower) && lower !~ /reason|사유/)
    emit("WAIVER_REASON_MISSING", "", "A reported waiver needs a reason.")
  wcag_heading = line_has(lower, "^## .*wcag")
  wcag_required = ((status == "pass") && (rendered == "complete")) || (wcag_heading == 1)
  if (wcag_required) {
    n = split("1.4.3 1.4.11 2.4.7 2.4.11 2.5.8 2.1.1 2.1.2 1.4.10 1.4.12 2.5.7 3.3.8 3.2.6 3.3.7", ids, " ")
    nlines = split(lower, wlines, "\n")
    for (k = 1; k <= n; k++) {
      state = 0
      esc = ids[k]
      gsub(/\./, "\\.", esc)
      idre = "(^|[^0-9])" esc "([^0-9]|$)"
      for (j = 1; j <= nlines && state != 2; j++) {
        ln = wlines[j]
        if (index(ln, ids[k]) == 0) continue
        if (index(ln, "|") == 0) continue
        # criterion cell: the pipe-delimited cell holding the id as a token.
        # the cell must start with the id with a token boundary (rejects "1.4.30" for "1.4.3")
        ncells = split(ln, cells, "|")
        ci = 0
        for (c = 1; c <= ncells; c++) {
          if (cells[c] ~ idre) { ci = c; break }
        }
        if (ci == 0) continue
        # one row, one criterion: count distinct SC ids in the whole row
        idcount = 0
        for (m = 1; m <= n; m++) {
          esc2 = ids[m]
          gsub(/\./, "\\.", esc2)
          if (ln ~ ("(^|[^0-9])" esc2 "([^0-9]|$)")) idcount++
        }
        vcell = (ci + 1 <= ncells) ? trim(cells[ci + 1]) : ""
        sub(/^`+/, "", vcell); sub(/`+$/, "", vcell)
        vcell = trim(vcell)
        rcell = (ci + 2 <= ncells) ? trim(cells[ci + 2]) : ""
        ecell = (ci + 3 <= ncells) ? trim(cells[ci + 3]) : ""
        if (state == 0) state = 1
        if (idcount == 1 && (vcell == "pass" || vcell == "fail" || vcell == "n/a") && rcell != "" && ecell != "") { state = 2; break }
      }
      if (state == 0)
        emit("WCAG_TABLE_MISSING", "", "WCAG 2.2 table must list criterion " ids[k] " on its own table row with PASS, FAIL, or N/A, a reason, and evidence.")
      else if (state == 1)
        emit("WCAG_ROW_INCOMPLETE", "", "WCAG row for criterion " ids[k] " must have exactly one SC id, a verdict cell that is exactly PASS, FAIL, or N/A, and non-empty reason and evidence cells.")
    }
  }
}
VR_AWK
}

# vr_validate <textfile> prints TSV errors (code, kind, value).
vr_validate() {
  local textfile=$1 noeol=0
  if [ -s "$textfile" ] && [ -n "$(tail -c 1 "$textfile" 2>/dev/null)" ]; then noeol=1; fi
  VR_TEXTFILE="$textfile" VR_NOEOL="$noeol" \
    VR_H1="${VR_KOREAN[0]}" VR_H2="${VR_KOREAN[1]}" VR_H3="${VR_KOREAN[2]}" \
    VR_H4="${VR_KOREAN[3]}" VR_H5="${VR_KOREAN[4]}" VR_H6="${VR_KOREAN[5]}" VR_H7="${VR_KOREAN[6]}" \
    VR_STATUS1='최종 상태' VR_STATUS2='Final status' \
    VR_ENGINES1='실행한 engine' VR_RENDERED1='렌더링 검증' \
    LC_ALL=C awk "$(vr_awk_prog)"
}

# vr_validate_english is the same contract against the English headings.
vr_validate_english() {
  local textfile=$1 noeol=0
  if [ -s "$textfile" ] && [ -n "$(tail -c 1 "$textfile" 2>/dev/null)" ]; then noeol=1; fi
  VR_TEXTFILE="$textfile" VR_NOEOL="$noeol" \
    VR_H1="${VR_ENGLISH[0]}" VR_H2="${VR_ENGLISH[1]}" VR_H3="${VR_ENGLISH[2]}" \
    VR_H4="${VR_ENGLISH[3]}" VR_H5="${VR_ENGLISH[4]}" VR_H6="${VR_ENGLISH[5]}" VR_H7="${VR_ENGLISH[6]}" \
    VR_STATUS1='최종 상태' VR_STATUS2='Final status' \
    VR_ENGINES1='실행한 engine' VR_RENDERED1='렌더링 검증' \
    LC_ALL=C awk "$(vr_awk_prog)"
}

# vr_errors_json prints the JSON errors array for TSV errors on stdin.
vr_errors_json() {
  LC_ALL=C awk -F '\t' '{
    if ($2 == "H") printf "{\"code\":%s,\"heading\":%s}\n", jstr($1), jstr($3)
    else printf "{\"code\":%s,\"message\":%s}\n", jstr($1), jstr($3)
  }
  function jstr(s,   out, i, ch) {
    out = ""
    for (i = 1; i <= length(s); i++) {
      ch = substr(s, i, 1)
      if (ch == "\\") out = out "\\\\"
      else if (ch == "\"") out = out "\\\""
      else if (ch == "\n") out = out "\\n"
      else if (ch == "\t") out = out "\\t"
      else out = out ch
    }
    return "\"" out "\""
  }'
}

vr_self_report() {
  local rendered=$1
  printf '%s\n\n%s\n- Detector: v2\n- 실행한 engine: text | context\n- Baseline delta: 미사용\n- Generic-output risk: low\n- 렌더링 검증: %s\n- 최종 상태: pass\n%s\n- 확인됨\n%s\n- 없음\n%s\n- 없음\n%s\n- Detector/baseline: pass\n%s\n- 없음\n' \
    "${VR_KOREAN[0]}" "${VR_KOREAN[1]}" "$rendered" "${VR_KOREAN[2]}" "${VR_KOREAN[3]}" "${VR_KOREAN[4]}" "${VR_KOREAN[5]}" "${VR_KOREAN[6]}"
}

vr_self_test() {
  local work valid conflict invalid ok cases
  work=$(mktemp "${TMPDIR:-/tmp}/slop-report.XXXXXX")
  vr_self_report static_only > "$work"
  valid=$(vr_validate "$work" | wc -l | tr -d ' ')
  printf '\n시각 pass\n' >> "$work"
  conflict=$(vr_validate "$work" | wc -l | tr -d ' ')
  printf '# AI Design Slop 정리 결과\n\n## 처리 요약\n' > "$work"
  invalid=$(vr_validate "$work" | wc -l | tr -d ' ')
  rm -f -- "$work"
  ok=false
  [ "$valid" = 0 ] && [ "$conflict" != 0 ] && [ "$invalid" != 0 ] && ok=true
  cases=$(jq -cn --argjson v "$([ "$valid" = 0 ] && echo true || echo false)" \
    --argjson c "$([ "$conflict" = 0 ] && echo true || echo false)" \
    --argjson i "$([ "$invalid" = 0 ] && echo true || echo false)" \
    '[{id: "valid-v2-korean-report", expected: true, actual: $v},
      {id: "static-only-claim-rejected", expected: false, actual: $c},
      {id: "missing-sections-rejected", expected: false, actual: $i}]')
  jq -n --argjson ok "$ok" --argjson cases "$cases" '{ok: $ok, cases: $cases}'
  [ "$ok" = true ]
}

vr_main() {
  local help=0 self_test=0 report='' json=0 errs ok json_out
  if [ $# -eq 0 ]; then self_test=1; fi
  while [ $# -gt 0 ]; do
    case "$1" in
      --report) shift; report=${1-}; case "$report" in ''|--*) printf '%s\n' '{"ok":false,"error":"--report requires a path"}' >&2; exit 2 ;; esac; if [ $# -gt 0 ]; then shift; fi ;;
      --json) json=1; shift ;;
      --help|-h) help=1; shift; break ;;
      *) printf '%s\n' "$(jq -cn --arg error "Unknown argument: $1" '{ok: false, error: $error}')" >&2; exit 2 ;;
    esac
  done
  if [ "$help" = 1 ]; then
    printf '%s\n' "$VR_USAGE"
    return 0
  fi
  if [ "$self_test" = 1 ]; then
    vr_self_test
    return $?
  fi
  [ -n "$report" ] || { printf '%s\n' '{"ok":false,"error":"--report is required"}' >&2; exit 2; }
  if [ ! -f "$report" ] || [ ! -r "$report" ]; then
    printf '%s\n' "$(jq -cn --arg error "ENOENT: no such file or directory, open '$report'" '{ok: false, error: $error}')" >&2
    exit 2
  fi
  if LC_ALL=C grep -q -F -- "${VR_KOREAN[0]}" "$report"; then
    errs=$(vr_validate "$report")
  else
    errs=$(vr_validate_english "$report")
  fi
  if [ -z "$errs" ]; then
    json_out='[]'
    ok=true
  else
    json_out=$(printf '%s\n' "$errs" | vr_errors_json | jq -s .)
    ok=false
  fi
  if [ "$json" = 1 ]; then
    jq -n --argjson ok "$ok" --argjson errors "$json_out" '{ok: $ok, errors: $errors}'
  elif [ "$ok" = true ]; then
    printf 'Report is valid.\n'
  else
    printf '%s\n' "$json_out" | jq -r '.[] | "\(.code): \(.heading // .message)"' >&2
  fi
  [ "$ok" = true ]
}

vr_main "$@"
