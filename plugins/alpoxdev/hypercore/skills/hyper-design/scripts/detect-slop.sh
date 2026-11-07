#!/usr/bin/env bash
# Deterministic static slop detector: collect supported files, run the registered rules,
# and report stable JSON.
set -euo pipefail

DS_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$DS_DIR/rule-shared.sh"
# shellcheck source=/dev/null
source "$DS_DIR/engine-text.sh"
# shellcheck source=/dev/null
source "$DS_DIR/engine-css.sh"
# shellcheck source=/dev/null
source "$DS_DIR/engine-markup.sh"
# shellcheck source=/dev/null
source "$DS_DIR/resolve-context.sh"

DS_USAGE='Usage: bash detect-slop.sh --target <file-or-directory> [--json] [--rules a,b] [--baseline result.json --only-new]'
DS_LIMITATIONS='["Static source signatures do not prove design intent, rendered appearance, contrast, usability, or accessibility conformance.","Candidate exceptions preserve findings for review; they do not suppress a rule or authorize automatic removal.","Rendered, keyboard, and accessibility claims require capability-provided evidence."]'

# ds_error <message> <json-requested> prints a detector error and exits with code 2.
ds_error() {
  if [ "$2" = 1 ]; then
    printf '%s\n' "$(jq -cn --arg error "$1" '{error: $error, detectorVersion: 2}')" >&2
  else
    printf 'Error: %s\n' "$1" >&2
  fi
  exit 2
}

# ds_collect_files <absolute-target> <json-requested> prints every supported file in scan order.
ds_collect_files() {
  local abs_target=$1 json=$2 ext path
  if [ -f "$abs_target" ]; then
    ext=$(rs_extname "$abs_target")
    if ! rs_is_supported_ext "$ext"; then
      [ -n "$ext" ] || ext='(none)'
      ds_error "Unsupported file type: $ext" "$json"
    fi
    printf '%s\n' "$abs_target"
    return 0
  fi
  if [ ! -d "$abs_target" ]; then
    ds_error 'Target must be a supported file or directory' "$json"
  fi
  find "$abs_target" \( -name .git -o -name node_modules -o -name dist -o -name build -o -name coverage \
    -o -name .next -o -name .nuxt -o -name .svelte-kit \) -prune -o -type f -print 2>/dev/null |
    while IFS= read -r path; do
      if rs_is_supported_ext "$(rs_extname "$path")"; then printf '%s\n' "$path"; fi
    done |
    LC_ALL=C sort
}

# ds_ids_for <engine> <selected-ids-csv> prints the selected rules that run in one engine.
ds_ids_for() {
  local ids=$2
  if [ -n "$ids" ]; then ids=",$ids,"; fi
  rule_registry_rows | LC_ALL=C awk -F '\t' -v engine="$1" -v ids="$ids" '
    {
      if (ids != "" && index(ids, "," $1 ",") == 0) next
      count = split($4, engines, ",")
      for (i = 1; i <= count; i++) if (engines[i] == engine) { print $1; next }
    }'
}

# ds_candidate <rule-id> <textfile> <brand> <pricing> <state> prints the exception status.
ds_candidate() {
  local id=$1 textfile=$2 brand=$3 comparison=$4 live=$5
  case "$id" in
    surface.gradient-text|surface.purple-gradient)
      if [ "$brand" = 1 ]; then printf 'candidate'; return 0; fi ;;
    structure.three-equal-cards)
      if [ "$comparison" = 1 ] || LC_ALL=C grep -E -i -q 'pricing|plan|tier|comparison' "$textfile"; then
        printf 'candidate'; return 0
      fi ;;
    surface.status-dot|motion.pulse-without-state)
      if [ "$live" = 1 ] || LC_ALL=C grep -E -i -q 'recording|live|sync|unread' "$textfile"; then
        printf 'candidate'; return 0
      fi ;;
  esac
  printf 'not-checked'
}

