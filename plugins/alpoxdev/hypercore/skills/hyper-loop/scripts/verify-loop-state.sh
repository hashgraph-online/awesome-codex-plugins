#!/usr/bin/env bash
# Verify a multi-goal loop's ledger against the current worktree snapshot.
#
# Prints one JSON object per run. Read-only: it never writes loop state and never
# mutates the repository. Exit 0 means the requested proof holds; 1 means the
# state does not satisfy the request; 2 means the arguments or input files are
# unusable; git or input failures that block a decision exit 2.
set -euo pipefail

HL_USAGE='Usage: bash verify-loop-state.sh [snapshot] [--dir <loop-dir>] [--repo <path>] [--limit <n>]
       bash verify-loop-state.sh --goal <goal-id> --dir <loop-dir> [--repo <path>] [--limit <n>]
       bash verify-loop-state.sh --final <final-gate.json> [--dir <loop-dir>] [--repo <path>]
       bash verify-loop-state.sh --self-test
       bash verify-loop-state.sh --help

snapshot    print the current fingerprint as JSON: tree, diff_sha256, untracked entries.
--goal ID   compare goal ID'"'"'s criteria in <loop-dir>/ledger.jsonl with the current
            fingerprint and report pass, stale, failing, missing, or missing-evidence-file
            per criterion. Exits 1 when an essential criterion lacks fresh passing proof.
--final F   check <loop-dir>/final-gate.json: every criterion needs a fresh passing ledger
            row and a passing surface row, every declared surface needs a row, the gate
            status must be complete, and the gate must be bound to the current fingerprint.
--self-test build a throwaway git repository, prove a fresh snapshot passes, prove an edited
            file turns the proof stale, and prove --final rejects a missing criterion.

The fingerprint covers `git rev-parse HEAD^{tree}` and the SHA-256 of
`git diff --binary HEAD` concatenated with one "<sha256>\t<path>" line per sorted
untracked file. Ignored files and the loop directory itself are excluded, so
appending to ledger.jsonl never invalidates an earlier proof.

Exit codes: 0 verified; 1 proof does not hold; 2 usage, input, or git failure.'

HL_MODE=''
HL_DIR=''
HL_REPO=''
HL_GOAL=''
HL_GATE=''
HL_LIMIT=200
HL_TMP=''

hl_cleanup() {
  if [ -n "$HL_TMP" ] && [ -d "$HL_TMP" ]; then rm -rf "$HL_TMP"; fi
}
trap hl_cleanup EXIT

hl_sha256() { # <file>
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    sha256sum "$1" | cut -d' ' -f1
  fi
}

hl_fail() { # <code> <message> [exit]
  jq -cn --arg code "$1" --arg message "$2" '{status: "error", code: $code, message: $message}'
  exit "${3:-2}"
}

hl_workdir() {
  if [ -z "$HL_TMP" ]; then
    HL_TMP=$(mktemp -d "${TMPDIR:-/tmp}/hyper-loop-verify.XXXXXX") || hl_fail TMP_FAILED "cannot create a temporary directory"
  fi
  printf '%s\n' "$HL_TMP"
}

hl_abs_dir() { # <path> -> physical absolute directory path
  ( cd "$1" 2>/dev/null && pwd -P )
}

