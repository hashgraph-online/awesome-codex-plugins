#!/usr/bin/env bash
set -euo pipefail

SCOPE="auto"
EPIC_ID=""
COLLECTION_DETAIL=""
# Grace window (seconds) for close-before-commit evidence.
# Commits landing within this window after bead close are still considered valid.
GRACE_SECONDS=86400  # 24 hours

usage() {
  cat <<'EOF'
Usage: bash skills/post-mortem/scripts/closure-integrity-audit.sh [--scope auto|commit|staged|worktree] <epic-id>
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope)
      SCOPE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$EPIC_ID" ]]; then
        EPIC_ID="$1"
        shift
      else
        echo "Unknown arg: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
done

case "$SCOPE" in
  auto|commit|staged|worktree) ;;
  *)
    echo "Invalid --scope: $SCOPE" >&2
    usage >&2
    exit 2
    ;;
esac

[[ -n "$EPIC_ID" ]] || {
  echo "epic id is required" >&2
  usage >&2
  exit 2
}

command -v jq >/dev/null 2>&1 || {
  echo "jq is required" >&2
  exit 1
}

command -v br >/dev/null 2>&1 || {
  echo "br is required" >&2
  exit 1
}

FILE_PATH_REGEX='([.[:alnum:]_-]+/)*[.[:alnum:]_-]+\.[[:alpha:]][[:alnum:]_-]*'
GENERIC_REPO_PATH_REGEX='([.[:alnum:]_-]+/)+[.[:alnum:]_-]+\.[[:alpha:]][[:alnum:]_-]*'

json_array_from_stream() {
  if ! sed '/^[[:space:]]*$/d' | sort -u | jq -R . | jq -s .; then
    printf '[]\n'
  fi
}

run_git_clean() {
  env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR git "$@"
}

# br is the current tracker (bd/Dolt retired). It needs BEADS_DIR; default to the
# repo's nested ledger (_beads) when the caller has not set it. Resolved lazily so
# run_git_clean (defined above) is available at call time.
br_cmd() {
  local beads_dir="${BEADS_DIR:-$(run_git_clean rev-parse --show-toplevel 2>/dev/null || pwd)/_beads}"
  BEADS_DIR="$beads_dir" br "$@"
}

regex_escape_extended() {
  printf '%s' "$1" | sed -e 's/[][(){}.^$*+?|\\-]/\\&/g'
}

# issue_show_json prints the single issue object for an id (br show --json returns
# a one-element array; bd did too, so the unwrap is identical).
issue_show_json() {
  local issue_id="$1"
  br_cmd show "$issue_id" --json 2>/dev/null | jq -ec 'if type == "array" then .[0] // empty else . end'
}

