#!/usr/bin/env bash
# Validates a repository-local skill package (default: skills/hyper-skill).
#
# Port of the former Bun validator. Runs on macOS /bin/bash 3.2 and on Linux bash 4/5 with POSIX
# utilities plus jq. `set -e` is deliberately omitted: every check must run and report what it found,
# and most checks treat "no match" as a normal result rather than a failure.
set -uo pipefail

# Node reports the physical working directory, so resolve against the same one.
CWD=$(pwd -P)

LC_ALL=C
export LC_ALL

# The latest calendar date already in effect somewhere on Earth (UTC+14). A source dated "today" by a
# reviewer east of UTC is still yesterday in UTC, so comparing against the UTC date would reject a date
# that is not in the future for the person who wrote it.
if [ -n "${SKILL_MAKER_VALIDATION_DATE:-}" ]; then
  VALIDATION_DATE=$SKILL_MAKER_VALIDATION_DATE
else
  VALIDATION_DATE=$(jq -n -r 'now + 50400 | strftime("%Y-%m-%d")')
fi

BASE_LAST_REVERIFIED="2026-11-03"
CORE_LINE_BUDGET=500
REFERENCE_TOC_THRESHOLD=100
BUNDLED_SCRIPT_EXTENSION=".sh"
BUNDLED_SCRIPT_SHEBANG="#!/usr/bin/env bash"

REQUIRED_SECTIONS="output_language purpose routing_rule instruction_contract activation_examples trigger_conditions skill_architecture loop_policy language_and_translation_default reference_routing support_file_read_order workflow required forbidden validation"

# Category floors in the order the report prints them.
CATEGORY_FLOOR_NAMES="positive negative boundary workflow source safety adversarial regression coexistence"
CATEGORY_FLOOR_VALUES="3 2 1 1 1 1 1 1 1"
LANGUAGE_FLOOR_NAMES="en ko mixed"
LANGUAGE_FLOOR_VALUES="1 1 1"

WORK=$(mktemp -d "${TMPDIR:-/tmp}/validate-hyper-skill.XXXXXX") || exit 2
trap 'rm -rf "$WORK"' EXIT INT TERM

ERRORS="$WORK/errors.jsonl"
CONTRACT="$WORK/contract.jsonl"
: > "$ERRORS"
: > "$CONTRACT"

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

# push_issue <sink-file> <code> <message> [extra-json-object]
# The object key order matches the JS `{ code, message, ...extra }` spread.
push_issue() {
  local sink=$1 code=$2 message=$3 extra=${4:-}
  if [ -z "$extra" ]; then extra='{}'; fi
  jq -cn --arg code "$code" --arg message "$message" --argjson extra "$extra" \
    '{code: $code, message: $message} + $extra' >> "$sink"
}

# relpath <from-abs> <to-abs>: lexical relative path, like path.relative on normalized paths.
relpath() {
  local from=$1 to=$2
  local -a f=() t=()
  local strip
  strip=${from#/}
  if [ -n "$strip" ]; then IFS=/ read -r -a f <<< "$strip"; else f=(); fi
  strip=${to#/}
  if [ -n "$strip" ]; then IFS=/ read -r -a t <<< "$strip"; else t=(); fi
  local common=0
  while [ "$common" -lt "${#f[@]}" ] && [ "$common" -lt "${#t[@]}" ] && [ "${f[$common]}" = "${t[$common]}" ]; do
    common=$((common + 1))
  done
  local out="" i
  i=$common
  while [ "$i" -lt "${#f[@]}" ]; do
    out="${out}../"
    i=$((i + 1))
  done
  i=$common
  while [ "$i" -lt "${#t[@]}" ]; do
    out="${out}${t[$i]}/"
    i=$((i + 1))
  done
  if [ -n "$out" ]; then out=${out%/}; fi
  printf '%s' "$out"
}

# normalize_path <absolute-path>: collapse "." and ".." segments lexically.
normalize_path() {
  local p=$1
  local -a parts=() out=()
  local strip part n
  strip=${p#/}
  if [ -n "$strip" ]; then IFS=/ read -r -a parts <<< "$strip"; else parts=(); fi
  for part in ${parts[@]+"${parts[@]}"}; do
    case $part in
      ''|.) ;;
      ..)
        n=${#out[@]}
        if [ "$n" -gt 0 ]; then unset "out[$((n - 1))]"; fi
        ;;
      *) out+=("$part") ;;
    esac
  done
  local IFS=/
  printf '/%s' "${out[*]+"${out[*]}"}"
}

# absolute_path <path>: path.resolve against the current directory.
absolute_path() {
  case $1 in
    /*) normalize_path "$1" ;;
    *) normalize_path "$CWD/$1" ;;
  esac
}

# file_extension <path>: like path.extname (last dot of the basename, "" for dotfiles).
file_extension() {
  local base=${1##*/}
  case $base in
    .)
      return 0
      ;;
    .*)
      local rest=${base#.}
      case $rest in
        *.*) printf '.%s' "${rest##*.}" ;;
        *) printf '' ;;
      esac
      ;;
    *.*) printf '.%s' "${base##*.}" ;;
    *) printf '' ;;
  esac
}

# frontmatter_value <file> <key>: first "key: value" inside the leading --- block.
frontmatter_value() {
  local file=$1 key=$2
  [ -f "$file" ] || return 0
  awk -v key="$key" '
    function trim(s) {
      sub(/^[ \t\r\n\v\f]+/, "", s)
      sub(/[ \t\r\n\v\f]+$/, "", s)
      return s
    }
    NR == 1 {
      line = $0
      sub(/\r$/, "", line)
      if (line != "---") exit
      inside = 1
      next
    }
    inside {
      line = $0
      sub(/\r$/, "", line)
      if (substr(line, 1, 3) == "---") { closed = 1; exit }
      if (found) next
      if (index(line, key ":") == 1) {
        rest = substr(line, length(key) + 2)
        if (rest == "") next
        value = trim(rest)
        found = 1
      }
    }
    END {
      if (found && closed) {
        if (substr(value, 1, 1) == "\"" || substr(value, 1, 1) == "\047") value = substr(value, 2)
        last = substr(value, length(value), 1)
        if (last == "\"" || last == "\047") value = substr(value, 1, length(value) - 1)
        printf "%s", value
      }
    }
  ' "$file"
}

# utf16_length <string>: JS String#length (UTF-16 code units).
utf16_length() {
  local bytes
  bytes=$(printf '%s' "$1" | iconv -f UTF-8 -t UTF-16LE 2>/dev/null | wc -c)
  printf '%s' $((bytes / 2))
}

# is_valid_date <YYYY-MM-DD>: true for a real calendar date.
is_valid_date() {
  local value=$1 year month day max
  case $value in
    [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
    *) return 1 ;;
  esac
  year=${value:0:4}
  month=${value:5:2}
  day=${value:8:2}
  year=$((10#$year))
  month=$((10#$month))
  day=$((10#$day))
  [ "$month" -ge 1 ] && [ "$month" -le 12 ] || return 1
  case $month in
    1|3|5|7|8|10|12) max=31 ;;
    4|6|9|11) max=30 ;;
    2)
      if { [ $((year % 4)) -eq 0 ] && [ $((year % 100)) -ne 0 ]; } || [ $((year % 400)) -eq 0 ]; then
        max=29
      else
        max=28
      fi
      ;;
  esac
  [ "$day" -ge 1 ] && [ "$day" -le "$max" ]
}

# json_string_array <lines-file>: a JSON array of the lines, in order.
json_line_array() {
  jq -R -s -c 'split("\n") | if length > 0 and .[-1] == "" then .[:-1] else . end' "$1"
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

ROOT_ARG="skills/hyper-skill"
EVALS_ARG="skills/hyper-skill/assets/evals/hyper-skill-cases.jsonl"
JSON_OUT=0
REQUIRE_SELF_CONTAINMENT=0
HELP=0
ALLOW=()

arg_error_code=""
arg_error_message=""

require_value() {
  # $1 = index, $2 = flag, prints the value and returns 0; sets ARG_NEXT on success.
  local idx=$1 flag=$2
  local value=${ARGV[$((idx + 1))]:-}
  if [ -z "$value" ] || [ "${value#--}" != "$value" ]; then
    arg_error_code="ARG_VALUE_MISSING"
    arg_error_message="$flag requires a value"
    return 1
  fi
  ARG_NEXT=$value
  return 0
}

ARGV=("$@")
argc=${#ARGV[@]}
idx=0
while [ "$idx" -lt "$argc" ]; do
  arg=${ARGV[$idx]}
  case $arg in
    --root)
      if ! require_value "$idx" "$arg"; then break; fi
      ROOT_ARG=$ARG_NEXT
      idx=$((idx + 2))
      ;;
    --evals)
      if ! require_value "$idx" "$arg"; then break; fi
      EVALS_ARG=$ARG_NEXT
      idx=$((idx + 2))
      ;;
    --require-self-containment)
      REQUIRE_SELF_CONTAINMENT=1
      idx=$((idx + 1))
      ;;
    --allow)
      if ! require_value "$idx" "$arg"; then break; fi
      ALLOW+=("$ARG_NEXT")
      idx=$((idx + 2))
      ;;
    --json)
      JSON_OUT=1
      idx=$((idx + 1))
      ;;
    --help|-h)
      HELP=1
      idx=$((idx + 1))
      ;;
    *)
      arg_error_code="ARG_UNKNOWN"
      arg_error_message="Unknown argument: $arg"
      break
      ;;
  esac
done

