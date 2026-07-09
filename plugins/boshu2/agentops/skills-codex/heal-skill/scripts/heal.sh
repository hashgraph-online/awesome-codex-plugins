#!/usr/bin/env bash
# heal.sh — Detect and fix common skill hygiene issues.
# Usage: heal.sh [--check|--fix] [--strict] [skills/path ...]
# Exit 0 = clean (or findings in non-strict mode).
# Exit 1 = findings reported in --strict mode (or --fix with findings).

set -euo pipefail

MODE="check"
STRICT=0
TARGETS=()

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)  MODE="check";  shift ;;
    --fix)    MODE="fix";    shift ;;
    --strict) STRICT=1;      shift ;;
    *)        TARGETS+=("$1"); shift ;;
  esac
done

# Find repo root (location of skills/ directory). HEAL_REPO_ROOT overrides for
# fixture-driven tests (tests/scripts/heal-dispositions.bats); production derives
# it from the script location.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${HEAL_REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
SKILLS_ROOT="$REPO_ROOT/skills"

# If no targets, scan all skill dirs (skills/ and skills-codex/)
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  for d in "$REPO_ROOT"/skills/*/; do
    [[ -d "$d" ]] && TARGETS+=("${d%/}")
  done
  for d in "$REPO_ROOT"/skills-codex/*/; do
    [[ -d "$d" ]] && TARGETS+=("${d%/}")
  done
