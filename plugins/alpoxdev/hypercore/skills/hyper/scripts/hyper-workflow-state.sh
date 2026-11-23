#!/usr/bin/env bash
# hyper-workflow-state.sh — deterministic stage/step state manager for hyper and stateful skills.
#
# Usage:
#   bash <skill-dir>/scripts/hyper-workflow-state.sh init --root <dir> --slug <slug> --job <build|report|resume> \
#     --delivery <mode> --request <text> --stages <s1,s2,...> [--reasons <r1|r2|...>] [--state-file <relpath>] [--reentry]
#   bash <skill-dir>/scripts/hyper-workflow-state.sh enter --root <dir> --slug <slug> --stage <stage> [--state-file <relpath>]
#   bash <skill-dir>/scripts/hyper-workflow-state.sh complete --root <dir> --slug <slug> --stage <stage> \
#     --artifact <relpath|stage-note> [--note <text>] [--state-file <relpath>]
#   bash <skill-dir>/scripts/hyper-workflow-state.sh skip --root <dir> --slug <slug> --stage <stage> --reason <text> [--state-file <relpath>]
#   bash <skill-dir>/scripts/hyper-workflow-state.sh stop --root <dir> --slug <slug> --stage <stage> --reason <text> [--state-file <relpath>]
#   bash <skill-dir>/scripts/hyper-workflow-state.sh append-stage --root <dir> --slug <slug> --stage <stage> --reason <text> [--state-file <relpath>]
#   bash <skill-dir>/scripts/hyper-workflow-state.sh resume --root <dir> [--slug <slug>] [--state-file <relpath>]
#   bash <skill-dir>/scripts/hyper-workflow-state.sh verify --root <dir> --slug <slug> [--state-file <relpath>]
#
# Requires bash 3.2+, POSIX utilities, and jq. Zero network or external runtime dependencies.

set -euo pipefail

die() {
  printf 'hyper-workflow-state: %s\n' "$1" >&2
  exit 1
}

usage_err() {
  printf 'hyper-workflow-state: %s\n' "$1" >&2
  exit 2
}

command -v jq >/dev/null 2>&1 || die "jq is required"

now_iso() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

resolve_root() {
  local dir=$1
  [ -d "$dir" ] || die "root directory does not exist: $dir"
  (CDPATH='' cd -- "$dir" && pwd)
}