print_help() {
  cat <<'EOF'
Usage: bash skills/hyper-skill/scripts/validate-hyper-skill.sh --root <dir> --evals <jsonl> [--json]

Validates the repository-local hyper-skill package with bash and jq only.

Options:
  --root <dir>     Skill root directory. Defaults to skills/hyper-skill.
  --evals <file>   JSONL eval cases. Defaults to assets/evals/hyper-skill-cases.jsonl.
  --json           Emit structured JSON.
  --require-self-containment
                   Report cross-skill references as errors for any package, not only for the
                   contract-adopting package. Use it on a skill this authoring skill produced.
  --allow <name>   Record a user-directed exception for one sibling skill name. Repeatable;
                   the finding is reported as a waiver warning.
  --help           Show this help.

EOF
}

# ---------------------------------------------------------------------------
# Result assembly
# ---------------------------------------------------------------------------

# emit_result <ok> [contract-package]
# Every section file holds one compact JSON value; missing files become null.
emit_result() {
  local ok=$1 contract=$2
  local discovery=$WORK/discovery.json
  local sections=$WORK/sections.json
  local links=$WORK/links.json
  local fences=$WORK/fences.json
  local pairs=$WORK/pairs.json
  local coreparity=$WORK/coreparity.json
  local triggers=$WORK/triggers.json
  local official=$WORK/official.json
  local sources=$WORK/sources.json
  local idparity=$WORK/idparity.json
  local selfcontain=$WORK/selfcontain.json
  local runtime=$WORK/runtime.json
  local frontmatter=$WORK/frontmatter.json
  local budget=$WORK/budget.json
  local toc=$WORK/toc.json
  local stray=$WORK/stray.json
  local warnings=$WORK/warnings.json
  local f
  for f in "$discovery" "$sections" "$links" "$fences" "$pairs" "$coreparity" "$triggers" \
    "$official" "$sources" "$idparity" "$selfcontain" "$runtime" "$frontmatter" "$budget" \
    "$toc" "$stray" "$warnings"; do
    [ -f "$f" ] || printf 'null' > "$f"
  done
  local errors_array='[]'
  if [ -s "$ERRORS" ]; then
    errors_array=$(jq -s -c '.' "$ERRORS")
  fi
  jq -n \
    --argjson ok "$ok" \
    --argjson contract "$contract" \
    --slurpfile discovery "$discovery" \
    --slurpfile sections "$sections" \
    --slurpfile links "$links" \
    --slurpfile fences "$fences" \
    --slurpfile pairs "$pairs" \
    --slurpfile coreparity "$coreparity" \
    --slurpfile triggers "$triggers" \
    --slurpfile official "$official" \
    --slurpfile sources "$sources" \
    --slurpfile idparity "$idparity" \
    --slurpfile selfcontain "$selfcontain" \
    --slurpfile runtime "$runtime" \
    --slurpfile frontmatter "$frontmatter" \
    --slurpfile budget "$budget" \
    --slurpfile toc "$toc" \
    --slurpfile stray "$stray" \
    --slurpfile warnings "$warnings" \
    --argjson errors "$errors_array" \
    '{
      ok: ($ok == 1),
      contractPackage: ($contract == 1),
      discoveryMetadata: $discovery[0],
      requiredSections: $sections[0],
      links: $links[0],
      codeFences: $fences[0],
      bilingualPairs: $pairs[0],
      bilingualCoreParity: $coreparity[0],
      triggerCases: $triggers[0],
      officialLastVerifiedGuard: $official[0],
      sourcesSections: $sources[0],
      idParity: $idparity[0],
      selfContainment: $selfcontain[0],
      scriptRuntime: $runtime[0],
      frontmatterConstraints: $frontmatter[0],
      coreLineBudget: $budget[0],
      referenceToc: $toc[0],
      strayDocs: $stray[0],
      warnings: $warnings[0],
      errors: $errors
    }'
}

write_result() {
  local result=$1 json=$2
  if [ "$json" -eq 1 ]; then
    printf '%s\n' "$result"
    return 0
  fi
  if [ "$(jq -r '.ok' <<< "$result")" = "true" ]; then
    printf 'hyper-skill validation passed\n'
  else
    printf 'hyper-skill validation failed\n' >&2
    jq -r '.errors[] | "\(.code): \(.message)"' <<< "$result" >&2
  fi
}

# Argument failures always print JSON, matching the original's writeResult(result, true).
if [ -n "$arg_error_code" ]; then
  result=$(jq -n --arg code "$arg_error_code" --arg message "$arg_error_message" '{
    ok: false,
    contractPackage: false,
    discoveryMetadata: null,
    requiredSections: null,
    links: null,
    codeFences: null,
    bilingualPairs: null,
    bilingualCoreParity: null,
    triggerCases: null,
    officialLastVerifiedGuard: null,
    sourcesSections: null,
    idParity: null,
    selfContainment: null,
    scriptRuntime: null,
    frontmatterConstraints: null,
    coreLineBudget: null,
    referenceToc: null,
    strayDocs: null,
    warnings: [],
    errors: [{code: $code, message: $message}]
  }')
  printf '%s\n' "$result"
  exit 2
fi

if [ "$HELP" -eq 1 ]; then
  print_help
  exit 0
fi

# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