else
  # Normalize targets to absolute paths
  normalized=()
  for t in "${TARGETS[@]}"; do
    if [[ "$t" = /* ]]; then
      normalized+=("$t")
    else
      normalized+=("$REPO_ROOT/$t")
    fi
  done
  TARGETS=("${normalized[@]}")
fi

FINDINGS=0

report() {
  local code="$1" path="$2" msg="$3"
  # Show relative path from repo root
  local rel="${path#"$REPO_ROOT"/}"
  echo "[$code] $rel: $msg"
  FINDINGS=$((FINDINGS + 1))
}

# Extract YAML frontmatter value. Handles quoted and unquoted values.
get_frontmatter() {
  local file="$1" key="$2"

  # Validate frontmatter structure: file must start with --- and have a closing ---
  local first_line
  first_line="$(head -1 "$file")"
  if [[ "$first_line" != "---" ]]; then
    return 1
  fi
  if ! awk 'NR==1{next} /^---$/{found=1; exit} END{exit !found}' "$file"; then
    return 1
  fi

  # Read between first --- pair
  local in_fm=0 value=""
  while IFS= read -r line; do
    if [[ "$line" == "---" ]]; then
      if [[ $in_fm -eq 1 ]]; then break; fi
      in_fm=1
      continue
    fi
    if [[ $in_fm -eq 1 ]]; then
      # Match key at start of line (not indented = top-level)
      if [[ "$line" =~ ^${key}:\ *(.*) ]]; then
        value="${BASH_REMATCH[1]}"
        # Strip surrounding quotes
        value="${value#\"}"
        value="${value%\"}"
        value="${value#\'}"
        value="${value%\'}"
        echo "$value"
        return 0
      fi
    fi
  done < "$file"
  return 1
}

# Check if a references/ file is linked in SKILL.md (as a proper markdown link or Read instruction)
is_linked() {
  local skill_md="$1" ref_file="$2"
  # Check for markdown link pattern [text](references/file) or Read tool pattern referencing it
  # Also accept any non-backtick reference to the file path
  local ref_basename
  ref_basename="$(basename "$ref_file")"
  # Escape dots in filename for grep regex
  local ref_basename_escaped="${ref_basename//./\\.}"
  local ref_rel="references/$ref_basename"
  # Linked = appears in a markdown link or Read instruction (not just bare backtick)
  # Allow optional suffix after filename: anchors (#section), query strings, or closing paren
  if grep -qE "\]\(references/${ref_basename_escaped}[^)]*\)" "$skill_md" 2>/dev/null; then
    return 0
  fi
  if grep -qE "Read.*references/${ref_basename_escaped}" "$skill_md" 2>/dev/null; then
    return 0
  fi
  # Also accept if referenced via a relative path in some other link form
  if grep -qE "\(references/${ref_basename_escaped}[^)]*\)" "$skill_md" 2>/dev/null; then
    return 0
  fi
  return 1
}

# Fix: add missing name field to frontmatter
fix_missing_name() {
  local file="$1" dirname="$2"
  # Insert name: after first ---
  local tmp
  tmp="$(mktemp)"
  local first_fence=0
  while IFS= read -r line; do
    echo "$line" >> "$tmp"
    if [[ "$line" == "---" && $first_fence -eq 0 ]]; then
      first_fence=1
      echo "name: $dirname" >> "$tmp"
    fi
  done < "$file"
  /bin/cp "$tmp" "$file"
  rm -f "$tmp"
}

# Fix: add missing description field to frontmatter
fix_missing_desc() {
  local file="$1" dirname="$2"
  # Insert description after name line, or after first ---
  local tmp
  tmp="$(mktemp)"
  local inserted=0 first_fence=0
  while IFS= read -r line; do
    echo "$line" >> "$tmp"
    if [[ $inserted -eq 0 ]]; then
      if [[ "$line" =~ ^name: ]]; then
        echo "description: '$dirname skill'" >> "$tmp"
        inserted=1
      elif [[ "$line" == "---" && $first_fence -eq 0 ]]; then
        first_fence=1
      elif [[ "$line" == "---" && $first_fence -eq 1 && $inserted -eq 0 ]]; then
        # Closing fence without finding name — shouldn't happen but handle it
        :
      fi
    fi
  done < "$file"
  if [[ $inserted -eq 0 ]]; then
    # Fallback: insert after first ---
    tmp2="$(mktemp)"
    first_fence=0
    while IFS= read -r line; do
      echo "$line" >> "$tmp2"
      if [[ "$line" == "---" && $first_fence -eq 0 ]]; then
        first_fence=1
        echo "description: '$dirname skill'" >> "$tmp2"
      fi
    done < "$file"
    /bin/cp "$tmp2" "$file"
    rm -f "$tmp2"
  else
    /bin/cp "$tmp" "$file"
  fi
  rm -f "$tmp"
}

# Fix: correct name mismatch
fix_name_mismatch() {
  local file="$1" dirname="$2"
  local tmp
  tmp="$(mktemp)"
  local in_fm=0
  while IFS= read -r line; do
    if [[ "$line" == "---" ]]; then
      in_fm=$((1 - in_fm))
      echo "$line" >> "$tmp"
      continue
    fi
    if [[ $in_fm -eq 1 && "$line" =~ ^name:\ * ]]; then
      echo "name: $dirname" >> "$tmp"
    else
      echo "$line" >> "$tmp"
    fi
  done < "$file"
  /bin/cp "$tmp" "$file"
  rm -f "$tmp"
}

# Fix: convert bare backtick ref to markdown link
fix_unlinked_ref() {
  local file="$1" ref_rel="$2"
  local ref_basename
  ref_basename="$(basename "$ref_rel")"
  # Replace bare `references/foo.md` with [references/foo.md](references/foo.md)
  local tmp
  tmp="$(mktemp)"
  sed "s|\`${ref_rel}\`|[${ref_rel}](${ref_rel})|g" "$file" > "$tmp"
  /bin/cp "$tmp" "$file"
  rm -f "$tmp"
}

# Process each skill directory
for skill_dir in "${TARGETS[@]}"; do
  dirname="$(basename "$skill_dir")"
  skill_md="$skill_dir/SKILL.md"

  # Check 5: Empty directory (no SKILL.md)
  if [[ ! -f "$skill_md" ]]; then
    # Only report if directory is truly empty (no files at all) or just missing SKILL.md
    if [[ -z "$(ls -A "$skill_dir" 2>/dev/null)" ]]; then
      report "EMPTY_DIR" "$skill_dir" "Directory exists but no SKILL.md"
      if [[ "$MODE" == "fix" ]]; then
        rmdir "$skill_dir" 2>/dev/null || true
      fi
    fi
    continue
  fi

  # Check 1: Missing name
  if ! name="$(get_frontmatter "$skill_md" "name")"; then
    report "MISSING_NAME" "$skill_dir" "No name field in frontmatter"
    if [[ "$MODE" == "fix" ]]; then
      fix_missing_name "$skill_md" "$dirname"
    fi
    name=""
  fi

  # Check 2: Missing description
  if ! get_frontmatter "$skill_md" "description" >/dev/null 2>&1; then
    report "MISSING_DESC" "$skill_dir" "No description field in frontmatter"
    if [[ "$MODE" == "fix" ]]; then
      fix_missing_desc "$skill_md" "$dirname"
    fi
  fi

  # Check 2b: Missing metadata.tier
  if [[ "$skill_dir" != "$REPO_ROOT"/skills-codex/* ]] && ! grep -q '^\s*tier:' "$skill_md"; then
    report "MISSING_TIER" "$skill_dir" "No metadata.tier in frontmatter"
  fi

  # Check 2c: Invalid metadata.stability
  stability_val="$(awk '/^[[:space:]]*stability:/{sub(/^[[:space:]]*stability:[[:space:]]*/,""); gsub(/^["'"'"']|["'"'"']$/,""); print; exit}' "$skill_md" 2>/dev/null || true)"
  if [[ -n "$stability_val" && "$stability_val" != "experimental" && "$stability_val" != "stable" ]]; then
    report "H010" "$skill_dir" "Invalid metadata.stability '$stability_val' (must be 'experimental' or 'stable')"
  fi

  # Check 3: Name mismatch
  if [[ -n "$name" && "$name" != "$dirname" ]]; then
    report "NAME_MISMATCH" "$skill_dir" "Frontmatter name '$name' != directory '$dirname'"
    if [[ "$MODE" == "fix" ]]; then
      fix_name_mismatch "$skill_md" "$dirname"
    fi
  fi

  # Check 4: Unlinked references (.md files — strict markdown-link / Read form)
  if [[ -d "$skill_dir/references" ]]; then
    for ref_file in "$skill_dir"/references/*.md; do
      [[ -f "$ref_file" ]] || continue
      ref_basename="$(basename "$ref_file")"
      ref_rel="references/$ref_basename"
      if ! is_linked "$skill_md" "$ref_file"; then
        report "UNLINKED_REF" "$skill_dir" "$ref_rel not linked in SKILL.md"
        if [[ "$MODE" == "fix" ]]; then
          fix_unlinked_ref "$skill_md" "$ref_rel"
        fi
      fi
    done
  fi

  # Check 4b: Unreferenced non-.md references (.feature, .json, .txt, etc.)
  #
  # Mirrors the Go contract test TestSkillContract_ReferencesLinkedInSKILLMD
  # (cli/cmd/ao/skill_contract_test.go): EVERY top-level file in references/
  # (any extension, excluding dotfiles and subdirectories) must have its
  # basename appear somewhere in SKILL.md. The Go test gates go-build, which is
  # path-filtered to cli/** — so a skills-only PR that adds an unreferenced
  # .feature file (e.g. PRs #504/#505) skipped go-build and merged the breakage
  # onto main, only surfacing on the next cli/ PR (soc-oemfm).
  #
  # heal.sh (skill-integrity job) runs on skills/** changes, so checking the
  # same invariant here closes the gap on the right trigger. The rule mirrors
  # the Go test's permissive basename containment (NOT the stricter markdown-link
  # form used for .md above) so this gate and the Go test agree exactly.
  if [[ -d "$skill_dir/references" ]]; then
    for ref_file in "$skill_dir"/references/*; do
      [[ -f "$ref_file" ]] || continue
      ref_basename="$(basename "$ref_file")"
      # Skip dotfiles and .md files (.md handled by Check 4 above).
      [[ "$ref_basename" == .* ]] && continue
      [[ "$ref_basename" == *.md ]] && continue
      ref_rel="references/$ref_basename"
      # Mirror the Go test: basename must appear anywhere in SKILL.md.
      if ! grep -qF "$ref_basename" "$skill_md" 2>/dev/null; then
        report "UNREFERENCED_REF" "$skill_dir" "$ref_rel not referenced in SKILL.md"
      fi
    done
  fi

  # Check 5b: Malformed ..$X links (shell variable artifacts in markdown)
  if grep -qE '\.\.\$[A-Za-z]' "$skill_md"; then
    report "MALFORMED_LINK" "$skill_dir" "Contains ..\$X link artifact (should be ../X)"
  fi

  # Check 5c: Duplicate reference links within a single listing section.
  # A reference appearing in BOTH "Reference Documents" AND "Local Resources" is fine.
  # Only flag duplicates within the SAME section.
  for _heading in "Reference Documents" "Local Resources"; do
    ref_section="$(awk -v h="$_heading" '/^## /{if(index($0,h)>0){found=1; next} else if(found){exit}} found' "$skill_md")"
    if [[ -n "$ref_section" ]]; then
      dupes="$(echo "$ref_section" | grep -oE '\]\(references/[^)]+\)' | sort | uniq -d || true)"
      if [[ -n "$dupes" ]]; then
        report "DUPLICATE_REF" "$skill_dir" "Duplicate reference links in $_heading section: $dupes"
      fi
    fi
  done

  # Check 6: Dead references (SKILL.md mentions references/ files that don't exist)
  # Strip fenced code blocks before scanning to avoid false positives from examples
  # Supports local (references/foo.md), shared (../shared/references/foo.md), and
  # cross-skill (../<skill>/references/foo.md) paths
  while IFS= read -r ref_path; do
    [[ -z "$ref_path" ]] && continue
    if [[ ! -f "$skill_dir/$ref_path" ]]; then
      report "DEAD_REF" "$skill_dir" "SKILL.md references non-existent $ref_path"
      if [[ "$MODE" == "fix" ]]; then
        echo "  [WARN] Cannot auto-fix DEAD_REF -- manually remove or create $ref_path"
      fi
    fi
  done < <(awk 'BEGIN{skip=0} /^```/{skip=1-skip; next} skip==0{print}' "$skill_md" | grep -oE '(\.\./[A-Za-z0-9_.-]+/)?references/[A-Za-z0-9_.-]+\.md' 2>/dev/null | sort -u || true)

  # Check 7: Script reference integrity
  # Strip fenced code blocks and URLs before scanning to avoid false positives from examples
  # URLs containing scripts/foo.sh are remote references, not local file paths
  while IFS= read -r ref; do
    [[ -z "$ref" ]] && continue
    if [[ ! -f "$skill_dir/$ref" && ! -f "$REPO_ROOT/$ref" ]]; then
      report "SCRIPT_REF_MISSING" "$skill_dir" "references $ref but file not found"
    fi
  done < <(awk 'BEGIN{skip=0} /^```/{skip=1-skip; next} skip==0{print}' "$skill_md" | sed -E 's|https?://[^[:space:]`"]*||g' | grep -oE '\bscripts/[a-zA-Z0-9_-]+\.[a-z]+' 2>/dev/null | sort -u || true)

  # Check 8: CLI command validation (prefer repo binary over PATH)
  ao_bin=""
  ao_cmds=""
  commands_md="$REPO_ROOT/cli/docs/COMMANDS.md"
  if [[ -f "$commands_md" ]]; then
    ao_cmds="$(
      awk '
        /^### `ao [^`]+`/ {
          line=$0
          sub(/^### `ao /, "", line)
          sub(/`.*$/, "", line)
          split(line, parts, " ")
          print parts[1]
          next
        }
        /^\*\*Aliases:\*\*/ {
          in_aliases=1
          next
        }
        in_aliases && /^[[:space:]]*[a-z][a-z,-]+/ {
          gsub(/,/, " ")
          for (i = 1; i <= NF; i++) print $i
          in_aliases=0
          next
        }
        in_aliases && /^### / {
          in_aliases=0
        }
      ' "$commands_md" 2>/dev/null \
        | sort -u || true
    )"
  fi
  if [[ -z "$ao_cmds" && -x "$REPO_ROOT/cli/bin/ao" ]]; then
    ao_bin="$REPO_ROOT/cli/bin/ao"
  elif command -v ao >/dev/null 2>&1; then
    ao_bin="$(command -v ao)"
  fi
  if [[ -z "$ao_cmds" && -n "$ao_bin" ]]; then
    ao_cmds="$("$ao_bin" help 2>&1 | grep -oE '^[[:space:]]+[a-z][-a-z]*' | tr -d ' ' | sort -u || true)"
    # Guard: skip if binary produced no commands (broken build)
    [[ -z "$ao_cmds" ]] && ao_bin=""
  fi
  if [[ -n "$ao_cmds" ]]; then
    while IFS= read -r subcmd; do
      [[ -z "$subcmd" ]] && continue
      if ! echo "$ao_cmds" | grep -qx "$subcmd"; then
        report "INVALID_AO_CMD" "$skill_dir" "references 'ao $subcmd' which is not a valid subcommand"
      fi
    done < <(grep -oE '`ao [a-z][-a-z]*`' "$skill_md" 2>/dev/null | sed 's/`//g; s/^ao //' | sort -u || true)
  fi

  # Check 9: Cross-reference validation (skill invocation references)
  # Strip fenced code blocks before scanning to avoid false positives from examples
  while IFS= read -r ref; do
    [[ -z "$ref" ]] && continue
    # Skip common filesystem path false positives
    case "$ref" in
      dev|tmp|usr|bin|etc|opt|var|home|proc|sys|path|null|dev/null|skill-name) continue ;;
      agents|hooks|mcp|memory|output-style|permissions|allowed-tools|approved-tools|health|healthz|readyz|name) continue ;;
      # Built-in CLI / Codex slash-commands that are deliberately NOT AgentOps
      # skills: /clear (Claude built-in), /goal (Codex --codex-goal flow), /skill
      # (the generic Skill tool). Referencing them is correct, not a dead xref.
      clear|goal|skill|help|compact) continue ;;
    esac
    if [[ ! -d "$SKILLS_ROOT/$ref" ]]; then
      report "DEAD_XREF" "$skill_dir" "references /$ref but skill directory not found"
    fi
  done < <(awk 'BEGIN{skip=0} /^```/{skip=1-skip; next} skip==0{print}' "$skill_md" | grep -oE '`/[a-z][-a-z]*`' 2>/dev/null | sed 's/`//g; s|^/||' | sort -u || true)