check_safe_relpath() {
  local rel=$1
  case $rel in
    '' | /* | *..*)
      die "unsafe or absolute relative path rejected: $rel"
      ;;
  esac
}

is_counted_stage() {
  local stage=$1
  local reentry=${2:-0}
  case $stage in
    hyper-git | hyper-browsing)
      return 1
      ;;
    hyper-handoff)
      if [ "$reentry" -eq 1 ]; then
        return 1
      fi
      return 0
      ;;
    *)
      return 0
      ;;
  esac
}

validate_chain_rules() {
  local csv=$1
  local reentry=${2:-0}
  local has_plan=0 has_debate=0 counted=0 total=0
  local old_ifs=$IFS
  local s
  IFS=','
  for s in $csv; do
    [ -n "$s" ] || continue
    total=$((total + 1))
    if [ "$s" = "hyper-plan" ]; then has_plan=1; fi
    if [ "$s" = "hyper-debate" ]; then has_debate=1; fi
    if is_counted_stage "$s" "$reentry"; then
      counted=$((counted + 1))
    fi
  done
  IFS=$old_ifs
  [ "$total" -gt 0 ] || die "at least one stage is required"
  if [ "$has_plan" -eq 1 ] && [ "$has_debate" -eq 1 ]; then
    die "cannot chain hyper-plan and hyper-debate in the same workflow"
  fi
  if [ "$counted" -gt 4 ]; then
    die "chain exceeds maximum of 4 counted core stages (got $counted)"
  fi
}

state_paths() {
  local root=$1 slug=$2 custom_state=$3
  if [ -n "$custom_state" ]; then
    check_safe_relpath "$custom_state"
    STATE_FILE="$root/$custom_state"
    MD_FILE=""
    STATE_REL="$custom_state"
  else
    [ -n "$slug" ] || usage_err "--slug is required when --state-file is omitted"
    case $slug in
      *[!A-Za-z0-9._-]* | '' | .* )
        die "invalid slug: $slug"
        ;;
    esac
    STATE_REL=".hyper/workflows/$slug/state.json"
    STATE_FILE="$root/$STATE_REL"
    MD_FILE="$root/.hyper/workflows/$slug.md"
  fi
}

render_markdown() {
  local state_file=$1 md_file=$2
  [ -n "$md_file" ] || return 0
  mkdir -p "$(dirname -- "$md_file")"
  local tmp="${md_file}.tmp.$$"
  jq -r '
    "# " + .slug + "\n\n" +
    "- 요청: " + .request + "\n" +
    "- 작업 종류: " + .job + "\n" +
    "- 전달: " + .delivery + "\n" +
    "- 상태: " + .status + "\n" +
    "- 정지 사유: " + (if (.stop_reason // "") == "" then "없음" else .stop_reason end) + "\n\n" +
    "## 단계\n\n" +
    "| # | 단계 | 선택 근거 | 상태 | 산출물 |\n" +
    "|---|---|---|---|---|\n" +
    (
      .stages
      | to_entries
      | map(
          "| " + ((.key + 1) | tostring) +
          " | " + .value.name +
          " | " + (.value.reason // "-") +
          " | " + .value.status +
          " | " + (if (.value.artifact // "") == "" then "-" else .value.artifact end) + " |"
        )
      | join("\n")
    ) + "\n\n## 단계 메모\n" +
    (
      .stages
      | to_entries
      | map(
          select((.value.note // "") != "")
          | "\n### " + ((.key + 1) | tostring) + ". " + .value.name + "\n" + .value.note + "\n"
        )
      | join("")
    )
  ' "$state_file" >"$tmp"
  mv "$tmp" "$md_file"
}

check_artifact_exists() {
  local root=$1 artifact=$2 note=${3:-}
  if [ "$artifact" = "stage-note" ]; then
    [ -n "$note" ] || die "stage-note artifact requires a non-empty --note"
    return 0
  fi
  check_safe_relpath "$artifact"
  local full="$root/$artifact"
  if [ -d "$full" ]; then
    local first_entry
    first_entry=$(find "$full" -mindepth 1 -maxdepth 2 -type f 2>/dev/null | head -n 1 || true)
    [ -n "$first_entry" ] || die "artifact directory exists but contains no files: $artifact"
    [ -s "$first_entry" ] || die "artifact directory contains only empty file: $first_entry"
    return 0
  fi
  [ -f "$full" ] || die "required stage artifact missing on disk: $artifact"
  [ -s "$full" ] || die "required stage artifact is empty on disk: $artifact"
}

SUBCMD=${1:-}
[ -n "$SUBCMD" ] || usage_err "missing subcommand (init|enter|complete|skip|stop|append-stage|resume|verify)"
shift

ROOT_ARG="."
SLUG=""
JOB="build"
DELIVERY="local"
REQUEST=""
STAGES_CSV=""
REASONS_PIPE=""
STAGE_NAME=""
ARTIFACT=""
NOTE=""
REASON=""
CUSTOM_STATE=""
REENTRY=0

while [ "$#" -gt 0 ]; do
  case $1 in
    --root)
      [ "$#" -ge 2 ] || usage_err "--root requires a value"
      ROOT_ARG=$2
      shift 2
      ;;
    --slug)
      [ "$#" -ge 2 ] || usage_err "--slug requires a value"
      SLUG=$2
      shift 2
      ;;
    --job)
      [ "$#" -ge 2 ] || usage_err "--job requires a value"
      JOB=$2
      shift 2
      ;;
    --delivery)
      [ "$#" -ge 2 ] || usage_err "--delivery requires a value"
      DELIVERY=$2
      shift 2
      ;;
    --request)
      [ "$#" -ge 2 ] || usage_err "--request requires a value"
      REQUEST=$2
      shift 2
      ;;
    --stages)
      [ "$#" -ge 2 ] || usage_err "--stages requires a value"
      STAGES_CSV=$2
      shift 2
      ;;
    --reasons)
      [ "$#" -ge 2 ] || usage_err "--reasons requires a value"
      REASONS_PIPE=$2
      shift 2
      ;;
    --stage)
      [ "$#" -ge 2 ] || usage_err "--stage requires a value"
      STAGE_NAME=$2
      shift 2
      ;;
    --artifact)
      [ "$#" -ge 2 ] || usage_err "--artifact requires a value"
      ARTIFACT=$2
      shift 2
      ;;
    --note)
      [ "$#" -ge 2 ] || usage_err "--note requires a value"
      NOTE=$2
      shift 2
      ;;
    --reason)
      [ "$#" -ge 2 ] || usage_err "--reason requires a value"
      REASON=$2
      shift 2
      ;;
    --state-file)
      [ "$#" -ge 2 ] || usage_err "--state-file requires a value"
      CUSTOM_STATE=$2
      shift 2
      ;;
    --reentry)
      REENTRY=1
      shift
      ;;
    -h | --help)
      sed -n '2,17p' "$0"
      exit 0
      ;;
    *)
      usage_err "unknown option: $1"
      ;;
  esac
done

ROOT=$(resolve_root "$ROOT_ARG")

case $SUBCMD in
  init)
    [ -n "$STAGES_CSV" ] || usage_err "init requires --stages"
    [ -n "$REQUEST" ] || usage_err "init requires --request"
    case $JOB in
      build | report | resume) ;;
      *) die "invalid --job '$JOB' (expected build, report, or resume)" ;;
    esac
    if [ -z "$CUSTOM_STATE" ]; then
      validate_chain_rules "$STAGES_CSV" "$REENTRY"
    fi
    state_paths "$ROOT" "$SLUG" "$CUSTOM_STATE"
    mkdir -p "$(dirname -- "$STATE_FILE")"
    TS=$(now_iso)
    TMP="${STATE_FILE}.tmp.$$"
    jq -n \
      --arg slug "${SLUG:-custom}" \
      --arg job "$JOB" \
      --arg delivery "$DELIVERY" \
      --arg request "$REQUEST" \
      --arg stages_csv "$STAGES_CSV" \
      --arg reasons_pipe "$REASONS_PIPE" \
      --arg ts "$TS" \
      --argjson reentry "$REENTRY" \
      '
      ($stages_csv | split(",") | map(select(length > 0))) as $names
      | ($reasons_pipe | if length > 0 then split("|") else [] end) as $reasons
      | {
          schema: "hyper-workflow-state/1",
          slug: $slug,
          job: $job,
          delivery: $delivery,
          request: $request,
          reentry: ($reentry == 1),
          status: "running",
          current_stage: null,
          stop_reason: null,
          created_at: $ts,
          updated_at: $ts,
          stages: (
            $names
            | to_entries
            | map({
                index: (.key + 1),
                name: .value,
                reason: ($reasons[.key] // "요청 신호 일치"),
                status: "pending",
                artifact: null,
                note: null,
                entered_at: null,
                completed_at: null
              })
          )
        }
      ' >"$TMP"
    mv "$TMP" "$STATE_FILE"
    render_markdown "$STATE_FILE" "$MD_FILE"
    CHAIN_STR=$(jq -r '.stages | map(.name) | join(" -> ")' "$STATE_FILE")
    printf '[라우팅: %s | 전달: %s | 상태 파일: %s]\n' "$CHAIN_STR" "$DELIVERY" "$STATE_REL"
    ;;

  enter)
    [ -n "$STAGE_NAME" ] || usage_err "enter requires --stage"
    state_paths "$ROOT" "$SLUG" "$CUSTOM_STATE"
    [ -f "$STATE_FILE" ] || die "state file not found: $STATE_REL"
    STAGE_IDX=$(jq -r --arg s "$STAGE_NAME" '(.stages | map(.name) | index($s)) // -1' "$STATE_FILE")
    [ "$STAGE_IDX" -ge 0 ] || die "stage '$STAGE_NAME' is not in workflow state"
    BLOCKING=$(jq -r --argjson idx "$STAGE_IDX" '
      .stages[:$idx]
      | map(select(.status != "done" and .status != "skipped") | .name)
      | join(", ")
    ' "$STATE_FILE")
    [ -z "$BLOCKING" ] || die "cannot enter '$STAGE_NAME' before prior stage(s) finish: $BLOCKING"
    TS=$(now_iso)
    TMP="${STATE_FILE}.tmp.$$"
    jq \
      --argjson idx "$STAGE_IDX" \
      --arg s "$STAGE_NAME" \
      --arg ts "$TS" \
      '
      .status = "running"
      | .stop_reason = null
      | .current_stage = $s
      | .updated_at = $ts
      | .stages[$idx].status = "running"
      | .stages[$idx].entered_at = (.stages[$idx].entered_at // $ts)
      ' "$STATE_FILE" >"$TMP"
    mv "$TMP" "$STATE_FILE"
    render_markdown "$STATE_FILE" "$MD_FILE"
    TOTAL=$(jq -r '.stages | length' "$STATE_FILE")
    HUMAN_IDX=$((STAGE_IDX + 1))
    printf '[현재 단계: %s/%s %s — 진행 중]\n' "$HUMAN_IDX" "$TOTAL" "$STAGE_NAME"
    ;;

  complete)
    [ -n "$STAGE_NAME" ] || usage_err "complete requires --stage"
    [ -n "$ARTIFACT" ] || usage_err "complete requires --artifact"
    state_paths "$ROOT" "$SLUG" "$CUSTOM_STATE"
    [ -f "$STATE_FILE" ] || die "state file not found: $STATE_REL"
    STAGE_IDX=$(jq -r --arg s "$STAGE_NAME" '(.stages | map(.name) | index($s)) // -1' "$STATE_FILE")
    [ "$STAGE_IDX" -ge 0 ] || die "stage '$STAGE_NAME' is not in workflow state"
    BLOCKING=$(jq -r --argjson idx "$STAGE_IDX" '
      .stages[:$idx]
      | map(select(.status != "done" and .status != "skipped") | .name)
      | join(", ")
    ' "$STATE_FILE")
    [ -z "$BLOCKING" ] || die "cannot complete '$STAGE_NAME' before prior stage(s) finish: $BLOCKING"
    check_artifact_exists "$ROOT" "$ARTIFACT" "$NOTE"
    TS=$(now_iso)
    TMP="${STATE_FILE}.tmp.$$"
    jq \
      --argjson idx "$STAGE_IDX" \
      --arg art "$ARTIFACT" \
      --arg note "$NOTE" \
      --arg ts "$TS" \
      '
      .stages[$idx].status = "done"
      | .stages[$idx].artifact = $art
      | .stages[$idx].note = (if $note == "" then .stages[$idx].note else $note end)
      | .stages[$idx].completed_at = $ts
      | .updated_at = $ts
      | ([.stages[] | select(.status != "done" and .status != "skipped") | .name][0] // null) as $next
      | .current_stage = $next
      | .status = (if $next == null then "done" else "running" end)
      ' "$STATE_FILE" >"$TMP"
    mv "$TMP" "$STATE_FILE"
    render_markdown "$STATE_FILE" "$MD_FILE"
    TOTAL=$(jq -r '.stages | length' "$STATE_FILE")
    NEXT_STAGE=$(jq -r '.current_stage // "없음"' "$STATE_FILE")
    HUMAN_IDX=$((STAGE_IDX + 1))
    printf '[현재 단계: %s/%s %s — 완료 | 산출물: %s | 다음: %s]\n' "$HUMAN_IDX" "$TOTAL" "$STAGE_NAME" "$ARTIFACT" "$NEXT_STAGE"
    ;;

  skip)
    [ -n "$STAGE_NAME" ] || usage_err "skip requires --stage"
    [ -n "$REASON" ] || usage_err "skip requires --reason"
    state_paths "$ROOT" "$SLUG" "$CUSTOM_STATE"
    [ -f "$STATE_FILE" ] || die "state file not found: $STATE_REL"
    STAGE_IDX=$(jq -r --arg s "$STAGE_NAME" '(.stages | map(.name) | index($s)) // -1' "$STATE_FILE")
    [ "$STAGE_IDX" -ge 0 ] || die "stage '$STAGE_NAME' is not in workflow state"
    TS=$(now_iso)
    TMP="${STATE_FILE}.tmp.$$"
    jq \
      --argjson idx "$STAGE_IDX" \
      --arg reason "$REASON" \
      --arg ts "$TS" \
      '
      .stages[$idx].status = "skipped"
      | .stages[$idx].note = $reason
      | .stages[$idx].completed_at = $ts
      | .updated_at = $ts
      | ([.stages[] | select(.status != "done" and .status != "skipped") | .name][0] // null) as $next
      | .current_stage = $next
      | .status = (if $next == null then "done" else "running" end)
      ' "$STATE_FILE" >"$TMP"
    mv "$TMP" "$STATE_FILE"
    render_markdown "$STATE_FILE" "$MD_FILE"
    TOTAL=$(jq -r '.stages | length' "$STATE_FILE")
    HUMAN_IDX=$((STAGE_IDX + 1))
    printf '[현재 단계: %s/%s %s — 건너뜀 | 사유: %s]\n' "$HUMAN_IDX" "$TOTAL" "$STAGE_NAME" "$REASON"
    ;;

  stop)
    [ -n "$STAGE_NAME" ] || usage_err "stop requires --stage"
    [ -n "$REASON" ] || usage_err "stop requires --reason"
    state_paths "$ROOT" "$SLUG" "$CUSTOM_STATE"
    [ -f "$STATE_FILE" ] || die "state file not found: $STATE_REL"
    STAGE_IDX=$(jq -r --arg s "$STAGE_NAME" '(.stages | map(.name) | index($s)) // -1' "$STATE_FILE")
    [ "$STAGE_IDX" -ge 0 ] || die "stage '$STAGE_NAME' is not in workflow state"
    TS=$(now_iso)
    TMP="${STATE_FILE}.tmp.$$"
    jq \
      --argjson idx "$STAGE_IDX" \
      --arg s "$STAGE_NAME" \
      --arg reason "$REASON" \
      --arg ts "$TS" \
      '
      .status = "stopped"
      | .stop_reason = $reason
      | .current_stage = $s
      | .updated_at = $ts
      | .stages[$idx].status = "stopped"
      | .stages[$idx].note = $reason
      ' "$STATE_FILE" >"$TMP"
    mv "$TMP" "$STATE_FILE"
    render_markdown "$STATE_FILE" "$MD_FILE"
    TOTAL=$(jq -r '.stages | length' "$STATE_FILE")
    HUMAN_IDX=$((STAGE_IDX + 1))
    printf '[현재 단계: %s/%s %s — 중단 | 사유: %s]\n' "$HUMAN_IDX" "$TOTAL" "$STAGE_NAME" "$REASON"
    ;;

  append-stage)
    [ -n "$STAGE_NAME" ] || usage_err "append-stage requires --stage"
    [ -n "$REASON" ] || usage_err "append-stage requires --reason"
    state_paths "$ROOT" "$SLUG" "$CUSTOM_STATE"
    [ -f "$STATE_FILE" ] || die "state file not found: $STATE_REL"
    # When hyper-plan is appended after debug/feedback handoff, drop pending hyper-git per stage-handoff §4.
    NEW_CSV=$(jq -r --arg s "$STAGE_NAME" '
      (if $s == "hyper-plan" then [.stages[] | select(.name != "hyper-git" or .status == "done") | .name] else [.stages[].name] end)
      + [$s]
      | join(",")
    ' "$STATE_FILE")
    REENTRY_FLAG=$(jq -r 'if .reentry then 1 else 0 end' "$STATE_FILE")
    if [ -z "$CUSTOM_STATE" ]; then
      validate_chain_rules "$NEW_CSV" "$REENTRY_FLAG"
    fi
    TS=$(now_iso)
    TMP="${STATE_FILE}.tmp.$$"
    jq \
      --arg s "$STAGE_NAME" \
      --arg reason "$REASON" \
      --arg ts "$TS" \
      '
      .stages = (
        (if $s == "hyper-plan" then [.stages[] | select(.name != "hyper-git" or .status == "done")] else .stages end)
        + [{
            index: 0,
            name: $s,
            reason: $reason,
            status: "pending",
            artifact: null,
            note: null,
            entered_at: null,
            completed_at: null
          }]
        | to_entries
        | map(.value + {index: (.key + 1)})
      )
      | .status = "running"
      | .current_stage = ([.stages[] | select(.status != "done" and .status != "skipped") | .name][0] // null)
      | .updated_at = $ts
      ' "$STATE_FILE" >"$TMP"
    mv "$TMP" "$STATE_FILE"
    render_markdown "$STATE_FILE" "$MD_FILE"
    CHAIN_STR=$(jq -r '.stages | map(.name) | join(" -> ")' "$STATE_FILE")
    printf '[체인 갱신: %s | 추가 단계: %s]\n' "$CHAIN_STR" "$STAGE_NAME"
    ;;

  resume)
    if [ -n "$CUSTOM_STATE" ] || [ -n "$SLUG" ]; then
      state_paths "$ROOT" "$SLUG" "$CUSTOM_STATE"
      [ -f "$STATE_FILE" ] || die "state file not found: $STATE_REL"
    else
      FOUND=""
      if [ -d "$ROOT/.hyper/workflows" ]; then
        while IFS= read -r candidate; do
          [ -n "$candidate" ] || continue
          st=$(jq -r '.status // ""' "$candidate" 2>/dev/null || true)
          if [ "$st" != "done" ]; then
            FOUND=$candidate
            break
          fi
        done < <(find "$ROOT/.hyper/workflows" -mindepth 2 -maxdepth 2 -name 'state.json' | LC_ALL=C sort)
      fi
      [ -n "$FOUND" ] || die "no open workflow state found under .hyper/workflows/"
      STATE_FILE=$FOUND
      STATE_REL=${STATE_FILE#"$ROOT"/}
    fi
    # Verify all done stages still have non-empty artifacts on disk
    DONE_COUNT=$(jq -r '[.stages[] | select(.status == "done")] | length' "$STATE_FILE")
    if [ "$DONE_COUNT" -gt 0 ]; then
      while IFS="$(printf '\t')" read -r d_name d_art d_note; do
        [ -n "$d_name" ] || continue
        if ! (check_artifact_exists "$ROOT" "$d_art" "$d_note") >/dev/null 2>&1; then
          die "artifact drift detected on resume: stage '$d_name' artifact missing or empty ($d_art)"
        fi
      done < <(jq -r '.stages[] | select(.status == "done") | [.name, (.artifact // ""), (.note // "")] | @tsv' "$STATE_FILE")
    fi
    NEXT_IDX=$(jq -r '([.stages | to_entries[] | select(.value.status != "done" and .value.status != "skipped") | .key][0]) // -1' "$STATE_FILE")
    TOTAL=$(jq -r '.stages | length' "$STATE_FILE")
    if [ "$NEXT_IDX" -lt 0 ]; then
      printf '[재개 확인: 모든 단계(%s/%s)가 이미 완료됨 | 상태 파일: %s]\n' "$TOTAL" "$TOTAL" "$STATE_REL"
      exit 0
    fi
    NEXT_NAME=$(jq -r --argjson i "$NEXT_IDX" '.stages[$i].name' "$STATE_FILE")
    HUMAN_IDX=$((NEXT_IDX + 1))
    printf '[현재 단계: %s/%s %s — 재개 대상 | 상태 파일: %s]\n' "$HUMAN_IDX" "$TOTAL" "$NEXT_NAME" "$STATE_REL"
    ;;

  verify)
    state_paths "$ROOT" "$SLUG" "$CUSTOM_STATE"
    [ -f "$STATE_FILE" ] || die "state file not found: $STATE_REL"
    WF_STATUS=$(jq -r '.status // ""' "$STATE_FILE")
    INCOMPLETE=$(jq -r '[.stages[] | select(.status != "done" and .status != "skipped") | (.name + ":" + .status)] | join(", ")' "$STATE_FILE")
    [ -z "$INCOMPLETE" ] || die "workflow has incomplete stages: $INCOMPLETE"
    [ "$WF_STATUS" = "done" ] || die "workflow status is '$WF_STATUS' (expected 'done')"
    while IFS="$(printf '\t')" read -r d_name d_art d_note; do
      [ -n "$d_name" ] || continue
      check_artifact_exists "$ROOT" "$d_art" "$d_note"
    done < <(jq -r '.stages[] | select(.status == "done") | [.name, (.artifact // ""), (.note // "")] | @tsv' "$STATE_FILE")
    TOTAL=$(jq -r '.stages | length' "$STATE_FILE")
    printf 'workflow state verified: %s (%s stage(s) complete)\n' "$STATE_REL" "$TOTAL"
    ;;

  *)
    usage_err "unknown subcommand: $SUBCMD"
    ;;
esac