ROOT=$(absolute_path "$ROOT_ARG")
EVALS_PATH=$(absolute_path "$EVALS_ARG")
EXPECTED_NAME=${ROOT##*/}
if [ "$ROOT" = "/" ]; then EXPECTED_NAME=""; fi

if [ ! -e "$ROOT" ] || [ ! -d "$ROOT" ]; then
  push_issue "$ERRORS" "ROOT_MISSING" "Root directory is missing: $ROOT_ARG" \
    "$(jq -cn --arg path "$ROOT_ARG" '{path: $path}')"
fi

FILES_LIST="$WORK/files.txt"
: > "$FILES_LIST"
if [ -e "$ROOT" ]; then
  if [ -d "$ROOT" ]; then
    find "$ROOT" -type f -print 2>/dev/null | LC_ALL=C sort > "$FILES_LIST"
  else
    push_issue "$ERRORS" "DIR_READ_FAILED" "Cannot read directory: $(relpath "$CWD" "$ROOT")" \
      "$(jq -cn --arg path "$(relpath "$CWD" "$ROOT")" --arg detail "readdir $ROOT" '{path: $path, detail: $detail}')"
  fi
fi

MARKDOWN_LIST="$WORK/markdown.txt"
grep -E '\.md$' "$FILES_LIST" > "$MARKDOWN_LIST" || : > "$MARKDOWN_LIST"

# Relative paths of the markdown files, and a second copy used for membership lookups so no command
# reads the file that also feeds a loop.
REL_LIST="$WORK/markdown.rel"
awk -v root="$ROOT" '{ if (root == "/") print substr($0, 2); else print substr($0, length(root) + 2) }' \
  "$MARKDOWN_LIST" > "$REL_LIST"
REL_LOOKUP="$WORK/markdown.lookup"
cp "$REL_LIST" "$REL_LOOKUP"

# The strengthened contract is an error for the package that adopted it and a warning elsewhere.
STRICT=0
if [ -f "$ROOT/SKILL.md" ] && [ "$(frontmatter_value "$ROOT/SKILL.md" name)" = "hyper-skill" ]; then
  STRICT=1
fi
if [ "$STRICT" -eq 1 ]; then CONTRACT_SINK=$ERRORS; else CONTRACT_SINK=$CONTRACT; fi

# ---------------------------------------------------------------------------
# checkDiscoveryMetadata
# ---------------------------------------------------------------------------
{
  ok=1
  files_json='[]'
  for target in "$ROOT/SKILL.md" "$ROOT/SKILL.ko.md"; do
    if [ ! -e "$target" ]; then
      ok=0
      continue
    fi
    name=$(frontmatter_value "$target" name)
    description=$(frontmatter_value "$target" description)
    rel=${target#"$ROOT"/}
    desc_len=$(utf16_length "$description")
    item=$(jq -cn --arg path "$rel" --arg name "$name" --argjson descriptionLength "$desc_len" \
      '{path: $path, name: $name, descriptionLength: $descriptionLength}')
    files_json=$(jq -nc --argjson arr "$files_json" --argjson item "$item" '$arr + [$item]')
    valid_name=0
    name_len=$(utf16_length "$name")
    if [ "$name" = "$EXPECTED_NAME" ] && [ "$name_len" -le 64 ] && printf '%s' "$name" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$'; then
      valid_name=1
    fi
    if [ "$valid_name" -eq 0 ]; then
      ok=0
      push_issue "$ERRORS" "FRONTMATTER_NAME" "Skill name must be lowercase kebab-case and match folder: $EXPECTED_NAME" "$item"
    fi
    if [ "$desc_len" -lt 1 ] || [ "$desc_len" -gt 1024 ]; then
      ok=0
      push_issue "$ERRORS" "FRONTMATTER_DESCRIPTION" "Skill description must contain 1–1024 characters" "$item"
    fi
    if [ "$target" = "$ROOT/SKILL.md" ] && ! printf '%s' "$description" | grep -qE '^Use this skill when([^A-Za-z0-9_]|$)'; then
      ok=0
      push_issue "$ERRORS" "FRONTMATTER_TRIGGER" "Canonical description must start with 'Use this skill when'" "$item"
    fi
  done
  jq -cn --argjson ok "$ok" --arg expectedName "$EXPECTED_NAME" --argjson files "$files_json" \
    '{ok: ($ok == 1), expectedName: $expectedName, files: $files}' > "$WORK/discovery.json"
}

# ---------------------------------------------------------------------------
# checkRequiredSections
# ---------------------------------------------------------------------------
{
  SECTION_STATUS=$WORK/sections.tsv
  SECTION_MISSING=$WORK/sections.missing
  : > "$SECTION_STATUS"
  : > "$SECTION_MISSING"
  if [ ! -f "$ROOT/SKILL.md" ]; then
    push_issue "$ERRORS" "SKILL_MISSING" "SKILL.md is missing" \
      "$(jq -cn --arg path "$ROOT/SKILL.md" '{path: $path}')"
    for section in $REQUIRED_SECTIONS; do
      printf '%s\t0\n' "$section" >> "$SECTION_STATUS"
      printf '%s\n' "$section" >> "$SECTION_MISSING"
    done
  else
    awk -v names="$REQUIRED_SECTIONS" '
      BEGIN { n = split(names, order, " ") }
      {
        low = tolower($0)
        for (i = 1; i <= n; i++) {
          name = order[i]
          if (name in found) continue
          if (low ~ ("<" name "([^a-z0-9_]|$)")) { found[name] = 1; continue }
          if (substr(low, 1, 1) == "#") {
            h = 0
            while (substr(low, h + 1, 1) == "#") h++
            if (h >= 1 && h <= 6 && substr(low, h + 1, 1) ~ /[ \t\r\v\f]/) {
              head = name
              gsub(/_/, "[ _-]", head)
              rest = substr(low, h + 1)
              sub(/^[ \t\r\v\f]+/, "", rest)
              if (rest ~ ("^" head)) found[name] = 1
            }
          }
        }
      }
      END {
        for (i = 1; i <= n; i++) printf "%s\t%d\n", order[i], (order[i] in found)
      }
    ' "$ROOT/SKILL.md" > "$SECTION_STATUS"
    while IFS=$'\t' read -r section hit; do
      if [ "$hit" -eq 0 ]; then printf '%s\n' "$section" >> "$SECTION_MISSING"; fi
    done < "$SECTION_STATUS"
    if [ -s "$SECTION_MISSING" ]; then
      jq -Rnc '[inputs | {code: "SECTION_MISSING", message: ("Required SKILL.md section is missing: " + .), section: .}] | .[]' \
        "$SECTION_MISSING" >> "$ERRORS"
    fi
  fi
  missing_json=$(jq -Rn -c '[inputs]' "$SECTION_MISSING")
  found_json=$(jq -Rn -c '[inputs | split("\t") | {key: .[0], value: (.[1] == "1")}] | from_entries' "$SECTION_STATUS")
  ok=1
  if [ -s "$SECTION_MISSING" ]; then ok=0; fi
  jq -cn --argjson ok "$ok" --arg s "$REQUIRED_SECTIONS" --argjson found "$found_json" --argjson missing "$missing_json" \
    '{ok: ($ok == 1), required: ($s | split(" ")), found: $found, missing: $missing}' > "$WORK/sections.json"
}

# rel_from_root <abs-path>: the repository-relative style path used in reports.
rel_from_root() {
  printf '%s' "${1#"$ROOT"/}"
}

# uri_decode <text>: percent-decoding of a markdown href, like decodeURIComponent without throwing.
uri_decode() {
  local input=$1 decoded="" ch hex
  while [ -n "$input" ]; do
    case $input in
      [%][0-9A-Fa-f][0-9A-Fa-f]*)
        hex=${input#%}
        hex=${hex:0:2}
        decoded="${decoded}\\$(printf '%03o' "$((16#$hex))")"
        input=${input:3}
        ;;
      *)
        ch=${input:0:1}
        if [ "$ch" = "\\" ]; then decoded="$decoded\\\\"; else decoded="$decoded$ch"; fi
        input=${input:1}
        ;;
    esac
  done
  printf '%b' "$decoded"
}

# ---------------------------------------------------------------------------
# checkLinks
# ---------------------------------------------------------------------------
{
  checked=0
  missing_json='[]'
  REFS=$WORK/links.refs
  awk -v root="$ROOT" -v listfile="$MARKDOWN_LIST" '
    function emit_at(line) {
      if (match(line, /^@[^ \t\r\n\v\f]+\.md[ \t\r\n\v\f]*$/)) {
        ref = substr(line, 2)
        sub(/[ \t\r\n\v\f]+$/, "", ref)
        if (ref != "") printf "%s\t%s\n", rel, ref
      }
    }
    function emit_md(line,   rest, m, h, p) {
      rest = line
      while (match(rest, /!?\[[^]]*\]\([^)[:space:]]+([[:space:]]+"[^"]*")?\)/)) {
        m = substr(rest, RSTART, RLENGTH)
        p = index(m, "](")
        h = substr(m, p + 2)
        sub(/\).*$/, "", h)
        sub(/[ \t].*$/, "", h)
        if (h != "" && h !~ /^(https?:\/\/|mailto:|#)/) printf "%s\t%s\n", rel, h
        rest = substr(rest, RSTART + RLENGTH)
      }
    }
    BEGIN {
      while ((getline f < listfile) > 0) {
        if (f == "") continue
        rel = substr(f, length(root) + 2)
        nl = 0
        while ((getline line < f) > 0) {
          nl++
          lines[nl] = line
          atline[nl] = 0
          if (match(line, /^@[^ \t\r\n\v\f]+\.md[ \t\r\n\v\f]*$/)) atline[nl] = 1
        }
        close(f)
        for (i = 1; i <= nl; i++) if (atline[i] == 1) emit_at(lines[i])
        for (i = 1; i <= nl; i++) emit_md(lines[i])
      }
    }
  ' > "$REFS"
  if [ -s "$REFS" ]; then
    while IFS=$'\t' read -r display ref; do
      [ -n "${ref:-}" ] || continue
      checked=$((checked + 1))
      base_dir=$ROOT/${display%/*}
      if [ "${display%/*}" = "$display" ]; then base_dir=$ROOT; fi
      if [ "${ref#/}" != "$ref" ]; then
        target=$(normalize_path "$ROOT/$ref")
      else
        decoded=$(uri_decode "${ref%%#*}")
        target=$(normalize_path "$base_dir/$decoded")
      fi
      rel=$(relpath "$ROOT" "$target")
      inside=1
      case $rel in
        ..*|/*) inside=0 ;;
      esac
      if [ "$inside" -eq 0 ] || [ ! -e "$target" ]; then
        resolved=$(relpath "$CWD" "$target")
        item=$(jq -cn --arg from "$display" --arg href "$ref" --arg resolved "$resolved" \
          '{from: $from, href: $href, resolved: $resolved}')
        missing_json=$(jq -nc --argjson arr "$missing_json" --argjson item "$item" '$arr + [$item]')
        push_issue "$ERRORS" "LINK_MISSING" "Local markdown link does not resolve: $display -> $ref" "$item"
      fi
    done < "$REFS"
  fi
  ok=1
  if [ "$(jq 'length' <<< "$missing_json")" -ne 0 ]; then ok=0; fi
  jq -cn --argjson ok "$ok" --argjson checked "$checked" --argjson missing "$missing_json" \
    '{ok: ($ok == 1), checked: $checked, missing: $missing}' > "$WORK/links.json"
}

# ---------------------------------------------------------------------------
# checkCodeFences
# ---------------------------------------------------------------------------
{
  FENCES=$WORK/fences.tsv
  awk -v root="$ROOT" -v listfile="$MARKDOWN_LIST" '
    BEGIN {
      while ((getline f < listfile) > 0) {
        if (f == "") continue
        rel = substr(f, length(root) + 2)
        top = 0
        nl = 0
        while ((getline line < f) > 0) {
          nl++
          if (match(line, /^[ \t\r\v\f]*[`~]/)) {
            ch = substr(line, RSTART + RLENGTH - 1, 1)
            pos = RSTART + RLENGTH
            run = 1
            while (substr(line, pos, 1) == ch) { run++; pos++ }
            if (run >= 3) {
              if (top > 0 && stack[top] == ch) {
                top--
              } else {
                top++
                stack[top] = ch
                stackline[top] = nl
              }
            }
          }
        }
        close(f)
        if (top == 0) {
          printf "%s\t1\t\n", rel
        } else {
          json = "["
          for (i = 1; i <= top; i++) {
            json = json (i > 1 ? "," : "") "{\"fence\":\"" stack[i] "\",\"line\":" stackline[i] "}"
          }
          json = json "]"
          printf "%s\t0\t%s\n", rel, json
        }
      }
    }
  ' > "$FENCES"
  files_json=$(jq -Rn -c '[inputs | split("\t") | {path: .[0], balanced: (.[1] == "1")} + (if .[2] == "" then {} else {unclosed: (.[2] | fromjson)} end)]' "$FENCES")
  if grep -q $'\t0\t' "$FENCES"; then
    jq -Rnc '[inputs | split("\t") | select(.[1] == "0") |
      {code: "CODE_FENCE_UNBALANCED", message: ("Unbalanced code fence in " + .[0]), path: .[0], balanced: false, unclosed: (.[2] | fromjson)}] | .[]' \
      "$FENCES" >> "$ERRORS"
  fi
  ok=1
  if grep -q $'\t0\t' "$FENCES"; then ok=0; fi
  jq -cn --argjson ok "$ok" --argjson files "$files_json" '{ok: ($ok == 1), files: $files}' > "$WORK/fences.json"
}

# ---------------------------------------------------------------------------
# checkBilingualPairs
# ---------------------------------------------------------------------------
{
  PAIRS=$WORK/pairs.tsv
  awk -v listfile="$REL_LOOKUP" '
    BEGIN {
      n = 0
      while ((getline line < listfile) > 0) {
        if (line == "") continue
        n++
        order[n] = line
        present[line] = 1
      }
      for (i = 1; i <= n; i++) {
        file = order[i]
        if (file ~ /\.ko\.md$/) {
          source = substr(file, 1, length(file) - 6) ".md"
          if (!(source in present)) printf "O\t%s\n", file
        } else {
          korean = substr(file, 1, length(file) - 3) ".ko.md"
          if (!(korean in present)) printf "M\t%s\n", korean
        }
      }
    }
  ' > "$PAIRS"
  missing_json=$(jq -Rn -c '[inputs | split("\t") | select(.[0] == "M") | .[1]]' "$PAIRS")
  orphan_json=$(jq -Rn -c '[inputs | split("\t") | select(.[0] == "O") | .[1]]' "$PAIRS")
  if [ -s "$PAIRS" ]; then
    jq -Rnc '[inputs | split("\t") |
      if .[0] == "M" then {code: "BILINGUAL_MISSING", message: ("Missing Korean markdown pair: " + .[1]), path: .[1]}
      else {code: "BILINGUAL_ORPHAN", message: ("Korean markdown pair has no English source: " + .[1]), path: .[1]} end] | .[]' \
      "$PAIRS" >> "$ERRORS"
  fi
  ok=1
  if [ -s "$PAIRS" ]; then ok=0; fi
  jq -cn --argjson ok "$ok" --argjson missing "$missing_json" --argjson orphan "$orphan_json" \
    '{ok: ($ok == 1), missing: $missing, orphan: $orphan}' > "$WORK/pairs.json"
}

# ---------------------------------------------------------------------------
# checkCoreParity
# ---------------------------------------------------------------------------
{
  en=$ROOT/SKILL.md
  ko=$ROOT/SKILL.ko.md
  if [ ! -e "$en" ] || [ ! -e "$ko" ]; then
    jq -cn '{ok: false, tags: false, supportLinks: false}' > "$WORK/coreparity.json"
  else
    tags_en=$WORK/tags.en
    tags_ko=$WORK/tags.ko
    grep -iE '^</?[a-z][a-z0-9_]*>[[:space:]]*$' "$en" | tr '[:upper:]' '[:lower:]' > "$tags_en"
    grep -iE '^</?[a-z][a-z0-9_]*>[[:space:]]*$' "$ko" | tr '[:upper:]' '[:lower:]' > "$tags_ko"
    links_en=$WORK/atlinks.en
    links_ko=$WORK/atlinks.ko
    sed -n 's/^@\([^[:space:]]*\.md\)[[:space:]]*$/\1/p' "$en" | sed -E 's/\.ko\.md$/.md/' > "$links_en"
    sed -n 's/^@\([^[:space:]]*\.md\)[[:space:]]*$/\1/p' "$ko" | sed -E 's/\.ko\.md$/.md/' > "$links_ko"
    tags=0
    if cmp -s "$tags_en" "$tags_ko"; then tags=1; fi
    support=0
    if cmp -s "$links_en" "$links_ko"; then support=1; fi
    if [ "$tags" -eq 0 ]; then
      push_issue "$ERRORS" "BILINGUAL_TAG_DRIFT" "SKILL.md and SKILL.ko.md structural tags differ" \
        "$(jq -cn --argjson a "$(json_line_array "$tags_en")" --argjson b "$(json_line_array "$tags_ko")" '{tagsEn: $a, tagsKo: $b}')"
    fi
    if [ "$support" -eq 0 ]; then
      push_issue "$ERRORS" "BILINGUAL_LINK_DRIFT" "SKILL.md and SKILL.ko.md support links differ" \
        "$(jq -cn --argjson a "$(json_line_array "$links_en")" --argjson b "$(json_line_array "$links_ko")" '{linksEn: $a, linksKo: $b}')"
    fi
    ok=0
    if [ "$tags" -eq 1 ] && [ "$support" -eq 1 ]; then ok=1; fi
    jq -cn --argjson ok "$ok" --argjson tags "$tags" --argjson support "$support" \
      '{ok: ($ok == 1), tags: ($tags == 1), supportLinks: ($support == 1)}' > "$WORK/coreparity.json"
  fi
}

# ---------------------------------------------------------------------------
# checkEvalCases
# ---------------------------------------------------------------------------
JQ_EVAL_ROW=$(cat <<'JQ'
def ne: (type == "string") and (test("\\S"));
def cats: ["positive", "negative", "boundary", "workflow", "source", "safety", "adversarial", "regression", "coexistence"];
def trigs: ["positive", "negative", "boundary", "coexistence"];
def langs: ["en", "ko", "mixed"];
def hasid: (. as $r | $r | has("id"));
if type != "object" then
  "false", "false", "null", "false", "null", "false", "null",
  ([{msg: "Eval case must be a JSON object", contract: false, extra: {line: $ln}}] | tojson)
else
  . as $r |
  (if ($r | has("id")) then {id: $r.id} else {} end) as $idExtra |
  (if ($r | has("category")) then {category: $r.category} else {} end) as $catExtra |
  {
    object: true,
    idNonEmpty: (($r | has("id")) and ($r.id | ne)),
    idValue: (if ($r | has("id")) then $r.id else null end),
    categoryOk: ((($r.category | type) == "string") and ((($r.category) as $c | cats | index($c)) != null)),
    categoryString: (($r.category | type) == "string"),
    categoryValue: (if ($r | has("category")) then $r.category else null end),
    languageOk: ((($r.language | type) == "string") and ((($r.language) as $c | langs | index($c)) != null)),
    languageString: (($r.language | type) == "string"),
    languageValue: (if ($r | has("language")) then $r.language else null end),
    intentOk: (($r | has("intent")) and ($r.intent | ne)),
    promptOk: (($r | has("prompt")) and ($r.prompt | ne)),
    contextOk: ((($r.context | type) == "object") and (($r.context.files | type) == "array") and (($r.context.sources | type) == "array")),
    metricsOk: ((($r.metrics | type) == "array") and (($r.metrics | length) > 0) and ([$r.metrics[] | ne] | all)),
    trigger: ((($r.category | type) == "string") and ((($r.category) as $c | trigs | index($c)) != null)),
    expectOk: ($r.expect == "trigger" or $r.expect == "no_trigger"),
    runsOk: (if ($r.runs | type) == "number" then ((($r.runs | floor) == $r.runs) and ($r.runs >= 1)) else false end),
    thresholdOk: (if ($r.threshold | type) == "number" then (($r.threshold > 0) and ($r.threshold < 1)) else false end),
    expectedOk: (($r.expected | type) == "object"),
    mustOk: ((($r.expected.must | type) == "array") and (($r.expected.must | length) > 0)),
    mustNotOk: ((($r.expected.mustNot | type) == "array") and (($r.expected.mustNot | length) > 0)),
    issues: [
      (if (($r | has("id")) and ($r.id | ne)) then empty else
        {msg: "Eval case requires non-empty id", contract: false, extra: ({line: $ln} + $idExtra)} end),
      (if ((($r.category | type) == "string") and ((($r.category) as $c | cats | index($c)) != null)) then empty else
        {msg: "Eval case requires a supported category", contract: false, extra: ({line: $ln} + $idExtra + $catExtra)} end),
      (if ((($r.language | type) == "string") and ((($r.language) as $c | langs | index($c)) != null)) then empty else
        {msg: "Eval case requires language en, ko, or mixed", contract: false,
         extra: ({line: $ln} + $idExtra + (if ($r | has("language")) then {language: $r.language} else {} end))} end),
      (if (($r | has("intent")) and ($r.intent | ne)) then empty else
        {msg: "Eval case requires non-empty intent", contract: false, extra: ({line: $ln} + $idExtra)} end),
      (if (($r | has("prompt")) and ($r.prompt | ne)) then empty else
        {msg: "Eval case requires non-empty prompt", contract: false, extra: ({line: $ln} + $idExtra)} end),
      (if ((($r.context | type) == "object") and (($r.context.files | type) == "array") and (($r.context.sources | type) == "array")) then empty else
        {msg: "EVAL_CASE_INVALID: eval case context requires files and sources arrays", contract: false, extra: ({line: $ln} + $idExtra)} end),
      (if ((($r.metrics | type) == "array") and (($r.metrics | length) > 0) and ([$r.metrics[] | ne] | all)) then empty else
        {msg: "EVAL_CASE_INVALID: eval case requires non-empty metrics", contract: false, extra: ({line: $ln} + $idExtra)} end),
      (if ((($r.category | type) == "string") and ((($r.category) as $c | trigs | index($c)) != null)) then
        (
          (if ($r.expect == "trigger" or $r.expect == "no_trigger") then empty else
            {msg: "EVAL_CASE_INVALID: trigger eval requires expect to be trigger or no_trigger", contract: true,
             extra: ({line: $ln} + $idExtra + (if ($r | has("expect")) then {expect: $r.expect} else {} end) + {contract: true})} end),
          (if (if ($r.runs | type) == "number" then ((($r.runs | floor) == $r.runs) and ($r.runs >= 1)) else false end) then empty else
            {msg: "EVAL_CASE_INVALID: trigger eval requires a positive integer runs value stated on the case", contract: true,
             extra: ({line: $ln} + $idExtra + (if ($r | has("runs")) then {runs: $r.runs} else {} end) + {contract: true})} end),
          (if (if ($r.threshold | type) == "number" then (($r.threshold > 0) and ($r.threshold < 1)) else false end) then empty else
            {msg: "EVAL_CASE_INVALID: trigger eval requires a threshold between 0 and 1 stated on the case", contract: true,
             extra: ({line: $ln} + $idExtra + (if ($r | has("threshold")) then {threshold: $r.threshold} else {} end) + {contract: true})} end)
        )
       else empty end),
      (if (($r.expected | type) == "object") then
        (
          (if ((($r.expected.must | type) == "array") and (($r.expected.must | length) > 0)) then empty else
            {msg: "EVAL_CASE_INVALID: expected.must must be a non-empty array", contract: false, extra: ({line: $ln} + $idExtra)} end),
          (if ((($r.expected.mustNot | type) == "array") and (($r.expected.mustNot | length) > 0)) then empty else
            {msg: "EVAL_CASE_INVALID: expected.mustNot must be a non-empty array", contract: false, extra: ({line: $ln} + $idExtra)} end)
        )
       else
        {msg: "EVAL_CASE_INVALID: eval case requires expected object", contract: false, extra: ({line: $ln} + $idExtra)}
       end)
    ]
  } as $out |
  "true",
  (if $out.idNonEmpty then "true" else "false" end),
  ($out.idValue | tojson),
  (if $out.categoryString then "true" else "false" end),
  ($out.categoryValue | tojson),
  (if $out.languageString then "true" else "false" end),
  ($out.languageValue | tojson),
  ($out.issues | tojson)
end
JQ
)

# counts_json <file>: counts of JSON-encoded keys recorded one per line, first-seen order.
counts_json() {
  if [ -s "$1" ]; then
    jq -R -s -c 'split("\n") | map(select(length > 0)) | reduce .[] as $line ({}; ($line | fromjson) as $k | if has($k) then .[$k] += 1 else .[$k] = 1 end)' "$1"
  else
    printf '{}'
  fi
}

{
  total=0
  : > "$WORK/ids.seen"
  : > "$WORK/categories.jsonl"
  : > "$WORK/languages.jsonl"
  line_no=0
  evals_present=1
  if [ ! -e "$EVALS_PATH" ]; then
    evals_present=0
    push_issue "$ERRORS" "EVAL_FILE_MISSING" "Eval JSONL file is missing: $EVALS_PATH" \
      "$(jq -cn --arg path "$EVALS_PATH" '{path: $path}')"
  else
    while IFS= read -r rawline || [ -n "$rawline" ]; do
      line_no=$((line_no + 1))
      line=${rawline%$'\r'}
      if [ -z "${line//[[:space:]]/}" ]; then continue; fi
      analysis=$(printf '%s\n' "$line" | jq -r --argjson ln "$line_no" "$JQ_EVAL_ROW" 2>/dev/null)
      result_lines=0
      if [ -n "$analysis" ]; then
        without_newlines=${analysis//$'\n'/}
        result_lines=$(( ${#analysis} - ${#without_newlines} + 1 ))
      fi
      if [ "$result_lines" -ne 8 ]; then
        push_issue "$ERRORS" "EVAL_CASE_INVALID" \
          "EVAL_CASE_INVALID: Eval case line $line_no is not valid JSON: invalid JSON" \
          "$(jq -cn --argjson line "$line_no" '{line: $line}')"
        continue
      fi
      {
        IFS= read -r field_object
        IFS= read -r field_id_nonempty
        IFS= read -r field_id
        IFS= read -r field_category_string
        IFS= read -r field_category
        IFS= read -r field_language_string
        IFS= read -r field_language
        IFS= read -r field_issues
      } <<< "$analysis"
      if [ "$field_object" != "true" ]; then
        push_issue "$ERRORS" "EVAL_CASE_INVALID" "EVAL_CASE_INVALID: Eval case must be a JSON object" \
          "$(jq -cn --argjson line "$line_no" '{line: $line}')"
        continue
      fi
      total=$((total + 1))
      if [ "$field_issues" != "[]" ]; then
        issue_count=$(jq 'length' <<< "$field_issues")
        issue_idx=0
        while [ "$issue_idx" -lt "$issue_count" ]; do
          rec=$(jq -c --argjson i "$issue_idx" '.[$i]' <<< "$field_issues")
          msg=$(jq -r '.msg' <<< "$rec")
          contract=$(jq -r '.contract' <<< "$rec")
          extra=$(jq -c '.extra' <<< "$rec")
          case $msg in
            *EVAL_CASE_INVALID*) final_msg=$msg ;;
            *) final_msg="EVAL_CASE_INVALID: $msg" ;;
          esac
          if [ "$contract" = "true" ]; then
            push_issue "$CONTRACT_SINK" "EVAL_CASE_INVALID" "$final_msg" "$extra"
          else
            push_issue "$ERRORS" "EVAL_CASE_INVALID" "$final_msg" "$extra"
          fi
          issue_idx=$((issue_idx + 1))
        done
      fi
      if [ "$field_id_nonempty" = "true" ]; then
        if grep -Fxq -- "$field_id" "$WORK/ids.seen"; then
          id_value=$(jq -r '.' <<< "$field_id")
          push_issue "$ERRORS" "EVAL_CASE_INVALID" "EVAL_CASE_INVALID: Duplicate eval case id: $id_value" \
            "$(jq -cn --argjson line "$line_no" --arg id "$id_value" '{line: $line, id: $id}')"
        fi
        printf '%s\n' "$field_id" >> "$WORK/ids.seen"
      fi
      if [ "$field_category_string" = "true" ]; then
        printf '%s\n' "$field_category" >> "$WORK/categories.jsonl"
      fi
      if [ "$field_language_string" = "true" ]; then
        printf '%s\n' "$field_language" >> "$WORK/languages.jsonl"
      fi
    done < "$EVALS_PATH"
  fi

  counts=$(counts_json "$WORK/categories.jsonl")
  language_counts=$(counts_json "$WORK/languages.jsonl")

  # Floors: coexistence belongs to the strengthened contract, so it applies only in strict mode.
  # A missing eval file returns before any floor is applied, but still reports the declared floors.
  required_json='{}'
  if [ "$evals_present" -eq 0 ]; then
    # shellcheck disable=SC2086 # intentional word splitting of the declared floor list
    set -- $CATEGORY_FLOOR_VALUES
    for name in $CATEGORY_FLOOR_NAMES; do
      floor=$1
      shift
      required_json=$(jq -c --argjson obj "$required_json" --arg k "$name" --argjson v "$floor" '$obj + {($k): $v}' <<< '{}')
    done
  else
  # shellcheck disable=SC2086 # intentional word splitting of the declared floor list
  set -- $CATEGORY_FLOOR_VALUES
  for name in $CATEGORY_FLOOR_NAMES; do
    floor=$1
    shift
    if [ "$name" = "coexistence" ] && [ "$STRICT" -ne 1 ]; then continue; fi
    actual=$(jq -r --arg k "$name" '.[$k] // 0' <<< "$counts")
    if [ "$actual" -lt "$floor" ]; then
      push_issue "$ERRORS" "EVAL_DIMENSION_COUNT" "Expected at least $floor category case(s) for $name" \
        "$(jq -cn --arg name "$name" --argjson expected "$floor" --argjson actual "$actual" \
          '{dimension: "category", name: $name, expected: $expected, actual: $actual}')"
    fi
    required_json=$(jq -nc --argjson obj "$required_json" --arg k "$name" --argjson v "$floor" '$obj + {($k): $v}' <<< '{}')
  done
  # shellcheck disable=SC2086 # intentional word splitting of the declared floor list
  set -- $LANGUAGE_FLOOR_VALUES
  for name in $LANGUAGE_FLOOR_NAMES; do
    floor=$1
    shift
    actual=$(jq -r --arg k "$name" '.[$k] // 0' <<< "$language_counts")
    if [ "$actual" -lt "$floor" ]; then
      push_issue "$ERRORS" "EVAL_DIMENSION_COUNT" "Expected at least $floor language case(s) for $name" \
        "$(jq -cn --arg name "$name" --argjson expected "$floor" --argjson actual "$actual" \
          '{dimension: "language", name: $name, expected: $expected, actual: $actual}')"
    fi
  done
  fi

  eval_ok=1
  if [ -s "$ERRORS" ]; then
    if [ "$(jq -s 'any(.[]; (.code | startswith("EVAL_")))' "$ERRORS")" = "true" ]; then eval_ok=0; fi
  fi
  required_languages=$(jq -cn '{en: 1, ko: 1, mixed: 1}')
  jq -cn \
    --argjson ok "$eval_ok" \
    --arg path "$EVALS_PATH" \
    --argjson total "$total" \
    --argjson counts "$counts" \
    --argjson languageCounts "$language_counts" \
    --argjson required "$required_json" \
    --argjson requiredLanguages "$required_languages" \
    '{ok: ($ok == 1), path: $path, total: $total, counts: $counts, languageCounts: $languageCounts, required: $required, requiredLanguages: $requiredLanguages}' \
    > "$WORK/triggers.json"
}

# ---------------------------------------------------------------------------
# checkOfficialLastVerified
# ---------------------------------------------------------------------------
{
  OFFICIAL_LIST=$WORK/official.list
  : > "$OFFICIAL_LIST"
  officialRoot=$ROOT/references/official
  if [ -e "$officialRoot" ]; then
    find "$officialRoot" -type f -print 2>/dev/null | LC_ALL=C sort | grep -E '\.md$' > "$OFFICIAL_LIST" || : > "$OFFICIAL_LIST"
  fi
  OFFICIAL_DATES=$WORK/official.dates
  awk -v root="$ROOT" -v listfile="$OFFICIAL_LIST" '
    BEGIN {
      while ((getline f < listfile) > 0) {
        if (f == "") continue
        rel = substr(f, length(root) + 2)
        joined = ""
        while ((getline line < f) > 0) {
          rest = line
          while (match(rest, /last_verified_at:[ \t\r\n\v\f]*[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/)) {
            m = substr(rest, RSTART, RLENGTH)
            p = index(m, "last_verified_at:")
            date = substr(m, p + 17)
            sub(/^[ \t\r\n\v\f]+/, "", date)
            if (joined == "") joined = date
            else joined = joined " " date
            rest = substr(rest, RSTART + RLENGTH)
          }
        }
        close(f)
        printf "%s\t%s\n", rel, joined
      }
    }
  ' "$OFFICIAL_LIST" > "$OFFICIAL_DATES"
  checked=0
  invalid_json='[]'
  while IFS=$'\t' read -r rel dates_str; do
    [ -n "$rel" ] || continue
    checked=$((checked + 1))
    invalid_dates=""
    for date in $dates_str; do
      if ! is_valid_date "$date" || [[ "$date" > "$VALIDATION_DATE" ]]; then
        invalid_dates="$invalid_dates $date"
      fi
    done
    if [ -z "$dates_str" ] || [ -n "$invalid_dates" ]; then
      item=$(jq -cn --arg path "$rel" \
        --argjson dates "$(jq -Rn -c --arg d "$dates_str" '[$d | split(" ") | .[] | select(length > 0)]')" \
        --argjson invalidDates "$(jq -Rn -c --arg d "$invalid_dates" '[$d | split(" ") | .[] | select(length > 0)]')" \
        '{path: $path, dates: $dates, invalidDates: $invalidDates}')
      invalid_json=$(jq -nc --argjson arr "$invalid_json" --argjson item "$item" '$arr + [$item]')
      push_issue "$ERRORS" "OFFICIAL_LAST_VERIFIED_AT" \
        "Official reference dates must be valid and not later than $VALIDATION_DATE" "$item"
    fi
  done < "$OFFICIAL_DATES"
  ok=1
  if [ "$(jq 'length' <<< "$invalid_json")" -ne 0 ]; then ok=0; fi
  jq -cn --argjson ok "$ok" --arg validationDate "$VALIDATION_DATE" --argjson checked "$checked" --argjson invalid "$invalid_json" \
    '{ok: ($ok == 1), validationDate: $validationDate, checked: $checked, invalid: $invalid}' > "$WORK/official.json"
}

# ---------------------------------------------------------------------------
# checkSourcesSections
# ---------------------------------------------------------------------------
{
  SOURCES_SINK=$CONTRACT_SINK
  SOURCES_TSV=$WORK/sources.tsv
  awk -v root="$ROOT" -v listfile="$REL_LOOKUP" '
    function is_target(rel) {
      return (rel ~ /^rules\//) || (rel ~ /^references\//)
    }
    BEGIN {
      while ((getline rel < listfile) > 0) {
        if (rel == "") continue
        if (!is_target(rel)) continue
        f = root "/" rel
        nl = 0
        while ((getline line < f) > 0) { nl++; lines[nl] = line }
        close(f)
        at = 0
        for (i = 1; i <= nl; i++) {
          if (lines[i] ~ /^## ([0-9]+\. )?Sources[ \t\r\v\f]*$/) { at = i; break }
        }
        if (at == 0) {
          printf "%s\tNOSECTION\t\n", rel
          continue
        }
        found = ""
        for (i = at; i <= at + 5 && i <= nl; i++) {
          low = tolower(lines[i])
          if (substr(low, 1, 2) != "> ") continue
          rest = low
          lastdate = ""
          while (match(rest, /(checked|확인)[ \t\r\v\f]+[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/)) {
            m = substr(rest, RSTART, RLENGTH)
            lastdate = substr(m, length(m) - 9)
            rest = substr(rest, RSTART + RLENGTH)
          }
          if (lastdate != "") { found = lastdate; break }
        }
        if (found == "") printf "%s\tNODATE\t\n", rel
        else printf "%s\tDATE\t%s\n", rel, found
        delete lines
      }
    }
  ' > "$SOURCES_TSV"
  checked=0
  invalid_json='[]'
  ISSUE_TSV=$WORK/sources.invalid
  : > "$ISSUE_TSV"
  while IFS=$'\t' read -r rel status date; do
    [ -n "$rel" ] || continue
    checked=$((checked + 1))
    case $status in
      NOSECTION)
        printf '%s\t%s\n' "$rel" "no Sources section" >> "$ISSUE_TSV"
        ;;
      NODATE)
        printf '%s\t%s\n' "$rel" "no checked-date line" >> "$ISSUE_TSV"
        ;;
      DATE)
        if ! is_valid_date "$date"; then
          printf '%s\t%s\t%s\n' "$rel" "impossible checked date $date" "$date" >> "$ISSUE_TSV"
        fi
        ;;
    esac
  done < "$SOURCES_TSV"
  if [ -s "$ISSUE_TSV" ]; then
    invalid_json=$(jq -Rn -c '[inputs | split("\t") | {path: .[0], reason: .[1]}]' "$ISSUE_TSV")
    jq -Rnc '[inputs | split("\t") |
      if .[1] == "no Sources section" then
        {code: "SOURCES_MISSING", message: ("Rules and reference files must carry a Sources section: " + .[0]), path: .[0]}
      elif .[1] == "no checked-date line" then
        {code: "SOURCES_CHECKED_DATE_MISSING", message: ("Sources section must carry a checked-date line: " + .[0]), path: .[0]}
      else
        {code: "SOURCES_CHECKED_DATE_INVALID", message: ("Sources section checked date is not a real calendar date: " + .[0] + " (" + .[2] + ")"), path: .[0], date: .[2]}
      end] | .[]' "$ISSUE_TSV" >> "$SOURCES_SINK"
  fi
  ok=1
  if [ "$(jq 'length' <<< "$invalid_json")" -ne 0 ]; then ok=0; fi
  jq -cn --argjson ok "$ok" --argjson checked "$checked" --argjson invalid "$invalid_json" \
    '{ok: ($ok == 1), checked: $checked, invalid: $invalid}' > "$WORK/sources.json"
}

# ---------------------------------------------------------------------------
# checkIdParity
# ---------------------------------------------------------------------------
{
  ID_DRIFT=$WORK/idparity.tsv
  awk -v root="$ROOT" -v listfile="$REL_LOOKUP" '
    function load_ids(f, outname,   line, id, seen, n) {
      n = 0
      while ((getline line < f) > 0) {
        if (line ~ /^- SK-[A-Z]-[0-9]+:/) {
          id = substr(line, 3)
          sub(/:.*/, "", id)
          if (!(id in seen)) { seen[id] = 1; ids[outname, ++n] = id }
        }
      }
      close(f)
      count[outname] = n
    }
    BEGIN {
      n = 0
      while ((getline line < listfile) > 0) {
        if (line == "") continue
        n++
        order[n] = line
        present[line] = 1
      }
      for (i = 1; i <= n; i++) {
        rel = order[i]
        if (rel ~ /\.ko\.md$/) continue
        ko = substr(rel, 1, length(rel) - 3) ".ko.md"
        if (!(ko in present)) continue
        delete ids
        delete count
        load_ids(root "/" rel, "en")
        load_ids(root "/" ko, "ko")
        for (j = 1; j <= count["en"]; j++) {
          id = ids["en", j]
          hit = 0
          for (k = 1; k <= count["ko"]; k++) if (ids["ko", k] == id) { hit = 1; break }
          if (!hit) printf "%s\t%s\t%s\n", rel, ko, id
        }
        for (j = 1; j <= count["ko"]; j++) {
          id = ids["ko", j]
          hit = 0
          for (k = 1; k <= count["en"]; k++) if (ids["en", k] == id) { hit = 1; break }
          if (!hit) printf "%s\t%s\t%s\n", ko, rel, id
        }
      }
    }
  ' > "$ID_DRIFT"
  drift_json='[]'
  if [ -s "$ID_DRIFT" ]; then
    drift_json=$(jq -Rn -c '[inputs | split("\t") | {path: .[0], missingIn: .[1], id: .[2]}]' "$ID_DRIFT")
    jq -Rnc '[inputs | split("\t") |
      {code: "ID_PARITY_DRIFT", message: ("Normative id " + .[2] + " is in " + .[0] + " but not in " + .[1]), path: .[0], missingIn: .[1], id: .[2]}] | .[]' \
      "$ID_DRIFT" >> "$ERRORS"
  fi
  ok=1
  if [ "$(jq 'length' <<< "$drift_json")" -ne 0 ]; then ok=0; fi
  jq -cn --argjson ok "$ok" --argjson drift "$drift_json" '{ok: ($ok == 1), drift: $drift}' > "$WORK/idparity.json"
}