# ds_emit_rows <file> <relative> <engine> <upstream-json> converts scan matches on stdin to findings.
ds_emit_rows() {
  local file=$1 rel=$2 engine=$3 meta=$4 brand=$5 comparison=$6 live=$7 rows=$8
  local id line excerpt metadata severity class evidence action fix cluster_key policy
  local exc confidence rem rcr
  while IFS=$'\t' read -r id _engine line excerpt; do
    [ -n "$id" ] || continue
    metadata=$(LC_ALL=C awk -F '\t' -v id="$id" '$1 == id { print $2 "\t" $3 "\t" $4 "\t" $5 "\t" $6 "\t" $7 "\t" $8; exit }' "$meta")
    severity=$(printf '%s' "$metadata" | cut -f1)
    class=$(printf '%s' "$metadata" | cut -f2)
    evidence=$(printf '%s' "$metadata" | cut -f3)
    action=$(printf '%s' "$metadata" | cut -f4)
    fix=$(printf '%s' "$metadata" | cut -f5)
    cluster_key=$(printf '%s' "$metadata" | cut -f6)
    policy=$(printf '%s' "$metadata" | cut -f7)
    exc=$(ds_candidate "$id" "$file" "$brand" "$comparison" "$live")
    confidence=medium
    [ "$class" = universal ] && confidence=high
    if [ "$exc" = candidate ]; then
      rem=low
    elif [ "$policy" = autofix-safe ]; then
      rem=medium
    else
      rem=low
    fi
    if [ "$class" = universal ]; then rcr=false; else rcr=true; fi
    printf '%s\t%s\t%s\t%s\n' "$rel" "$line" "$id" "$(jq -cn --arg id "$id" --arg severity "$severity" --arg confidence "$confidence" \
      --arg scope "$class" --arg file "$rel" --argjson line "$line" \
      --arg evidence "$evidence: $excerpt" --arg action "$action" --arg fix "$fix" \
      --arg engine "$engine" --arg detectionConfidence "$confidence" \
      --arg remediationConfidence "$rem" --arg ruleClass "$class" \
      --arg clusterKey "$cluster_key" --argjson renderConfirmationRequired "$rcr" \
      --arg exceptionStatus "$exc" \
      '{id: $id, severity: $severity, confidence: $confidence, scope: $scope,
        location: {file: $file, line: $line}, evidence: $evidence, action: $action, fix: $fix,
        engine: $engine, evidenceKind: "static-source", detectionConfidence: $detectionConfidence,
        remediationConfidence: $remediationConfidence, ruleClass: $ruleClass,
        clusterKey: $clusterKey, renderConfirmationRequired: $renderConfirmationRequired,
        exceptionStatus: $exceptionStatus}')" >> "$rows"
  done
}

