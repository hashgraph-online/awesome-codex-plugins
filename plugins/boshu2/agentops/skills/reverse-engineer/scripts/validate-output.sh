#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage: validate-output.sh --output-dir DIR [--phase teardown|complete]
                          [--security-audit 0|1] [--sbom 0|1]
                          [--upstream-ref-set 0|1]
EOF
  exit 2
}

output_dir=""
phase="complete"
security_audit=0
sbom=0
upstream_ref_set=0
while (($#)); do
  case "$1" in
    --output-dir) (($# >= 2)) || usage; output_dir=$2; shift 2 ;;
    --phase) (($# >= 2)) || usage; phase=$2; shift 2 ;;
    --security-audit) (($# >= 2)) || usage; security_audit=$2; shift 2 ;;
    --sbom) (($# >= 2)) || usage; sbom=$2; shift 2 ;;
    --upstream-ref-set) (($# >= 2)) || usage; upstream_ref_set=$2; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

[[ -n "$output_dir" ]] || usage
[[ "$phase" == teardown || "$phase" == complete ]] || usage
[[ "$security_audit" =~ ^[01]$ ]] || usage
[[ "$sbom" =~ ^[01]$ ]] || usage
[[ "$upstream_ref_set" =~ ^[01]$ ]] || usage
[[ -d "$output_dir" && ! -L "$output_dir" ]] || {
  echo "error: output directory must be a real directory: $output_dir" >&2
  exit 1
}

required=(
  feature-inventory.md
  feature-registry.yaml
  feature-catalog.md
  spec-architecture.md
  spec-code-map.md
  spec-clone-vs-use.md
  spec-clone-mvp.md
  analysis-root-path.txt
  validate-feature-registry.py
)
for name in "${required[@]}"; do
  path="$output_dir/$name"
  [[ -f "$path" && ! -L "$path" && -s "$path" ]] || {
    echo "error: required regular nonempty artifact missing: $path" >&2
    exit 1
  }
done

[[ -f "$output_dir/docs-features.txt" && ! -L "$output_dir/docs-features.txt" ]] || {
  echo "error: docs-features.txt must be a regular file" >&2
  exit 1
}
if [[ -e "$output_dir/spec-cli-surface.md" || -L "$output_dir/spec-cli-surface.md" ]]; then
  [[ -f "$output_dir/spec-cli-surface.md" && ! -L "$output_dir/spec-cli-surface.md" && -s "$output_dir/spec-cli-surface.md" ]] || {
    echo "error: spec-cli-surface.md must be a regular nonempty file when present" >&2
    exit 1
  }
fi

python3 "$output_dir/validate-feature-registry.py"

if [[ "$upstream_ref_set" == 1 ]]; then
  metadata="$output_dir/clone-metadata.json"
  [[ -f "$metadata" && ! -L "$metadata" && -s "$metadata" ]] || {
    echo "error: --upstream-ref requires clone-metadata.json" >&2
    exit 1
  }
  python3 - "$metadata" <<'PY'
import json, pathlib, re, sys
path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
if not isinstance(data, dict):
    raise SystemExit("clone metadata must be an object")
commit = data.get("resolved_commit")
if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-fA-F]{40,64}", commit):
    raise SystemExit("clone metadata lacks a full resolved commit OID")
if not data.get("upstream_ref"):
    raise SystemExit("clone metadata lacks upstream_ref")
PY
fi

if [[ "$phase" == complete ]]; then
  steal_map="$output_dir/steal-map.md"
  [[ -f "$steal_map" && ! -L "$steal_map" && -s "$steal_map" ]] || {
    echo "error: complete output requires a regular nonempty steal-map.md" >&2
    exit 1
  }
  grep -Fqx '| Their capability | Our surface today | Verdict |' "$steal_map" || {
    echo "error: steal-map.md lacks the required table header" >&2
    exit 1
  }
  awk -F'|' '
    BEGIN { found = 0 }
    /^\|/ {
      capability=$2; ours=$3; verdict=$4
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", capability)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", ours)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", verdict)
      gsub(/\*\*/, "", verdict)
      if (capability != "" && capability != "Their capability" && capability !~ /^-+$/ &&
          ours != "" && verdict ~ /^(have|gap|steal|park|reject)$/) found = 1
    }
    END { exit found ? 0 : 1 }
  ' "$steal_map" || {
    echo "error: steal-map.md needs at least one nonempty row with a valid verdict" >&2
    exit 1
  }
fi

if [[ "$security_audit" == 1 ]]; then
  gate="$output_dir/security/validate-security-audit.sh"
  [[ -x "$gate" && ! -L "$gate" ]] || {
    echo "error: security validator is missing or unsafe" >&2
    exit 1
  }
  if [[ "$sbom" == 1 ]]; then
    "$gate" "$output_dir" --sbom
  else
    "$gate" "$output_dir" --no-sbom
  fi
else
  [[ "$sbom" == 0 ]] || {
    echo "error: --sbom requires --security-audit 1" >&2
    exit 1
  }
fi

echo "PASS: reverse-engineer $phase output is structurally valid"