# ---------------------------------------------------------------------------
# checkSelfContainment
# ---------------------------------------------------------------------------
SELF_CONTAINMENT_TEXTS=".md .jsonl .json .mjs .js .sh .py .html .css .yml .yaml .toml .txt"
{
  parent=${ROOT%/*}
  if [ -z "$parent" ]; then parent="/"; fi
  self_name=${ROOT##*/}
  SIBLINGS=$WORK/siblings.txt
  : > "$SIBLINGS"
  if [ -d "$parent" ]; then
    find "$parent" -mindepth 1 -maxdepth 1 -type d -print 2>/dev/null | LC_ALL=C sort |
      while IFS= read -r candidate; do
        name=${candidate##*/}
        if [ "$name" = "$self_name" ]; then continue; fi
        if [ -f "$candidate/SKILL.md" ]; then printf '%s\n' "$name"; fi
      done > "$SIBLINGS"
  fi
  ALLOW_FILE=$WORK/allow.txt
  : > "$ALLOW_FILE"
  if [ "${#ALLOW[@]}" -gt 0 ]; then
    for name in ${ALLOW[@]+"${ALLOW[@]}"}; do printf '%s\n' "$name" >> "$ALLOW_FILE"; done
  fi
  TEXT_LIST=$WORK/textfiles.txt
  awk -v exts="$SELF_CONTAINMENT_TEXTS" '
    BEGIN { n = split(exts, want, " "); for (i = 1; i <= n; i++) allowed[want[i]] = 1 }
    function last_dot(text,   i, p) {
      p = 0
      for (i = 1; i <= length(text); i++) if (substr(text, i, 1) == ".") p = i
      return p
    }
    {
      base = $0
      sub(/.*\//, "", base)
      ext = ""
      if (substr(base, 1, 1) == ".") {
        rest = substr(base, 2)
        p = last_dot(rest)
        if (p > 0) ext = substr(rest, p)
      } else {
        p = last_dot(base)
        if (p > 0) ext = substr(base, p)
      }
      if (tolower(ext) in allowed) print $0
    }
  ' "$FILES_LIST" > "$TEXT_LIST"
  HIT_FILE=$WORK/selfhits.tsv
  awk -v root="$ROOT" -v self="$self_name" -v strict="$REQUIRE_SELF_CONTAINMENT" \
    -v sibfile="$SIBLINGS" -v allowfile="$ALLOW_FILE" -v listfile="$TEXT_LIST" '
    function emit(relname, ln, text,   i, key, no, seen, order, name, rest, p, start, nm, j, form) {
      split("", seen)
      no = 0
      for (i = 1; i <= ns; i++) {
        name = sibs[i]
        key = ""
        if (text ~ ("\\$" name "([^A-Za-z0-9-]|$)")) key = name "|$" name
        else if (index(text, "skills/" name "/") > 0) key = name "|skills/" name "/"
        else if (index(name, "-") > 0 && (text ~ ("(^|[^A-Za-z0-9-])" name "([^A-Za-z0-9-]|$)"))) key = name "|" name
        if (key != "" && !(key in seen)) { seen[key] = 1; order[++no] = key }
      }
      if (strict == 1) {
        rest = text
        while ((p = index(rest, "skills/")) > 0) {
          start = substr(rest, p + 7)
          if (match(start, /^[A-Za-z0-9][A-Za-z0-9._-]*\//)) {
            nm = substr(start, 1, RLENGTH - 1)
            if (nm != self) {
              key = nm "|skills/" nm "/"
              if (!(key in seen)) { seen[key] = 1; order[++no] = key }
            }
            rest = substr(rest, p + 7 + RLENGTH)
          } else {
            rest = substr(rest, p + 7)
          }
        }
      }
      for (i = 1; i <= no; i++) {
        key = order[i]
        j = index(key, "|")
        nm = substr(key, 1, j - 1)
        form = substr(key, j + 1)
        printf "%s\t%d\t%s\t%s\t%d\n", relname, ln, nm, form, (nm in allowed)
      }
    }
    BEGIN {
      ns = 0
      while ((getline line < sibfile) > 0) if (line != "") sibs[++ns] = line
      while ((getline line < allowfile) > 0) if (line != "") allowed[line] = 1
      while ((getline tf < listfile) > 0) {
        if (tf == "") continue
        relname = substr(tf, length(root) + 2)
        ln = 0
        while ((getline line < tf) > 0) { ln++; emit(relname, ln, line) }
        close(tf)
      }
      exit
    }
  ' > "$HIT_FILE"
  findings_json='[]'
  waivers_json='[]'
  if [ -s "$HIT_FILE" ]; then
    findings_json=$(jq -Rn -c '[inputs | split("\t") | select(.[4] != "1") | {path: .[0], line: (.[1] | tonumber), name: .[2], form: .[3]}]' "$HIT_FILE")
    waivers_json=$(jq -Rn -c '[inputs | split("\t") | select(.[4] == "1") | {path: .[0], line: (.[1] | tonumber), name: .[2], form: .[3]}]' "$HIT_FILE")
    if [ "$REQUIRE_SELF_CONTAINMENT" -eq 1 ] || [ "$CONTRACT_SINK" = "$ERRORS" ]; then
      jq -Rnc '[inputs | split("\t") | select(.[4] != "1") |
        {code: "CROSS_SKILL_REFERENCE", message: ("Cross-skill reference to " + .[2] + " (" + .[3] + "): " + .[0] + ":" + .[1]), path: .[0], name: .[2], form: .[3], line: (.[1] | tonumber)}] | .[]' \
        "$HIT_FILE" >> "$ERRORS"
      jq -Rnc '[inputs | split("\t") | select(.[4] == "1") |
        {code: "SELF_CONTAINMENT_WAIVER", message: ("User-directed cross-skill reference waiver for " + .[2] + ": " + .[0] + ":" + .[1]), path: .[0], name: .[2], form: .[3]}] | .[]' \
        "$HIT_FILE" >> "$CONTRACT"
    else
      jq -Rnc '[inputs | split("\t") |
        if .[4] == "1" then
          {code: "SELF_CONTAINMENT_WAIVER", message: ("User-directed cross-skill reference waiver for " + .[2] + ": " + .[0] + ":" + .[1]), path: .[0], name: .[2], form: .[3]}
        else
          {code: "CROSS_SKILL_REFERENCE", message: ("Cross-skill reference to " + .[2] + " (" + .[3] + "): " + .[0] + ":" + .[1]), path: .[0], name: .[2], form: .[3], line: (.[1] | tonumber)}
        end] | .[]' \
        "$HIT_FILE" >> "$CONTRACT"
    fi
  fi
  checked_files=$(wc -l < "$TEXT_LIST" | tr -d ' ')
  siblings_json=$(json_line_array "$SIBLINGS")
  ok=1
  if [ "$(jq 'length' <<< "$findings_json")" -ne 0 ]; then ok=0; fi
  jq -cn --argjson ok "$ok" --argjson strict "$REQUIRE_SELF_CONTAINMENT" --argjson siblings "$siblings_json" \
    --argjson checkedFiles "$checked_files" --argjson findings "$findings_json" --argjson waivers "$waivers_json" \
    '{ok: ($ok == 1), strict: ($strict == 1), siblings: $siblings, checkedFiles: $checkedFiles, findings: $findings, waivers: $waivers}' \
    > "$WORK/selfcontain.json"
}

