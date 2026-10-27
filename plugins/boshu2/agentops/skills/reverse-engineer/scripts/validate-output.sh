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
  # Every row of the steal-map table: both cells filled, one valid verdict, a
  # source tag in the capability cell, and no steal without code evidence.
  awk -F'|' -v header='| Their capability | Our surface today | Verdict |' '
    function trim(s) { gsub(/^[[:space:]]+|[[:space:]]+$/, "", s); return s }
    function bad(msg) { printf "error: steal-map.md line %d: %s\n", NR, msg > "/dev/stderr"; errors++ }
    $0 == header { in_table = 1; next }
    in_table && !/^\|/ { in_table = 0 }
    !in_table { next }
    {
      capability = trim($2); ours = trim($3); verdict = trim($4)
      gsub(/\*\*/, "", verdict)
      if (capability ~ /^:?-+:?$/) next
      rows++
      code = (capability ~ /\(code:[[:space:]]*[^)[:space:]]/)
      if (capability == "" || ours == "") bad("both the capability and our surface need content")
      else if (verdict !~ /^(have|gap|steal|park|reject)$/) bad("verdict must be have, gap, steal, park or reject")
      else if (!code && capability !~ /\((docs|hosted)[:)]/) bad("tag the capability (code: <file:line>), (docs) or (hosted)")
      else if (verdict == "steal" && !code) bad("steal needs code evidence; a docs or hosted row is gap, park or reject")
    }
    END {
      if (rows == 0) { print "error: steal-map.md table has no rows" > "/dev/stderr"; exit 1 }
      exit errors ? 1 : 0
    }
  ' "$steal_map" || exit 1
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

# Secret scan over every output, in every phase and mode.
bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/security/scan_secrets.sh" "$output_dir"

echo "PASS: reverse-engineer $phase output is structurally valid"