done

# Check 10 (CATALOG_MISSING) was removed: it only ran when
# skills/using-agentops/SKILL.md existed, and that skill no longer exists, so
# the check was permanently dead. Catalog completeness is gated by Check 12
# (MISSING_DISPOSITION) against docs/contracts/skill-dispositions.yaml.

# Check 11: skill_api_version presence (global, not per-skill)
for skill_check in "$SKILLS_ROOT"/*/SKILL.md; do
  [[ -f "$skill_check" ]] || continue
  check_dir="$(dirname "$skill_check")"
  check_name="$(basename "$check_dir")"
  if ! get_frontmatter "$skill_check" "skill_api_version" >/dev/null 2>&1; then
    report "MISSING_API_VERSION" "$check_dir" "No skill_api_version field in frontmatter"
    if [[ "$MODE" == "fix" ]]; then
      # Insert skill_api_version: 1 after description: line
      tmp="$(mktemp)"
      inserted=0
      while IFS= read -r line; do
        echo "$line" >> "$tmp"
        if [[ $inserted -eq 0 && "$line" =~ ^description: ]]; then
          echo "skill_api_version: 1" >> "$tmp"
          inserted=1
        fi
      done < "$skill_check"
      /bin/cp "$tmp" "$skill_check"
      rm -f "$tmp"
    fi
  fi
done

# Check 12: Dispositions coverage (global, not per-skill). Every user-invocable
# skills/<n> must have a row in docs/contracts/skill-dispositions.yaml. This is
# the gate that silently passed when /burndown (ag-3yl8 #600) was added, costing
# a CI round — heal --strict now catches it locally (ag-cw2y item 1).
DISPOSITIONS_FILE="$REPO_ROOT/docs/contracts/skill-dispositions.yaml"
if [[ -f "$DISPOSITIONS_FILE" ]]; then
  for skill_check in "$SKILLS_ROOT"/*/SKILL.md; do
    [[ -f "$skill_check" ]] || continue
    check_dir="$(dirname "$skill_check")"
    check_name="$(basename "$check_dir")"
    # Skip internal/non-invocable skills (same exemptions as catalog check).
    if grep -q 'user-invocable: false' "$skill_check" 2>/dev/null; then continue; fi
    if grep -q 'internal: true' "$skill_check" 2>/dev/null; then continue; fi
    if ! grep -qE "^[[:space:]]*-[[:space:]]+skill:[[:space:]]+${check_name}[[:space:]]*$" "$DISPOSITIONS_FILE" 2>/dev/null; then
      report "MISSING_DISPOSITION" "$check_dir" "user-invocable but has no row in docs/contracts/skill-dispositions.yaml"
    fi
  done
fi

if [[ $FINDINGS -gt 0 ]]; then
  echo ""
  echo "$FINDINGS finding(s) detected."
  if [[ $STRICT -eq 1 || "$MODE" == "fix" ]]; then
    exit 1
  fi
  exit 0
else
  echo "All clean. No findings."
  exit 0
fi
