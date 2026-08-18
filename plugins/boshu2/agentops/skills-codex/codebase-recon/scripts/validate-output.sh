#!/usr/bin/env bash
set -euo pipefail

# Physical pwd: this skill is invoked through a symlink (e.g.
# ~/.claude/skills/codebase-recon -> the repo checkout). A logical `pwd`
# would resolve `../../..` against the symlink's parent (`.claude`) and point
# evidence resolution at the wrong tree. `pwd -P` follows the link to the real
# checkout.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

usage() {
  echo "usage: $0 [--repo-root <dir>] [--discover-priors | <codebase-recon.json>]" >&2
}

# Evidence paths in a recon manifest are relative to the repository being
# reconstructed, which is NOT necessarily the checkout that ships this skill.
# --repo-root lets the caller point resolution at the target repo; it defaults
# to the skill's own checkout for the in-repo self-test case.
repo_root=""
artifact=""
discover_priors=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      shift
      [[ $# -gt 0 ]] || { usage; exit 2; }
      repo_root="$1"
      ;;
    --repo-root=*) repo_root="${1#--repo-root=}" ;;
    --discover-priors) discover_priors=1 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "unknown flag: $1" >&2; usage; exit 2 ;;
    *)
      if [[ -n "$artifact" ]]; then
        echo "only one artifact may be supplied" >&2
        exit 2
      fi
      artifact="$1"
      ;;
  esac
  shift
done

if [[ "$discover_priors" == "1" && -n "$artifact" ]]; then
  echo "--discover-priors does not accept an artifact" >&2
  usage
  exit 2
fi
if [[ "$discover_priors" != "1" && ( -z "$artifact" || ! -f "$artifact" || -L "$artifact" ) ]]; then
  usage
  exit 2
fi

if [[ -z "$repo_root" ]]; then
  repo_root="$(cd "$script_dir/../../.." && pwd -P)"
fi
if [[ ! -d "$repo_root" ]]; then
  echo "repo root does not exist: $repo_root" >&2
  exit 2
fi
repo_root="$(cd "$repo_root" && pwd -P)"

snapshot_root="$(mktemp -d "${TMPDIR:-/tmp}/codebase-recon-validate.XXXXXX")"
cleanup() {
  rm -rf -- "$snapshot_root"
}
trap cleanup EXIT HUP INT TERM

declare -a watched_sources=()
declare -a watched_identities=()
declare -a watched_hashes=()
snapshot_counter=0

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

sha256_stream() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum | awk '{print $1}'
  else
    shasum -a 256 | awk '{print $1}'
  fi
}

file_identity() {
  if stat -f '%d:%i:%z:%m' "$1" >/dev/null 2>&1; then
    stat -f '%d:%i:%z:%m' "$1"
  else
    stat -c '%d:%i:%s:%Y' "$1"
  fi
}

# Snapshot each manifest/report exactly once. cp -P copies a raced-in symlink as
# a symlink rather than following it; the destination type check then fails.
watch_regular_file() {
  local source="$1" label="$2" before after source_hash snapshot_hash snapshot
  [[ -f "$source" && ! -L "$source" ]] || {
    echo "$label must be a real regular file: $source" >&2
    return 1
  }
  before="$(file_identity "$source")" || return 1
  snapshot_counter=$((snapshot_counter + 1))
  snapshot="$snapshot_root/$snapshot_counter"
  cp -P -- "$source" "$snapshot"
  [[ -f "$snapshot" && ! -L "$snapshot" ]] || {
    echo "$label changed shape while being snapshotted: $source" >&2
    return 1
  }
  after="$(file_identity "$source")" || return 1
  [[ "$before" == "$after" ]] || {
    echo "$label changed identity while being snapshotted: $source" >&2
    return 1
  }
  source_hash="$(sha256_file "$source")"
  snapshot_hash="$(sha256_file "$snapshot")"
  [[ "$source_hash" == "$snapshot_hash" ]] || {
    echo "$label changed bytes while being snapshotted: $source" >&2
    return 1
  }
  watched_sources+=("$source")
  watched_identities+=("$before")
  watched_hashes+=("$snapshot_hash")
  WATCHED_SNAPSHOT="$snapshot"
}

