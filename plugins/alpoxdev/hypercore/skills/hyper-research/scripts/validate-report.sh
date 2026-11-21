#!/usr/bin/env bash
# Validate a saved research report for citation and number lineage defects.
#
# Reads the report and its sources ledger and prints the defects it finds:
# unsourced_number, section_without_citation, unresolved_citation, and
# missing_required_section. Exit 0 means no defect, 1 means at least one
# defect, and 2 means a usage error.
set -euo pipefail

VD_USAGE='Usage: bash validate-report.sh --report <report.md> --ledger <ledger.md> [--json]
       bash validate-report.sh --self-test
       bash validate-report.sh --help'

VD_REQUIRED='Executive Summary
Key Findings
Source Ledger
Query Log
Validation Notes
References'

VD_DEFECT_CAP=50

# Sections that describe the run or disclose an absence rather than make a
# sourced claim. They never carry a citation, so citation coverage skips them;
# a claim-bearing section without a citation is still a defect.
VD_EXEMPT='Scope And Fidelity
Query Log
Expansion Trace
Validation Notes
Report gates
Risks And Caveats
Known Gaps'

# A narrower set whose prose is pure run bookkeeping (budgets, counts, anchors,
# attempt logs). Its numbers are parameters of the run, not sourced claims.
# Risks And Caveats and Known Gaps stay out: a number there still needs a
# lineage label or a citation.
VD_NUMBER_EXEMPT='Scope And Fidelity
Query Log
Expansion Trace
Validation Notes
Report gates'

