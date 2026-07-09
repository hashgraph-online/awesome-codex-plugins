#!/usr/bin/env bash
# convert.sh — Cross-platform skill converter pipeline
# Usage: bash skills/converter/scripts/convert.sh <skill-dir> <target> [output-dir]
#        bash skills/converter/scripts/convert.sh --all <target> [output-dir]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SKILL_PATTERN=""
CODEX_LAYOUT="modular"
ARGS_SKILL_DIR_OR_FLAG=""
ARGS_TARGET=""
ARGS_OUTPUT_DIR=""

# ─── Helpers ───────────────────────────────────────────────────────────

die() { echo "ERROR: $*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage:
  bash skills/converter/scripts/convert.sh [--codex-layout modular|inline] <skill-dir> <target> [output-dir]
  bash skills/converter/scripts/convert.sh [--codex-layout modular|inline] --all <target> [output-dir]

Targets: codex, cursor, test

Examples:
  bash skills/converter/scripts/convert.sh skills/council codex
  bash skills/converter/scripts/convert.sh --codex-layout inline skills/council codex
  bash skills/converter/scripts/convert.sh --all codex
  bash skills/converter/scripts/convert.sh skills/vibe test /tmp/out
EOF
  exit 1
}

parse_args() {
  local positional=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --codex-layout)
        [[ $# -ge 2 ]] || die "--codex-layout requires a value: modular|inline"
        CODEX_LAYOUT="$2"
        shift 2
        ;;
      --codex-layout=*)
        CODEX_LAYOUT="${1#*=}"
        shift
        ;;
      --all)
        positional+=("--all")
        shift
        ;;
      -h|--help)
        usage
        ;;
      --)
        shift
        while [[ $# -gt 0 ]]; do
          positional+=("$1")
          shift
        done
        break
        ;;
      -*)
        die "Unknown flag: $1"
        ;;
      *)
        positional+=("$1")
        shift
        ;;
    esac
  done

  [[ "$CODEX_LAYOUT" == "modular" || "$CODEX_LAYOUT" == "inline" ]] \
    || die "Invalid --codex-layout '$CODEX_LAYOUT'. Expected: modular|inline"

  [[ ${#positional[@]} -ge 2 ]] || usage
  ARGS_SKILL_DIR_OR_FLAG="${positional[0]}"
  ARGS_TARGET="${positional[1]}"
  ARGS_OUTPUT_DIR="${positional[2]:-}"
}

yaml_escape_single_quote() {
  printf '%s' "$1" | sed "s/'/''/g"
}

# Build an alternation regex for all known skill names.
load_skill_pattern() {
  local names=()
  local d
  for d in "$REPO_ROOT"/skills/*/; do
    [[ -f "$d/SKILL.md" ]] || continue
    names+=("$(basename "$d")")
  done

  # Some command aliases are valid in docs even when no source skill directory
  # exists in this repo (for example, migrated or generated-only skills).
  # Keep these in the rewrite pattern so slash forms still convert to $ forms.
  names+=("knowledge" "learn" "extract" "inbox")

  if [[ ${#names[@]} -eq 0 ]]; then
    SKILL_PATTERN=""
    return
  fi

  local escaped=()
  local name
  for name in "${names[@]}"; do
    escaped+=("$(printf '%s' "$name" | sed -E 's/[][(){}.^$*+?|\\-]/\\&/g')")
  done
  SKILL_PATTERN="$(IFS='|'; printf '%s' "${escaped[*]}")"
}

# Rewrite Claude-style slash command references to Codex-style dollar references.
# Example: /plan -> $plan (for known skill names only).
codex_rewrite_text() {
  local input="$1"
  local output="$input"

  if [[ -n "$SKILL_PATTERN" ]]; then
    output="$(printf '%s' "$output" | SKILL_PATTERN="$SKILL_PATTERN" perl -0pe '
      my $pattern = qr/$ENV{SKILL_PATTERN}/;
      s{(?<![A-Za-z0-9_/])/($pattern)(?![A-Za-z0-9-])}{\$$1}g;
    ')"
  fi

  output="$(printf '%s' "$output" | perl -0pe '
    s/\bClaude[ ]Code\b/Codex/g;
    s/\bClaude[ ]Native[ ]Teams\b/Codex sub-agents/g;
    s/\bClaude[ ]native[ ]team\b/Codex sub-agent/g;
    s/\bClaude[ ]teams\b/Codex sub-agents/g;
    s/\bclaude[ ]teams\b/codex sub-agents/g;
    s/\bClaude[ ]session(s)?\b/Codex session$1/g;
    s/\bclaude[ ]session(s)?\b/codex session$1/g;
    s/\bClaude[ ]runtime\b/Codex runtime/g;
    s/\bclaude[ ]runtime\b/codex runtime/g;
    s/\bClaude[ ]workers\b/Codex workers/g;
    s/\bclaude[ ]workers\b/codex workers/g;
    s/\bclaude-native-teams\b/codex-sub-agents/g;
    s{~/.claude/skills/}{~/.agents/skills/}g;
    s{~/.claude/}{~/.codex/}g;
    s{\$HOME/.claude/}{\$HOME/.codex/}g;
    s{/.claude/}{/.codex/}g;
    s{\.claude/}{.codex/}g;
    s/backend-claude-teams\.md/backend-codex-subagents.md/g;
    s/\bclaude agents\b/codex agents/g;
    # Map Claude tools to Codex tools
    s/\bthe Read tool\b/read_file/g;
    s/\bthe Edit tool\b/apply_patch/g;
    s/\bthe Grep tool\b/rg/g;
    s/\bthe Glob tool\b/glob_file_search/g;
    s/\bAgent\(subagent_type="Explore"/spawn a sub-agent (explorer role/g;
    s/\bsubagent_type:\s*"Explore"/role: explorer/g;
    # Rewrite Skill() tool invocations to $skill syntax
    s/Skill\(skill="([^"]+)"(?:,\s*args="([^"]*)")?\)/\$$1 $2/g;
    # Strip lines with Claude primitives (no Codex equivalent — empirically verified)
    s/.*\b(?:TaskCreate|TaskUpdate|TaskList|TaskGet|TaskStop)\b.*\n?//g;
    s/.*\b(?:TeamCreate|TeamDelete)\b.*\n?//g;
    s/.*\b(?:SendMessage)\b.*\n?//g;
    s/.*\b(?:EnterPlanMode|ExitPlanMode|EnterWorktree)\b.*\n?//g;
    s/.*\*\*USE THE TASK TOOL\*\*.*\n?//g;
    s/.*\bTool:\s*Task\b.*\n?//g;
    # Post-rewrite dedup: collapse doubled runtime phrases
    s/Codex sub-agents in Codex sessions, Codex sub-agents in Codex sessions/Codex sub-agents in Codex sessions/g;
    s/Codex session -> Codex sub-agents; Codex session -> Codex sub-agents/Codex session -> Codex sub-agents/g;
  ')"

  printf '%s' "$output"
}

# Deduplicate semantically equivalent Codex runtime headings while preserving
# all section content. If multiple "In Codex" headings exist after rewrites,
# keep the first heading and drop subsequent duplicate heading lines.
codex_dedupe_runtime_headings() {
  local input="$1"
  printf '%s' "$input" | awk '
    function norm(line, t) {
      t = tolower(line)
      gsub(/^[[:space:]]*#+[[:space:]]*/, "", t)
      gsub(/^[[:space:]]*\*\*[[:space:]]*/, "", t)
      gsub(/[[:space:]]*\*\*[[:space:]]*$/, "", t)
      gsub(/[[:space:]]*:[[:space:]]*$/, "", t)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", t)
      return t
    }
    {
      key = norm($0)
      if (key == "in codex") {
        if (seen[key] == 1) {
          next
        }
        seen[key] = 1
      }
      print
    }
  '
}