recheck_watched_files() {
  local i source
  for ((i = 0; i < ${#watched_sources[@]}; i++)); do
    source="${watched_sources[$i]}"
    [[ -f "$source" && ! -L "$source" ]] || {
      echo "validated artifact changed shape during validation: $source" >&2
      return 1
    }
    [[ "$(file_identity "$source")" == "${watched_identities[$i]}" ]] || {
      echo "validated artifact changed identity during validation: $source" >&2
      return 1
    }
    [[ "$(sha256_file "$source")" == "${watched_hashes[$i]}" ]] || {
      echo "validated artifact changed bytes during validation: $source" >&2
      return 1
    }
  done
}

repo_head_initial="$(git -C "$repo_root" rev-parse --verify 'HEAD^{commit}' 2>/dev/null || true)"
repo_status_initial="$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all -- . ':(exclude).agents' 2>/dev/null || true)"

recheck_repo_state() {
  local current_head current_status
  current_head="$(git -C "$repo_root" rev-parse --verify 'HEAD^{commit}' 2>/dev/null || true)"
  current_status="$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all -- . ':(exclude).agents' 2>/dev/null || true)"
  [[ -n "$repo_head_initial" && "$current_head" == "$repo_head_initial" ]] || {
    echo "target repository HEAD changed during validation" >&2
    return 1
  }
  [[ "$current_status" == "$repo_status_initial" && -z "$current_status" ]] || {
    echo "target repository index or worktree changed during validation" >&2
    return 1
  }
}

# Resolve the prior manifest's exact path. Unlike evidence citations, a prior
# reference has no :LINE syntax: silently stripping such a suffix would accept
# a different path than the manifest declared.
resolve_prior_manifest() {
  local candidate="$1" artifact_dir="$2"
  local -a roots=()
  if [[ "$candidate" = /* ]]; then
    roots=("$candidate")
  else
    roots=("$repo_root/$candidate" "$artifact_dir/$candidate")
  fi
  local p
  for p in "${roots[@]}"; do
    [[ -f "$p" ]] && { printf '%s\n' "$p"; return 0; }
  done
  return 1
}

# resolve_manifest_commit ARTIFACT
#
# A manifest's commit is evidence only when it resolves to an immutable commit
# in the target repository. Symbolic names such as HEAD are deliberately
# rejected because their meaning changes after the artifact is written.
resolve_manifest_commit() {
  local manifest="$1" declared declared_normalized resolved resolved_normalized object_format oid_length
  declared="$(jq -r '.commit // empty' "$manifest")"
  if ! object_format="$(git -C "$repo_root" rev-parse --show-object-format=storage 2>/dev/null)"; then
    object_format="$(git -C "$repo_root" rev-parse --show-object-format 2>/dev/null)" || {
      echo "could not determine target repository object format" >&2
      return 1
    }
  fi
  object_format="${object_format%%$'\n'*}"
  case "$object_format" in
    sha1) oid_length=40 ;;
    sha256) oid_length=64 ;;
    *) echo "unsupported target repository object format: $object_format" >&2; return 1 ;;
  esac
  if [[ ! "$declared" =~ ^[0-9a-fA-F]{$oid_length}$ ]]; then
    echo "manifest commit is not a full $object_format object id: $declared" >&2
    return 1
  fi
  if ! resolved="$(git -C "$repo_root" rev-parse --verify "${declared}^{commit}" 2>/dev/null)"; then
    echo "manifest commit does not resolve in target repository: $declared" >&2
    return 1
  fi
  declared_normalized="$(printf '%s' "$declared" | tr '[:upper:]' '[:lower:]')"
  resolved_normalized="$(printf '%s' "$resolved" | tr '[:upper:]' '[:lower:]')"
  if [[ "$resolved_normalized" != "$declared_normalized" ]]; then
    echo "manifest commit resolved through a mutable or abbreviated name: $declared" >&2
    return 1
  fi
  printf '%s\n' "$resolved_normalized"
}

# resolve_repo_path_at_commit CITATION COMMIT MUST_BE_FILE
#
# Fact/inference evidence belongs to the repository commit named by the
# manifest, never to whichever bytes happen to be in the current worktree or
# beside the artifact. A trailing :LINE is checked against that committed blob.
resolve_repo_path_at_commit() {
  local citation="$1" commit="$2" must_file="$3" candidate="$1" line="" line_number=""
  local tree_entry mode object_type object_id line_count
  if [[ "$candidate" =~ ^(.+):([0-9]+)$ ]]; then
    candidate="${BASH_REMATCH[1]}"
    line="${BASH_REMATCH[2]}"
  fi
  while [[ "$candidate" == ./* ]]; do candidate="${candidate#./}"; done
  if [[ -z "$candidate" || "$candidate" == "." || "$candidate" = /* || "$candidate" == */ || "$candidate" == ".." || "$candidate" == ../* || "$candidate" == */../* || "$candidate" == */.. ]]; then
    echo "evidence citation is not a safe repository-relative path: $citation" >&2
    return 1
  fi
  if ! tree_entry="$(git -C "$repo_root" ls-tree "$commit" -- ":(literal)$candidate")" || [[ -z "$tree_entry" ]]; then
    echo "evidence path is absent from manifest commit: $citation" >&2
    return 1
  fi
  read -r mode object_type object_id _ <<<"$tree_entry"
  if [[ "$must_file" == "1" && ( "$mode" != 100* || "$object_type" != "blob" ) ]]; then
    echo "evidence citation is not a regular file in manifest commit: $citation" >&2
    return 1
  fi
  if [[ -n "$line" ]]; then
    line_number=$((10#$line))
    if [[ "$must_file" != "1" || "$line_number" -lt 1 ]]; then
      echo "invalid evidence line citation: $citation" >&2
      return 1
    fi
    if ! line_count="$(git -C "$repo_root" cat-file blob "$object_id" | awk 'END { print NR }')"; then
      echo "could not read evidence blob from manifest commit: $citation" >&2
      return 1
    fi
    if (( line_number > line_count )); then
      echo "evidence line is outside committed blob: $citation" >&2
      return 1
    fi
  fi
  printf '%s\n' "$candidate"
}

require_clean_source_tree() {
  local source_status
  if ! source_status="$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all -- . ':(exclude).agents' 2>&1)"; then
    echo "could not inspect target repository worktree: $source_status" >&2
    return 1
  fi
  if [[ -n "$source_status" ]]; then
    echo "target repository has source changes not bound by the manifest commit:" >&2
    printf '%s\n' "$source_status" >&2
    return 1
  fi
}

require_report_marker() {
  local report="$1" key="$2" expected="$3" count
  count="$(grep -Fxc "$key: $expected" "$report" || true)"
  if [[ "$count" != "1" ]]; then
    echo "companion report must contain exactly one '$key: $expected' marker" >&2
    return 1
  fi
}

validate_companion_report() {
  local manifest="$1" manifest_dir="$2" report_rel report_source report_snapshot declared_sha actual_sha
  local commit mode flows_sha claims_sha coverage_sha
  report_rel="$(jq -r '.report.path // empty' "$manifest")"
  declared_sha="$(jq -r '.report.sha256 // empty' "$manifest")"
  if [[ "$report_rel" != "codebase-recon.md" || ! "$declared_sha" =~ ^[0-9a-f]{64}$ ]]; then
    echo "manifest must bind companion report codebase-recon.md by lowercase SHA-256" >&2
    return 1
  fi
  report_source="$manifest_dir/$report_rel"
  if ! watch_regular_file "$report_source" "companion codebase-recon report"; then
    return 1
  fi
  report_snapshot="$WATCHED_SNAPSHOT"
  actual_sha="$(sha256_file "$report_snapshot")"
  if [[ "$actual_sha" != "$declared_sha" ]]; then
    echo "companion report digest does not match manifest: $report_source" >&2
    return 1
  fi

  commit="$(jq -r '.commit' "$manifest")"
  mode="$(jq -r '.mode' "$manifest")"
  flows_sha="$(jq -cS '.flows' "$manifest" | sha256_stream)"
  claims_sha="$(jq -cS '.claims' "$manifest" | sha256_stream)"
  coverage_sha="$(jq -cS '.coverage' "$manifest" | sha256_stream)"
  grep -Fqx '<!-- codebase-recon-report.v1 -->' "$report_snapshot" || {
    echo "companion report lacks codebase-recon-report.v1 identity marker" >&2
    return 1
  }
  require_report_marker "$report_snapshot" manifest_commit "$commit" || return 1
  require_report_marker "$report_snapshot" manifest_mode "$mode" || return 1
  require_report_marker "$report_snapshot" flows_sha256 "$flows_sha" || return 1
  require_report_marker "$report_snapshot" claims_sha256 "$claims_sha" || return 1
  require_report_marker "$report_snapshot" coverage_sha256 "$coverage_sha" || return 1
}

# validate_artifact ARTIFACT DEPTH STACK REQUIRE_CURRENT_HEAD
#
# Delta manifests form a provenance chain. Validate every cited manifest in
# that chain, with a bounded depth and cycle check, before accepting the leaf.
# STACK is a newline-delimited list of normalized artifact paths.
# REQUIRE_CURRENT_HEAD=1 is used for the artifact the caller is validating;
# recursively cited/discovered historical manifests need only resolve in the
# repository because their commit is expected to predate HEAD.
validate_artifact() {
  local current_input="$1" depth="$2" stack="$3" require_current_head="$4"
  if [[ ! -f "$current_input" || -L "$current_input" ]]; then
    echo "missing codebase-recon.v1 artifact: $current_input" >&2
    return 1
  fi

  if (( depth > 32 )); then
    echo "prior recon chain exceeds 32 manifests: $current_input" >&2
    return 1
  fi

  local current_dir current_source current
  current_dir="$(cd "$(dirname "$current_input")" && pwd -P)"
  current_source="$current_dir/$(basename "$current_input")"
  case $'\n'"$stack"$'\n' in
    *$'\n'"$current_source"$'\n'*)
      echo "cyclic prior recon chain: $current_source" >&2
      return 1
      ;;
  esac

  local next_stack
  if [[ -n "$stack" ]]; then
    next_stack="$stack"$'\n'"$current_source"
  else
    next_stack="$current_source"
  fi

  if ! watch_regular_file "$current_source" "codebase-recon manifest"; then
    return 1
  fi
  current="$WATCHED_SNAPSHOT"

  jq -e '
    def text: type == "string" and length > 0;
    def path_text: text and (test("[\u0000-\u001f\u007f]") | not);
    .schema_version == "codebase-recon.v1"
    and (.mode == "baseline" or .mode == "delta")
    and (.commit | text)
    and (.flows
      | type == "array"
      and all(.[];
        (.entry | path_text)
        and (.domain | path_text)
        and (.integration | path_text)
        and (.tests | path_text)))
    and (.claims
      | type == "array"
      and all(.[];
        (.kind == "fact" or .kind == "inference" or .kind == "unknown")
        and (.text | text)
        and (.confidence == "high" or .confidence == "medium" or .confidence == "low")
        and (.evidence | type == "array" and all(.[]; path_text))
        and (if .kind == "unknown" then true else (.evidence | length > 0) end)))
    and (.coverage | type == "object")
    and (.coverage.inspected | type == "array" and length > 0 and all(.[]; text))
    and (.coverage.uninspected | type == "array" and length > 0 and all(.[]; text))
    and (.report | type == "object")
    and (.report.path == "codebase-recon.md")
    and (.report.sha256 | type == "string" and test("^[0-9a-f]{64}$"))
    and (
      if .mode == "baseline" then
        (.flows | length > 0)
        and ((has("prior_recon") | not) or .prior_recon == "" or .prior_recon == null)
      else
        (.prior_recon | path_text)
        and .baseline_verified == true
        and (.delta
          | type == "array" and length > 0
          and all(.[]; (.path | path_text) and (.change | text)))
      end
    )
  ' "$current" >/dev/null || {
    echo "invalid codebase-recon.v1 artifact: $current_source" >&2
    return 1
  }
  if ! validate_companion_report "$current" "$current_dir"; then
    echo "invalid companion report for: $current_source" >&2
    return 1
  fi

  if ! git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "target is not a git repository: $repo_root" >&2
    return 1
  fi
  if ! require_clean_source_tree; then
    return 1
  fi

  local current_commit
  if ! current_commit="$(resolve_manifest_commit "$current")"; then
    return 1
  fi
  if [[ "$require_current_head" == "1" ]]; then
    local target_head
    if ! target_head="$(git -C "$repo_root" rev-parse --verify 'HEAD^{commit}' 2>/dev/null)"; then
      echo "target repository has no current commit: $repo_root" >&2
      return 1
    fi
    if [[ "$current_commit" != "$target_head" ]]; then
      echo "manifest commit is not the target repository's current commit: $(jq -r '.commit' "$current")" >&2
      return 1
    fi
  fi

  local evidence
  while IFS= read -r evidence; do
    if ! resolve_repo_path_at_commit "$evidence" "$current_commit" 1 >/dev/null; then
      echo "invalid or unbound claim evidence: $evidence" >&2
      return 1
    fi
  done < <(jq -r '.claims[] | select(.kind == "fact" or .kind == "inference") | .evidence[]' "$current")

  local flow_path
  while IFS= read -r flow_path; do
    if ! resolve_repo_path_at_commit "$flow_path" "$current_commit" 1 >/dev/null; then
      echo "invalid or unbound flow file: $flow_path" >&2
      return 1
    fi
  done < <(jq -r '.flows[] | .entry, .tests' "$current")
  while IFS= read -r flow_path; do
    if ! resolve_repo_path_at_commit "$flow_path" "$current_commit" 0 >/dev/null; then
      echo "invalid or unbound flow path: $flow_path" >&2
      return 1
    fi
  done < <(jq -r '.flows[] | .domain, .integration' "$current")

  if [[ "$(jq -r '.mode' "$current")" == "delta" ]]; then
    local prior prior_path prior_commit
    prior="$(jq -r '.prior_recon' "$current")"
    if ! prior_path="$(resolve_prior_manifest "$prior" "$current_dir")"; then
      echo "missing or non-file prior recon pack: $prior" >&2
      return 1
    fi
    if ! validate_artifact "$prior_path" "$((depth + 1))" "$next_stack" 0; then
      echo "invalid prior recon pack: $prior" >&2
      return 1
    fi
    prior_commit="$VALIDATED_COMMIT"
    if ! git -C "$repo_root" merge-base --is-ancestor "$prior_commit" "$current_commit"; then
      echo "prior recon commit is not an ancestor of manifest commit: $prior" >&2
      return 1
    fi

    local declared_delta actual_delta declared_count unique_count
    declared_delta="$(jq -r '.delta[].path' "$current" | LC_ALL=C sort -u)"
    declared_count="$(jq -r '.delta | length' "$current")"
    unique_count="$(printf '%s\n' "$declared_delta" | sed '/^$/d' | wc -l | tr -d ' ')"
    if [[ "$declared_count" != "$unique_count" ]]; then
      echo "delta contains duplicate changed paths: $current" >&2
      return 1
    fi
    if ! actual_delta="$(git -C "$repo_root" diff --name-only --diff-filter=ACDMRTUXB "$prior_commit" "$current_commit" -- | LC_ALL=C sort -u)"; then
      echo "could not derive repository delta for $current" >&2
      return 1
    fi
    if [[ "$declared_delta" != "$actual_delta" ]]; then
      echo "declared delta paths do not match git diff ${prior_commit}..${current_commit}" >&2
      return 1
    fi
  fi
  VALIDATED_COMMIT="$current_commit"
}

discover_valid_priors() {
  local -a candidates=()
  shopt -s nullglob
  candidates+=("$repo_root"/.agents/scratch/codebase-recon/*/codebase-recon.json)
  candidates+=("$repo_root"/.agents/recon/*/codebase-recon.json)
  shopt -u nullglob

  if [[ "${#candidates[@]}" -eq 0 ]]; then
    return 0
  fi

  local candidate found=0
  while IFS= read -r candidate; do
    if validate_artifact "$candidate" 0 "" 0 >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      found=1
    else
      echo "ignoring invalid prior recon pack: $candidate" >&2
    fi
  done < <(printf '%s\n' "${candidates[@]}" | LC_ALL=C sort)

  if [[ "$found" == "0" ]]; then
    echo "no validated prior recon packs found under current or earlier default roots" >&2
    return 1
  fi
}

if [[ "$discover_priors" == "1" ]]; then
  discover_valid_priors
  recheck_watched_files
  recheck_repo_state
  exit $?
fi

validate_artifact "$artifact" 0 "" 1
recheck_watched_files
recheck_repo_state
echo "valid codebase-recon.v1: $artifact"