# hl_snapshot <repo> <exclude-rel> <workdir>
# Sets HL_TREE, HL_DIFF_SHA, HL_UNTRACKED_COUNT and writes <workdir>/untracked.json.
hl_snapshot() {
  local repo=$1 excl=$2 work=$3 diff=$3/diff untracked=$3/untracked sorted=$3/untracked.sorted
  local manifest=$3/untracked.manifest entries=$3/untracked.jsonl combined=$3/combined
  local p sha count=0 listed=0 limit=$HL_LIMIT truncated=false

  if ! HL_TREE=$(git -C "$repo" rev-parse 'HEAD^{tree}' 2>/dev/null); then
    hl_fail NOT_A_REPOSITORY "no git tree at HEAD under $repo"
  fi

  if [ -n "$excl" ]; then
    if ! git -C "$repo" diff --binary HEAD -- . ":(exclude)$excl" >"$diff" 2>"$work/diff.err"; then
      hl_fail GIT_DIFF_FAILED "git diff failed under $repo: $(tr -d '\n' <"$work/diff.err")"
    fi
  else
    if ! git -C "$repo" diff --binary HEAD >"$diff" 2>"$work/diff.err"; then
      hl_fail GIT_DIFF_FAILED "git diff failed under $repo: $(tr -d '\n' <"$work/diff.err")"
    fi
  fi

  if ! git -C "$repo" ls-files --others --exclude-standard >"$untracked" 2>"$work/ls.err"; then
    hl_fail GIT_LS_FAILED "git ls-files failed under $repo: $(tr -d '\n' <"$work/ls.err")"
  fi
  LC_ALL=C sort "$untracked" >"$sorted"
  : >"$manifest"
  : >"$entries"
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    if [ -n "$excl" ]; then
      case $p in
        "$excl"|"$excl"/*) continue ;;
      esac
    fi
    count=$((count + 1))
    sha=$(hl_sha256 "$repo/$p")
    printf '%s\t%s\n' "$sha" "$p" >>"$manifest"
    if [ "$listed" -lt "$limit" ]; then
      jq -cn --arg path "$p" --arg sha "$sha" '{path: $path, sha256: $sha}' >>"$entries"
      listed=$((listed + 1))
    else
      truncated=true
    fi
  done <"$sorted"

  cat "$diff" "$manifest" >"$combined"
  HL_DIFF_SHA=$(hl_sha256 "$combined")
  HL_UNTRACKED_COUNT=$count
  if [ -s "$entries" ]; then
    jq -s --argjson count "$count" --argjson truncated "$truncated" \
      '{untracked: ., untracked_count: $count, untracked_truncated: $truncated}' "$entries" >"$3/untracked.json"
  else
    jq -cn --argjson count "$count" --argjson truncated "$truncated" \
      '{untracked: [], untracked_count: $count, untracked_truncated: $truncated}' >"$3/untracked.json"
  fi
}

hl_resolve_repo() { # <loop-dir-or-empty>
  local dir=$1 top
  if [ -n "$HL_REPO" ]; then
    top=$(hl_abs_dir "$HL_REPO") || hl_fail REPO_MISSING "repository path does not exist: $HL_REPO"
  elif [ -n "$dir" ]; then
    top=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null) || hl_fail NOT_A_REPOSITORY "not inside a git worktree: $dir"
  else
    top=$(git rev-parse --show-toplevel 2>/dev/null) || hl_fail NOT_A_REPOSITORY "not inside a git worktree"
  fi
  printf '%s\n' "$top"
}

hl_exclusion() { # <repo-top> <loop-dir>
  local repo=$1 dir=$2 abs
  [ -n "$dir" ] || return 0
  abs=$(hl_abs_dir "$dir") || return 0
  case $abs in
    "$repo") return 0 ;;
    "$repo"/*) printf '%s\n' "${abs#"$repo"/}" ;;
  esac
}

# hl_ledger_row <ledger> <goal-id> <criterion-id>
# Prints the last evidence row for the criterion, or nothing.
hl_ledger_row() {
  local ledger=$1 goal=$2 crit=$3
  [ -f "$ledger" ] || return 0
  jq -c -s --arg g "$goal" --arg c "$crit" \
    '[.[] | select((.event // "evidence") == "evidence" and .goal_id == $g and .criterion_id == $c)] | last // empty' \
    "$ledger" 2>/dev/null || true
}

# hl_criterion_state <expected_evidence> <ledger-row-json> <tree> <diff_sha> <repo>
hl_criterion_state() {
  local expected=$1 row=$2 tree=$3 diff=$4 repo=$5
  local ev_path
  if [ -z "$row" ]; then
    printf 'missing\n'
    return 0
  fi
  if [ "$(printf '%s' "$row" | jq -r '.verdict // "fail"')" != "pass" ]; then
    printf 'failing\n'
    return 0
  fi
  if [ "$(printf '%s' "$row" | jq -r '.tree // ""')" != "$tree" ] ||
    [ "$(printf '%s' "$row" | jq -r '.diff_sha256 // ""')" != "$diff" ]; then
    printf 'stale\n'
    return 0
  fi
  ev_path=$expected
  case $ev_path in
    '') printf 'missing-evidence-file\n'; return 0 ;;
    /*) ;;
    *) ev_path=$repo/$ev_path ;;
  esac
  if [ ! -s "$ev_path" ]; then
    printf 'missing-evidence-file\n'
    return 0
  fi
  printf 'pass\n'
}

hl_mode_snapshot() {
  local dir=$1 repo excl work untracked
  repo=$(hl_resolve_repo "$dir")
  excl=$(hl_exclusion "$repo" "$dir")
  work=$(hl_workdir)
  hl_snapshot "$repo" "$excl" "$work"
  untracked=$(cat "$work/untracked.json")
  jq -cn --arg cwd "$repo" --arg tree "$HL_TREE" --arg diff "$HL_DIFF_SHA" --arg excl "$excl" \
    --argjson u "$untracked" \
    '{status: "ok", mode: "snapshot", cwd: $cwd, tree: $tree, diff_sha256: $diff, excluded: $excl,
      untracked: $u.untracked, untracked_count: $u.untracked_count, untracked_truncated: $u.untracked_truncated}'
}

hl_mode_goal() {
  local id=$1 dir=$2 repo excl work goals ledger tree diff row expected essential state crit
  local rows failures pass=0 stale=0 missing=0 failing=0 unverified=0 blocked=0
  local essential_fresh=true overall

  [ -n "$dir" ] || hl_fail DIR_REQUIRED "--goal requires --dir <loop-dir>"
  dir=$(hl_abs_dir "$dir") || hl_fail DIR_MISSING "loop directory does not exist: $2"
  goals=$dir/goals.json
  ledger=$dir/ledger.jsonl
  [ -f "$goals" ] || hl_fail GOALS_MISSING "goals file not found: $goals"
  jq -e --arg id "$id" '.goals | type == "array"' "$goals" >/dev/null 2>&1 ||
    hl_fail GOALS_INVALID "goals.json must hold a goals array: $goals"
  jq -e --arg id "$id" 'any(.goals[]; .id == $id)' "$goals" >/dev/null 2>&1 ||
    hl_fail GOAL_NOT_FOUND "goal not found in goals.json: $id"

  repo=$(hl_resolve_repo "$dir")
  excl=$(hl_exclusion "$repo" "$dir")
  work=$(hl_workdir)
  rows=$work/goal-rows.jsonl
  failures=$work/goal-failures.jsonl
  : >"$rows"
  : >"$failures"
  hl_snapshot "$repo" "$excl" "$work"
  tree=$HL_TREE
  diff=$HL_DIFF_SHA

  for crit in $(jq -r --arg id "$id" '.goals[] | select(.id == $id) | .criteria[].id' "$goals"); do
    expected=$(jq -r --arg id "$id" --arg c "$crit" \
      '.goals[] | select(.id == $id) | .criteria[] | select(.id == $c) | .expected_evidence // ""' "$goals")
    if jq -e --arg id "$id" --arg c "$crit" \
      '.goals[] | select(.id == $id) | .criteria[] | select(.id == $c) | (.essential == null or .essential == true)' \
      "$goals" >/dev/null 2>&1; then
      essential=true
    else
      essential=false
    fi
    row=$(hl_ledger_row "$ledger" "$id" "$crit")
    state=$(hl_criterion_state "$expected" "$row" "$tree" "$diff" "$repo")
    case $state in
      pass) pass=$((pass + 1)) ;;
      stale) stale=$((stale + 1)) ;;
      missing) missing=$((missing + 1)) ;;
      failing) failing=$((failing + 1)) ;;
      missing-evidence-file) unverified=$((unverified + 1)) ;;
      *) blocked=$((blocked + 1)) ;;
    esac
    if [ "$essential" = true ] && [ "$state" != pass ]; then
      essential_fresh=false
      jq -cn --arg ref "$id:$crit" --arg state "$state" '{criterionRef: $ref, reason: $state}' >>"$failures"
    fi
    jq -cn --arg id "$crit" --arg state "$state" --argjson essential "$essential" \
      --arg expected "$expected" --arg row "$row" \
      '{id: $id, essential: $essential, state: $state, expected_evidence: $expected,
        bound_tree: (if $row == "" then null else ($row | fromjson | .tree // null) end),
        bound_diff_sha256: (if $row == "" then null else ($row | fromjson | .diff_sha256 // null) end),
        capture_command: (if $row == "" then null else ($row | fromjson | .command // null) end)}' >>"$rows"
  done

  overall=fail
  if [ "$essential_fresh" = true ]; then overall=ok; fi
  jq -cn --arg status "$overall" --arg goal "$id" --arg tree "$tree" --arg diff "$diff" \
    --argjson essentialFresh "$essential_fresh" --slurpfile criteria "$rows" --slurpfile failures "$failures" \
    --argjson pass "$pass" --argjson stale "$stale" --argjson missing "$missing" \
    --argjson failing "$failing" --argjson unverified "$unverified" --argjson blocked "$blocked" \
    '{status: $status, mode: "goal", goal_id: $goal, tree: $tree, diff_sha256: $diff,
      essential_fresh: $essentialFresh, criteria: $criteria,
      summary: {total: ($criteria | length), pass: $pass, stale: $stale, missing: $missing,
        failing: $failing, missing_evidence_file: $unverified, other: $blocked},
      failures: $failures}'

  if [ "$essential_fresh" = true ]; then exit 0; fi
  exit 1
}

hl_mode_final() {
  local gate=$1 dir=$2 repo excl work goals tree diff gate_tree gate_diff gate_status bound
  local rows surfaces required covered surface_raw unique_bare crit goal_ref row state verdict missing_rows=0
  local pass=0 stale=0 missing=0 failing=0 unverified=0 all_ok=true status_ok=false surfaces_ok=true
  local essential=true expected surface

  [ -n "$gate" ] || hl_fail GATE_REQUIRED "--final requires a gate file path"
  [ -f "$gate" ] || hl_fail GATE_MISSING "gate file not found: $gate"
  jq -e 'type == "object"' "$gate" >/dev/null 2>&1 || hl_fail GATE_INVALID "gate file is not a JSON object: $gate"
  gate_status=$(jq -r '.status // ""' "$gate")
  case $gate_status in
    complete|blocked|paused) ;;
    '') hl_fail GATE_INVALID "gate file needs a status of complete, blocked, or paused: $gate" ;;
    *) hl_fail GATE_INVALID "gate status must be complete, blocked, or paused, found: $gate_status" ;;
  esac
  if [ "$gate_status" = complete ]; then status_ok=true; fi

  if [ -z "$dir" ]; then dir=$(cd "$(dirname -- "$gate")" && pwd -P); fi
  dir=$(hl_abs_dir "$dir") || hl_fail DIR_MISSING "loop directory does not exist: $2"
  goals=$dir/goals.json
  [ -f "$goals" ] || hl_fail GOALS_MISSING "goals file not found: $goals"

  repo=$(hl_resolve_repo "$dir")
  excl=$(hl_exclusion "$repo" "$dir")
  work=$(hl_workdir)
  rows=$work/final-rows.jsonl
  surfaces=$work/final-surfaces.jsonl
  required=$work/required-surfaces
  covered=$work/covered-surfaces
  surface_raw=$work/surface-rows.jsonl
  unique_bare=$work/unique-bare.json
  jq -c '[.goals[].criteria[].id] | group_by(.) | map(select(length == 1) | .[0])' "$goals" >"$unique_bare" \
    || hl_fail GOALS_INVALID "cannot list criterion ids from goals.json: $goals"
  : >"$rows"
  : >"$surfaces"
  : >"$required"
  : >"$covered"
  jq -c '.surfaceEvidence[]?' "$gate" >"$surface_raw" 2>/dev/null || : >"$surface_raw"
  hl_snapshot "$repo" "$excl" "$work"
  tree=$HL_TREE
  diff=$HL_DIFF_SHA
  gate_tree=$(jq -r '.tree // ""' "$gate")
  gate_diff=$(jq -r '.diff_sha256 // ""' "$gate")
  bound=false
  if [ "$gate_tree" = "$tree" ] && [ "$gate_diff" = "$diff" ]; then bound=true; fi

  for goal_ref in $(jq -r '.goals[].id' "$goals"); do
    for crit in $(jq -r --arg g "$goal_ref" '.goals[] | select(.id == $g) | .criteria[].id' "$goals"); do
      crit="$goal_ref:$crit"
      row=$(hl_ledger_row "$dir/ledger.jsonl" "$goal_ref" "${crit#*:}")
      expected=$(jq -r --arg g "$goal_ref" --arg c "${crit#*:}" \
        '.goals[] | select(.id == $g) | .criteria[] | select(.id == $c) | .expected_evidence // ""' "$goals")
      state=$(hl_criterion_state "$expected" "$row" "$tree" "$diff" "$repo")
      case $state in
        pass) pass=$((pass + 1)) ;;
        stale) stale=$((stale + 1)) ;;
        missing) missing=$((missing + 1)) ;;
        failing) failing=$((failing + 1)) ;;
        *) unverified=$((unverified + 1)) ;;
      esac
      if jq -e --arg g "$goal_ref" --arg c "${crit#*:}" \
        '.goals[] | select(.id == $g) | .criteria[] | select(.id == $c) | (.essential == null or .essential == true)' \
        "$goals" >/dev/null 2>&1; then
        essential=true
      else
        essential=false
      fi
      verdict=$(jq -r -s --arg ref "$crit" --arg bare "${crit#*:}" --argjson uniq "$(cat "$unique_bare")" \
        '[.[] | select(.criterionRef == $ref or (.criterionRef == $bare and ($uniq | index($bare) != null))) | .verdict // ""] | last // ""' \
        "$surface_raw")
      if [ "$verdict" != passed ]; then
        missing_rows=$((missing_rows + 1))
        all_ok=false
      fi
      if [ "$state" != pass ]; then
        all_ok=false
      fi
      jq -cn --arg ref "$crit" --arg state "$state" --arg surface "$verdict" --argjson essential "$essential" \
        '{criterionRef: $ref, evidence: $state, surface: (if $surface == "" then "missing" else $surface end),
          essential: $essential}' >>"$rows"
    done
  done

  jq -r '.goals[].surfaces[]?' "$goals" | LC_ALL=C sort -u >"$required" || true
  jq -r '.surfaceEvidence[]? | select(.verdict == "passed") | .surface // ""' "$gate" | LC_ALL=C sort -u >"$covered" || true
  while IFS= read -r surface; do
    [ -n "$surface" ] || continue
    if grep -qxF -- "$surface" "$covered" 2>/dev/null; then
      jq -cn --arg s "$surface" '{surface: $s, state: "covered"}' >>"$surfaces"
    else
      jq -cn --arg s "$surface" '{surface: $s, state: "missing"}' >>"$surfaces"
      surfaces_ok=false
      all_ok=false
    fi
  done <"$required"
  if [ ! -s "$surfaces" ]; then
    jq -cn '{surface: "-", state: "none-declared"}' >"$surfaces"
  fi

  overall=fail
  if [ "$bound" = true ] && [ "$status_ok" = true ] && [ "$all_ok" = true ] && [ "$surfaces_ok" = true ]; then
    overall=ok
  fi

  jq -cn --arg status "$overall" --arg gateStatus "$gate_status" --arg tree "$tree" --arg diff "$diff" \
    --argjson bound "$bound" --slurpfile criteria "$rows" --slurpfile surfaces "$surfaces" \
    --argjson pass "$pass" --argjson stale "$stale" --argjson missing "$missing" \
    --argjson failing "$failing" --argjson unverified "$unverified" --argjson surfaceMissing "$missing_rows" \
    '{status: $status, mode: "final", gate_status: $gateStatus, tree: $tree, diff_sha256: $diff,
      snapshot_bound: $bound, criteria: $criteria, surfaces: $surfaces,
      summary: {total: ($criteria | length), pass: $pass, stale: $stale, missing: $missing,
        failing: $failing, missing_evidence_file: $unverified, criteria_without_passing_surface: $surfaceMissing}}'

  if [ "$overall" = ok ]; then exit 0; fi
  exit 1
}

hl_mode_self_test() {
  local self tmp repo loop tree diff snapshot goal_rc final_rc stale_state okcase io
  command -v git >/dev/null 2>&1 || hl_fail SELF_TEST_NO_GIT "git is required for --self-test"

  self=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)/$(basename -- "$0")
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/hyper-loop-self-test.XXXXXX") || hl_fail SELF_TEST_TMP "cannot create a temporary directory"
  HL_TMP=$tmp
  repo=$tmp/repo
  loop=$repo/.hyper/loop/selftest
  mkdir -p "$repo/src" "$loop/evidence"
  printf 'one\n' >"$repo/src/app.txt"
  printf 'run 1\n' >"$loop/evidence/g1-c1.log"
  printf 'run 1\n' >"$loop/evidence/g1-c2.log"
  printf '# brief\n\nself test\n' >"$loop/brief.md"
  git -C "$repo" init -q
  git -C "$repo" add src/app.txt
  git -C "$repo" -c user.name=hyper-loop -c user.email=loop@example.invalid commit -q -m 'selftest: base'

  cat >"$loop/goals.json" <<'JSON'
{
  "schema_version": 1,
  "objective": "self test objective",
  "status": "active",
  "goals": [
    {
      "id": "G1",
      "title": "first goal",
      "status": "in_progress",
      "depends_on": [],
      "surfaces": ["cli"],
      "criteria": [
        {
          "id": "C1",
          "scenario": "run the shipped command with no arguments",
          "pass_condition": "the command exits 0 and writes src/app.txt output",
          "expected_evidence": ".hyper/loop/selftest/evidence/g1-c1.log",
          "essential": true,
          "cleanup": "no resources created"
        },
        {
          "id": "C2",
          "scenario": "run the shipped command with --help",
          "pass_condition": "the command prints usage and exits 0",
          "expected_evidence": ".hyper/loop/selftest/evidence/g1-c2.log",
          "essential": false,
          "cleanup": "no resources created"
        }
      ]
    }
  ]
}
JSON
  : >"$loop/ledger.jsonl"

  snapshot=$(bash "$self" snapshot --dir "$loop" --repo "$repo")
  tree=$(printf '%s' "$snapshot" | jq -r '.tree')
  diff=$(printf '%s' "$snapshot" | jq -r '.diff_sha256')
  [ -n "$tree" ] && [ -n "$diff" ] || hl_fail SELF_TEST_SNAPSHOT "snapshot returned no fingerprint"

  jq -cn --arg t "$tree" --arg d "$diff" --arg g G1 --arg c C1 \
    '{event: "evidence", goal_id: $g, criterion_id: $c, verdict: "pass", tree: $t, diff_sha256: $d,
      command: "bash verify-loop-state.sh --goal G1", evidence: "wrote src/app.txt output"}' >>"$loop/ledger.jsonl"
  jq -cn --arg t "$tree" --arg d "$diff" --arg g G1 --arg c C2 \
    '{event: "evidence", goal_id: $g, criterion_id: $c, verdict: "pass", tree: $t, diff_sha256: $d,
      command: "bash verify-loop-state.sh --goal G1", evidence: "printed usage"}' >>"$loop/ledger.jsonl"

  jq -cn --arg t "$tree" --arg d "$diff" \
    '{status: "complete", tree: $t, diff_sha256: $d,
      surfaceEvidence: [{criterionRef: "G1:C1", surface: "cli", invocation: "app", verdict: "passed", artifactRefs: ["log-1"]}]}' \
    >"$tmp/gate-missing.json"
  jq -cn --arg t "$tree" --arg d "$diff" \
    '{status: "complete", tree: $t, diff_sha256: $d,
      surfaceEvidence: [
        {criterionRef: "G1:C1", surface: "cli", invocation: "app", verdict: "passed", artifactRefs: ["log-1"]},
        {criterionRef: "G1:C2", surface: "cli", invocation: "app --help", verdict: "passed", artifactRefs: ["log-2"]}
      ]}' >"$tmp/gate-complete.json"

  goal_rc=0
  bash "$self" --goal G1 --dir "$loop" >"$tmp/goal-fresh.json" 2>&1 || goal_rc=$?
  final_rc=0
  bash "$self" --final "$tmp/gate-missing.json" --dir "$loop" >"$tmp/final-partial.json" 2>&1 || final_rc=$?

  printf 'two\n' >"$repo/src/app.txt"
  stale_rc=0
  bash "$self" --goal G1 --dir "$loop" >"$tmp/goal-stale.json" 2>&1 || stale_rc=$?

  okcase=0
  bash "$self" --final "$tmp/gate-complete.json" --dir "$loop" >"$tmp/final-stale.json" 2>&1 || okcase=$?

  io=true
  [ "$goal_rc" -eq 0 ] || io=false
  [ "$final_rc" -eq 1 ] || io=false
  [ "$stale_rc" -eq 1 ] || io=false
  [ "$okcase" -eq 1 ] || io=false
  grep -q '"stale"' "$tmp/goal-stale.json" || io=false
  [ "$(printf '%s' "$(cat "$tmp/final-partial.json")" | jq -r '.summary.criteria_without_passing_surface' 2>/dev/null)" = 1 ] || io=false
  [ "$(cat "$tmp/final-stale.json" | jq -r '.snapshot_bound' 2>/dev/null)" = false ] || io=false
  [ "$(cat "$tmp/goal-fresh.json" | jq -r '.status' 2>/dev/null)" = ok ] || io=false

  if [ "$io" = true ]; then
    jq -cn --arg tree "$tree" --arg diff "$diff" \
      '{ok: true, checks: {fresh_goal_exit: 0, partial_gate_exit: 1, stale_goal_exit: 1,
        stale_gate_exit: 1, stale_detected: true}, tree: $tree, diff_sha256: $diff}'
    exit 0
  fi
  jq -cn --argjson goalRc "$goal_rc" --argjson finalRc "$final_rc" --argjson staleRc "$stale_rc" \
    --argjson staleGateRc "$okcase" '{ok: false, rerun: "bash verify-loop-state.sh --self-test",
      exits: {fresh_goal: $goalRc, partial_gate: $finalRc, stale_goal: $staleRc, stale_gate: $staleGateRc}}'
  exit 1
}

while [ "$#" -gt 0 ]; do
  case $1 in
    --help|-h)
      printf '%s\n' "$HL_USAGE"
      exit 0
      ;;
    snapshot)
      [ -z "$HL_MODE" ] || hl_fail BAD_ARGUMENT "only one mode may be given (got $HL_MODE and snapshot)"
      HL_MODE=snapshot
      ;;
    --goal|--goal=*)
      [ -z "$HL_MODE" ] || hl_fail BAD_ARGUMENT "only one mode may be given (got $HL_MODE and --goal)"
      HL_MODE=goal
      case $1 in
        --goal=*) HL_GOAL=${1#--goal=} ;;
        *)
          shift
          [ "$#" -gt 0 ] || hl_fail BAD_ARGUMENT "--goal requires a goal id"
          HL_GOAL=$1
          ;;
      esac
      [ -n "$HL_GOAL" ] || hl_fail BAD_ARGUMENT "--goal requires a goal id"
      ;;
    --final|--final=*)
      [ -z "$HL_MODE" ] || hl_fail BAD_ARGUMENT "only one mode may be given (got $HL_MODE and --final)"
      HL_MODE=final
      case $1 in
        --final=*) HL_GATE=${1#--final=} ;;
        *)
          shift
          [ "$#" -gt 0 ] || hl_fail BAD_ARGUMENT "--final requires a gate file path"
          HL_GATE=$1
          ;;
      esac
      [ -n "$HL_GATE" ] || hl_fail BAD_ARGUMENT "--final requires a gate file path"
      ;;
    --self-test)
      [ -z "$HL_MODE" ] || hl_fail BAD_ARGUMENT "only one mode may be given (got $HL_MODE and --self-test)"
      HL_MODE=selftest
      ;;
    --dir|--dir=*)
      case $1 in
        --dir=*) HL_DIR=${1#--dir=} ;;
        *)
          shift
          [ "$#" -gt 0 ] || hl_fail BAD_ARGUMENT "--dir requires a path"
          HL_DIR=$1
          ;;
      esac
      ;;
    --repo|--repo=*)
      case $1 in
        --repo=*) HL_REPO=${1#--repo=} ;;
        *)
          shift
          [ "$#" -gt 0 ] || hl_fail BAD_ARGUMENT "--repo requires a path"
          HL_REPO=$1
          ;;
      esac
      ;;
    --limit|--limit=*)
      case $1 in
        --limit=*) HL_LIMIT=${1#--limit=} ;;
        *)
          shift
          [ "$#" -gt 0 ] || hl_fail BAD_ARGUMENT "--limit requires a number"
          HL_LIMIT=$1
          ;;
      esac
      case $HL_LIMIT in
        ''|*[!0-9]*) hl_fail BAD_ARGUMENT "--limit requires a non-negative integer, got: $HL_LIMIT" ;;
      esac
      ;;
    *)
      hl_fail BAD_ARGUMENT "unknown argument: $1"
      ;;
  esac
  shift
done

case $HL_MODE in
  snapshot) hl_mode_snapshot "$HL_DIR" ;;
  goal) hl_mode_goal "$HL_GOAL" "$HL_DIR" ;;
  final) hl_mode_final "$HL_GATE" "$HL_DIR" ;;
  selftest) hl_mode_self_test ;;
  '')
    hl_fail BAD_ARGUMENT "missing mode: use snapshot, --goal <id>, --final <file>, --self-test, or --help"
    ;;
esac