vd_awk_prog() {
  cat <<'VD_AWK'
function trim(s) {
  sub(/^[ \t\r\n]+/, "", s)
  sub(/[ \t\r\n]+$/, "", s)
  return s
}
function strip_tabs(s) {
  gsub(/\t/, " ", s)
  return s
}
function emit(code, line, text) {
  if (nout >= cap) return
  text = strip_tabs(text)
  if (length(text) > 200) text = substr(text, 1, 197) "..."
  nout++
  out[nout] = sprintf("%d\t%s\t%s", line, code, text)
}
# prose_len counts characters other than whitespace in a line.
function prose_len(s) {
  s = strip_tabs(s)
  gsub(/[ \t]+/, "", s)
  return length(s)
}
function line_is_prose(s) {
  if (s ~ /^[ \t]*$/) return 0
  if (s ~ /^[ \t]*```/) return 0
  if (s ~ /^#+[ \t]/) return 0
  if (s ~ /^[ \t]*\|/) return 0
  # The template header is a blockquote of run metadata (counts, as-of date).
  if (s ~ /^[ \t]*>/) return 0
  if (s ~ /^[ \t]*<!--/) return 0
  return 1
}
# number_tokens appends each distinct unsourced number in s to the global list.
# A token is one quantity: digits with optional thousands separators, an
# optional fraction (3.5), an optional percent suffix (37%), or a ratio (4:1).
# Words that merely contain digits (p95, h2, S1) are not tokens. Version-like
# forms are exempt: a v2.1 prefix, the word version followed by a number, and
# dotted sequences with two or more dots (1.2.3). A bare decimal stays a
# quantity (3.5%, 2.5 GB per second).
function number_tokens(s,   tok, seen, cnt, simple) {
  gsub(/\[S[0-9]+\]/, " ", s)
  gsub(/`[^`]*`/, " ", s)
  gsub(/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/, " ", s)
  gsub(/[0-9][0-9]?:[0-9][0-9](:[0-9][0-9])?/, " ", s)
  gsub(/([Ff]igure|[Ff]ig\.|[Tt]able)[ \t]*[0-9]+/, " ", s)
  gsub(/[vV][0-9]+(\.[0-9]+)+/, " ", s)
  gsub(/([Vv]ersion|[Vv])[ \t]+[0-9]+(\.[0-9]+)+/, " ", s)
  gsub(/[0-9]+(\.[0-9]+){2,}/, " ", s)
  split("", seen)
  cnt = 0
  s = " " s " "
  while (match(s, /([^A-Za-z0-9_]|^)[0-9][0-9,]*([.][0-9]+)?%?([:][0-9]+)?/)) {
    tok = substr(s, RSTART, RLENGTH)
    # Drop any leading separator character the match may have included.
    sub(/^[^0-9]/, "", tok)
    s = substr(s, RSTART + RLENGTH)
    # A percent suffix was captured; keep it so 37% and 37 differ.
    if (tok ~ /%/) {
      simple = tok
      sub(/%/, "", simple)
    } else {
      simple = tok
    }
    if (simple ~ /^(19|20)[0-9][0-9]$/) continue
    # A ratio stands alone as one token; its digits are never split out.
    if (tok in seen) continue
    seen[tok] = 1
    cnt++
    found[cnt] = tok
  }
  return cnt
}
BEGIN {
  cap = ENVIRON["VD_CAP"] + 0
  if (cap <= 0) cap = 50
  nout = 0

  ne = split(ENVIRON["VD_EXEMPT"], elist, "\n")
  for (i = 1; i <= ne; i++) {
    name = trim(elist[i])
    if (name != "") exempt[name] = 1
  }

  nn = split(ENVIRON["VD_NUMBER_EXEMPT"], nlist, "\n")
  for (i = 1; i <= nn; i++) {
    name = trim(nlist[i])
    if (name != "") num_exempt[name] = 1
  }

  n = 0
  while ((getline line < ENVIRON["VD_REPORT"]) > 0) {
    n++
    L[n] = line
  }
  close(ENVIRON["VD_REPORT"])

  while ((getline line < ENVIRON["VD_LEDGER"]) > 0) {
    if (split(line, cells, "|") >= 2) {
      cell = trim(cells[2])
      sub(/^\[/, "", cell)
      sub(/\]$/, "", cell)
      if (cell ~ /^S[0-9]+$/) known[cell] = 1
    }
  }
  close(ENVIRON["VD_LEDGER"])

  # Required sections.
  nreq = split(ENVIRON["VD_REQUIRED"], req, "\n")
  for (i = 1; i <= nreq; i++) {
    if (req[i] == "") continue
    found_heading = 0
    for (j = 1; j <= n; j++) {
      h = trim(L[j])
      if (h == "## " req[i]) found_heading = 1
    }
    if (!found_heading) emit("missing_required_section", 0, "## " req[i])
  }

  # Section citation coverage.
  infence = 0
  for (j = 1; j <= n; j++) {
    if (L[j] ~ /^[ \t]*```/) { infence = !infence; continue }
    if (infence) continue
    if (L[j] !~ /^## /) continue
    heading = trim(L[j])
    if ((substr(heading, 4)) in exempt) continue
    chars = 0
    cited = 0
    for (k = j + 1; k <= n; k++) {
      if (L[k] ~ /^#{1,2}[ \t]/) break
      if (L[k] ~ /^[ \t]*$/) continue
      if (L[k] ~ /^[ \t]*\|/) continue
      if (L[k] ~ /^[ \t]*```/) continue
      chars += prose_len(L[k])
      if (L[k] ~ /\[S[0-9]+\]/) cited = 1
    }
    if (heading ~ /\[S[0-9]+\]/) cited = 1
    if (chars > 120 && !cited) emit("section_without_citation", j, heading)
  }

  # Paragraph number lineage.
  infence = 0
  j = 1
  while (j <= n) {
    if (L[j] ~ /^[ \t]*```/) {
      infence = !infence
      j++
      continue
    }
    if (infence || !line_is_prose(L[j])) {
      j++
      continue
    }
    # A paragraph inside an exempt run-metadata section describes the run
    # (budgets, counts, anchors), so its numbers are not sourced claims.
    sec = ""
    for (s = j; s >= 1; s--) {
      if (L[s] ~ /^## /) { sec = substr(trim(L[s]), 4); break }
    }
    if (sec in num_exempt) {
      j++
      continue
    }
    start = j
    para = L[j]
    j++
    while (j <= n && line_is_prose(L[j])) {
      para = para " " trim(L[j])
      j++
    }
    if (para ~ /\[S[0-9]+\]/) continue
    if (para ~ /MEASURED|ASSUMED|DERIVED/) continue
    cnt = number_tokens(para)
    for (k = 1; k <= cnt; k++) emit("unsourced_number", start, para)
  }

  # Unresolved citations.
  infence = 0
  for (j = 1; j <= n; j++) {
    if (L[j] ~ /^[ \t]*```/) { infence = !infence; continue }
    if (infence) continue
    rest = L[j]
    while (match(rest, /\[S[0-9]+\]/) > 0) {
      marker = substr(rest, RSTART + 1, RLENGTH - 2)
      rest = substr(rest, RSTART + RLENGTH)
      if (marker in known) continue
      key = j SUBSEP marker
      if (key in reported) continue
      reported[key] = 1
      emit("unresolved_citation", j, marker)
    }
  }

  for (i = 1; i <= nout; i++) print out[i]
}
VD_AWK
}

