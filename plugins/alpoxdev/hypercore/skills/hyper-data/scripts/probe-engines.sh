#!/usr/bin/env bash
# probe-engines.sh - report the local data toolchain as one JSON object.
#
# Usage: bash probe-engines.sh [--help | --self-test]
#   (no argument)  probe this machine and print one JSON object
#   --help         print this usage block and exit 0
#   --self-test    run the bundled shape test in a temporary directory and exit 0
#
# Output (stdout, exactly one JSON object):
#   {"schemaVersion": 1,
#    "platform": "darwin" | "linux" | "other",
#    "python3": {"path": "...", "version": "3.13.1"} | null,
#    "packages": {"duckdb": {"version": "1.3.2"} | null,
#                 "polars": {"version": "..."} | null,
#                 "pyarrow": {"version": "..."} | null,
#                 "numpy": {"version": "..."} | null,
#                 "matplotlib": {"version": "..."} | null},
#    "duckdbCli": {"path": "...", "version": "v1.3.2"} | null,
#    "memory": {"freeBytes": 123456789, "source": "vm_stat" | "meminfo"} | null}
#
# Exit codes: 0 printed the object or the usage/self-test path, 2 usage error,
# 3 jq is missing.
#
# The script writes nothing outside the --self-test temporary directory, installs
# nothing, and reports a missing engine instead of adding it. Versions come from the
# interpreter's own installed-distribution metadata (`python3 -m pip list --format=json`,
# then a dist-info scan of the interpreter's site directories). The script runs no
# Python program of its own: the query run that follows performs the import, and an
# import failure becomes a missing prerequisite there.
set -euo pipefail

PACKAGES='duckdb polars pyarrow numpy matplotlib'

usage_error() { printf 'probe-engines: %s\n' "$1" >&2; exit 2; }

self_test_fail() { printf 'probe-engines: self-test failed: %s\n' "$1" >&2; exit 1; }

all_versions_null() {
  jq -n --arg names "$PACKAGES" 'reduce ($names | split(" ")[]) as $n ({}; .[$n] = null)'
}

pip_versions() {
  local py=$1 raw
  raw=$("$py" -m pip list --format=json --disable-pip-version-check 2>/dev/null || true)
  [ -n "$raw" ] || return 0
  printf '%s' "$raw" | jq -c --arg names "$PACKAGES" '
    if type != "array" then empty else
      (map({key: (.name | ascii_downcase), value: .version}) | from_entries) as $by_name
      | reduce ($names | split(" ")[]) as $n ({}; .[$n] = ($by_name[$n] // null))
    end' 2>/dev/null || true
}

installed_version() {
  local dir=$1 pkg=$2 dist meta
  for dist in "$dir/$pkg"-*.dist-info; do
    [ -d "$dist" ] || continue
    meta=$dist/METADATA
    [ -f "$meta" ] || continue
    sed -n 's/^Version:[[:space:]]*//p' "$meta" | sed -n '1p'
    return 0
  done
  for dist in "$dir/$pkg".egg-info; do
    [ -d "$dist" ] || continue
    meta=$dist/PKG-INFO
    [ -f "$meta" ] || continue
    sed -n 's/^Version:[[:space:]]*//p' "$meta" | sed -n '1p'
    return 0
  done
  return 0
}

site_versions() {
  local py=$1 dirs dir pkg version rows=''
  dirs=$("$py" -m site 2>/dev/null | sed -n "s/^[[:space:]]*'\(.*\)'.*\$/\1/p" || true)
  [ -n "$dirs" ] || return 0
  while IFS= read -r dir; do
    [ -n "$dir" ] || continue
    [ -d "$dir" ] || continue
    for pkg in $PACKAGES; do
      version=$(installed_version "$dir" "$pkg")
      [ -n "$version" ] || continue
      rows="${rows}${pkg}	${version}
"
    done
  done <<<"$dirs"
  printf '%s' "$rows" | jq -Rn -c --arg names "$PACKAGES" '
    [inputs | select(length > 0) | split("\t") | {key: .[0], value: .[1]}]
    | (reduce .[] as $e ({}; if .[$e.key] == null then .[$e.key] = $e.value else . end)) as $found
    | reduce ($names | split(" ")[]) as $n ({}; .[$n] = ($found[$n] // null))' 2>/dev/null || true
}

free_memory() {
  local system
  system=$(uname -s 2>/dev/null || true)
  case $system in
    Darwin)
      vm_stat 2>/dev/null | awk '
        /page size of/ { for (i = 1; i <= NF; i++) if ($i ~ /^[0-9]+$/) { ps = $i; break } }
        /^Pages free:/ { n = $0; gsub(/[^0-9]/, "", n); free = n + 0 }
        /^Pages inactive:/ { n = $0; gsub(/[^0-9]/, "", n); inact = n + 0 }
        END {
          if (ps > 0 && (free > 0 || inact > 0))
            printf "{\"freeBytes\":%d,\"source\":\"vm_stat\"}", (free + inact) * ps
        }' || true
      ;;
    Linux)
      awk '/^MemAvailable:/ { printf "{\"freeBytes\":%d,\"source\":\"meminfo\"}", $2 * 1024 }' \
        /proc/meminfo 2>/dev/null || true
      ;;
    *) : ;;
  esac
}

self_test() {
  local tmp site python_stub duckdb_stub out rc checks
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/probe-engines-selftest.XXXXXX")
  # shellcheck disable=SC2064
  trap "rm -rf '$tmp'" EXIT INT TERM
  site=$tmp/site
  mkdir -p "$tmp/bin" "$site/duckdb-1.3.2.dist-info" "$site/duckdb"
  printf 'Metadata-Version: 2.1\nName: duckdb\nVersion: 1.3.2\n' \
    >"$site/duckdb-1.3.2.dist-info/METADATA"
  : >"$site/duckdb/__init__.py"

  python_stub=$tmp/bin/python3
  cat >"$python_stub" <<EOF
#!/bin/sh
case "\$1" in
  --version) echo "Python 3.11.9" ;;
  -m)
    case "\$2" in
      pip) exit 1 ;;
      site) printf 'sys.path = [\n    %s,\n]\n' "'$site'" ;;
      *) exit 1 ;;
    esac ;;
  *) exit 1 ;;