# ---------------------------------------------------------------------------
# checkScriptRuntime
# ---------------------------------------------------------------------------
{
  findings_json='[]'
  report_runtime() {
    # report_runtime <code> <message> <extra-json>
    findings_json=$(jq -nc --argjson arr "$findings_json" --arg code "$1" --arg message "$2" --argjson extra "$3" \
      '$arr + [{code: $code, message: $message} + $extra]')
    push_issue "$ERRORS" "$1" "$2" "$3"
  }
  candidates=$WORK/scripts.candidates
  : > "$candidates"
  if [ -d "$ROOT" ]; then
    find "$ROOT" -mindepth 1 -maxdepth 1 -print 2>/dev/null | LC_ALL=C sort > "$WORK/rootentries.txt"
    while IFS= read -r entry; do
      [ -n "$entry" ] || continue
      base=${entry##*/}
      lower=$(printf '%s' "$base" | tr '[:upper:]' '[:lower:]')
      if [ "$lower" = "scripts" ]; then printf '%s\n' "$entry" >> "$candidates"; fi
    done < "$WORK/rootentries.txt"
  fi
  entries_list=$WORK/scriptentries.txt
  : > "$entries_list"
  if [ -s "$candidates" ]; then
    while IFS= read -r candidate; do
      [ -n "$candidate" ] || continue
      rel=$(rel_from_root "$candidate")
      if [ ! -e "$candidate" ]; then
        message="$rel must resolve to a directory of bash .sh scripts"
        report_runtime "SCRIPT_RUNTIME_EXTENSION" "$message" "$(jq -cn --arg path "$rel" '{path: $path}')"
        continue
      fi
      if [ ! -d "$candidate" ]; then
        printf '%s\n' "$candidate" >> "$entries_list"
        continue
      fi
      DIR_STACK=("$candidate")
      while [ "${#DIR_STACK[@]}" -gt 0 ]; do
        top=$((${#DIR_STACK[@]} - 1))
        dir=${DIR_STACK[$top]}
        unset "DIR_STACK[$top]"
        listing=$WORK/scripts.entries
        # A trailing slash makes find treat a symlinked scripts directory as the directory it points to,
        # while symlinked entries inside it stay entries rather than being followed.
        if ! find "$dir/" -mindepth 1 -maxdepth 1 -print0 > "$listing" 2>/dev/null; then
          dir_rel=$(rel_from_root "$dir")
          message="$dir_rel could not be read, so the bundled-script rule cannot be verified there"
          report_runtime "SCRIPT_RUNTIME_UNREADABLE" "$message" "$(jq -cn --arg path "$dir_rel" '{path: $path}')"
          continue
        fi
        while IFS= read -r -d '' entry; do
          if [ -d "$entry" ] && [ ! -L "$entry" ]; then
            DIR_STACK+=("$entry")
          else
            printf '%s\n' "$entry" >> "$entries_list"
          fi
        done < "$listing"
      done
    done < "$candidates"
  fi
  LC_ALL=C sort -o "$entries_list" "$entries_list"
  checked=0
  while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    checked=$((checked + 1))
    rel=$(rel_from_root "$entry")
    ext=$(file_extension "$entry")
    if [ "$ext" != "$BUNDLED_SCRIPT_EXTENSION" ]; then
      message="$rel must be a bash .sh script; a bundled scripts directory ships no other extension"
      report_runtime "SCRIPT_RUNTIME_EXTENSION" "$message" "$(jq -cn --arg path "$rel" '{path: $path}')"
      continue
    fi
    first_line=""
    if [ -f "$entry" ]; then
      first_line=$(awk 'NR == 1 { sub(/\r$/, "", $0); printf "%s", $0; exit }' "$entry")
    fi
    if [ "$first_line" != "$BUNDLED_SCRIPT_SHEBANG" ]; then
      message="$rel must start with $BUNDLED_SCRIPT_SHEBANG"
      report_runtime "SCRIPT_RUNTIME_SHEBANG" "$message" \
        "$(jq -cn --arg path "$rel" --arg firstLine "$first_line" '{path: $path, firstLine: $firstLine}')"
    fi
  done < "$entries_list"
  ok=1
  if [ "$(jq 'length' <<< "$findings_json")" -ne 0 ]; then ok=0; fi
  jq -cn --argjson ok "$ok" --argjson checked "$checked" --argjson findings "$findings_json" \
    '{ok: ($ok == 1), checked: $checked, findings: $findings}' > "$WORK/runtime.json"
}

# ---------------------------------------------------------------------------
# checkFrontmatterConstraints
# ---------------------------------------------------------------------------
{
  if [ ! -f "$ROOT/SKILL.md" ]; then
    jq -cn '{ok: false, violations: []}' > "$WORK/frontmatter.json"
  else
    text_file=$ROOT/SKILL.md
    name=$(frontmatter_value "$text_file" name)
    description=$(frontmatter_value "$text_file" description)
    violations_json='[]'
    note_violation() {
      local field=$1 reason=$2 code=$3
      violations_json=$(jq -nc --argjson arr "$violations_json" --arg field "$field" --arg reason "$reason" \
        '$arr + [{field: $field, reason: $reason}]')
      push_issue "$ERRORS" "$code" "$field $reason" \
        "$(jq -cn --arg field "$field" --arg reason "$reason" '{field: $field, reason: $reason}')"
    }
    if [ -n "$name" ] && printf '%s' "$name" | grep -qE '<[^>]+>'; then
      note_violation "name" "must not contain XML tags" "FRONTMATTER_XML_TAG"
    fi
    if [ -n "$description" ] && printf '%s' "$description" | grep -qE '<[^>]+>'; then
      note_violation "description" "must not contain XML tags" "FRONTMATTER_XML_TAG"
    fi
    if [ -n "$name" ]; then
      lower_name=$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')
      for word in anthropic claude; do
        case $lower_name in
          *"$word"*) note_violation "name" "must not contain the reserved word \"$word\"" "FRONTMATTER_RESERVED_WORD" ;;
        esac
      done
    fi
    ok=1
    if [ "$(jq 'length' <<< "$violations_json")" -ne 0 ]; then ok=0; fi
    jq -cn --argjson ok "$ok" --argjson violations "$violations_json" \
      '{ok: ($ok == 1), violations: $violations}' > "$WORK/frontmatter.json"
  fi
}

# ---------------------------------------------------------------------------
# checkCoreLineBudget
# ---------------------------------------------------------------------------
{
  if [ ! -f "$ROOT/SKILL.md" ]; then
    jq -cn --argjson budget "$CORE_LINE_BUDGET" '{ok: false, lines: 0, budget: $budget}' > "$WORK/budget.json"
  else
    newlines=$(tr -cd '\n' < "$ROOT/SKILL.md" | wc -c | tr -d ' ')
    lines=$((newlines + 1))
    if [ "$lines" -gt "$CORE_LINE_BUDGET" ]; then
      push_issue "$ERRORS" "CORE_LINE_BUDGET" "SKILL.md has $lines lines, over the $CORE_LINE_BUDGET-line budget" \
        "$(jq -cn --argjson lines "$lines" --argjson budget "$CORE_LINE_BUDGET" '{lines: $lines, budget: $budget}')"
      jq -cn --argjson lines "$lines" --argjson budget "$CORE_LINE_BUDGET" '{ok: false, lines: $lines, budget: $budget}' > "$WORK/budget.json"
    else
      jq -cn --argjson lines "$lines" --argjson budget "$CORE_LINE_BUDGET" '{ok: true, lines: $lines, budget: $budget}' > "$WORK/budget.json"
    fi
  fi
}

# ---------------------------------------------------------------------------
# checkReferenceToc
# ---------------------------------------------------------------------------
{
  invalid_json='[]'
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    case $rel in
      references/*) ;;
      *) continue ;;
    esac
    newlines=$(tr -cd '\n' < "$ROOT/$rel" | wc -c | tr -d ' ')
    lines=$((newlines + 1))
    if [ "$lines" -gt "$REFERENCE_TOC_THRESHOLD" ]; then
      if ! grep -qiE '^## ([0-9]+\. )?(Contents|Table of Contents|목차)[[:space:]]*$' "$ROOT/$rel"; then
        item=$(jq -cn --arg path "$rel" --argjson lines "$lines" '{path: $path, lines: $lines}')
        invalid_json=$(jq -nc --argjson arr "$invalid_json" --argjson item "$item" '$arr + [$item]')
        push_issue "$ERRORS" "REFERENCE_TOC_MISSING" \
          "Reference file over $REFERENCE_TOC_THRESHOLD lines must carry a table of contents: $rel ($lines lines)" "$item"
      fi
    fi
  done < "$REL_LIST"
  ok=1
  if [ "$(jq 'length' <<< "$invalid_json")" -ne 0 ]; then ok=0; fi
  jq -cn --argjson ok "$ok" --argjson invalid "$invalid_json" '{ok: ($ok == 1), invalid: $invalid}' > "$WORK/toc.json"
}

# ---------------------------------------------------------------------------
# checkStrayDocs
# ---------------------------------------------------------------------------
{
  found_json='[]'
  STRAY_NAMES="README.md CHANGELOG.md QUICK_REFERENCE.md"
  DIR_STACK=("$ROOT")
  DEPTH_STACK=(0)
  while [ "${#DIR_STACK[@]}" -gt 0 ]; do
    top=$((${#DIR_STACK[@]} - 1))
    dir=${DIR_STACK[$top]}
    depth=${DEPTH_STACK[$top]}
    unset "DIR_STACK[$top]"
    unset "DEPTH_STACK[$top]"
    if [ "$depth" -gt 2 ]; then continue; fi
    listing=$WORK/stray.entries
    if [ ! -d "$dir" ] || ! find "$dir" -mindepth 1 -maxdepth 1 -print0 > "$listing" 2>/dev/null; then
      rel=$(relpath "$ROOT" "$dir")
      push_issue "$ERRORS" "DIR_READ_FAILED" "Cannot read directory while checking stray docs: $rel" \
        "$(jq -cn --arg path "$rel" --arg detail "readdir failed" '{path: $path, detail: $detail}')"
      continue
    fi
    while IFS= read -r -d '' entry; do
      if [ -L "$entry" ]; then
        continue
      elif [ -d "$entry" ]; then
        DIR_STACK+=("$entry")
        DEPTH_STACK+=($((depth + 1)))
      elif [ -f "$entry" ]; then
        base=${entry##*/}
        for stray in $STRAY_NAMES; do
          if [ "$base" = "$stray" ]; then
            rel=$(rel_from_root "$entry")
            found_json=$(jq -nc --argjson arr "$found_json" --arg p "$rel" '$arr + [$p]')
            push_issue "$ERRORS" "STRAY_DOC" \
              "Stray broad documentation file is not allowed under maxdepth 2: $rel" \
              "$(jq -cn --arg path "$rel" '{path: $path}')"
          fi
        done
      fi
    done < "$listing"
  done
  ok=1
  if [ "$(jq 'length' <<< "$found_json")" -ne 0 ]; then ok=0; fi
  jq -cn --argjson ok "$ok" --argjson found "$found_json" '{ok: ($ok == 1), found: $found}' > "$WORK/stray.json"
}

# ---------------------------------------------------------------------------
# warnings: staleness (non-fatal) followed by contract findings
# ---------------------------------------------------------------------------
{
  WARNINGS=$WORK/staleness.jsonl
  : > "$WARNINGS"
  if [ -s "$OFFICIAL_DATES" ]; then
    while IFS=$'\t' read -r rel dates_str; do
      [ -n "$rel" ] || continue
      for date in $dates_str; do
        if [[ "$date" < "$BASE_LAST_REVERIFIED" ]]; then
          jq -cn --arg path "$rel" --arg date "$date" '{path: $path, date: $date}' >> "$WARNINGS"
        fi
      done
    done < "$OFFICIAL_DATES"
  fi
  {
    if [ -s "$WARNINGS" ]; then jq -s -c '.' "$WARNINGS"; fi
    if [ -s "$CONTRACT" ]; then jq -s -c '.' "$CONTRACT"; fi
  } | jq -s -c 'add // []' > "$WORK/warnings.json"
}

# ---------------------------------------------------------------------------
# Result assembly
# ---------------------------------------------------------------------------

# Result
# ---------------------------------------------------------------------------
if [ -s "$ERRORS" ]; then
  OK=0
else
  OK=1
fi
RESULT=$(emit_result "$OK" "$STRICT")
write_result "$RESULT" "$JSON_OUT"
if [ "$OK" -eq 1 ]; then exit 0; else exit 1; fi
