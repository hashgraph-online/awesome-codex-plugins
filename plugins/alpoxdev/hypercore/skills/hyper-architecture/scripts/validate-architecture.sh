#!/usr/bin/env bash
# Validate the structure of the hyper-architecture skill folder: every stack guide
# routed from SKILL.md and rules/stack-detection.md exists with its rule set, every
# local path a Markdown file points at resolves, every English file has its Korean
# sibling, code fences balance, guides stay within their size caps, eval fixtures and
# JSON setup templates parse.
#
# Usage: bash skills/hyper-architecture/scripts/validate-architecture.sh [--root <skill-dir>]
# Run from the repository root. Requires bash 3.2+ and jq 1.6+.
# Prints one JSON summary on success (exit 0); prints every failure to stderr (exit 1).
set -euo pipefail

root_arg='skills/hyper-architecture'
while [ "$#" -gt 0 ]; do
  case $1 in
    --root)
      [ "$#" -ge 2 ] || { echo 'usage: validate-architecture.sh [--root <skill-dir>]' >&2; exit 2; }
      root_arg=$2
      shift 2
      ;;
    *)
      echo "usage: validate-architecture.sh [--root <skill-dir>] (unknown argument: $1)" >&2
      exit 2
      ;;
  esac
done

errors=()
add_error() { errors+=("$1"); }

fail_now() {
  echo 'hyper-architecture validation failed:' >&2
  local e
  for e in "$@"; do echo "- $e" >&2; done
  exit 1
}

[ -d "$root_arg" ] || fail_now "skill root not found: $root_arg"
root=$(cd "$root_arg" && pwd -P)
[ -f "$root/SKILL.md" ] || fail_now "SKILL.md not found under $root_arg"
[ -f "$root/rules/stack-detection.md" ] || fail_now "rules/stack-detection.md not found under $root_arg"

line_count() { # $1 = file
  awk 'END { print NR }' "$1"
}

# --- stacks: directories, routing table, detection table -----------------------
stacks=()
while IFS= read -r dir; do
  [ -n "$dir" ] || continue
  stacks+=("$(basename "$dir")")
done < <(find "$root/stacks" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | LC_ALL=C sort)
[ "${#stacks[@]}" -gt 0 ] || add_error 'no stack guide directories under stacks/'

skill_text=$(cat "$root/SKILL.md")
detection_text=$(cat "$root/rules/stack-detection.md")
for stack in ${stacks[@]+"${stacks[@]}"}; do
  for rel in "stacks/$stack/core.md" "stacks/$stack/core.ko.md" \
    "stacks/$stack/architecture-rules.md" "stacks/$stack/architecture-rules.ko.md" \
    "rules/$stack/performance.md" "rules/$stack/performance.ko.md" \
    "assets/evals/$stack-cases.jsonl"; do
    [ -e "$root/$rel" ] || add_error "stack $stack missing $rel"
  done
  case $skill_text in
    *"stacks/$stack/core.md"*) ;;
    *) add_error "SKILL.md routing table does not route to stacks/$stack/core.md" ;;
  esac
  case $detection_text in
    *"stacks/$stack/core.md"*) ;;
    *) add_error "rules/stack-detection.md has no detection row for stacks/$stack/core.md" ;;
  esac
done

# Every stack guide the router names must exist.
while IFS= read -r routed; do
  [ -n "$routed" ] || continue
  [ -e "$root/$routed" ] || add_error "SKILL.md routes to a missing guide: $routed"
done < <(printf '%s' "$skill_text" | grep -oE 'stacks/[a-z0-9-]+/core\.md' | LC_ALL=C sort -u)

# --- size caps -------------------------------------------------------------------
n=$(line_count "$root/SKILL.md")
[ "$n" -le 500 ] || add_error "SKILL.md too long: $n lines > 500"
for stack in ${stacks[@]+"${stacks[@]}"}; do
  f="$root/stacks/$stack/core.md"
  [ -f "$f" ] || continue
  n=$(line_count "$f")
  [ "$n" -le 300 ] || add_error "stacks/$stack/core.md too long: $n lines > 300"
done

# --- markdown files: Korean siblings, fences, local paths -------------------------
md_files=()
while IFS= read -r f; do
  [ -n "$f" ] || continue
  md_files+=("$f")
done < <(find "$root" -type f -name '*.md' ! -type l | LC_ALL=C sort)