ds_main() {
  local target='' baseline='' rules_arg='' only_new=0 json=0 help=0 rules_given=0 json_requested=0
  local arg abs_target root scanned=0 text_ids css_ids markup_ids engines='context'
  local context brand pricing state reduced token selected='' file rel ext
  local files_file meta rows findings final_file filtered_file baseline_fps
  local alltext first first_file baseline_used=false known=0 total=0 final_count=0
  local risk=low findings_json summary categories engines_json only_new_json=false

  for arg in "$@"; do
    case "$arg" in
      --json) json_requested=1 ;;
    esac
  done
  while [ $# -gt 0 ]; do
    case "$1" in
      --target) shift; target=${1-}; if [ $# -gt 0 ]; then shift; fi ;;
      --baseline) shift; baseline=${1-}; if [ $# -gt 0 ]; then shift; fi ;;
      --rules) shift; rules_arg=${1-}; rules_given=1; if [ $# -gt 0 ]; then shift; fi ;;
      --only-new) only_new=1; shift ;;
      --json) json=1; shift ;;
      --help|-h) help=1; shift ;;
      *) ds_error "Unknown argument: $1" "$json_requested" ;;
    esac
  done
  if [ "$help" = 1 ]; then
    printf '%s\n' "$DS_USAGE"
    return 0
  fi
  [ -n "$target" ] || ds_error '--target is required' "$json_requested"
  if [ "$only_new" = 1 ] && [ -z "$baseline" ]; then
    ds_error '--only-new requires --baseline <result.json>' "$json_requested"
  fi

  if [ "$rules_given" = 1 ]; then
    local saved_ifs=$IFS
    IFS=','
    for token in $rules_arg; do
      token=$(printf '%s' "$token" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
      [ -n "$token" ] || continue
      if ! rule_by_id_exists "$token"; then
        IFS=$saved_ifs
        ds_error "Unknown rule: $token" "$json_requested"
      fi
      selected="$selected,$token"
    done
    IFS=$saved_ifs
    [ -n "$selected" ] || selected=','
  fi

  abs_target=$(rs_resolve "$target")
  [ -e "$abs_target" ] || ds_error "ENOENT: no such file or directory, stat '$abs_target'" "$json_requested"
  if [ -d "$abs_target" ]; then
    root=$abs_target
  else
    root=$(dirname -- "$abs_target")
  fi

  files_file=$(mktemp "${TMPDIR:-/tmp}/slop-files.XXXXXX")
  meta=$(mktemp "${TMPDIR:-/tmp}/slop-meta.XXXXXX")
  rows=$(mktemp "${TMPDIR:-/tmp}/slop-rows.XXXXXX")
  findings=$(mktemp "${TMPDIR:-/tmp}/slop-findings.XXXXXX")
  alltext=$(mktemp "${TMPDIR:-/tmp}/slop-all.XXXXXX")
  final_file=$findings
  filtered_file=$findings
  baseline_fps=$findings
  : > "$rows"
  ds_collect_files "$abs_target" "$json_requested" > "$files_file"
  scanned=$(wc -l < "$files_file" | tr -d ' ')

  context=$(resolve_context "$abs_target")
  brand=$(printf '%s' "$context" | cut -f1)
  pricing=$(printf '%s' "$context" | cut -f2)
  state=$(printf '%s' "$context" | cut -f3)
  reduced=$(printf '%s' "$context" | cut -f4)

  text_ids=$(ds_ids_for text "$selected" | tr '\n' ',')
  css_ids=$(ds_ids_for css "$selected" | tr '\n' ',')
  markup_ids=$(ds_ids_for markup "$selected" | tr '\n' ',')

  rule_registry_rows | LC_ALL=C awk -F '\t' \
    '{ print $1 "\t" $2 "\t" $3 "\t" $5 "\t" $6 "\t" $7 "\t" $11 "\t" $10 }' > "$meta"

  first=1
  while IFS= read -r file; do
    [ -n "$file" ] || continue
    rel=${file#"$root"/}
    [ -n "$rel" ] || rel=$file
    if [ -n "$text_ids" ]; then
      scan_text "$file" "$file" "$root" "$text_ids" | ds_emit_rows "$file" "$rel" text "$meta" "$brand" "$pricing" "$state" "$rows"
      engines="$engines
text"
    fi
    if [ -n "$css_ids" ]; then
      scan_css "$file" "$file" "$root" "$css_ids" | ds_emit_rows "$file" "$rel" css "$meta" "$brand" "$pricing" "$state" "$rows"
      engines="$engines
css"
    fi
    ext=$(rs_extname "$file")
    if rs_is_markup_ext "$ext" && [ -n "$markup_ids" ]; then
      scan_markup "$file" "$file" "$root" "$markup_ids" | ds_emit_rows "$file" "$rel" markup "$meta" "$brand" "$pricing" "$state" "$rows"
      engines="$engines
markup"
    fi
    if [ "$first" = 1 ]; then first=0; else printf '\n' >> "$alltext"; fi
    cat -- "$file" >> "$alltext"
  done < "$files_file"

  if [ "$reduced" != 1 ] && LC_ALL=C grep -E -i -q 'animation[[:space:]]*:|@keyframes|(^|[^A-Za-z0-9_])animate-[A-Za-z0-9_-]+' "$alltext"; then
    first_file=$(head -n 1 "$files_file")
    rel=${first_file#"$root"/}
    [ -n "$rel" ] || rel=$first_file
    printf '%s\t1\tmotion.missing-reduced-motion\t%s\n' "$rel" "$(jq -cn --arg file "$rel" \
      '{id: "motion.missing-reduced-motion", severity: "P1", confidence: "high", scope: "universal",
        location: {file: $file, line: 1},
        evidence: "Motion signature exists without a project reduced-motion signature.: animation signature",
        action: "review", fix: "Check project-wide reduced-motion handling before adding a scoped fallback.",
        engine: "css", evidenceKind: "static-source", detectionConfidence: "high",
        remediationConfidence: "low", ruleClass: "universal", clusterKey: "motion-reduced-preference",
        renderConfirmationRequired: false, exceptionStatus: "not-checked"}')" >> "$rows"
  fi

  LC_ALL=C sort -s -t "$(printf '\t')" -k1,1 -k2,2n -k3,3 "$rows" | cut -f4- > "$findings"

  total=$(wc -l < "$findings" | tr -d ' ')
  known=0
  if [ -n "$baseline" ]; then
    baseline_used=true
    local baseline_abs
    baseline_abs=$(rs_resolve "$baseline")
    if [ ! -f "$baseline_abs" ]; then
      ds_error "Invalid baseline: ENOENT: no such file or directory, open '$baseline_abs'" "$json_requested"
    fi
    if ! jq . "$baseline_abs" > /dev/null 2>&1; then
      ds_error 'Invalid baseline: malformed JSON document' "$json_requested"
    fi
    if ! jq -e '(.detectorVersion == 2) and ((.findings | type) == "array")' "$baseline_abs" > /dev/null 2>&1; then
      ds_error 'Invalid baseline: expected detectorVersion 2 with findings array' "$json_requested"
    fi
    baseline_fps=$(mktemp "${TMPDIR:-/tmp}/slop-baseline.XXXXXX")
    : > "$baseline_fps"
    while IFS= read -r row; do
      [ -n "$row" ] || continue
      rs_fingerprint "$(jq -r '.id' <<< "$row")" "$(jq -r '.location.file' <<< "$row")" \
        "$(jq -r '.location.line' <<< "$row")" "$(jq -r '.evidence' <<< "$row")" >> "$baseline_fps"
    done < <(jq -c '.findings[]' "$baseline_abs")
    if [ "$only_new" = 1 ]; then
      filtered_file=$(mktemp "${TMPDIR:-/tmp}/slop-onlynew.XXXXXX")
      : > "$filtered_file"
      while IFS= read -r row; do
        [ -n "$row" ] || continue
        fp=$(rs_fingerprint "$(jq -r '.id' <<< "$row")" "$(jq -r '.location.file' <<< "$row")" \
          "$(jq -r '.location.line' <<< "$row")" "$(jq -r '.evidence' <<< "$row")")
        if ! grep -qxF -- "$fp" "$baseline_fps"; then printf '%s\n' "$row" >> "$filtered_file"; fi
      done < "$findings"
      final_file=$filtered_file
    fi
    known=$((total - $(wc -l < "$final_file" | tr -d ' ')))
  fi

  final_count=$(wc -l < "$final_file" | tr -d ' ')
  findings_json=$(jq -s '.' < "$final_file")
  summary=$(jq -s 'reduce .[] as $f ({P0: 0, P1: 0, P2: 0, P3: 0}; .[$f.severity] += 1)' < "$final_file")
  categories=$(jq -s '[.[] | select(.ruleClass == "default-risk" and .exceptionStatus != "candidate") | .id | split(".")[0]] | unique | length' < "$final_file")
  if [ "$categories" -ge 2 ]; then risk=medium; else risk=low; fi
  if [ "$only_new" = 1 ]; then only_new_json=true; fi
  engines_json=$(printf '%s\n' "$engines" | LC_ALL=C sort -u | jq -R . | jq -s '.')

  if [ "$json" = 1 ]; then
    jq -n --arg target "$target" --argjson scannedFiles "$scanned" --argjson engines "$engines_json" \
      --argjson findings "$findings_json" --argjson summary "$summary" --arg risk "$risk" \
      --argjson baselineUsed "$baseline_used" --argjson onlyNew "$only_new_json" --argjson known "$known" \
      --argjson limitations "$DS_LIMITATIONS" \
      '{target: $target, version: 2, detectorVersion: 2, scannedFiles: $scannedFiles,
        enginesRun: $engines, findings: $findings, summary: $summary, genericOutputRisk: $risk,
        baseline: {used: $baselineUsed, onlyNew: $onlyNew, knownFindingsFiltered: $known},
        limitations: $limitations}'
  else
    printf 'Scanned %s files; found %s findings (generic-output risk: %s).\n' "$scanned" "$final_count" "$risk"
  fi
  rm -f -- "$files_file" "$meta" "$rows" "$findings" "$alltext" "$filtered_file" "$baseline_fps"
}

ds_main "$@"