# ─── Stage 1: Parse ───────────────────────────────────────────────────

# Parse SKILL.md frontmatter and body.
# Sets: BUNDLE_NAME, BUNDLE_DESC, BUNDLE_BODY, BUNDLE_FRONTMATTER
parse_skill_md() {
  local skill_md="$1"
  [[ -f "$skill_md" ]] || die "SKILL.md not found: $skill_md"

  local content
  content="$(<"$skill_md")"

  # Extract frontmatter (between first and second --- lines)
  local in_fm=0
  local fm_lines=()
  local body_lines=()
  local fm_ended=0
  local line_num=0

  while IFS= read -r line; do
    line_num=$((line_num + 1))
    if [[ $line_num -eq 1 && "$line" == "---" ]]; then
      in_fm=1
      continue
    fi
    if [[ $in_fm -eq 1 && "$line" == "---" ]]; then
      in_fm=0
      fm_ended=1
      continue
    fi
    if [[ $in_fm -eq 1 ]]; then
      fm_lines+=("$line")
    elif [[ $fm_ended -eq 1 ]]; then
      body_lines+=("$line")
    fi
  done <<< "$content"

  BUNDLE_FRONTMATTER="$(printf '%s\n' "${fm_lines[@]}")"

  # Extract name and description from frontmatter
  BUNDLE_NAME="$(echo "$BUNDLE_FRONTMATTER" | sed -n 's/^name: *//p' | tr -d "'" | tr -d '"')"
  BUNDLE_DESC="$(
    awk '
      BEGIN {
        capture = 0
        first = 1
      }
      /^description:[[:space:]]*[>|]-?[[:space:]]*$/ {
        capture = 1
        next
      }
      /^description:[[:space:]]*/ {
        sub(/^description:[[:space:]]*/, "", $0)
        gsub(/^'\''|'\''$/, "", $0)
        gsub(/^"|"$/, "", $0)
        print
        exit
      }
      capture {
        if ($0 ~ /^[^[:space:]]/ && $0 !~ /^$/) {
          exit
        }
        line = $0
        sub(/^[[:space:]]+/, "", line)
        if (line == "") {
          next
        }
        if (!first) {
          printf " "
        }
        printf "%s", line
        first = 0
      }
    ' <<< "$BUNDLE_FRONTMATTER"
  )"

  # Body: join with newlines
  BUNDLE_BODY="$(printf '%s\n' "${body_lines[@]}")"
}