# vd_validate <report> <ledger> prints TSV defects: line, code, text.
vd_validate() {
  local report=$1 ledger=$2
  VD_REPORT=$report VD_LEDGER=$ledger VD_REQUIRED=$VD_REQUIRED VD_CAP=$VD_DEFECT_CAP \
    VD_EXEMPT=$VD_EXEMPT VD_NUMBER_EXEMPT=$VD_NUMBER_EXEMPT \
    LC_ALL=C awk "$(vd_awk_prog)"
}

vd_self_ledger() {
  cat <<'VD_LEDGER'
# Sources

| # | Source | URL/path | Publisher | Published/updated | Accessed | Version/freshness | Channel | Grade | Role | Relevant claim | Used? | Caveat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | Example report | https://example.com/report | Example | 2026-01-02 | 2026-11-09 | 1.0 | web | S | primary-evidence | C1 | yes | |
| S2 | Example registry | https://example.org/registry | Example | 2026-02-03 | 2026-11-09 | 2.1 | web | A | supporting | C1 | yes | |
VD_LEDGER
}

vd_self_report() {
  cat <<'VD_REPORT'
# Example Research Report

> As of: 2026-11-09 | Depth: default | Run state: converged
> Sources reviewed: 2 | Sources cited: 2 | Domains: 2

## Executive Summary

Adoption grew in the surveyed period [S1].

## Scope And Fidelity

- Core question: did adoption grow
- Axes: one

## Key Findings

### 1. Adoption

- Claim: adoption grew by 20 percent [S1]
- Numbers: 20 percent MEASURED [S1]

## Comparison

| Criteria | Option A | Option B | Sources |
|---|---|---|---|
| Price | 1,200 | 2,400 | [S2] |

## Source Ledger

| # | Source | URL/path |
|---|---|---|
| S1 | Example report | https://example.com/report |
| S2 | Example registry | https://example.org/registry |

## Query Log

- adoption query, web search, axis one

## Validation Notes

- Gates: structure, citation, lineage, recency, read-back pass

## References

- [S1] [Example report](https://example.com/report), accessed 2026-11-09
- [S2] [Example registry](https://example.org/registry), accessed 2026-11-09
VD_REPORT
}

# vd_codes <report> <ledger> prints the sorted defect codes.
vd_codes() {
  vd_validate "$1" "$2" | cut -f2 | LC_ALL=C sort
}

# vd_case <id> <want> <actual> <pass> appends one case; its pass flag decides ok.
# The verdict comes from the same comparison that sets the case's actual, so a
# case never reports a pass it did not earn.
vd_case() {
  local id=$1 want=$2 actual=$3 pass=$4
  cases=$(jq -cn --argjson c "$cases" --arg id "$id" --argjson e "$want" --argjson a "$actual" \
    '$c + [{id: $id, expected: $e, actual: $a}]')
  [ "$pass" = true ] || { ok=false; }
}

vd_self_test() {
  local work base defects codes actual pass ok=true cases='[]'
  work=$(mktemp -d "${TMPDIR:-/tmp}/research-report.XXXXXX")
  vd_self_ledger >"$work/ledger.md"
  vd_self_report >"$work/base.md"
  base=$work/base.md

  defects=$(vd_validate "$base" "$work/ledger.md" | wc -l | tr -d ' ')
  actual=$([ "$defects" -eq 0 ] && echo true || echo false)
  pass=$([ "$defects" -eq 0 ] && echo true || echo false)
  vd_case valid-report-clean true "$actual" "$pass"

  # An exempt run-metadata section may hold long prose without a citation, but
  # a claim-bearing section may not.
  awk '/^## Scope And Fidelity$/ { print; print ""; print "This run covers the whole product line, every region, and both the current and previous major release, so the answer applies to the migration decision."; next } { print }' \
    "$base" >"$work/exempt-section.md"
  defects=$(vd_validate "$work/exempt-section.md" "$work/ledger.md" | wc -l | tr -d ' ')
  actual=$([ "$defects" -eq 0 ] && echo true || echo false)
  pass=$actual
  vd_case exempt-section-without-citation-clean true "$actual" "$pass"

  awk '/^## References$/ { print "## Recommendation"; print ""; print "Adopt the widget for the next migration cycle across every team that already runs the previous generation, and revisit the decision once the maintainers publish their next support policy."; print ""; print; next } { print }' \
    "$base" >"$work/uncited-findings.md"
  defects=$(vd_validate "$work/uncited-findings.md" "$work/ledger.md" | wc -l | tr -d ' ')
  codes=$(vd_codes "$work/uncited-findings.md" "$work/ledger.md" | tr '\n' ' ')
  actual=$([ "$defects" -eq 1 ] && [ "$codes" = "section_without_citation " ] && echo true || echo false)
  pass=$actual
  vd_case claim-section-without-citation-detected true "$actual" "$pass"

  awk '/^## Executive Summary$/ { print; print ""; print "Adoption grew 37% in 2025."; next } { print }' \
    "$base" >"$work/unsourced.md"
  defects=$(vd_validate "$work/unsourced.md" "$work/ledger.md" | wc -l | tr -d ' ')
  codes=$(vd_codes "$work/unsourced.md" "$work/ledger.md" | tr '\n' ' ')
  actual=$([ "$defects" -eq 1 ] && [ "$codes" = "unsourced_number " ] && echo true || echo false)
  pass=$actual
  vd_case unsourced-number-detected true "$actual" "$pass"

  awk '/^## Executive Summary$/ { print; print ""; print "Revenue grew 3.5% in 2025."; next } { print }' \
    "$base" >"$work/decimal.md"
  defects=$(vd_validate "$work/decimal.md" "$work/ledger.md" | wc -l | tr -d ' ')
  codes=$(vd_codes "$work/decimal.md" "$work/ledger.md" | tr '\n' ' ')
  actual=$([ "$defects" -eq 1 ] && [ "$codes" = "unsourced_number " ] && echo true || echo false)
  pass=$actual
  vd_case decimal-quantity-detected true "$actual" "$pass"

  awk '/^## Executive Summary$/ { print; print ""; print "Ships with v2.1 and 1.2.3."; next } { print }' \
    "$base" >"$work/version.md"
  defects=$(vd_validate "$work/version.md" "$work/ledger.md" | wc -l | tr -d ' ')
  actual=$([ "$defects" -eq 0 ] && echo true || echo false)
  pass=$actual
  vd_case version-tokens-clean true "$actual" "$pass"

  awk '/^## Executive Summary$/ { print; print ""; print "Released in 2025."; next } { print }' \
    "$base" >"$work/year-only.md"
  defects=$(vd_validate "$work/year-only.md" "$work/ledger.md" | wc -l | tr -d ' ')
  actual=$([ "$defects" -eq 0 ] && echo true || echo false)
  pass=$actual
  vd_case year-only-sentence-clean true "$actual" "$pass"

  awk '{ print } /^\| Price \|/ { print "| Volume | 37 | 42 | [S2] |" }' \
    "$base" >"$work/table.md"
  defects=$(vd_validate "$work/table.md" "$work/ledger.md" | wc -l | tr -d ' ')
  actual=$([ "$defects" -eq 0 ] && echo true || echo false)
  pass=$actual
  vd_case table-row-numbers-ignored true "$actual" "$pass"

  awk '/^## Executive Summary$/ { print; print ""; print "Market share is 12% [S9]."; next } { print }' \
    "$base" >"$work/unresolved.md"
  defects=$(vd_validate "$work/unresolved.md" "$work/ledger.md" | wc -l | tr -d ' ')
  codes=$(vd_codes "$work/unresolved.md" "$work/ledger.md" | tr '\n' ' ')
  actual=$([ "$defects" -eq 1 ] && [ "$codes" = "unresolved_citation " ] && echo true || echo false)
  pass=$actual
  vd_case unresolved-citation-detected true "$actual" "$pass"

  awk '!/^## References$/ && !/^- \[S1\]/ && !/^- \[S2\]/' "$base" >"$work/missing.md"
  defects=$(vd_validate "$work/missing.md" "$work/ledger.md" | wc -l | tr -d ' ')
  codes=$(vd_codes "$work/missing.md" "$work/ledger.md" | tr '\n' ' ')
  actual=$([ "$defects" -eq 1 ] && [ "$codes" = "missing_required_section " ] && echo true || echo false)
  pass=$actual
  vd_case missing-required-section-detected true "$actual" "$pass"

  rm -rf "$work"
  jq -n --argjson ok "$([ "$ok" = true ] && echo true || echo false)" --argjson cases "$cases" \
    '{ok: $ok, cases: $cases}'
  [ "$ok" = true ]
}

vd_main() {
  local help=0 self_test=0 report='' ledger='' json=0 errs ok defects
  if [ $# -eq 0 ]; then
    printf '%s\n' "$VD_USAGE" >&2
    exit 2
  fi
  while [ $# -gt 0 ]; do
    case "$1" in
      --report)
        shift
        report=${1-}
        case "$report" in '' | --*) printf '%s\n' '{"ok":false,"error":"--report requires a path"}' >&2; exit 2 ;; esac
        if [ $# -gt 0 ]; then shift; fi
        ;;
      --ledger)
        shift
        ledger=${1-}
        case "$ledger" in '' | --*) printf '%s\n' '{"ok":false,"error":"--ledger requires a path"}' >&2; exit 2 ;; esac
        if [ $# -gt 0 ]; then shift; fi
        ;;
      --json) json=1; shift ;;
      --self-test) self_test=1; shift ;;
      --help | -h) help=1; shift; break ;;
      *) printf '%s\n' "$(jq -cn --arg error "Unknown argument: $1" '{ok: false, error: $error}')" >&2; exit 2 ;;
    esac
  done
  if [ "$help" = 1 ]; then
    printf '%s\n' "$VD_USAGE"
    return 0
  fi
  if [ "$self_test" = 1 ]; then
    vd_self_test
    return $?
  fi
  [ -n "$report" ] || { printf '%s\n' '{"ok":false,"error":"--report is required"}' >&2; exit 2; }
  [ -n "$ledger" ] || { printf '%s\n' '{"ok":false,"error":"--ledger is required"}' >&2; exit 2; }
  if [ ! -f "$report" ] || [ ! -r "$report" ]; then
    printf '%s\n' "$(jq -cn --arg error "ENOENT: no such file or directory, open '$report'" '{ok: false, error: $error}')" >&2
    exit 2
  fi
  if [ ! -f "$ledger" ] || [ ! -r "$ledger" ]; then
    printf '%s\n' "$(jq -cn --arg error "ENOENT: no such file or directory, open '$ledger'" '{ok: false, error: $error}')" >&2
    exit 2
  fi

  errs=$(vd_validate "$report" "$ledger")
  if [ -z "$errs" ]; then
    ok=true
    defects='[]'
  else
    ok=false
    defects=$(printf '%s\n' "$errs" | LC_ALL=C sort -t "$(printf '\t')" -k1,1n -k2,2 |
      jq -Rn '[inputs | split("\t") | {code: .[1], line: (.[0] | tonumber), text: .[2]}]')
  fi
  if [ "$json" = 1 ]; then
    jq -n --argjson ok "$ok" --argjson defects "$defects" '{ok: $ok, defects: $defects}'
  elif [ "$ok" = true ]; then
    printf 'Report is valid.\n'
  else
    printf '%s\n' "$defects" | jq -r '.[] | "\(.code) (line \(.line)): \(.text)"' >&2
  fi
  [ "$ok" = true ]
}

vd_main "$@"
