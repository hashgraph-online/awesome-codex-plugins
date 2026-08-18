#!/usr/bin/env bash
# capture_cli_help.sh — Recursively capture --help output from a CLI binary.
#
# Usage: capture_cli_help.sh <binary_path> <out_dir>
#
# Writes:
#   <out_dir>/cli-help-tree.txt   — Structured help output per command/subcommand
#   <out_dir>/cli-commands.txt    — One command path per line
#
# Constraints:
#   - 5-second timeout per invocation
#   - 120-second total execution cap
#   - Max recursion depth: 3
#   - Exit 0 always (best-effort)

set -euo pipefail

BINARY_PATH="${1:?Usage: capture_cli_help.sh <binary_path> <out_dir>}"
OUT_DIR="${2:?Usage: capture_cli_help.sh <binary_path> <out_dir>}"

BINARY_NAME="$(basename "$BINARY_PATH")"
PER_CMD_TIMEOUT=5
TOTAL_TIMEOUT=120
MAX_DEPTH=3

# Help-like keywords that indicate valid help output.
HELP_KEYWORDS="Usage|Commands|Available|Flags|Options|usage|commands|available|flags|options|USAGE|COMMANDS|AVAILABLE|FLAGS|OPTIONS|help|HELP|Synopsis|SYNOPSIS|Arguments|ARGUMENTS"

# Resolve timeout command (GNU coreutils `timeout` or macOS `gtimeout`).
TIMEOUT_CMD=""
if command -v timeout &>/dev/null; then
    TIMEOUT_CMD="timeout"
elif command -v gtimeout &>/dev/null; then
    TIMEOUT_CMD="gtimeout"
fi

mkdir -p "$OUT_DIR"

TREE_FILE="$OUT_DIR/cli-help-tree.txt"
CMDS_FILE="$OUT_DIR/cli-commands.txt"
SEEN_PATHS_FILE="$OUT_DIR/.seen-command-paths.tmp"
VISITED_PREFIX_FILE="$OUT_DIR/.visited-prefixes.tmp"

# Start fresh.
: > "$TREE_FILE"
: > "$CMDS_FILE"
: > "$SEEN_PATHS_FILE"
: > "$VISITED_PREFIX_FILE"

# Track total elapsed time.
START_TIME="$(date +%s)"

elapsed() {
    local now
    now="$(date +%s)"
    echo $(( now - START_TIME ))
}

budget_exceeded() {
    [ "$(elapsed)" -ge "$TOTAL_TIMEOUT" ]
}

# Run a command with per-invocation timeout. Captures stdout+stderr.
# Returns the output; exit code 0 on success, non-zero on timeout/failure.
run_with_timeout() {
    if [ -n "$TIMEOUT_CMD" ]; then
        "$TIMEOUT_CMD" "$PER_CMD_TIMEOUT" "$@" 2>&1 || true
    else
        # Fallback: no timeout command available, just run it.
        "$@" 2>&1 || true
    fi
}

# Check if text looks like help output.
looks_like_help() {
    local text="$1"
    if [ -z "$text" ]; then
        return 1
    fi
    if echo "$text" | grep -qE "$HELP_KEYWORDS"; then
        return 0
    fi
    return 1
}

seen_contains() {
    local file="$1"
    local key="$2"
    grep -Fqx -- "$key" "$file" 2>/dev/null
}

seen_add() {
    local file="$1"
    local key="$2"
    printf '%s\n' "$key" >> "$file"
}

record_command_path() {
    local path="$1"
    [ -z "$path" ] && return 0
    if seen_contains "$SEEN_PATHS_FILE" "$path"; then
        return 0
    fi
    seen_add "$SEEN_PATHS_FILE" "$path"
    echo "$path" >> "$CMDS_FILE"
}

extract_usage_path() {
    local help_text="$1"
    local usage_line
    usage_line="$(echo "$help_text" | awk '
        /^Usage:/ {
            line=$0
            sub(/^Usage:[[:space:]]*/, "", line)
            if (line != "") {
                print line
                exit
            }
            in_usage=1
            next
        }
        in_usage {
            if ($0 ~ /^[[:space:]]*$/) {
                in_usage=0
                next
            }
            line=$0
            sub(/^[[:space:]]+/, "", line)
            if (line != "") {
                print line
                exit
            }
        }
    ')"
    [ -z "$usage_line" ] && return 0
    echo "$usage_line" | awk '
        {
            out=""
            for (i=1; i<=NF; i++) {
                t=$i
                first = substr(t, 1, 1)
                if (first == "[" || first == "<" || first == "-" || first == "(" || first == "{") break
                out = (out ? out " " : "") t
            }
            print out
        }
    '
}