esac
EOF
  chmod 755 "$python_stub"

  duckdb_stub=$tmp/bin/duckdb
  cat >"$duckdb_stub" <<'EOF'
#!/bin/sh
[ "$1" = "--version" ] && echo "v1.2.3" || exit 1
EOF
  chmod 755 "$duckdb_stub"

  rc=0
  out=$(PATH="$tmp/bin:$PATH" bash "$0" 2>"$tmp/stderr") || rc=$?
  [ "$rc" -eq 0 ] || self_test_fail "probe exited $rc: $(sed -n '1p' "$tmp/stderr")"
  printf '%s' "$out" | jq -e '
    .schemaVersion == 1
    and (.python3.version == "3.11.9")
    and ((.python3.path | type) == "string" and (.python3.path | endswith("/bin/python3")))
    and (.packages.duckdb.version == "1.3.2")
    and (.packages.polars == null)
    and (.packages.pyarrow == null)
    and (.packages.numpy == null)
    and (.packages.matplotlib == null)
    and (.duckdbCli.version == "v1.2.3")
    and ((.memory == null) or ((.memory.freeBytes | type) == "number"))' >/dev/null 2>&1 \
    || self_test_fail "probe JSON shape: $(printf '%s' "$out" | sed -n '1p')"

  rc=0
  bash "$0" --bogus >/dev/null 2>&1 || rc=$?
  [ "$rc" -eq 2 ] || self_test_fail "an unknown argument must exit 2 (got $rc)"

  checks='{"python":true,"packages":true,"duckdbCli":true,"json":true,"usageError":true}'
  jq -cn --argjson checks "$checks" '{ok:true, checks:$checks}'
}

case ${1:-} in
  '') ;;
  -h | --help)
    sed -n '2,28p' "$0"
    exit 0
    ;;
  --self-test) self_test && exit 0 ;;
  *) usage_error "unknown argument: $1" ;;
esac
[ "$#" -le 1 ] || usage_error "unexpected extra arguments"

command -v jq >/dev/null 2>&1 || {
  printf 'probe-engines: jq is required\n' >&2
  exit 3
}

platform=$(uname -s 2>/dev/null | tr '[:upper:]' '[:lower:]' || true)
case $platform in
  darwin | linux) : ;;
  *) platform='other' ;;
esac

python_path=$(command -v python3 2>/dev/null || true)
python_version=''
if [ -n "$python_path" ]; then
  python_version=$("$python_path" --version 2>&1 | sed -n 's/^Python[[:space:]]*//p' | sed -n '1p' || true)
fi

versions=$(all_versions_null)
if [ -n "$python_path" ]; then
  probed=$(pip_versions "$python_path")
  if [ -z "$probed" ]; then
    probed=$(site_versions "$python_path")
  fi
  if [ -n "$probed" ] && printf '%s' "$probed" | jq -e 'type == "object"' >/dev/null 2>&1; then
    versions=$probed
  fi
fi

duckdb_path=$(command -v duckdb 2>/dev/null || true)
duckdb_version=''
if [ -n "$duckdb_path" ]; then
  duckdb_version=$("$duckdb_path" --version 2>/dev/null | sed -n '1p' || true)
fi

memory_json=$(free_memory)
[ -n "$memory_json" ] || memory_json='null'
printf '%s' "$memory_json" | jq -e . >/dev/null 2>&1 || memory_json='null'

jq -n \
  --arg platform "$platform" \
  --arg pythonPath "$python_path" \
  --arg pythonVersion "$python_version" \
  --argjson versions "$versions" \
  --arg duckdbPath "$duckdb_path" \
  --arg duckdbVersion "$duckdb_version" \
  --argjson memory "$memory_json" '
  {schemaVersion: 1,
   platform: $platform,
   python3: (if $pythonPath == "" then null
             else {path: $pythonPath,
                   version: (if $pythonVersion == "" then null else $pythonVersion end)} end),
   packages: ($versions | with_entries(
     .value = (if .value == null then null else {version: .value} end))),
   duckdbCli: (if $duckdbPath == "" then null
               else {path: $duckdbPath,
                     version: (if $duckdbVersion == "" then null else $duckdbVersion end)} end),
   memory: $memory}'