resolve_from() { # $1 = base dir, $2 = relative path -> prints normalized absolute path
  printf '%s/%s\n' "$1" "$2" | awk -F/ '
    {
      n = 0
      for (i = 1; i <= NF; i++) {
        p = $i
        if (p == "" || p == ".") continue
        if (p == "..") { if (n > 0) n--; continue }
        parts[++n] = p
      }
      out = ""
      for (i = 1; i <= n; i++) out = out "/" parts[i]
      print (out == "" ? "/" : out)
    }'
}

for file in ${md_files[@]+"${md_files[@]}"}; do
  rel=${file#"$root"/}
  dir=$(dirname "$file")

  case $rel in
    *.ko.md)
      en=${file%.ko.md}.md
      [ -e "$en" ] || add_error "$rel has no English canonical ${rel%.ko.md}.md"
      ;;
    *)
      [ -e "${file%.md}.ko.md" ] || add_error "$rel missing Korean sibling ${rel%.md}.ko.md"
      ;;
  esac

  fences=$(grep -cE '^[[:space:]]*```' "$file" || true)
  [ $((fences % 2)) -eq 0 ] || add_error "$rel has unbalanced code fences"

  # @-imports resolve relative to the importing file.
  while IFS= read -r target; do
    [ -n "$target" ] || continue
    [ -e "$(resolve_from "$dir" "$target")" ] || add_error "$rel imports a missing file: @$target"
  done < <(grep -oE '^@[^[:space:]]+\.md$' "$file" | sed 's/^@//' || true)

  # Markdown links resolve relative to the linking file.
  while IFS= read -r target; do
    [ -n "$target" ] || continue
    case $target in
      http:* | https:* | mailto:* | '#'*) continue ;;
    esac
    target=${target%%#*}
    [ -n "$target" ] || continue
    [ -e "$(resolve_from "$dir" "$target")" ] || add_error "$rel links to a missing file: $target"
  done < <(grep -oE '\]\([^) ]+\)' "$file" | sed -E 's/^\]\((.*)\)$/\1/' || true)

  # Backticked skill-root paths (rules/, stacks/, references/, assets/, scripts/) resolve
  # from the skill root. Placeholders and globs are not paths.
  while IFS= read -r target; do
    [ -n "$target" ] || continue
    case $target in
      *'<'* | *'*'* | *'{'* | *'['*) continue ;;
    esac
    target=$(printf '%s' "$target" | sed -E 's/:[0-9][0-9,-]*$//')
    [ -e "$root/$target" ] || add_error "$rel names a missing skill path: $target"
  done < <(grep -oE '`(rules|stacks|references|assets|scripts)/[^`[:space:]]+`' "$file" | tr -d '`' | LC_ALL=C sort -u || true)
done

# --- eval fixtures -------------------------------------------------------------------
eval_files=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  eval_files=$((eval_files + 1))
  rel=${f#"$root"/}
  lineno=0
  while IFS= read -r line || [ -n "$line" ]; do
    lineno=$((lineno + 1))
    [ -n "$line" ] || continue
    if ! printf '%s' "$line" | jq -e 'type == "object" and (.id | type == "string") and (.category | type == "string") and (.prompt | type == "string")' >/dev/null 2>&1; then
      add_error "$rel line $lineno is not an eval case with string id, category, and prompt"
    fi
  done <"$f"
done < <(find "$root/assets/evals" -type f -name '*.jsonl' 2>/dev/null | LC_ALL=C sort)

# --- JSON setup templates ---------------------------------------------------------------
template_files=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  template_files=$((template_files + 1))
  jq -e . "$f" >/dev/null 2>&1 || add_error "${f#"$root"/} is not valid JSON"
done < <(find "$root/assets/templates" -type f -name '*.json' 2>/dev/null | LC_ALL=C sort)

if [ "${#errors[@]}" -ne 0 ]; then
  fail_now "${errors[@]}"
fi

printf '%s\n' ${stacks[@]+"${stacks[@]}"} | jq -R . | jq -s \
  --argjson markdown "${#md_files[@]}" \
  --argjson evals "$eval_files" \
  --argjson templates "$template_files" \
  '{ok: true, stacks: ., checkedMarkdownFiles: $markdown, checkedEvalFiles: $evals, checkedJsonTemplates: $templates, checks: ["stack-files", "routing-table", "detection-table", "size-caps", "korean-siblings", "code-fences", "local-paths", "eval-fixtures", "json-templates"]}'