issue_audit_text() {
  local child="$1"
  local child_json=""

  child_json="$(issue_show_json "$child" 2>/dev/null)" || return 0
  [[ -n "$child_json" ]] || return 0
  printf '%s\n' "$child_json" \
    | jq -r '
        [
          (.title // ""),
          (.description // ""),
          (.acceptance_criteria // ""),
          (.close_reason // "")
        ]
        | map(select(type == "string" and length > 0))
        | join("\n\n")
      '
}

# Children are the epic's parent-child dependents. br has no `children`
# subcommand; the authoritative source is `br show <epic> --json` .dependents
# (each carries dependency_type). The bd `children`/human-output collectors were
# removed with the bd retirement.
collect_children() {
  local children_output=""

  children_output="$(
    br_cmd show "$EPIC_ID" --json 2>/dev/null \
      | jq -er '
          .[]? |
          ((.dependents // .children // [])[]? |
            select((.dependency_type // .type // "parent-child") == "parent-child") |
            (.id // .child_id // .issue_id // empty))
        ' 2>/dev/null \
      | sed '/^[[:space:]]*$/d' \
      | sort -u
  )"

  if [[ -n "$children_output" ]]; then
    printf '%s\n' "$children_output"
    return 0
  fi

  COLLECTION_DETAIL="no child issues discovered from br show --json dependents"
  return 1
}

extract_validation_block_from_text() {
  awk '
    /^```validation[[:space:]]*$/ { in_block = 1; next }
    in_block && /^```[[:space:]]*$/ { exit }
    in_block { print }
  '
}

extract_validation_files_from_block() {
  local validation_block="$1"

  [[ -n "$validation_block" ]] || return 0
  printf '%s\n' "$validation_block" \
    | jq -r '
        def as_items:
          if type == "array" then .[]
          else .
          end;
        (
          (.files // [])[]?,
          (.files_exist // [])[]?,
          ((.content_check // empty) | as_items | .file?),
          ((.content_checks // empty) | as_items | .file?),
          ((.paired_files // empty) | as_items | .file?)
        )
        | select(type == "string" and length > 0)
      ' 2>/dev/null || true
}

extract_file_paths_from_stream() {
  grep -oE "$FILE_PATH_REGEX" || true
}

strip_urls_from_stream() {
  sed -E 's@[[:alpha:]][[:alnum:]+.-]*://[^[:space:])>]+@@g'
}

extract_first_file_path_from_stream() {
  extract_file_paths_from_stream | head -n 1
}

extract_files_section_from_text() {
  awk '
    tolower($0) ~ /^[[:space:]]*files:[[:space:]]*$/ { in_files = 1; next }
    tolower($0) ~ /^[[:space:]]*files likely owned:[[:space:]]*$/ { in_files = 1; next }
    tolower($0) ~ /^[[:space:]]*likely files:[[:space:]]*$/ { in_files = 1; next }
    tolower($0) ~ /^[[:space:]]*primary files:[[:space:]]*$/ { in_files = 1; next }
    tolower($0) ~ /^[[:space:]]*scoped files:[[:space:]]*$/ { in_files = 1; next }
    in_files {
      if ($0 ~ /^[[:space:]]*$/ || $0 ~ /^```/) {
        exit
      }
      # Accept lines starting with - or * (bullet points)
      if ($0 !~ /^[[:space:]]*[-*]/) {
        exit
      }
      # Strip bullet prefix and backticks
      sub(/^[[:space:]]*[-*][[:space:]]*/, "", $0)
      gsub(/`/, "", $0)
      print
    }
  ' | extract_file_paths_from_stream
}

extract_labeled_files_from_text() {
  local line=""
  local candidate=""

  while IFS= read -r line; do
    candidate=""

    if [[ "$line" =~ (^|[[:space:][:punct:]])New[[:space:]]+[Ff][Ii][Ll][Ee][Ss]?:[[:space:]]*(.*)$ ]]; then
      candidate="${BASH_REMATCH[2]}"
    elif [[ "$line" =~ (^|[[:space:][:punct:]])File:[[:space:]]*(.*)$ ]]; then
      candidate="${BASH_REMATCH[2]}"
    fi

    if [[ -n "$candidate" ]]; then
      printf '%s\n' "$candidate" | extract_first_file_path_from_stream
    fi
  done
}

extract_repo_relative_paths_from_text() {
  local line=""

  while IFS= read -r line; do
    printf '%s\n' "$line" \
      | strip_urls_from_stream \
      | grep -oE "$GENERIC_REPO_PATH_REGEX" || true
  done
}

extract_prose_file_paths_from_text() {
  strip_urls_from_stream | extract_file_paths_from_stream | grep -vx 'SKILL[.]md' || true
}

extract_validation_command_strings_from_block() {
  local validation_block="$1"

  [[ -n "$validation_block" ]] || return 0
  printf '%s\n' "$validation_block" \
    | jq -r '
        def roots:
          if type == "array" then .[]
          else .
          end;
        roots |
        (
          .command?,
          .commands[]?,
          .test?,
          .tests?,
          .validation_command?,
          .validation_commands[]?
        )
        | select(type == "string" and length > 0)
      ' 2>/dev/null || true
}

trim_path_punctuation() {
  printf '%s\n' "$1" | sed -E 's@[[:punct:]]+$@@; s@/$@@'
}

normalize_command_path() {
  local raw="$1"
  local cd_dir="$2"
  local path="$raw"
  local base=""

  path="${path#./}"
  path="${path%/}"
  cd_dir="${cd_dir#./}"
  cd_dir="${cd_dir%/}"
  path="$(trim_path_punctuation "$path")"
  cd_dir="$(trim_path_punctuation "$cd_dir")"

  [[ -n "$path" ]] || return 0
  if [[ -n "$cd_dir" && "$raw" == ./* ]]; then
    printf '%s/%s\n' "$cd_dir" "$path"
  elif [[ -n "$cd_dir" && "$raw" == ../* ]]; then
    base="$cd_dir"
    while [[ "$path" == ../* ]]; do
      path="${path#../}"
      if [[ "$base" == */* ]]; then
        base="${base%/*}"
      else
        base=""
      fi
    done
    if [[ -n "$base" ]]; then
      printf '%s/%s\n' "$base" "$path"
    else
      printf '%s\n' "$path"
    fi
  else
    printf '%s\n' "$path"
  fi
}

extract_paths_from_command_string() {
  local command_text="$1"
  local cd_dir=""
  local cd_regex='(^|[[:space:];|&])cd[[:space:]]+([^[:space:];|&]+)[[:space:]]*&&'
  local raw_path=""

  if [[ "$command_text" =~ $cd_regex ]]; then
    cd_dir="${BASH_REMATCH[2]}"
    cd_dir="${cd_dir%\"}"
    cd_dir="${cd_dir#\"}"
    cd_dir="${cd_dir%\'}"
    cd_dir="${cd_dir#\'}"
  fi

  {
    printf '%s\n' "$command_text" \
      | strip_urls_from_stream \
      | grep -oE '(\./)?([.[:alnum:]_-]+/)+[.[:alnum:]_-]+/?' || true
    printf '%s\n' "$command_text" \
      | strip_urls_from_stream \
      | extract_file_paths_from_stream
  } | while IFS= read -r raw_path; do
    normalize_command_path "$raw_path" "$cd_dir"
  done
}

filter_probable_repo_paths() {
  local path=""

  while IFS= read -r path; do
    path="$(trim_path_punctuation "$path")"
    [[ -n "$path" ]] || continue
    if [[ "$path" == ./* ]]; then
      path="${path#./}"
    fi
    while [[ "$path" == ../* ]]; do
      path="${path#../}"
    done

    case "$path" in
      .agents/*|.github/*|cli/*|docs/*|schemas/*|scripts/*|skills/*|skills-codex/*|hooks/*|tests/*|evals/*|lib/*)
        printf '%s\n' "$path"
        continue
        ;;
      AGENTS.md|GOALS.md|PRODUCT.md|README.md|SKILL-TIERS.md)
        printf '%s\n' "$path"
        continue
        ;;
    esac

    if [[ -e "$path" ]]; then
      printf '%s\n' "$path"
      continue
    fi
    if run_git_clean ls-files --error-unmatch -- "$path" >/dev/null 2>&1; then
      printf '%s\n' "$path"
    fi
  done
}

extract_command_paths_from_text() {
  local line=""

  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    extract_paths_from_command_string "$line"
  done
}

extract_validation_command_paths_from_block() {
  local validation_block="$1"
  local command_text=""

  extract_validation_command_strings_from_block "$validation_block" \
    | while IFS= read -r command_text; do
      extract_paths_from_command_string "$command_text"
    done
}

expand_scoped_paths_from_stream() {
  local path=""
  local expanded=""

  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    printf '%s\n' "$path"

    if [[ "$path" != */* && "$path" == *.* ]]; then
      expanded="$(run_git_clean ls-files --cached --others --exclude-standard -- "$path" ":(glob)**/$path" 2>/dev/null || true)"
      [[ -n "$expanded" ]] && printf '%s\n' "$expanded"
    fi
  done
}

extract_backticked_files_from_text() {
  # Handle backticked filenames across multiple lines, including nested backticks
  # and paths with spaces or special characters inside backticks
  tr '\n' '\0' \
    | grep -zoE "\`[^\`]+\`" \
    | tr '\0' '\n' \
    | tr -d '`' \
    | grep -E "$FILE_PATH_REGEX" \
    | grep -oE "$FILE_PATH_REGEX" || true
}

extract_scoped_files() {
  local child="$1"
  local audit_text=""
  local validation_block=""

  audit_text="$(issue_audit_text "$child")"

  validation_block="$(printf '%s\n' "$audit_text" | extract_validation_block_from_text)"

  {
    extract_validation_files_from_block "$validation_block"
    extract_validation_command_paths_from_block "$validation_block"
    printf '%s\n' "$audit_text" | extract_labeled_files_from_text
    printf '%s\n' "$audit_text" | extract_files_section_from_text
    printf '%s\n' "$audit_text" | extract_backticked_files_from_text
    printf '%s\n' "$audit_text" | extract_command_paths_from_text
    printf '%s\n' "$audit_text" | extract_repo_relative_paths_from_text
    printf '%s\n' "$audit_text" | extract_prose_file_paths_from_text
  } | sed '/^[[:space:]]*$/d' | expand_scoped_paths_from_stream | filter_probable_repo_paths | sort -u
}

issue_text_has_file_patterns() {
  # Returns 0 (true) if the bead's own structured text mentions file-like patterns
  # (contains "/" or ".go" or ".sh" or ".md"). Used to distinguish a genuine
  # parser miss from a bead that simply has no file scope at all.
  local child="$1"
  local audit_text=""

  audit_text="$(issue_audit_text "$child")"
  printf '%s\n' "$audit_text" | grep -qE '/|\.go|\.sh|\.md'
}

issue_timestamp() {
  local child_json="$1"
  local field="$2"
  printf '%s\n' "$child_json" | jq -r --arg field "$field" '.[$field] // empty'
}

commit_ref_exists() {
  local child="$1"
  local escaped_child
  local pattern

  escaped_child="$(regex_escape_extended "$child")"
  pattern="(^|[^[:alnum:]_.-])${escaped_child}([^[:alnum:]_.-]|$)"
  run_git_clean log -n 1 --format='%H' --all --extended-regexp --grep="$pattern" 2>/dev/null | grep -q .
}

target_is_closed_non_epic() {
  local target_id="$1"
  local target_json=""
  local issue_type=""

  target_json="$(issue_show_json "$target_id" 2>/dev/null)" || return 1
  [[ -n "$target_json" ]] || return 1
  child_is_closed "$target_json" || return 1
  issue_type="$(
    printf '%s\n' "$target_json" \
      | jq -r '(.issue_type // .type // "") | ascii_downcase'
  )"
  [[ "$issue_type" == "epic" ]] && return 1
  [[ -n "$issue_type" ]] && return 0
  return 1
}

extract_pr_numbers_from_text() {
  grep -Eio '((pull[ -]?request|pr)[[:space:]#:]*[0-9]+|pull/[0-9]+|#[0-9]+)' \
    | grep -oE '[0-9]+' \
    | sort -u || true
}

task_queue_pr_merge_matches_json() {
  local target_id="$1"
  local audit_text=""
  local pr_number=""
  local commit_sha=""
  local -a matches=()

  audit_text="$(issue_audit_text "$target_id")"
  while IFS= read -r pr_number; do
    [[ -n "$pr_number" ]] || continue
    commit_sha="$(
      run_git_clean log -n 1 --format='%H' --all --fixed-strings --grep="#${pr_number}" 2>/dev/null \
        | head -n 1
    )"
    if [[ -n "$commit_sha" ]]; then
      matches+=("#${pr_number} ${commit_sha}")
    fi
  done < <(printf '%s\n' "$audit_text" | extract_pr_numbers_from_text)

  if [[ "${#matches[@]}" -eq 0 ]]; then
    printf '[]\n'
    return 0
  fi

  printf '%s\n' "${matches[@]}" | json_array_from_stream
}

commit_matches_json() {
  local since="$1"
  local until="$2"
  shift 2
  local file
  local -a matched_files=()
  local -a git_args=(log -n 1 --format=%H --all --diff-filter=ACMR)

  [[ -n "$since" ]] && git_args+=("--since=$since")
  [[ -n "$until" ]] && git_args+=("--until=$until")

  for file in "$@"; do
    if run_git_clean "${git_args[@]}" -- "$file" 2>/dev/null | grep -q .; then
      matched_files+=("$file")
    fi
  done

  if [[ "${#matched_files[@]}" -eq 0 ]]; then
    printf '[]\n'
    return 0
  fi

  printf '%s\n' "${matched_files[@]}" | json_array_from_stream
}

staged_matches_json() {
  if [[ "$#" -eq 0 ]]; then
    printf '[]\n'
    return 0
  fi
  run_git_clean diff --cached --name-only --diff-filter=ACMR -- "$@" 2>/dev/null | json_array_from_stream
}

worktree_matches_json() {
  if [[ "$#" -eq 0 ]]; then
    printf '[]\n'
    return 0
  fi

  {
    run_git_clean diff --name-only --diff-filter=ACMR -- "$@" 2>/dev/null || true
    run_git_clean ls-files --others --exclude-standard -- "$@" 2>/dev/null || true
  } | json_array_from_stream
}

is_discovery_phase_path() {
  # Discovery-phase artifacts are ephemeral seeds for brainstorm/research/discovery
  # sessions. They are NOT durable proof surfaces. A closed bead that cites one
  # but never persisted it should not hard-fail closure-integrity-audit as long
  # as the bead has other real proof (commit referencing the id, a non-discovery
  # scoped file that does have evidence, or an evidence-only packet).
  local path="$1"
  [[ "$path" == .agents/brainstorm/* ]] && return 0
  [[ "$path" == .agents/research/* ]] && return 0
  [[ "$path" == .agents/discovery/* ]] && return 0
  return 1
}

all_scoped_files_are_discovery() {
  # Returns 0 (true) if every scoped file is a discovery-phase artifact AND
  # there is at least one such file. Empty input returns 1 (false).
  local file
  local any=1
  for file in "$@"; do
    any=0
    is_discovery_phase_path "$file" || return 1
  done
  return $any
}

child_has_nondiscovery_proof_surface() {
  # Returns 0 (true) if the bead has at least one non-discovery proof surface
  # that audits can replay against:
  #   - a commit message referencing the bead id
  #   - a durable evidence-only packet
  #   - a .agents/plans/ or .agents/findings/ file referenced in the bead text
  #     that actually exists on disk
  #   - any non-discovery file path referenced in the bead text (description +
  #     close reason) that has real git history
  # Used only to downgrade discovery-only timing misses to discovery_miss WARN.
  local child="$1"
  local packet_path=""

  if commit_ref_exists "$child"; then
    return 0
  fi
  if packet_path="$(durable_packet_path_for_child "$child")" && packet_is_valid_for_child "$packet_path" "$child"; then
    return 0
  fi

  local audit_text=""
  audit_text="$(issue_audit_text "$child" 2>/dev/null || true)"
  [[ -n "$audit_text" ]] || return 1

  # Collect all file-like paths from the bead's structured text (title +
  # description + acceptance + close reason). Filter to non-discovery paths.
  local candidate=""
  while IFS= read -r candidate; do
    [[ -n "$candidate" ]] || continue
    is_discovery_phase_path "$candidate" && continue
    case "$candidate" in
      .agents/plans/*|.agents/findings/*|.agents/council/*|.agents/releases/*)
        [[ -e "$candidate" ]] && return 0
        ;;
    esac
    # Any non-discovery file path that exists OR has git history counts.
    if [[ -e "$candidate" ]]; then
      return 0
    fi
    if run_git_clean log -n 1 --format=%H --all --diff-filter=ACMR -- "$candidate" 2>/dev/null | grep -q .; then
      return 0
    fi
  done < <(
    printf '%s\n' "$audit_text" \
      | strip_urls_from_stream \
      | extract_file_paths_from_stream \
      | sed '/^[[:space:]]*$/d' \
      | sort -u
  )

  # Last proof surface: a non-trivial close_reason (>= 24 chars). A substantive
  # close reason written at close time is itself auditable evidence that the
  # work was accepted. Empty or generic close reasons do NOT count.
  local child_json="" close_reason_len=0
  child_json="$(issue_show_json "$child" 2>/dev/null || true)"
  if [[ -n "$child_json" ]]; then
    close_reason_len="$(printf '%s\n' "$child_json" | jq -r '(.close_reason // "") | length')"
    if [[ "$close_reason_len" =~ ^[0-9]+$ && "$close_reason_len" -ge 24 ]]; then
      return 0
    fi
  fi

  return 1
}

child_is_closed() {
  local child_json="$1"

  printf '%s\n' "$child_json" \
    | jq -e '
        (.status // "" | ascii_downcase) == "closed" or
        ((.closed_at // "") | length > 0)
      ' >/dev/null 2>&1
}

add_grace_to_timestamp() {
  local ts="$1"
  local grace="$2"
  local normalized_ts=""
  local naive_ts=""
  local epoch=""

  [[ -n "$ts" ]] || return 1
  if date -d "$ts + ${grace} seconds" -Iseconds 2>/dev/null; then
    return 0
  fi

  # macOS date fallback: parse UTC Z or strip colon from timezone offset for %z.
  if [[ "$ts" == *Z ]]; then
    epoch="$(date -u -jf '%Y-%m-%dT%H:%M:%SZ' "$ts" '+%s' 2>/dev/null)" || true
  fi

  if [[ -z "$epoch" ]]; then
    normalized_ts="$ts"
    if [[ "$normalized_ts" =~ [+-][0-9]{2}:[0-9]{2}$ ]]; then
      normalized_ts="${normalized_ts%:*}${normalized_ts##*:}"
    fi
    epoch="$(date -jf '%Y-%m-%dT%H:%M:%S%z' "$normalized_ts" '+%s' 2>/dev/null)" || true
  fi

  if [[ -z "$epoch" ]]; then
    # Last resort: parse date portion only (loses TZ accuracy, acceptable for grace)
    naive_ts="$(printf '%s\n' "$ts" | sed -E 's/Z$//; s/[+-][0-9]{2}:?[0-9]{2}$//')"
    epoch="$(date -jf '%Y-%m-%dT%H:%M:%S' "$naive_ts" '+%s' 2>/dev/null)" || return 1
  fi

  date -u -r $((epoch + grace)) '+%Y-%m-%dT%H:%M:%S+00:00' 2>/dev/null
}

packet_is_valid_for_child() {
  local packet_path="$1"
  local child="$2"

  [[ -f "$packet_path" ]] || return 1
  # Accept any packet whose target_id matches and has at least one artifact.
  # The packet's evidence_mode field describes what was happening in the repo at
  # write time (commit/staged/worktree/auto); it does NOT determine whether the
  # packet itself is valid closure proof.  The file's presence at the
  # evidence-only-closures path is the proof — do not gatekeep on evidence_mode.
  jq -e --arg child "$child" '
    .target_id == $child and
    (.evidence.artifacts | type == "array" and length > 0)
  ' "$packet_path" >/dev/null 2>&1
}

durable_packet_path_for_child() {
  local child="$1"
  local safe_child="${child//\//_}"

  if [[ -f ".agents/releases/evidence-only-closures/${safe_child}.json" ]]; then
    printf '.agents/releases/evidence-only-closures/%s.json\n' "$safe_child"
    return 0
  fi
  if [[ -f ".agents/council/evidence-only-closures/${safe_child}.json" ]]; then
    printf '.agents/council/evidence-only-closures/%s.json\n' "$safe_child"
    return 0
  fi
  return 1
}

has_evidence_only_packet() {
  # Returns 0 iff a durable evidence-only closure packet exists for the given
  # target id AND parses as JSON containing both `evidence_mode` and
  # `repo_state` keys (the schema written by
  # skills/post-mortem/scripts/write-evidence-only-closure.sh).
  #
  # Used as a top-of-loop short-circuit in classify_child: when this returns 0,
  # the bead is accepted as fully closed (PASS, evidence-only-packet) and ALL
  # other classification paths (parser_miss, timing_miss, discovery_miss) are
  # skipped. This makes evidence-only packets the strongest proof surface.
  local target_id="$1"
  local safe_target="${target_id//\//_}"
  local packet_path=""

  if [[ -f ".agents/releases/evidence-only-closures/${safe_target}.json" ]]; then
    packet_path=".agents/releases/evidence-only-closures/${safe_target}.json"
  elif [[ -f ".agents/council/evidence-only-closures/${safe_target}.json" ]]; then
    packet_path=".agents/council/evidence-only-closures/${safe_target}.json"
  else
    return 1
  fi

  jq -e 'has("evidence_mode") and has("repo_state")' "$packet_path" >/dev/null 2>&1
}

packet_matches_json() {
  local packet_path="$1"

  jq -c --arg path "$packet_path" '[$path, (.evidence.artifacts[]?)] | unique' "$packet_path"
}

build_child_result() {
  local child="$1"
  local scoped_json="$2"
  local mode="$3"
  local detail="$4"
  local matches_json="$5"
  local status="$6"
  local closure_mode="${7:-}"

  jq -n \
    --arg child_id "$child" \
    --arg status "$status" \
    --arg evidence_mode "$mode" \
    --arg detail "$detail" \
    --arg closure_mode "$closure_mode" \
    --argjson scoped_files "$scoped_json" \
    --argjson matched_files "$matches_json" \
    '{
      child_id: $child_id,
      status: $status,
      evidence_mode: $evidence_mode,
      detail: $detail,
      scoped_files: $scoped_files,
      matched_files: $matched_files
    }
    + (if ($closure_mode | length) > 0 then {closure_mode: $closure_mode} else {} end)'
}

classify_task_queue_target() {
  local target_id="$1"
  local packet_path=""
  local packet_json=""
  local pr_merge_json=""

  target_is_closed_non_epic "$target_id" || return 1
  COLLECTION_DETAIL="${COLLECTION_DETAIL:-no child issues discovered from br show --json dependents}; task-queue fallback requires PR merge evidence in git history or a valid evidence-only closure packet"

  if packet_path="$(durable_packet_path_for_child "$target_id")" && packet_is_valid_for_child "$packet_path" "$target_id"; then
    packet_json="$(packet_matches_json "$packet_path")"
    build_child_result "$target_id" '[]' "evidence-only-packet" "task_queue_closure: matched durable closure proof packet for no-child target" "$packet_json" "pass" "task-queue"
    return 0
  fi

  if commit_ref_exists "$target_id"; then
    build_child_result "$target_id" '[]' "commit" "task_queue_closure: matched target id in git history for no-child target" '[]' "pass" "task-queue"
    return 0
  fi

  pr_merge_json="$(task_queue_pr_merge_matches_json "$target_id")"
  if echo "$pr_merge_json" | jq -e 'length > 0' >/dev/null 2>&1; then
    build_child_result "$target_id" '[]' "commit" "task_queue_closure: matched PR merge evidence in git history for no-child target" "$pr_merge_json" "pass" "task-queue"
    return 0
  fi

  return 1
}

# classify_single_epic_target handles a CLOSED epic that has no children of its
# own (a single-epic closure — work tracked and landed directly on the epic, not
# fanned out to child beads). It distinguishes a VALID commit-backed single-epic
# closure (landed SHAs / commit referencing the epic id / evidence-only packet /
# substantive close reason) from an INVALID no-child epic (closed with no proof).
# Without this, every legitimate single-epic closure trips collection_failed.
classify_single_epic_target() {
  local target_id="$1"
  local target_json="" issue_type="" close_reason="" packet_path="" packet_json=""

  target_json="$(issue_show_json "$target_id" 2>/dev/null || true)"
  [[ -n "$target_json" ]] || return 1
  child_is_closed "$target_json" || return 1
  issue_type="$(printf '%s\n' "$target_json" | jq -r '(.issue_type // .type // "") | ascii_downcase')"
  [[ "$issue_type" == "epic" ]] || return 1

  # Strongest proof: durable evidence-only closure packet.
  if packet_path="$(durable_packet_path_for_child "$target_id")" && packet_is_valid_for_child "$packet_path" "$target_id"; then
    packet_json="$(packet_matches_json "$packet_path")"
    build_child_result "$target_id" '[]' "evidence-only-packet" "single_epic_closure: matched durable closure proof packet for no-child epic" "$packet_json" "pass" "single-epic"
    return 0
  fi

  # Commit referencing the epic id directly in git history.
  if commit_ref_exists "$target_id"; then
    build_child_result "$target_id" '[]' "commit" "single_epic_closure: matched epic id in git history (commit-backed closure)" '[]' "pass" "single-epic"
    return 0
  fi

  # Close reason citing a landed SHA: each 7-40 hex token in the close reason is
  # a candidate commit ref, but a bare hex token is NOT proof — it must resolve to
  # a REAL commit in git history (else "done deadbeef" or an incidental hex word
  # would false-pass). Verify every candidate against the object database; only a
  # token that resolves to an actual commit counts. Generic close reasons with no
  # resolvable SHA do NOT count — an invalid no-child epic must still fail.
  local sha=""
  close_reason="$(printf '%s\n' "$target_json" | jq -r '.close_reason // ""')"
  while IFS= read -r sha; do
    [[ -n "$sha" ]] || continue
    if run_git_clean rev-parse --verify --quiet "${sha}^{commit}" >/dev/null 2>&1; then
      build_child_result "$target_id" '[]' "close-reason" "single_epic_closure: close reason cites a landed commit ($sha) for no-child epic" '[]' "pass" "single-epic"
      return 0
    fi
  done < <(printf '%s' "$close_reason" | grep -oE '\b[0-9a-f]{7,40}\b' | sort -u)

  return 1
}

classify_child() {
  local child="$1"
  local child_json=""
  local created_at=""
  local closed_at=""
  local packet_path=""
  local scoped_json commit_json staged_json worktree_json packet_json
  local -a scoped_files=()

  # Only closed children are audited; a child the tracker cannot resolve (no
  # json) is skipped silently (open children also skip).
  child_json="$(issue_show_json "$child" 2>/dev/null || true)"
  [[ -n "$child_json" ]] || return 0
  if ! child_is_closed "$child_json"; then
    return 0
  fi
  created_at="$(issue_timestamp "$child_json" "created_at")"
  closed_at="$(issue_timestamp "$child_json" "closed_at")"
  if [[ -z "$closed_at" ]]; then
    closed_at="$(issue_timestamp "$child_json" "updated_at")"
  fi

  # Evidence-only packet short-circuit: when a durable closure packet exists
  # for this bead AND it has the schema written by write-evidence-only-closure.sh
  # (must contain `evidence_mode` and `repo_state` keys), accept the bead as
  # fully closed and skip ALL other classification paths. Evidence-only packets
  # are the strongest proof surface — they bypass parser_miss, timing_miss, and
  # discovery_miss because the packet itself is the durable, replayable proof.
  if has_evidence_only_packet "$child"; then
    if packet_path="$(durable_packet_path_for_child "$child")"; then
      packet_json="$(packet_matches_json "$packet_path" 2>/dev/null || printf '[]')"
    else
      packet_json='[]'
    fi
    build_child_result "$child" '[]' "evidence-only-packet" "evidence-only closure packet accepted (short-circuit)" "$packet_json" "pass"
    return 0
  fi

  mapfile -t scoped_files < <(extract_scoped_files "$child")
  scoped_json="$(printf '%s\n' "${scoped_files[@]}" | json_array_from_stream)"

  case "$SCOPE" in
    auto|commit)
      if commit_ref_exists "$child"; then
        build_child_result "$child" "$scoped_json" "commit" "matched child id in git history" '[]' "pass"
        return 0
      fi
      commit_json="$(commit_matches_json "$created_at" "$closed_at" "${scoped_files[@]}")"
      if echo "$commit_json" | jq -e 'length > 0' >/dev/null 2>&1; then
        build_child_result "$child" "$scoped_json" "commit" "matched scoped files in git history during issue lifetime" "$commit_json" "pass"
        return 0
      fi
      # Grace window: check for close-before-commit pattern
      if [[ -n "$closed_at" ]]; then
        local grace_until=""
        grace_until="$(add_grace_to_timestamp "$closed_at" "$GRACE_SECONDS" 2>/dev/null)" || true
        if [[ -n "$grace_until" ]]; then
          commit_json="$(commit_matches_json "$created_at" "$grace_until" "${scoped_files[@]}")"
          if echo "$commit_json" | jq -e 'length > 0' >/dev/null 2>&1; then
            build_child_result "$child" "$scoped_json" "grace-window" "matched scoped files in git history within grace window after close (close-before-commit)" "$commit_json" "pass"
            return 0
          fi
        fi
      fi
      if [[ "$SCOPE" == "commit" ]]; then
        # Check evidence-only closure packets before declaring any miss.
        # Maintenance epics that close via proof packets instead of code commits
        # are valid regardless of whether scoped files were found.
        if packet_path="$(durable_packet_path_for_child "$child")" && packet_is_valid_for_child "$packet_path" "$child"; then
          packet_json="$(packet_matches_json "$packet_path")"
          if [[ "${#scoped_files[@]}" -eq 0 ]]; then
            build_child_result "$child" "$scoped_json" "evidence-only-packet" "matched durable closure proof packet (no scoped files)" "$packet_json" "pass"
          else
            build_child_result "$child" "$scoped_json" "evidence-only-packet" "matched durable closure proof packet (no commit evidence for scoped files)" "$packet_json" "pass"
          fi
        elif [[ "${#scoped_files[@]}" -eq 0 ]]; then
          if issue_text_has_file_patterns "$child"; then
            build_child_result "$child" "$scoped_json" "none" "parser_miss: description mentions file-like paths but extraction found 0 scoped files — manual review recommended" '[]' "warn"
          else
            build_child_result "$child" "$scoped_json" "none" "parser_miss: no scoped files extracted from description" '[]' "fail"
          fi
        else
          if all_scoped_files_are_discovery "${scoped_files[@]}" && child_has_nondiscovery_proof_surface "$child"; then
            build_child_result "$child" "$scoped_json" "discovery-seed-missing" "discovery_miss: closed bead cites discovery-phase artifact(s) (.agents/brainstorm/.agents/research/.agents/discovery/) that were never persisted, but other proof surface exists" '[]' "warn"
            return 0
          fi
          build_child_result "$child" "$scoped_json" "none" "timing_miss: scoped files found but no commit evidence (checked grace window)" '[]' "fail"
        fi
        return 0
      fi
      ;;
  esac

  if [[ "${#scoped_files[@]}" -eq 0 ]]; then
    # Check evidence-only closure packets before declaring parser_miss
    if packet_path="$(durable_packet_path_for_child "$child")" && packet_is_valid_for_child "$packet_path" "$child"; then
      packet_json="$(packet_matches_json "$packet_path")"
      build_child_result "$child" "$scoped_json" "evidence-only-packet" "matched durable closure proof packet (no scoped files)" "$packet_json" "pass"
    else
      if issue_text_has_file_patterns "$child"; then
        build_child_result "$child" "$scoped_json" "none" "parser_miss: description mentions file-like paths but extraction found 0 scoped files — manual review recommended" '[]' "warn"
      else
        build_child_result "$child" "$scoped_json" "none" "parser_miss: no scoped files extracted from description" '[]' "fail"
      fi
    fi
    return 0
  fi

  case "$SCOPE" in
    auto|staged)
      staged_json="$(staged_matches_json "${scoped_files[@]}")"
      if echo "$staged_json" | jq -e 'length > 0' >/dev/null 2>&1; then
        build_child_result "$child" "$scoped_json" "staged" "matched scoped files in git index" "$staged_json" "pass"
        return 0
      fi
      if [[ "$SCOPE" == "staged" ]]; then
        build_child_result "$child" "$scoped_json" "none" "timing_miss: scoped files found but no staged evidence" '[]' "fail"
        return 0
      fi
      ;;
  esac

  case "$SCOPE" in
    auto|worktree)
      worktree_json="$(worktree_matches_json "${scoped_files[@]}")"
      if echo "$worktree_json" | jq -e 'length > 0' >/dev/null 2>&1; then
        build_child_result "$child" "$scoped_json" "worktree" "matched scoped files in working tree" "$worktree_json" "pass"
        return 0
      fi
      ;;
  esac

  if packet_path="$(durable_packet_path_for_child "$child")" && packet_is_valid_for_child "$packet_path" "$child"; then
    packet_json="$(packet_matches_json "$packet_path")"
    build_child_result "$child" "$scoped_json" "evidence-only-packet" "matched durable closure proof packet" "$packet_json" "pass"
    return 0
  fi

  # Discovery-phase seed artifacts (.agents/brainstorm/, .agents/research/,
  # .agents/discovery/) are ephemeral and commonly not persisted. If EVERY
  # scoped file is such a seed AND the bead has any other proof surface
  # (commit referencing the bead id, evidence-only packet, plan/finding
  # file, or non-discovery file mentioned in bead text with real history),
  # downgrade to WARN (discovery_miss) instead of hard-failing. Non-discovery
  # scoped misses still hard-fail.
  if all_scoped_files_are_discovery "${scoped_files[@]}" && child_has_nondiscovery_proof_surface "$child"; then
    build_child_result "$child" "$scoped_json" "discovery-seed-missing" "discovery_miss: closed bead cites discovery-phase artifact(s) (.agents/brainstorm/.agents/research/.agents/discovery/) that were never persisted, but other proof surface exists (commit-ref/packet/plan/finding)" '[]' "warn"
    return 0
  fi

  build_child_result "$child" "$scoped_json" "none" "timing_miss: scoped files found but no evidence in any scope (commit/grace/staged/worktree/packet)" '[]' "fail"
}

emit_results_summary() {
  local results_file="$1"

  jq -s \
    --arg epic_id "$EPIC_ID" \
    --arg scope "$SCOPE" \
    '{
      epic_id: $epic_id,
      scope: $scope,
      summary: {
        checked_children: length,
        passed: ([.[] | select(.status == "pass")] | length),
        warned: ([.[] | select(.status == "warn")] | length),
        failed: ([.[] | select(.status == "fail")] | length),
        evidence_modes: {
          commit: ([.[] | select(.status == "pass" and .evidence_mode == "commit") | .child_id] | sort),
          staged: ([.[] | select(.status == "pass" and .evidence_mode == "staged") | .child_id] | sort),
          worktree: ([.[] | select(.status == "pass" and .evidence_mode == "worktree") | .child_id] | sort),
          "evidence-only-packet": ([.[] | select(.status == "pass" and .evidence_mode == "evidence-only-packet") | .child_id] | sort),
          "grace-window": ([.[] | select(.status == "pass" and .evidence_mode == "grace-window") | .child_id] | sort),
          "discovery-seed-missing": ([.[] | select(.status == "warn" and .evidence_mode == "discovery-seed-missing") | .child_id] | sort)
        },
        closure_modes: {
          "task-queue": ([.[] | select(.closure_mode == "task-queue") | .child_id] | sort),
          "single-epic": ([.[] | select(.closure_mode == "single-epic") | .child_id] | sort)
        }
      },
      children: .,
      warnings: [.[] | select(.status == "warn") | {child_id, detail, warning_type: (if (.detail | startswith("parser_miss")) then "parser_miss" elif (.detail | startswith("discovery_miss")) then "discovery_miss" else "unknown" end)}],
      failures: [.[] | select(.status == "fail") | {child_id, detail, failure_type: (if (.detail | startswith("parser_miss")) then "parser_miss" elif (.detail | startswith("timing_miss")) then "timing_miss" elif (.detail | startswith("discovery_miss")) then "discovery_miss" else "unknown" end)}]
    }' "$results_file"
}

tmp_results="$(mktemp)"
children_file="$(mktemp)"
trap 'rm -f "$tmp_results" "$children_file"' EXIT

if ! collect_children >"$children_file"; then
  if target_is_closed_non_epic "$EPIC_ID"; then
    COLLECTION_DETAIL="${COLLECTION_DETAIL:-no child issues discovered from br show --json dependents}; task-queue fallback requires PR merge evidence in git history or a valid evidence-only closure packet"
    if task_result="$(classify_task_queue_target "$EPIC_ID")" && [[ -n "$task_result" ]]; then
      printf '%s\n' "$task_result" > "$tmp_results"
      emit_results_summary "$tmp_results"
      exit 0
    fi
  fi

  # A closed epic with no children is a single-epic closure: accept it when the
  # closure is commit-backed (landed SHAs / commit-ref / evidence packet),
  # otherwise fall through to the collection_failed hard-fail below.
  if single_epic_result="$(classify_single_epic_target "$EPIC_ID")" && [[ -n "$single_epic_result" ]]; then
    printf '%s\n' "$single_epic_result" > "$tmp_results"
    emit_results_summary "$tmp_results"
    exit 0
  fi

  jq -n \
    --arg epic_id "$EPIC_ID" \
    --arg scope "$SCOPE" \
    --arg detail "${COLLECTION_DETAIL:-failed to collect child issues}" \
    '{
      epic_id: $epic_id,
      scope: $scope,
      summary: {
        checked_children: 0,
        passed: 0,
        failed: 1,
        collection_failed: true
      },
      children: [],
      failures: [
        {
          child_id: null,
          detail: $detail
        }
      ]
    }'
  exit 1
fi

children_output="$(cat "$children_file")"
while IFS= read -r child; do
  [[ -n "$child" ]] || continue
  child_result="$(classify_child "$child")"
  [[ -n "$child_result" ]] || continue
  printf '%s\n' "$child_result" >> "$tmp_results"
done <<< "$children_output"

emit_results_summary "$tmp_results"