# Collect files from a subdirectory into parallel arrays.
# Args: <dir> <array-name-names> <array-name-contents>
collect_files() {
  local dir="$1"
  local -n names_arr="$2"
  local -n contents_arr="$3"
  names_arr=()
  contents_arr=()

  if [[ -d "$dir" ]]; then
    local f _old_lc="${LC_ALL:-}"
    LC_ALL=C
    for f in "$dir"/*; do
      [[ -f "$f" ]] || continue
      names_arr+=("$(basename "$f")")
      contents_arr+=("$(<"$f")")
    done
    LC_ALL="${_old_lc}"
  fi
}

# Full parse: populate all BUNDLE_* variables and REF/SCRIPT arrays
parse_bundle() {
  local skill_dir="$1"
  parse_skill_md "$skill_dir/SKILL.md"
  collect_files "$skill_dir/references" REF_NAMES REF_CONTENTS
  collect_files "$skill_dir/scripts" SCRIPT_NAMES SCRIPT_CONTENTS
}

# ─── Stage 2: Convert ─────────────────────────────────────────────────

# Test target: emit SkillBundle as structured markdown
convert_test() {
  local out=""
  out+="# SkillBundle: ${BUNDLE_NAME}"$'\n\n'
  out+="## Name"$'\n\n'
  out+="${BUNDLE_NAME}"$'\n\n'
  out+="## Description"$'\n\n'
  out+="${BUNDLE_DESC}"$'\n\n'
  out+="## Frontmatter"$'\n\n'
  out+='```yaml'$'\n'
  out+="${BUNDLE_FRONTMATTER}"$'\n'
  out+='```'$'\n\n'
  out+="## Body"$'\n\n'
  out+="${BUNDLE_BODY}"$'\n\n'

  out+="## References (${#REF_NAMES[@]})"$'\n\n'
  local i
  for i in "${!REF_NAMES[@]}"; do
    out+="### ${REF_NAMES[$i]}"$'\n\n'
    out+='```'$'\n'
    out+="${REF_CONTENTS[$i]}"$'\n'
    out+='```'$'\n\n'
  done

  out+="## Scripts (${#SCRIPT_NAMES[@]})"$'\n\n'
  for i in "${!SCRIPT_NAMES[@]}"; do
    out+="### ${SCRIPT_NAMES[$i]}"$'\n\n'
    out+='```'$'\n'
    out+="${SCRIPT_CONTENTS[$i]}"$'\n'
    out+='```'$'\n\n'
  done

  CONVERTED_OUTPUT="$out"
  CONVERTED_FILENAME="bundle.md"
}

# Codex target: SKILL.md + prompt.md
# Codex may load these skills from ~/.codex/skills or from a native plugin cache.
# Description max 1024 chars, no hooks support, tool names pass through
convert_codex() {
  local desc="$BUNDLE_DESC"
  local body
  body="$(codex_rewrite_text "$BUNDLE_BODY")"
  body="$(codex_dedupe_runtime_headings "$body")"

  # Truncate description to 1024 chars at word boundary
  if [[ ${#desc} -gt 1024 ]]; then
    desc="${desc:0:1021}"
    # Trim to last word boundary (space)
    desc="${desc% *}..."
  fi
  desc="$(codex_rewrite_text "$desc")"
  local desc_escaped
  desc_escaped="$(yaml_escape_single_quote "$desc")"

  # ── Build SKILL.md ──
  local skill_md=""
  skill_md+="---"$'\n'
  skill_md+="name: ${BUNDLE_NAME}"$'\n'
  skill_md+="description: '${desc_escaped}'"$'\n'
  skill_md+="---"$'\n\n'
  skill_md+="${body}"$'\n'

  if [[ "$CODEX_LAYOUT" == "inline" ]]; then
    # Inline references as appended sections (legacy/portable mode)
    if [[ ${#REF_NAMES[@]} -gt 0 ]]; then
      skill_md+=$'\n'"---"$'\n\n'
      skill_md+="## References"$'\n\n'
      local i
      for i in "${!REF_NAMES[@]}"; do
        skill_md+="### ${REF_NAMES[$i]}"$'\n\n'
        skill_md+="$(codex_rewrite_text "${REF_CONTENTS[$i]}")"$'\n\n'
      done
    fi

    # Inline scripts as code blocks (legacy/portable mode)
    if [[ ${#SCRIPT_NAMES[@]} -gt 0 ]]; then
      skill_md+=$'\n'"---"$'\n\n'
      skill_md+="## Scripts"$'\n\n'
      local i
      for i in "${!SCRIPT_NAMES[@]}"; do
        # Detect language from extension
        local ext="${SCRIPT_NAMES[$i]##*.}"
        local lang=""
        case "$ext" in
          sh|bash) lang="bash" ;;
          py)      lang="python" ;;
          js)      lang="javascript" ;;
          ts)      lang="typescript" ;;
          *)       lang="$ext" ;;
        esac
        skill_md+="### ${SCRIPT_NAMES[$i]}"$'\n\n'
        skill_md+="\`\`\`${lang}"$'\n'
        skill_md+="$(codex_rewrite_text "${SCRIPT_CONTENTS[$i]}")"$'\n'
        skill_md+="\`\`\`"$'\n\n'
      done
    fi
  else
    # Modular mode: keep SKILL.md concise and reference copied resources.
    if [[ ${#REF_NAMES[@]} -gt 0 || ${#SCRIPT_NAMES[@]} -gt 0 ]]; then
      skill_md+=$'\n'"## Local Resources"$'\n\n'
      local i
      if [[ ${#REF_NAMES[@]} -gt 0 ]]; then
        skill_md+="### references/"$'\n\n'
        for i in "${!REF_NAMES[@]}"; do
          skill_md+="- [references/${REF_NAMES[$i]}](references/${REF_NAMES[$i]})"$'\n'
        done
        skill_md+=$'\n'
      fi
      if [[ ${#SCRIPT_NAMES[@]} -gt 0 ]]; then
        skill_md+="### scripts/"$'\n\n'
        for i in "${!SCRIPT_NAMES[@]}"; do
          skill_md+="- \`scripts/${SCRIPT_NAMES[$i]}\`"$'\n'
        done
        skill_md+=$'\n'
      fi
    fi
  fi

  # ── Build prompt.md ──
  local prompt_md=""
  prompt_md+="# ${BUNDLE_NAME}"$'\n\n'
  prompt_md+="${desc}"$'\n\n'
  prompt_md+="## Instructions"$'\n\n'
  prompt_md+="Load and follow the skill instructions from the sibling \`SKILL.md\` file for this skill."$'\n'
  if [[ "$CODEX_LAYOUT" == "modular" && ( ${#REF_NAMES[@]} -gt 0 || ${#SCRIPT_NAMES[@]} -gt 0 ) ]]; then
    prompt_md+="Then read local files in \`references/\` and \`scripts/\` when needed."$'\n'
  fi

  # Set primary output (SKILL.md)
  CONVERTED_OUTPUT="$skill_md"
  CONVERTED_FILENAME="SKILL.md"

  # Set secondary output (prompt.md)
  CONVERTED_OUTPUT_2="$prompt_md"
  CONVERTED_FILENAME_2="prompt.md"
}

# Cursor target: .mdc rule file with YAML frontmatter + optional mcp.json
# Cursor rules format: .cursor/rules/<name>.mdc (Cursor 0.40+)
# Max output size: 100KB (102400 bytes). References are budget-fitted.
CURSOR_MAX_BYTES=102400

convert_cursor() {
  local out=""

  # ── YAML frontmatter ──
  out+="---"$'\n'
  out+="description: ${BUNDLE_DESC}"$'\n'
  out+="globs: "$'\n'
  out+="alwaysApply: false"$'\n'
  out+="---"$'\n\n'

  # ── Body content ──
  out+="${BUNDLE_BODY}"$'\n'

  # ── Scripts as code blocks (included before references — smaller, higher value) ──
  if [[ ${#SCRIPT_NAMES[@]} -gt 0 ]]; then
    out+=$'\n'"## Scripts"$'\n\n'
    local i
    for i in "${!SCRIPT_NAMES[@]}"; do
      local ext="${SCRIPT_NAMES[$i]##*.}"
      local lang=""
      case "$ext" in
        sh|bash) lang="bash" ;;
        py)      lang="python" ;;
        js)      lang="javascript" ;;
        ts)      lang="typescript" ;;
        *)       lang="$ext" ;;
      esac
      out+="### ${SCRIPT_NAMES[$i]}"$'\n\n'
      out+="\`\`\`${lang}"$'\n'
      out+="${SCRIPT_CONTENTS[$i]}"$'\n'
      out+="\`\`\`"$'\n\n'
    done
  fi

  # ── Inline references (budget-fitted to stay under CURSOR_MAX_BYTES) ──
  if [[ ${#REF_NAMES[@]} -gt 0 ]]; then
    local current_size=${#out}
    local budget=$(( CURSOR_MAX_BYTES - current_size - 200 ))  # 200 byte margin for section header + omission note
    local ref_section=""
    local omitted=0
    local i

    ref_section+=$'\n'"## References"$'\n\n'
    for i in "${!REF_NAMES[@]}"; do
      local entry=""
      entry+="### ${REF_NAMES[$i]}"$'\n\n'
      entry+="${REF_CONTENTS[$i]}"$'\n\n'
      local entry_size=${#entry}

      if [[ $budget -ge $entry_size ]]; then
        ref_section+="$entry"
        budget=$(( budget - entry_size ))
      else
        omitted=$(( omitted + 1 ))
      fi
    done

    if [[ $omitted -gt 0 ]]; then
      ref_section+="*${omitted} reference(s) omitted to stay under 100KB size limit.*"$'\n\n'
      echo "WARN: ${BUNDLE_NAME}: omitted $omitted reference(s) to stay under 100KB" >&2
    fi

    out+="$ref_section"
  fi

  CONVERTED_OUTPUT="$out"
  CONVERTED_FILENAME="${BUNDLE_NAME}.mdc"

  # ── MCP detection: scan body + references for MCP server references ──
  # If skill content references MCP servers, generate a stub mcp.json
  local all_content="${BUNDLE_BODY}"
  local i
  for i in "${!REF_CONTENTS[@]}"; do
    all_content+=$'\n'"${REF_CONTENTS[$i]}"
  done

  if echo "$all_content" | grep -qiE '(mcpServers|mcp_server|"mcp"|mcp\.json)'; then
    CONVERTED_OUTPUT_2='{
  "mcpServers": {}
}'
    CONVERTED_FILENAME_2="mcp.json"
  fi
}

run_convert() {
  local target="$1"
  case "$target" in
    test)   convert_test ;;
    codex)  convert_codex ;;
    cursor) convert_cursor ;;
    *)      die "Unknown target: $target. Supported: codex, cursor, test" ;;
  esac
}

# ─── Stage 3: Write ───────────────────────────────────────────────────

copy_passthrough_resources() {
  local source_dir="$1"
  local output_dir="$2"
  local entry base

  # Preserve non-generated skill resources (e.g., templates/, assets/, schemas/,
  # examples/, agents/, and other auxiliary files) so converted skills retain
  # runnable/supporting artifacts beyond SKILL.md/prompt.md.
  while IFS= read -r -d '' entry; do
    base="$(basename "$entry")"

    case "$base" in
      SKILL.md|prompt.md)
        continue
        ;;
    esac

    # Copy and dereference symlinks to keep output plugin-compatible.
    if [[ -d "$entry" ]]; then
      # For directories (references/, scripts/, etc.), copy then rewrite .md files
      rsync -a --copy-links "$entry" "$output_dir"/
      local subdir="$output_dir/$base"
      if [[ -d "$subdir" ]]; then
        while IFS= read -r md_file; do
          local content
          content="$(<"$md_file")"
          local rewritten
          rewritten="$(codex_rewrite_text "$content")"
          if [[ "$rewritten" != "$content" ]]; then
            printf '%s\n' "$rewritten" > "$md_file"
          fi
        done < <(find "$subdir" -name '*.md' -type f 2>/dev/null)
      fi
    else
      rsync -a --copy-links "$entry" "$output_dir"/
      # Rewrite top-level .md files too (e.g., validation-contract.md)
      if [[ "$entry" == *.md ]]; then
        local out_file="$output_dir/$base"
        if [[ -f "$out_file" ]]; then
          local content
          content="$(<"$out_file")"
          local rewritten
          rewritten="$(codex_rewrite_text "$content")"
          if [[ "$rewritten" != "$content" ]]; then
            printf '%s\n' "$rewritten" > "$out_file"
          fi
        fi
      fi
    fi
  done < <(find "$source_dir" -mindepth 1 -maxdepth 1 -print0)
}

verify_passthrough_resources() {
  local source_dir="$1"
  local output_dir="$2"
  local entry base
  local missing=()

  while IFS= read -r -d '' entry; do
    base="$(basename "$entry")"
    case "$base" in
      SKILL.md|prompt.md)
        continue
        ;;
    esac

    if [[ ! -e "$output_dir/$base" ]]; then
      missing+=("$base")
    fi
  done < <(find "$source_dir" -mindepth 1 -maxdepth 1 -print0)

  if [[ ${#missing[@]} -gt 0 ]]; then
    die "Passthrough parity check failed for '$source_dir'; missing in output: ${missing[*]}"
  fi
}

write_output() {
  local output_dir="$1"
  local source_dir="$2"

  # Clean-write: delete target dir before writing
  if [[ -d "$output_dir" ]]; then
    rm -rf "$output_dir"
  fi
  mkdir -p "$output_dir"

  printf '%s\n' "$CONVERTED_OUTPUT" > "$output_dir/$CONVERTED_FILENAME"
  echo "OK: $output_dir/$CONVERTED_FILENAME"

  # Write secondary output if present (e.g., codex prompt.md)
  if [[ -n "${CONVERTED_OUTPUT_2:-}" && -n "${CONVERTED_FILENAME_2:-}" ]]; then
    printf '%s\n' "$CONVERTED_OUTPUT_2" > "$output_dir/$CONVERTED_FILENAME_2"
    echo "OK: $output_dir/$CONVERTED_FILENAME_2"
  fi

  copy_passthrough_resources "$source_dir" "$output_dir"
  verify_passthrough_resources "$source_dir" "$output_dir"
}

# ─── Main ─────────────────────────────────────────────────────────────

convert_one_skill() {
  local skill_dir="$1"
  local target="$2"
  local output_dir="$3"

  # Resolve skill_dir to absolute if relative
  if [[ "$skill_dir" != /* ]]; then
    skill_dir="$REPO_ROOT/$skill_dir"
  fi

  [[ -d "$skill_dir" ]] || die "Skill directory not found: $skill_dir"
  [[ -f "$skill_dir/SKILL.md" ]] || die "No SKILL.md in: $skill_dir"

  parse_bundle "$skill_dir"

  [[ -n "$BUNDLE_NAME" ]] || die "Failed to parse name from $skill_dir/SKILL.md"

  # Default output dir
  if [[ -z "$output_dir" ]]; then
    output_dir="$REPO_ROOT/.agents/converter/$target/$BUNDLE_NAME"
  elif [[ "$output_dir" != /* ]]; then
    output_dir="$REPO_ROOT/$output_dir"
  fi

  # Reset output variables
  CONVERTED_OUTPUT=""
  CONVERTED_FILENAME=""
  CONVERTED_OUTPUT_2=""
  CONVERTED_FILENAME_2=""

  run_convert "$target"
  write_output "$output_dir" "$skill_dir"
}

main() {
  parse_args "$@"

  local skill_dir_or_flag="$ARGS_SKILL_DIR_OR_FLAG"
  local target="$ARGS_TARGET"
  local output_dir="$ARGS_OUTPUT_DIR"

  load_skill_pattern

  if [[ "$skill_dir_or_flag" == "--all" ]]; then
    local skills_root="$REPO_ROOT/skills"
    local count=0
    for d in "$skills_root"/*/; do
      [[ -f "$d/SKILL.md" ]] || continue
      local sname
      sname="$(basename "$d")"
      local out="$output_dir"
      if [[ -n "$out" ]]; then
        # Per-skill subdir under the provided output dir
        if [[ "$out" != /* ]]; then
          out="$REPO_ROOT/$out/$sname"
        else
          out="$out/$sname"
        fi
      fi
      convert_one_skill "$d" "$target" "$out"
      count=$((count + 1))
    done
    echo "Converted $count skills to target '$target'"
  else
    convert_one_skill "$skill_dir_or_flag" "$target" "$output_dir"
  fi
}

main "$@"
