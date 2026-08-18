#!/usr/bin/env bash
set -euo pipefail

# Physical pwd: this skill is invoked through a symlink (e.g.
# ~/.claude/skills/codebase-recon -> the repo checkout). A logical `pwd`
# would resolve `../../..` against the symlink's parent (`.claude`) and point
# evidence resolution at the wrong tree. `pwd -P` follows the link to the real
# checkout.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

usage() {
  echo "usage: $0 [--repo-root <dir>] <codebase-recon.json>" >&2
}

# Evidence paths in a recon manifest are relative to the repository being
# reconstructed, which is NOT necessarily the checkout that ships this skill.
# --repo-root lets the caller point resolution at the target repo; it defaults
# to the skill's own checkout for the in-repo self-test case.
repo_root=""
artifact=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      shift
      [[ $# -gt 0 ]] || { usage; exit 2; }
      repo_root="$1"
      ;;
    --repo-root=*) repo_root="${1#--repo-root=}" ;;
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

if [[ -z "$artifact" || ! -f "$artifact" ]]; then
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
artifact_dir="$(cd "$(dirname "$artifact")" && pwd -P)"

jq -e '
  def text: type == "string" and length > 0;
  .schema_version == "codebase-recon.v1"
  and (.mode == "baseline" or .mode == "delta")
  and (.commit | text)
  and (.flows
    | type == "array"
    and all(.[];
      (.entry | text)
      and (.domain | text)
      and (.integration | text)
      and (.tests | text)))
  and (.claims
    | type == "array"
    and all(.[];
      (.kind == "fact" or .kind == "inference" or .kind == "unknown")
      and (.text | text)
      and (.confidence == "high" or .confidence == "medium" or .confidence == "low")
      and (.evidence | type == "array" and all(.[]; text))
      and (if .kind == "unknown" then true else (.evidence | length > 0) end)))
  and (.coverage | type == "object")
  and (.coverage.inspected | type == "array" and length > 0 and all(.[]; text))
  and (.coverage.uninspected | type == "array" and length > 0 and all(.[]; text))
  and (
    if .mode == "baseline" then
      (.flows | length > 0)
      and ((has("prior_recon") | not) or .prior_recon == "" or .prior_recon == null)
    else
      (.prior_recon | text)
      and .baseline_verified == true
      and (.delta
        | type == "array" and length > 0
        and all(.[]; (.path | text) and (.change | text)))
    end
  )
' "$artifact" >/dev/null || {
  echo "invalid codebase-recon.v1 artifact: $artifact" >&2
  exit 1
}

# resolve_evidence CANDIDATE MUST_BE_FILE
#   MUST_BE_FILE=1 → claim evidence: the contract is "existing file paths,
#   optionally followed by a line number", so the resolved path must be a
#   regular file. A directory is a coverage gap, not a citation, and no longer
#   passes silently (the old `-e` accepted directories).
#   MUST_BE_FILE=0 → prior-recon pack reference: any existing path resolves.
resolve_evidence() {
  local candidate="$1" must_file="$2"
  if [[ "$candidate" =~ ^(.+):[0-9]+$ ]]; then
    candidate="${BASH_REMATCH[1]}"
  fi
  local -a roots=()
  if [[ "$candidate" = /* ]]; then
    roots=("$candidate")
  else
    roots=("$repo_root/$candidate" "$artifact_dir/$candidate")
  fi
  local p
  for p in "${roots[@]}"; do
    if [[ "$must_file" == "1" ]]; then
      [[ -f "$p" ]] && return 0
    else
      [[ -e "$p" ]] && return 0
    fi
  done
  return 1
}

while IFS= read -r evidence; do
  if ! resolve_evidence "$evidence" 1; then
    echo "missing or non-file claim evidence: $evidence" >&2
    exit 1
  fi
done < <(jq -r '.claims[] | select(.kind == "fact" or .kind == "inference") | .evidence[]' "$artifact")

if [[ "$(jq -r '.mode' "$artifact")" == "delta" ]]; then
  prior="$(jq -r '.prior_recon' "$artifact")"
  if ! resolve_evidence "$prior" 0; then
    echo "missing prior recon pack: $prior" >&2
    exit 1
  fi
fi

echo "valid codebase-recon.v1: $artifact"