# Extract subcommand names from help output.
# Looks for lines after "Commands:" or "Available Commands:" header,
# matching pattern: leading whitespace, then a word (the subcommand name).
extract_subcommands() {
    local help_text="$1"
    local in_commands_section=0
    local subcmds=()

    while IFS= read -r line; do
        # Detect start of commands section.
        if echo "$line" | grep -qiE '^\s*(Available\s+)?Commands\s*:'; then
            in_commands_section=1
            continue
        fi

        if [ "$in_commands_section" -eq 1 ]; then
            # Empty line or a new section header ends the commands block.
            if [ -z "$line" ] || echo "$line" | grep -qE '^[A-Z].*:$'; then
                in_commands_section=0
                continue
            fi
            # Extract the first word (subcommand name) from indented lines.
            local cmd
            cmd="$(echo "$line" | sed -n 's/^[[:space:]]\{1,\}\([a-zA-Z0-9_-]\{1,\}\)[[:space:]].*/\1/p')"
            if [ -n "$cmd" ]; then
                # Skip common non-command words that appear in help sections.
                case "$cmd" in
                    help|completion) ;;  # skip meta-commands
                    *) subcmds+=("$cmd") ;;
                esac
            fi
        fi
    done <<< "$help_text"

    # Output one per line.
    for sc in "${subcmds[@]+"${subcmds[@]}"}"; do
        echo "$sc"
    done
}

# Recursive help capture.
# Args: depth cmd_prefix args...
#   depth      — current recursion depth (0-based)
#   cmd_prefix — display prefix for tree (e.g., "forge transcript")
#   args...    — actual command + args to run
capture_help() {
    local depth="$1"; shift
    local cmd_prefix="$1"; shift
    # Remaining args are the command to execute.
    if seen_contains "$VISITED_PREFIX_FILE" "$cmd_prefix"; then
        return 0
    fi
    seen_add "$VISITED_PREFIX_FILE" "$cmd_prefix"

    if budget_exceeded; then
        return 0
    fi

    if [ "$depth" -gt "$MAX_DEPTH" ]; then
        return 0
    fi

    local help_output
    help_output="$(run_with_timeout "$@" --help)"

    if ! looks_like_help "$help_output"; then
        if [ "$depth" -eq 0 ]; then
            # Top-level binary doesn't produce help. Write note and bail.
            echo "# CLI Help Tree" >> "$TREE_FILE"
            echo "" >> "$TREE_FILE"
            echo "NOTE: $BINARY_NAME --help did not produce recognizable help output." >> "$TREE_FILE"
        fi
        return 0
    fi

    # Write to tree file.
    echo "## $cmd_prefix" >> "$TREE_FILE"
    echo "" >> "$TREE_FILE"
    echo "$help_output" >> "$TREE_FILE"
    echo "" >> "$TREE_FILE"

    # Resolve canonical path from Usage: for alias handling and de-noising.
    local usage_path=""
    usage_path="$(extract_usage_path "$help_output" || true)"

    # Write to commands file (skip top-level binary name alone).
    if [ "$depth" -gt 0 ]; then
        # Strip first token (binary executable/command name) to compare subcommand paths robustly.
        local subcmd_path="${cmd_prefix#* }"
        local canonical_subcmd_path=""
        if [ -n "$usage_path" ] && [ "$usage_path" != "${usage_path#* }" ]; then
            canonical_subcmd_path="${usage_path#* }"
        fi
        if [ -n "$canonical_subcmd_path" ]; then
            record_command_path "$canonical_subcmd_path"
        else
            record_command_path "$subcmd_path"
        fi

        # If Usage path subcommands differ from invocation subcommands, this likely hit
        # an alias/help redirect. Stop recursion to avoid fake paths like "mail inbox inbox".
        if [ -n "$canonical_subcmd_path" ] && [ "$canonical_subcmd_path" != "$subcmd_path" ]; then
            return 0
        fi
    fi

    # Extract and recurse into subcommands.
    local subcmds
    subcmds="$(extract_subcommands "$help_output")"
    if [ -z "$subcmds" ]; then
        return 0
    fi

    while IFS= read -r subcmd; do
        [ -z "$subcmd" ] && continue
        if budget_exceeded; then
            return 0
        fi
        capture_help "$(( depth + 1 ))" "$cmd_prefix $subcmd" "$@" "$subcmd"
    done <<< "$subcmds"
}

# Write tree header.
echo "# CLI Help Tree" >> "$TREE_FILE"
echo "" >> "$TREE_FILE"

# Start recursive capture from the top-level binary.
capture_help 0 "$BINARY_NAME" "$BINARY_PATH"

# If commands file is empty but tree has content, write the top-level command.
if [ ! -s "$CMDS_FILE" ] && [ -s "$TREE_FILE" ]; then
    # No subcommands found; the binary itself is the only entry.
    : # cli-commands.txt stays empty — top-level is implicit.
fi

exit 0
